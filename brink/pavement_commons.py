# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
"""
Shared pavement methods used in Chevah project.

This file is copied into the root of each repo as pavement_lib.py

Brace yoursef for watching how wheels are reinvented.

Do not modify this file inside the branch.


A `product` is a repository delived to customers or a library.
A `project` is a collection of products.

This scripts assume that you have dedicated folder for the project, and
inside the project folder, there is one folder for each products.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )

import getpass
import os
import sys
import subprocess

from paver.easy import call_task, cmdopts, task, pushd, needs
from paver.tasks import BuildFailure, environment, help, consume_args

from brink.configuration import SETUP, DIST_EXTENSION, DIST_TYPE
from brink.utils import BrinkPaver
from brink.qm import (
    github,
    merge_init,
    merge_commit,
    pqm,
    rqm,
    publish,
    )


pave = BrinkPaver(setup=SETUP)


class MD5SumFile(object):
    """
    A file storing md5 checksums for files.
    """

    def __init__(self, segments):
        """
        Initialize by creating an empty file.
        """
        self._segments = segments
        pave.fs.createEmptyFile(target=self._segments)

    def addFile(self, file_path):
        """
        Add file to file listed in md5 file.
        """
        content = pave.createMD5Sum([file_path]) + '  ' + file_path + '\n'
        pave.fs.appendContentToFile(
            destination=self._segments, content=content)


@task
@cmdopts([
    ('all', 'a', 'Run linter for all changed files.'),
    ('branch=', 'b', 'Name of the branch for which test is executed.'),
    ])
def lint(options):
    """
    Run static code checks for files that were changed.
    """
    all = pave.getOption(options, 'lint', 'all', default_value=False)
    branch_name = pave.getOption(
        options, 'lint', 'branch', default_value=None)

    options = SETUP['scame']

    # If branch name was not specified from command line, try to get it from
    # environment or from the current branch.
    if not branch_name:
        branch_name = os.environ.get('BRANCH', None)
    if not branch_name:
        branch_name = pave.git.branch_name

    pocket_lint_result = pave.scame(
        quick=not all,
        branch_name=branch_name,
        options=options,
        )

    if pocket_lint_result > 0:
        raise BuildFailure('Lint failed.')

    towncrier_options = options.towncrier
    if not towncrier_options['enabled']:
        return 0

    release_notes = towncrier_options['fragments_directory']
    is_release_series_branch = (
        branch_name in ['master', 'trunk'] or
        branch_name.startswith('series-')
        )
    if release_notes and not is_release_series_branch:
        # This repo has managed release notes.
        members = pave.fs.listFolder(release_notes)

        if '-release-' in branch_name:
            # Check that release notes have all fragments published.
            ignored_files = towncrier_options['excluded_fragments']
            fragments = [m for m in members if m.lower() not in ignored_files]
            if fragments:
                raise BuildFailure(
                    u'Branch name hint it is a release branch. '
                    u'It has unpublished release notes. %s' % (fragments,))
        else:
            # Check that it has release notes fragment.
            ticket_id = branch_name.split('-', 1)[0]
            ticket_mark = '%s.' % (ticket_id,)
            has_fragment = False
            for member in members:
                if member.startswith(ticket_mark):
                    has_fragment = True
            if not has_fragment:
                raise BuildFailure(
                    u'No release notes fragment for %s' % (ticket_id,))

    return 0


@task
def default():
    '''
    Default task. Shows this help.
    '''
    environment.args = []
    help()


@task
def deps():
    """Copy external dependencies.

    Each project should define custom deps_runtime and deps_builtime
    targets.
    """
    pave.installBuildDependencies()


@task
@needs('build')
@consume_args
def test_normal(args):
    """
    Run the test suite as regular user.
    """
    exit_code = run_test(
        python_command=pave.python_command_normal,
        switch_user='-',
        arguments=args,
        )

    if exit_code != 0:
        sys.exit(exit_code)
    return exit_code


@task
@needs('build')
@consume_args
def test_super(args):
    """
    Run the test suite as root user.
    """
    exit_code = run_test(
        python_command=pave.python_command_super,
        switch_user=getpass.getuser(),
        arguments=args,
        )

    if exit_code != 0:
        sys.exit(exit_code)
    return exit_code


@needs('build')
@consume_args
def test_python(args):
    """
    Execute Python tests.
    """
    super_result = 0

    default_arguments = SETUP['test']['nose_options']
    call_arguments = []

    # Filter empty arguments that might be generated by buildbot.
    args = [arg for arg in args if arg]

    empty_args = False
    if not len(args):
        empty_args = True
        call_arguments = default_arguments[:]

    call_arguments.append('-s')
    call_arguments.extend(args)

    if empty_args:
        call_arguments.append('--exclude=(elevated|selenium)')
        environment.args = call_arguments
        normal_result = test_normal(call_arguments)
        call_arguments.pop()

        if SETUP['test']['elevated']:
            environment.args = [SETUP['test']['elevated']]
            environment.args.extend(call_arguments)
            super_result = test_super(call_arguments)
    else:
        normal_result = test_normal(call_arguments)

        run_elevated = False
        if SETUP['test']['elevated']:
            for arg in args:
                if arg.startswith(SETUP['test']['elevated']):
                    run_elevated = True
                    break
        if run_elevated:
            super_result = test_super(call_arguments)

    if not (normal_result == 0 and super_result == 0):
        sys.exit(1)


@task
# Args are required to trigger environment creation.
@consume_args
def test_review(args):
    """
    Run test suite for review process.
    """
    result = pave.git.status()
    if result:
        print('Please commit all files before requesting the release.')
        print('Aborted.')
        sys.exit(1)

    arguments = ['gk-review']

    if args:
        pull_id = args[0]
        arguments.append('--properties=github_pull_id=%s' % (pull_id,))

    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)


@consume_args
def test_os_dependent(args):
    """
    Execute all tests.
    """
    call_task('test_python', args=args)

    # Only publish coverage for os dependent tests.
    codecov_token = os.environ.get('CODECOV_TOKEN', '')
    if codecov_token:
        # Only publish if we have a token.
        call_task('coverage_publish')


@task
def test_os_independent():
    """
    Run os independent tests in buildbot.
    """
    call_task('lint', options={'all': True})
    call_task('test_documentation')


@task
@consume_args
def test_remote(args):
    """
    Run the tests on the remote buildbot.

    test_remote [BUILDER [TEST_ARG1 TEST_ARG2] [--properties=prop1=value1]]

    You can use short names for builders. Insteas of 'server-ubuntu-1004-x86'
    you can use 'ubuntu-1004-x86'.
    """
    if not len(args):
        buildbot_list()
        sys.exit(1)

    # Check if we need to extend the builder name.
    repo_name = SETUP['repository']['name'].lower()
    if args[0].startswith(repo_name):
        builder = b'--builder=' + args[0]
    else:
        builder = b'--builder=' + repo_name + b'-' + args[0]

    arguments = [builder]
    test_arguments = []

    for argument in args[1:]:
        if argument.startswith('--properties=') or argument == '--wait':
            arguments.append(argument)
        elif argument.startswith('--force'):
            argument = argument[2:].replace('-', '_')
            if '=' not in argument:
                # Buildot property require an explicit value.
                argument += '=yes'
            arguments.append('--properties=%s' % argument)
        else:
            test_arguments.append(argument)

    if test_arguments:
        # Add all test arguments in one property.
        arguments.append(
            '--properties=test=' + ' '.join(test_arguments))

    # There is no point in waiting for pqm, all or other long builds.
    if '--wait' not in arguments:
        print('Builder execute in non-interactive mode.')
        print('Check Buildbot page for status or wait for email.')
        print('Use --wait if you want to wait to test result.')
        print('-------------------------------------------------')

    environment.args = arguments
    buildbot_try(arguments)


def run_test(python_command, switch_user, arguments):
    test_command = python_command[:]
    test_command.extend([
        pave.fs.join([pave.path.python_scripts, 'nose_runner.py']),
        switch_user,
        ])

    # Maybe we are in buildslave and all arguments are sent in a single
    # argument.
    if len(arguments) == 1:
        arguments = arguments[0].split(' ')

    test_args = arguments[:]

    if '--pdb' in test_args:
        test_args.append('--pdb-failures')

    have_explicit_tests = False
    test_module = SETUP['test']['package']
    for index, item in enumerate(test_args):
        # Check for explicit full test name arguments.
        if item.startswith(test_module):
            have_explicit_tests = True
        # Check for explicit short name arguments.
        # Add explicit test package to shorthand tests.
        if not item.startswith(test_module) and not item.startswith(u'-'):
            have_explicit_tests = True
            test_args[index] = test_module + '.' + item

        # Add generic regex to match if they are missing
        if item.startswith(u'--match'):
            rule = item[8:]
            test_args[index] = '--match=.*' + rule + '.*'

    if not have_explicit_tests:
        # Add all test if no particular test was asked.
        test_args.append(test_module)

    test_command.extend(test_args)
    with pushd(pave.path.build):
        print(test_command)
        exit_code = subprocess.call(test_command)
        print('Exit code is: %d' % (exit_code))
        return exit_code


@task
def coverage_prepare():
    """
    Prepare for a new coverage execution.
    """
    # Delete previous coverage
    pave.fs.deleteFile([pave.path.build, '.coverage'])
    pave.fs.deleteFile([pave.path.build, 'coverage.xml'])

    # Update configuration file.
    pave.fs.copyFile(
        source=['.coveragerc'],
        destination=[pave.path.build, '.coveragerc'],
        )


@task
def coverage_publish():
    """
    Send the coverage report.

    It expects that the GITHUB_PULL_ID environment variable is set.
    """
    from pkg_resources import load_entry_point
    import coverage

    codecov_main = load_entry_point('codecov', 'console_scripts', 'codecov')

    builder_name = os.environ.get('BUILDER_NAME', pave.getHostname())
    github_pull_id = os.environ.get('GITHUB_PULL_ID', '')
    branch_name = os.environ.get('BRANCH', '')

    with pushd(pave.path.build):

        cov = coverage.Coverage()
        cov.load()
        cov.report(show_missing=False)
        cov.xml_report(outfile='coverage.xml')

        sys.argv = [
            'codecov',
            '--build', builder_name,
            '--file', 'coverage.xml',
            ]

        if branch_name:
            # We know the branch name from the env.
            sys.argv.extend(['--branch', branch_name])

        if github_pull_id:
            # We are publishing for a PR.
            sys.argv.extend(['--pr', github_pull_id])

        codecov_main()


@task
@consume_args
def test_coverage(args):
    """
    Run tests with coverage.
    """
    import coverage
    # Trigger coverage creation.
    os.environ['CODECOV_TOKEN'] = 'local'

    call_task('test', args=args)

    # Generate reports.
    with pushd(pave.path.build):
        cov = coverage.Coverage(auto_data=True, config_file='.coveragerc')
        cov.load()
        cov.report()
        cov.xml_report()
        cov.html_report()


@task
@needs('build')
def harness():
    '''Start a Python shell.'''
    with pushd(pave.path.build):
        import code
        shell = code.InteractiveConsole(globals())
        shell.interact()


@task
@consume_args
def sphinx(args):
    '''Call the Sphinx command line tool.'''
    with pushd(pave.path.build):
        pave.sphinx.call(arguments=args)


@task
@needs('build')
def apidoc():
    '''Generates automatic API documentation files..'''

    module = 'chevah.' + SETUP['folders']['source']
    with pushd(pave.path.build):
        pave.sphinx.apidoc(module=module, destination=['doc', 'api'])

    pave.fs.copyFile(
        source=['apidoc_conf.py'],
        destination=[pave.path.build, 'doc', 'conf.py'],
        )
    pave.sphinx.createHTML()


@task
@consume_args
def buildbot_try(args):
    '''Launch a try job on buildmaster.'''

    from buildbot.scripts import runner
    from unidecode import unidecode

    builder = ''

    for index, arg in enumerate(args):
        if arg == '-b':
            builder = args[index + 1]
            break
        if arg.startswith('--builder='):
            builder = arg[10:]
            break

    if not builder:
        print('No builder was specified. Use "-b" to send tests to a builder.')
        sys.exit(1)

    who = unidecode(pave.git.account)
    if not who:
        print('Git user info not configured.')
        print('Use:')
        print('git config --global user.name Your Name')
        print('git config --global user.email your@email.tld')
        sys.exit(1)

    buildbot_who = b'--who="' + who.encode('utf-8') + b'"'
    buildbot_master = (
        b'--master=' +
        SETUP['buildbot']['server'].encode('utf-8') + ':' +
        str(SETUP['buildbot']['port'])
        )

    new_args = [
        b'buildbot', b'try',
        b'--connect=pb',
        buildbot_master,
        b'--web-status=%s' % (SETUP['buildbot']['web_url'],),
        b'--username=%s' % (SETUP['buildbot']['username']),
        b'--passwd=%s' % (SETUP['buildbot']['password']),
        b'--vc=%s' % (SETUP['buildbot']['vcs']),
        buildbot_who,
        b'--branch=%s' % (pave.git.branch_name),
        b'--properties=author=%s' % (who.encode('utf-8'),),
        ]
    new_args.extend(args)
    sys.argv = new_args

    # Push the latest changes to remote repo, as otherwise the diff will
    # not be valid.
    pave.git.push()

    print('Running %s' % new_args)
    runner.run()


@task
@consume_args
def buildbot_list(args):
    '''List builder names available on the remote buildbot master.

    To get the list of all remote builder, call this target with 'all'
    argument.
    '''
    from buildbot.scripts import runner

    new_args = [
        'buildbot', 'try',
        '--connect=pb',
        '--master=%s:%d' % (
            SETUP['buildbot']['server'],
            SETUP['buildbot']['port']
            ),
        '--username=%s' % (SETUP['buildbot']['username']),
        '--passwd=%s' % (SETUP['buildbot']['password']),
        '--get-builder-names',
        ]
    sys.argv = new_args

    print('Running %s' % new_args)

    new_out = None
    if 'all' not in args:
        from StringIO import StringIO
        new_out = StringIO()
        sys.stdout = new_out

    try:
        runner.run()
    finally:
        if new_out:
            sys.stdout = sys.__stdout__
            if SETUP['buildbot']['builders_filter']:
                selector = (
                    SETUP['buildbot']['builders_filter'])
            elif SETUP['repository']['name']:
                selector = SETUP['repository']['name']
            else:
                selector = ''
            for line in new_out.getvalue().split('\n'):
                if selector in line:
                    print(line)


@task
@needs('deps', 'update_setup')
@consume_args
def publish_distributables(args):
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish

    [production|staging] [yes|no]
    """
    try:
        target = args[0]
    except IndexError:
        target = 'staging'

    try:
        latest = args[1]
        if latest == 'no':
            latest = False
        else:
            latest = True
    except IndexError:
        latest = True

    url_fragment = SETUP['product']['url_fragment']
    version = SETUP['product']['version']
    version_major = SETUP['product']['version_major']
    version_minor = SETUP['product']['version_minor']

    # Set download site.
    if target == 'production':
        server = SETUP['publish']['download_production_hostname']
    else:
        server = SETUP['publish']['download_staging_hostname']

    # Start with a clean base.
    pave.fs.deleteFolder(target=[pave.path.dist])
    pave.fs.createFolder(destination=[pave.path.dist])

    # Create the things.
    call_task('create_download_page', args=[server])
    call_task('dist')

    # Copy to the to be outbox folder for publishing.
    publish_downloads_folder = [pave.path.publish, 'downloads']
    publish_website_folder = [pave.path.publish, 'website']
    product_folder = [pave.fs.join(publish_downloads_folder), url_fragment]
    release_publish_folder = [
        pave.fs.join(publish_downloads_folder),
        url_fragment, version_major, version_minor]

    # Create publishing content for download site.
    pave.fs.deleteFolder(publish_downloads_folder)
    pave.fs.createFolder(release_publish_folder, recursive=True)

    # Copy the download files.
    pave.fs.copyFolderContent(
        source=[pave.path.dist],
        destination=release_publish_folder,
        )

    # Copy publishing content for presentation site.
    pave.fs.deleteFolder(publish_website_folder)
    pave.fs.createFolder(publish_website_folder)
    pave.fs.createFolder([pave.fs.join(publish_website_folder), 'downloads'])
    release_html_name = version + '.html'
    pave.fs.copyFile(
        source=[pave.path.dist, release_html_name],
        destination=[
            pave.path.publish, 'website', 'downloads', release_html_name],
        )

    # For production, update latest download page.
    publish_config = SETUP['publish']
    if target == 'production':
        pave.fs.writeContentToFile(
            destination=[pave.fs.join(product_folder), 'LATEST'],
            content=version,
            )
        download_hostname = publish_config['download_production_hostname']
        download_username = publish_config['download_production_username']

        documentation_hostname = publish_config['website_production_hostname']
        documentation_username = publish_config['website_production_username']
    else:
        download_hostname = publish_config['download_staging_hostname']
        download_username = publish_config['download_staging_username']

        documentation_hostname = publish_config['website_staging_hostname']
        documentation_username = publish_config['website_staging_username']

    if latest:
        pave.fs.copyFile(
            source=[pave.path.dist, release_html_name],
            destination=[
                pave.path.publish, 'website', 'downloads', 'index.html'],
            )

    print("Publishing distributable(s) to %s ..." % (download_hostname))
    pave.rsync(
        username=download_username,
        hostname=download_hostname,
        source=[pave.path.publish, 'downloads', url_fragment + '/'],
        destination=download_hostname + '/' + url_fragment,
        verbose=True,
        )

    print("Publishing download pages to %s..." % (documentation_hostname))
    pave.rsync(
        username=documentation_username,
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'downloads/'],
        destination=documentation_hostname + '/downloads/' + url_fragment,
        verbose=True,
        )

    print("Distributable(s) published.")


@task
@needs('update_setup')
@consume_args
def publish_documentation(args):
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish

    [production|staging] [yes|no]
    """
    try:
        target = args[0]
    except IndexError:
        target = 'staging'

    try:
        latest = args[1]
        if latest == 'no':
            latest = False
        else:
            latest = True
    except IndexError:
        latest = True

    product_name = SETUP['product']['name'].lower()
    version = SETUP['product']['version']

    publish_website_folder = [pave.path.publish, 'website']
    publish_documentation_folder = [
        pave.path.publish, 'website', 'documentation']
    publish_documentation_versioned_folder = [
        pave.path.publish, 'website', 'documentation', 'v']
    publish_release_folder = [
        pave.path.publish, 'website', 'documentation', 'v', version]
    publish_latest_folder = [
        pave.path.publish, 'website', 'documentation', 'latest']
    publish_experimental_folder = [
        pave.path.publish, 'website', 'documentation', 'experimental']
    publish_experimental_release_folder = [
        pave.path.publish, 'website', 'documentation', 'experimental',
        version]

    # Create publishing content for website.
    pave.fs.createFolder([pave.path.publish])
    pave.fs.deleteFolder(publish_website_folder)
    pave.fs.createFolder(publish_website_folder)
    pave.fs.createFolder(publish_documentation_folder)
    pave.fs.createFolder(publish_documentation_versioned_folder)
    pave.fs.createFolder(publish_experimental_folder)

    call_task('documentation_website')
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html'],
        destination=publish_release_folder,
        )

    call_task(
        'documentation_website',
        options={'experimental': True},
        )
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html'],
        destination=publish_experimental_release_folder,
        )

    # If we are releasing the latest version, also copy file to latest folder.
    if latest:
        pave.fs.copyFolder(
            source=[pave.path.build, 'doc', 'html'],
            destination=publish_latest_folder,
            )

    publish_config = SETUP['publish']
    if target == 'production':
        documentation_hostname = publish_config['website_production_hostname']
        documentation_username = publish_config['website_production_username']
        destination_root = (
            documentation_hostname + '/documentation/' + product_name)
    else:
        documentation_hostname = publish_config['website_staging_hostname']
        documentation_username = publish_config['website_staging_username']
        destination_root = (
            documentation_hostname + '/documentation/' + product_name)

    print("Publishing documentation to %s..." % (documentation_hostname))
    pave.rsync(
        username=documentation_username,
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'documentation/'],
        destination=destination_root,
        verbose=True,
        )

    print("Documentation published.")


@task
def clean():
    """
    Clean build and dist folders.

    This is just a placeholder, since clean is handled by the outside
    paver.sh scripts.
    """


__all__ = [
    'DIST_EXTENSION',
    'DIST_TYPE',
    'github',
    'merge_init',
    'merge_commit',
    'pqm',
    'rqm',
    'publish',
    ]
