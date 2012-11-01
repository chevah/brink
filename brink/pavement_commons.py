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

import getpass
import os
import sys
import subprocess

from paver.easy import cmdopts, task, pushd, needs
from paver.tasks import environment, help, consume_args

from brink.utils import BrinkPaver


def _p(path):
    '''
    Shortcut for converting a list to a path using os.path.join.
    '''
    result = os.path.join(*path)
    if os.name == 'posix':
        result = result.encode('utf-8')
    return result


SETUP = {
    'product': {
        'name': 'ChevahProduct',
        'version': '0.0.1',
        'version_major': '0',
        'version_minor': '0',
        'copyright_holder': 'Chevah Project',
        'distributables': {}
    },
    'python': {
        'version': '2.5',
    },
    'folders': {
        'source': None,
        'static': u'static',
        'dist': u'dist',
        'publish': u'publish',
        'configuration': u'configuration',
        'deps': u'deps',
        'brink': u'brink',
        'test_data': u'test_data',
        'nsis': 'nsis'
    },
    'repository': {
        'name': None,
        'base_uri': 'http://172.20.0.11/git/',
    },
    'buildbot': {
        'vcs': 'git',
        'server': '172.20.0.11',
        'port': 10087,
        'username': 'chevah_buildbot',
        'password': 'chevah_password',
        'web_url': 'http://172.20.0.11:10088',
        'builders_filter': None,
    },
    'publish': {
        'download_production_hostname': 'download.chevah.com',
        'download_staging_hostname': 'staging.download.chevah.com',
        'website_production_hostname': 'chevah.com',
        'website_staging_hostname': 'staging.chevah.com'
    },
    'pypi': {
        'index_url': 'http://172.20.0.1:10042/simple',
    },
    'pocket-lint': {
        'exclude_files': [
            'ftplib.py',
            'reset.css',
            'default.css',
            'state.sqlite',
            ],
        'exclude_folders': [],
        'include_files': ['pavement.py'],
        'include_folders': [],
    },
    'website_package': 'chevah.website',
    'test': {
        'package': 'chevah.product.tests',
    },
}

DIST_TYPE = {
    'ZIP': 0,
    'NSIS': 1,
    'TAR_GZ': 2,
    'NSIS_RENAMED': 3,
    }

DIST_EXTENSION = {
    DIST_TYPE['ZIP']: 'zip',
    DIST_TYPE['NSIS']: 'exe',
    DIST_TYPE['TAR_GZ']: 'tar.gz',
    DIST_TYPE['NSIS_RENAMED']: 'rename_to_exe'
}


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
        pave.fs.createEmtpyFile(target=self._segments)

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
        options.deps_update, 'uri', default_value=default_uri)
    pave.updateRepositories(projects=projects, uri=base_uri)


@task
def lint():
    '''Run static codse checks.'''
    pocketlint_reports_count = pave.pocketLint(
        folder=SETUP['folders']['source'])

    # Check for additional files outside of source folder.
    pocketlint_reports_count += pave.pocketLint(
        files=SETUP['pocket-lint']['include_files'])

    for folder in SETUP['pocket-lint']['include_folders']:
        pocketlint_reports_count += pave.pocketLint(folder=folder)

    if pocketlint_reports_count > 0:
            raise SystemExit(True)
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
def test(args):
    '''Run the test suite.'''
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
    '''Run the test suite using root. On Windows is runs as a normal user.'''
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
def test_all(args):
    """
    Execute all tests.
    """

    default_arguments = ['--with-run-reporter', '--with-timer']
    call_arguments = []

    empty_args = False
    if not len(args):
        empty_args = True
        call_arguments = default_arguments[:]
    call_arguments.append('-s')
    call_arguments.extend(args)

    environment.args = call_arguments
    normal_result = test(call_arguments)

    super_result = 0
    if os.name == 'posix':
        environment.args = ['elevated']
        environment.args.extend(call_arguments)
        super_result = test_super(call_arguments)

    lint_result = 0
    if empty_args:
        lint_result = lint()

    if not (normal_result == 0 and super_result == 0 and lint_result == 0):
        sys.exit(1)


def run_test(python_command, switch_user, arguments):
    test_command = python_command[:]
    test_command.extend(
        [_p([pave.path.python_scripts, 'nose_runner.py']),
        switch_user])

    test_args = arguments[:]

    if '--pdb' in test_args:
        test_args.append('--pdb-failures')

    have_explicit_tests = False
    source_folder = SETUP['folders']['source']
    test_module = u'chevah.' + source_folder + '.tests'

    test_module = SETUP['test']['package']
    for index, item in enumerate(test_args):
        # Look for appending package name to test module name.
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

    if not len(args):
        print 'User "-b builder_name" to run the try on builder_name.'
        print 'You can use multiple builders by using multiple -b args.'
        buildbot_list()
        sys.exit(1)

    # Add -b in front of the last argument if no builder where specified
    if not '-b' in args:
        builder_name = args[-1]
        args[-1] = '-b'
        args.append(builder_name)

    from buildbot.scripts import runner
    from unidecode import unidecode

    # Push the latest changes to remote repo, as otherwise the diff will
    # not be valide.
    pave.git.push()

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
        '--who="%s"' % (unidecode(pave.git.account)),
        '--branch=%s' % (pave.git.branch_name),
        ]

    if not ('--no-wait' in args):
        print ('Use "--no-wait" if you only want to trigger the build '
                'without waiting for result.')
        args.append('--wait')
    else:
        args.remove('--no-wait')

    new_args.extend(args)
    sys.argv = new_args
    try:
        runner.run()
    finally:
        pave.buildbotShowLastStep(args)


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
            elif SETUP['folders']['source']:
                selector = SETUP['folders']['source']
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

    username = pave.getOption(options.review, 'username', default_value=None)

    if not username:
        # Get the ReviewBoard username based on git account.
        # Translate: Name Surname <name@domain.tld>
        # As: namesurname
        from unidecode import unidecode
        username = unidecode(pave.git.account)
        username = username.split('<')[0].strip().lower()
        username = username.replace(' ', '')

    review_id = pave.getOption(options.review, 'review_id')

    # Try to get the bug number from branch name as 23-some_description.
    # If it is not number, set it to None.
    bug = branch_name.split('-')[0]
    try:
        int(bug)
    except ValueError:
        bug = None

    name = pave.getOption(options.review, 'name')
    if name is None:
        name = branch_name

    description = pave.getOption(options.review, 'description')

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
@needs('build', 'update_setup')
def doc_html():
    """
    Generates the documentation.
    """
    product_name = SETUP['product']['name']
    version = SETUP['product']['version']

    website_path = pave.importAsString(
        SETUP['website_package']).get_module_path()

    pave.sphinx.createConfiguration(
        destination=[pave.path.build, 'doc_source', 'conf.py'],
        project=product_name,
        version=version,
        copyright=SETUP['product']['copyright_holder'],
        themes_path=os.path.join(website_path, 'sphinx'),
        theme_name='standalone'
        )
    destination = [pave.path.build, 'doc', 'html']
    exit_code = pave.sphinx.createHTML(
        arguments=[],
        source=['doc_source'],
        target=destination,
        )

    pave.fs.copyFolder(
        source=[website_path, 'media'],
        destination=[pave.path.build, 'doc', 'html', 'media'])

    print "Documentation files generated in %s" % _p(destination)
    return exit_code


@task
@needs('update_setup', 'dist', 'doc_html')
def publish():
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish
    """
    product_name = SETUP['product']['name'].lower()
    version = SETUP['product']['version']
    version_major = SETUP['product']['version_major']
    version_minor = SETUP['product']['version_minor']

    publish_downloads_folder = [pave.path.publish, 'downloads']
    publish_website_folder = [pave.path.publish, 'website']
    product_folder = [_p(publish_downloads_folder), product_name]
    release_publish_folder = [
        _p(publish_downloads_folder),
        product_name, version_major, version_minor]

    # Create publising content for download site.
    pave.fs.deleteFolder(publish_downloads_folder)
    pave.fs.createFolder(release_publish_folder, recursive=True)
    pave.fs.writeContentToFile(
        destination=[_p(product_folder), 'LATEST'], content=version)
    pave.fs.createEmtpyFile([_p(product_folder), 'index.html'])
    pave.fs.copyFolderContent(
        source=[pave.path.dist],
        destination=release_publish_folder,
        )

    # Create publising content for presentation site.
    pave.fs.deleteFolder(publish_website_folder)
    pave.fs.createFolder(publish_website_folder)
    pave.fs.createFolder([_p(publish_website_folder), 'downloads'])
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html'],
        destination=[pave.path.publish, 'website', 'documentation'],
        )
    release_html_name = 'release-' + version + '.html'
    pave.fs.copyFile(
        source=[pave.path.dist, release_html_name],
        destination=[
            pave.path.publish, 'website', 'downloads', release_html_name],
        )
    pave.fs.copyFile(
        source=[pave.path.dist, release_html_name],
        destination=[pave.path.publish, 'website', 'downloads', 'index.html'],
        )

    publish_config = SETUP['publish']
    if pave.git.branch_name == 'production':
        download_hostname = publish_config['download_production_hostname']
        documentation_hostname = publish_config['website_production_hostname']
    else:
        download_hostname = publish_config['download_staging_hostname']
        documentation_hostname = publish_config['website_staging_hostname']

    print "Publishing distributables to %s ..." % (download_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=download_hostname,
        source=[pave.path.publish, 'downloads', product_name + '/'],
        destination=download_hostname + '/' + product_name
        )

    print "Publishing documentation to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'documentation/'],
        destination=documentation_hostname + '/documentation/' + product_name
        )

    print "Publishing download pages to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'downloads/'],
        destination=documentation_hostname + '/downloads/' + product_name
        )

    print "Publish done."


@task
def clean():
    '''Clean build and dist folders.

    This is just a placeholder, since clean is handeld by the outside
    paver.sh scripts.
    '''