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
from __future__ import with_statement

from optparse import make_option
import getpass
import sys
import subprocess
import threading

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
    )

# Silence lint.
DIST_EXTENSION
DIST_TYPE
github
merge_init
merge_commit
pqm
rqm

pave = BrinkPaver(setup=SETUP)


RELEASE_MANAGERS = [
    'adi.roiban@chevah.com',
    'laura.gheorghiu@chevah.com',
    ]


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
    ('uri=', None, 'Base repository URI.'),
])
def deps_update(options):
    '''Update dependencies source.'''

    projects = [
        'agent',
        'agent-1.5',
        'commons',
        'deps',
        'server',
        'webadmin-1.6',
        ]
    default_uri = SETUP['repository']['base_uri']
    base_uri = pave.getOption(
        options, 'deps_update', 'uri', default_value=default_uri)
    pave.updateRepositories(projects=projects, uri=base_uri)


@task
@cmdopts([
     ('quick', 'q', 'Run quick linter for recently changed files.'),
     ('dry', 'd', 'Don\'t run the linter and only show linted files.'),
])
def lint(options):
    """
    Run static code checks.
    """
    quick = pave.getOption(options, 'lint', 'quick', default_value=False)
    dry = pave.getOption(options, 'lint', 'dry', default_value=False)

    if not quick:
        folders = SETUP['pocket-lint']['include_folders'][:]
        files = SETUP['pocket-lint']['include_files'][:]
    else:
        folders = []
        changes = pave.git.diffFileNames()
        # Filter deleted changes since we can not lint then.
        files = [change[1] for change in changes if change[0] != 'd']

    excluded_folders = SETUP['pocket-lint']['exclude_folders'][:]
    excluded_files = SETUP['pocket-lint']['exclude_files'][:]

    if dry:
        print "\n---\nFiles\n---"
        for name in files:
            print name
        print "\n---\nFolders\n---"
        for name in folders:
            print name
        print "\n---\nExcluded files\n---"
        for name in excluded_files:
            print name
        print "\n---\nExcluded folders\n---"
        for name in excluded_folders:
            print name
        return 0

    result = pave.pocketLint(
        folders=folders, excluded_folders=excluded_folders,
        files=files, excluded_files=excluded_files,
        )

    if result > 0:
            raise BuildFailure('Lint failed.')
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

    default_arguments = ['--with-run-reporter', '--with-timer']
    call_arguments = []

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
                if SETUP['test']['elevated'] in arg:
                    run_elevated = True
                    break
        if run_elevated:
            super_result = test_super(call_arguments)

    if not (normal_result == 0 and super_result == 0):
        sys.exit(1)


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
        builder = '--builder=' + args[0]
    else:
        builder = '--builder=' + repo_name + '-' + args[0]

    arguments = [builder]
    test_arguments = []

    for argument in args[1:]:
        if argument.startswith('--properties=') or argument == '--wait':
            arguments.append(argument)
        else:
            test_arguments.append(argument)

    if test_arguments:
        # Add all test arguments in one property.
        arguments.append(
            '--properties=test=' + ' '.join(test_arguments))

    # There is no point in waiting for pqm, all or other long builds.
    if not '--wait' in arguments:
        print 'Builder execute in non-interactive mode.'
        print 'Check Buildbot page for status or wait for email.'
        print 'Use --wait if you want to wait to test result.'
        print '-------------------------------------------------'

    environment.args = arguments
    buildbot_try(arguments)


def run_test(python_command, switch_user, arguments):
    test_command = python_command[:]
    test_command.extend(
        [pave.fs.join([pave.path.python_scripts, 'nose_runner.py']),
        switch_user])

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
        if (not item.startswith(test_module) and not item.startswith(u'-')):
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
        print test_command
        exit_code = subprocess.call(test_command)
        print 'Exit code is: %d' % (exit_code)
        return exit_code


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

    status_thread = None
    interactive = True
    builder = ''

    for index, arg in enumerate(args):
        if arg == '-b':
            builder = args[index + 1]
            break
        if arg.startswith('--builder='):
            builder = arg[10:]
            break

    if not builder:
        print 'No builder was specified. Use "-b" to send tests to a builder.'
        sys.exit(1)

    if '--wait' in args:
        interactive = True
    else:
        interactive = False

    who = unidecode(pave.git.account)
    if not who:
        print 'Git user info not configured.'
        print 'Use:'
        print 'git config --global user.name Your Name'
        print 'git config --global user.email your@email.tld'
        sys.exit(1)

    new_args = [
        'buildbot', 'try',
        '--connect=pb',
        '--master=%s:%d' % (
            SETUP['buildbot']['server'],
            SETUP['buildbot']['port']
            ),
        '--username=%s' % (SETUP['buildbot']['username']),
        '--passwd=%s' % (SETUP['buildbot']['password']),
        '--vc=%s' % (SETUP['buildbot']['vcs']),
        '--who="%s"' % (who),
        '--branch=%s' % (pave.git.branch_name),
        '--properties=author=%s' % (who),
        ]
    new_args.extend(args)
    sys.argv = new_args

    # Push the latest changes to remote repo, as otherwise the diff will
    # not be valid.
    pave.git.push()

    print 'Running %s' % new_args

    if interactive:
        status_thread = threading.Thread(
            target=pave.buildbotShowProgress, args=(builder,))
        try:
            status_thread.start()
            runner.run()
        finally:
            status_thread.join()
    else:
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

    print 'Running %s' % new_args

    new_out = None
    if not 'all' in args:
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
                    print line


@task
@cmdopts([
    ('username=', None, 'Username for which to request review.'),
    ('review_id=', 'r', 'Review ID to update.'),
    ('name=', 'n', 'The name of this review.'),
    ('description=', 'd', 'Description of changes.'),
])
def review(options):
    '''Creates and updates reviews hosted on ReviewBoard.'''
    from rbtools.postreview import main as postreview_main

    branch_name = pave.git.branch_name

    print "Pushing changes..."
    git_push = ['git', 'push', '--set-upstream', 'origin', branch_name]
    pave.execute(git_push)

    username = pave.getOption(
        options, 'review', 'username', default_value=None)

    if not username:
        # Get the ReviewBoard username based on git account.
        # Translate: Name Surname <name@domain.tld>
        # As: namesurname
        from unidecode import unidecode
        username = unidecode(pave.git.account)
        username = username.split('<')[0].strip().lower()
        username = username.replace(' ', '')

    review_id = pave.getOption(options, 'review', 'review_id')

    # Try to get the bug number from branch name as 23-some_description.
    # If it is not number, set it to None.
    bug = pave.getTicketIDFromBranchName(branch_name)
    try:
        int(bug)
    except ValueError:
        bug = None

    name = pave.getOption(options, 'review', 'name')
    if name is None:
        name = branch_name

    description = pave.getOption(options, 'review', 'description')

    module = SETUP['repository']['name']

    new_args = ['rbtools']
    new_args.extend([
        '--server=http://review.chevah.com/',
        '--repository-url=/srv/git/' + module + '.git',
        '--username=%s' % username,
        ])

    if review_id:
        new_args.append('--review-request-id=%s' % review_id)

        if description is None:
            description = pave.git.last_commit
        new_args.append('--change-description=' + description)

        # We don't want to update the summary when posting an updated diff.
        name = None
        description = None
        bug = None

    if name:
        new_args.append('--summary=' + name)

    if description:
        new_args.append('--description=' + description)

    if bug:
        new_args.append('--bugs-closed=' + bug)

    sys.argv = new_args
    print 'Posting review as user: ' + username
    postreview_main()


@task
@cmdopts([
    make_option(
        "-c", "--check",
        help="Check all pages.",
        default=False,
        action="store_true"
        ),
    ('all', None, 'Create all files.'),
    ('production', None, 'Build with only production sections.'),
])
@needs('build', 'update_setup')
def doc_html(options):
    """
    Generates the documentation.
    """
    arguments = []
    if pave.getOption(options, 'doc_html', 'all'):
        arguments.extend(['-a', '-E', '-n'])
    if pave.getOption(options, 'doc_html', 'production'):
        experimental = False
    else:
        experimental = True
    return _generateProjectDocumentation(arguments, experimental=experimental)


@task
@needs('build', 'update_setup')
def test_documentation():
    """
    Generates the documentation in testing mode.

    Any warning are treated as errors.
    """
    exit_code = _generateProjectDocumentation(
        ['-a', '-E', '-W', '-N', '-n'])
    if exit_code:
        raise BuildFailure('Documentation test failed.')


def _generateProjectDocumentation(arguments=None, experimental=False):
    """
    Generate project documentation and return exit code.
    """
    if arguments is None:
        arguments = []

    product_name = SETUP['product']['name']
    version = SETUP['product']['version']

    website_path = pave.importAsString(
        SETUP['website_package']).get_module_path()

    pave.sphinx.createConfiguration(
        destination=[pave.path.build, 'doc_source', 'conf.py'],
        project=product_name,
        version=version,
        copyright=SETUP['product']['copyright_holder'],
        themes_path=pave.fs.join([website_path, 'sphinx']),
        theme_name='standalone',
        experimental=experimental,
        )
    destination = [pave.path.build, 'doc', 'html']
    exit_code = pave.sphinx.createHTML(
        arguments=arguments,
        source=['doc_source'],
        target=destination,
        )

    pave.fs.copyFolder(
        source=[website_path, 'media'],
        destination=[pave.path.build, 'doc', 'html', 'media'])

    print "Documentation files generated in %s" % pave.fs.join(destination)
    print "Exit with %d." % (exit_code)
    return exit_code


@task
@consume_args
def release(args):
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish
    """

    try:
        target = args[0]
    except IndexError:
        target = 'staging'

    try:
        latest = args[1]
    except IndexError:
        latest = None

    if args:
        target = args[0]
        author_email = args[-1].replace('<', '').replace('>', '')
    else:
        target = 'staging'
        author_email = 'unknown'

    if target == 'production' and author_email not in RELEASE_MANAGERS:
        print 'You are not allowed to release in production.'
        exit(1)

    arguments = [target, latest]
    call_task('publish_documentation', args=arguments)
    call_task('publish_distributables', args=arguments)


@task
@needs('update_setup', 'dist')
@consume_args
def publish_distributables(args):
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish
    """
    try:
        target = args[0]
    except IndexError:
        target = 'staging'

    try:
        latest = args[1]
    except IndexError:
        latest = None

    product_name = SETUP['product']['name'].lower()
    version = SETUP['product']['version']
    version_major = SETUP['product']['version_major']
    version_minor = SETUP['product']['version_minor']

    # Set download site.
    if target == 'production':
        server = SETUP['publish']['download_production_hostname']
    else:
        server = SETUP['publish']['download_staging_hostname']

    call_task('create_download_page', args=[server])

    publish_downloads_folder = [pave.path.publish, 'downloads']
    publish_website_folder = [pave.path.publish, 'website']
    product_folder = [pave.fs.join(publish_downloads_folder), product_name]
    release_publish_folder = [
        pave.fs.join(publish_downloads_folder),
        product_name, version_major, version_minor]

    # Create publishing content for download site.
    pave.fs.deleteFolder(publish_downloads_folder)
    pave.fs.createFolder(release_publish_folder, recursive=True)

    pave.fs.copyFolderContent(
        source=[pave.path.dist],
        destination=release_publish_folder,
        )

    # Create publishing content for presentation site.
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
        documentation_hostname = publish_config['website_production_hostname']
    else:
        download_hostname = publish_config['download_staging_hostname']
        documentation_hostname = publish_config['website_staging_hostname']

    if latest == 'yes':
        pave.fs.copyFile(
            source=[pave.path.dist, release_html_name],
            destination=[
                pave.path.publish, 'website', 'downloads', 'index.html'],
            )

    print "Publishing distributable(s) to %s ..." % (download_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=download_hostname,
        source=[pave.path.publish, 'downloads', product_name + '/'],
        destination=download_hostname + '/' + product_name,
        verbose=True,
        )

    print "Publishing download pages to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'downloads/'],
        destination=documentation_hostname + '/downloads/' + product_name,
        verbose=True,
        )

    print "Distributable(s) published."


@task
@needs('update_setup')
@consume_args
def publish_documentation(args):
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish
    """
    try:
        target = args[0]
    except IndexError:
        target = 'staging'

    try:
        latest = args[1]
    except IndexError:
        latest = None

    product_name = SETUP['product']['name'].lower()
    version = SETUP['product']['version']

    publish_website_folder = [pave.path.publish, 'website']
    publish_documentation_folder = [
        pave.path.publish, 'website', 'documentation']
    publish_release_folder = [
        pave.path.publish, 'website', 'documentation', version]
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
    pave.fs.createFolder(publish_experimental_folder)

    call_task(
        'doc_html',
        options={
            'production': True,
            'all': True,
            },
        )
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html'],
        destination=publish_release_folder,
        )

    call_task(
        'doc_html',
        options={
            'production': False,
            'all': True,
            },
        )
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html'],
        destination=publish_experimental_release_folder,
        )

    publish_config = SETUP['publish']
    if target == 'production':
        documentation_hostname = publish_config['website_production_hostname']
        destination_root = (
            documentation_hostname + '/documentation/' + product_name)
    else:
        documentation_hostname = publish_config['website_staging_hostname']
        destination_root = (
            documentation_hostname + '/documentation/' + product_name)

    if latest == 'yes':
        # Also create a latest redirect.
        data = {
            'url': 'http://%s/%s' % (destination_root, version),
            'title': 'Redirecting to latest %s documentation' % (
                product_name),
        }
        template_root = pave.fs.join([pave.path.build, 'doc_source'])
        content = pave.renderJinja(template_root, 'latest.j2', data)
        redirect = [pave.fs.join(publish_documentation_folder), 'index.html']
        pave.fs.writeContentToFile(redirect, content=content)

    print "Publishing documentation to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'documentation/'],
        destination=destination_root,
        verbose=True,
        )

    print "Documentation published."


@task
def clean():
    """
    Clean build and dist folders.

    This is just a placeholder, since clean is handled by the outside
    paver.sh scripts.
    """
