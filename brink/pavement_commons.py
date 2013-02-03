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
import threading

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
        'push_uri': 'git@git.chevah.com:'
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
        'exclude_files': [],
        'exclude_folders': [],
        'include_files': ['pavement.py'],
        'include_folders': [],
    },
    'website_package': 'chevah.website',
    'test': {
        'package': 'chevah.product.tests',
        # Module inside the test-package where elevated test are located.
        'elevated': None,
    },
    'github': {
        'base_url': 'https://github.com',
        'repo': 'chevah',
    }
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

    folders = SETUP['pocket-lint']['include_folders'][:]
    files = SETUP['pocket-lint']['include_files'][:]
    excluded_folders = SETUP['pocket-lint']['exclude_folders'][:]
    excluded_files = SETUP['pocket-lint']['exclude_files'][:]

    result = pave.pocketLint(
        folders=folders, excluded_folders=excluded_folders,
        files=files, excluded_files=excluded_files,
        )

    if result > 0:
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

    On Windows is does nothing.
    """
    if os.name != 'posix':
        return 0

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
def test(args):
    """
    Execute all tests.
    """

    default_arguments = ['--with-run-reporter', '--with-timer']
    call_arguments = []

    empty_args = False
    if not len(args):
        empty_args = True
        call_arguments = default_arguments[:]

    run_elevated = False
    if SETUP['test']['elevated']:
        for arg in args:
            if SETUP['test']['elevated'] in arg:
                run_elevated = True
                break

    call_arguments.append('-s')
    call_arguments.extend(args)

    environment.args = call_arguments
    normal_result = test_normal(call_arguments)

    super_result = 0
    if empty_args and SETUP['test']['elevated']:
        environment.args = [SETUP['test']['elevated']]
        environment.args.extend(call_arguments)
        super_result = test_super(call_arguments)
    elif run_elevated:
        super_result = test_super(call_arguments)
    else:
        pass

    lint_result = 0
    if empty_args:
        lint_result = lint()

    if not (normal_result == 0 and super_result == 0 and lint_result == 0):
        sys.exit(1)


@task
@consume_args
def test_remote(args):
    """
    Run the tests on the remote buildbot.

    test_remote [BUILDER_NAME [TEST_ARG1 TEST_ARG2]]

    You can use short names for builders. Insteas of 'server-ubuntu-1004-x86'
    you can use 'ubuntu-1004-x86'.
    """
    if not len(args):
        buildbot_list()
        sys.exit(1)

    repo_name = SETUP['repository']['name'].lower()
    if args[0].startswith(repo_name):
        builder = '--builder=' + args[0]
    else:
        builder = '--builder=' + repo_name + '-' + args[0]

    new_args = [builder]
    new_args.append('--properties=test=' + ' '.join(args[1:]))
    environment.args = new_args
    buildbot_try(new_args)


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

    if '--no-wait' in args:
        interactive = False
        args.remove('--no-wait')
    else:
        interactive = True
        args.append('--wait')

    # There is no point in waiting for pqm builds
    # so they are force as non-interactive
    if 'pqm' in builder or 'all' in builder:
        print 'Forcing PQM/ALL builds in non-interactive mode.'
        print 'Check Buildbot page for status or wait for email.'
        print '-----------------------------------------------'
        interactive = False
        args.remove('--wait')

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
    # not be valide.
    pave.git.push()

    if not interactive:
        print ('Use "--no-wait" if you only want to trigger the build '
                'without waiting for result.')
    else:
        status_thread = threading.Thread(
            target=pave.buildbotShowProgress, args=(builder,))

    print 'Running %s' % new_args
    if interactive:
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


@task
@consume_args
def github(args):
    """
    Helpers for interacting with GitHub website.
    """
    def github_help():
        print "Usage: github COMMNAND ARGUMENTS."
        print ""
        print "List of commands:"
        print "    open - Open the repository in githuh."
        print "    new  - Open the page for creating a new pull request"

    if not len(args):
        github_help()
        sys.exit(1)

    import webbrowser

    if args[0] == 'open':
        url = "%s/%s" % (SETUP['github']['base_url'], SETUP['github']['repo'])
        webbrowser.open_new_tab(url)
        sys.exit(0)

    if args[0] == 'new':
        pave.git.publish()
        url = "%s/%s/pull/new/%s" % (
            SETUP['github']['base_url'],
            SETUP['github']['repo'],
            pave.git.branch_name)
        webbrowser.open_new_tab(url)
        sys.exit(0)


@task
@consume_args
def github_token(args):
    """
    Return an authorization token from GitHub for chevah-robot account.
    """
    if len(args) != 1:
        print "Usage: PASSWORD"
        sys.exit(1)

    from github import Github

    # f56915f622a549332712813e5be064057b3cd915
    github = Github('chevah-robot', args[0])
    user = github.get_user()
    authorization = user.create_authorization(
        scopes=['repo'],
        note='Chevah PQM',
        note_url='http://build.chevah.com/waterfall')
    print authorization.token


REVIEWERS_LIST_MARKER = ['review', 'reviewer', 'reviewers']
REVIEWER_MARKER = '@'
APPROVAL_MARKERS = [
    'approved',
    'aproved',
    'approve',
    'aprove',
    ':shipit:',
    'ship it',
    ]
APPROVAL_SHA_MARKER = 'sha@'


def _review_properties(token, pull_id):
    """
    Helper for calling this task from multiple places, without messing
    with paver arguments.
    """
    try:
        pull_id = int(pull_id)
    except:
        print "Failed to get pull_id from %s" % str(pull_id)
        sys.exit(1)

    from github import Github, GithubException
    try:
        repo_name = SETUP['github']['repo']
        github = Github(token)
        repo = github.get_repo(repo_name)
        pull_request = repo.get_pull(pull_id)

        # Fail early if branch can not be merged.
        if not pull_request.mergeable:
            print "GitHub sais that branch can not be merged."
            print "Please merge latest code from master and pull all changes."
            sys.exit(1)

        comments = []
        for comment in pull_request.get_issue_comments():
            comments.append((
                comment.user.login, comment.body, comment.updated_at))

    except GithubException, error:
        print "Failed to get GitHub details"
        print str(error)
        sys.exit(1)

    def getReviewers(content):
        """
        Parse content and return the list of reviewers.
        """
        reviewers = []
        for line in content.split('\n'):
            words = line.strip().split(' ')
            # Check if line starts with reviewrs marker.
            if not words[0] in REVIEWERS_LIST_MARKER:
                continue
            # Check if words starts with review marker.
            for word in words:
                if not word.startswith(REVIEWER_MARKER):
                    continue
                reviewers.append(word.strip(REVIEWER_MARKER))

        if not len(reviewers):
            print "This review has no reviewers."
            sys.exit(1)

        return reviewers

    def getReviewTitle(content, ticket_id=None):
        """
        Parse line and return merge commit message.
        """
        result = content.strip()

        if len(result.split('\n')) > 1:
            print "Commit merge message should be single line."
            sys.exit(1)

        # Make sure the title does not starts  with ticket id as it will
        # be appended later.
        if ticket_id:
            first_word = result.split(' ')[0]
            if ticket_id in first_word:
                # Redo the title without the first word.
                result = ' '.join(result.split(' ')[1:])

        # Make sure first letter is upper case... just for the style.
        result = result.capitalize()

        # Make sure message end with '.' ... just for style.
        result = result.rstrip('.').strip() + '.'

        return result

    def checkReviewApproval(comments, reviewers, sha):
        """
        Check comments to see if review was approved by all reviewers.
        """
        # We sort all comments in reverse order as they were updated.
        comments = sorted(
            comments, key=lambda comment: comment[2], reverse=True)

        # Get last comment of each review and check that the review was
        # approved.
        pending_approval = []
        for reviewer in reviewers:
            approved_sha = getApprovedSHA(reviewer, comments)
            if not approved_sha:
                pending_approval.append((reviewer, 'Not approved yet.'))
                continue

            if not sha.startswith(approved_sha):
                pending_approval.append((
                    reviewer, 'Approved at %s. Branch at %s.' % (
                        approved_sha, sha)))

        if pending_approval:
            print "Review not approved. See list below"
            for reason in pending_approval:
                print reason
            sys.exit(1)

    def getApprovedSHA(reviewer, comments):
        """
        Return the line in which the review has approved the review.

        Return None if no approval comment was found.
        """
        for author, content, updated_at in comments:
            if reviewer != author:
                # Not a comment from reviewer.
                continue

            for line in content.split('\n'):
                line = line.strip()
                first_word = line.split(' ')[0]
                if first_word in APPROVAL_MARKERS:
                    for word in line.split(' '):
                        word = word.lower()
                        if word.startswith(APPROVAL_SHA_MARKER):
                            sha = word[len(APPROVAL_SHA_MARKER):]
                            return sha
        return None

    branch_name = pull_request.head.ref
    branch_sha = pull_request.head.sha.lower()
    ticket_id = branch_name.split('-')[0]

    reviewers = getReviewers(pull_request.body)
    checkReviewApproval(
        comments=comments, reviewers=reviewers, sha=branch_sha)

    review_title = getReviewTitle(pull_request.title, ticket_id)
    commit_message = "[#%s] %s" % (ticket_id, review_title)

    return (pull_request, commit_message)


@task
@consume_args
def merge_init(args):
    """
    Merge the current branch into master, without a commit.
    """
    if len(args) != 2:
        print "Usage: TOKEN GITHUB_PULL_ID"
        sys.exit(1)

    from git import GitCommandError, Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branch_name = repo.head.ref.name
    if branch_name in ['master', 'production']:
        print "You can not merge the main branches."
        sys.exit(1)

    try:
        int(branch_name.split('-')[0])
    except:
        print "Branch name '%s' does not start with ticket id." % (
            branch_name)
        sys.exit(1)

    # Check pull request details on Github.
    (pull_request, message) = _review_properties(
        token=args[0], pull_id=args[1])

    remote_sha = pull_request.head.sha.lower()
    remote_name = pull_request.head.ref

    from git import Repo
    repo = Repo(os.getcwd())
    remote_name = repo.head.ref.name
    local_sha = repo.head.commit.hexsha

    if remote_sha != local_sha:
        print "Local branch and review branch are at different revision."
        print "Local sha:  %s %s" % (local_sha, remote_name)
        print "Review sha: %s %s" % (remote_sha, remote_name)
        sys.exit(1)

    # Clear any unused files from this repo.
    print git.clean(force=True, quiet=True)

    # Buildbot repos don't have a remote configured.
    try:
        print git.remote(
            'add', 'origin',
            '%s%s.git' % (
                SETUP['repository']['push_uri'],
                SETUP['repository']['name'],
                ),
            )
    except GitCommandError:
        pass

    try:
        # Switch to master
        try:
            repo.heads['master'].checkout()
        except IndexError:
            # It looks we don't have a master branch.
            # Let's get it.
            repo.remotes['origin'].fetch()
            print git.checkout('origin/master', b='master')

        # Merge original branch
        print git.merge(branch_name, no_commit=True, no_ff=True)

        # Check for merge conflicts.
        result = git.ls_files(unmerged=True).split('\n')
        result = [line.strip() for line in result if line.strip()]
        if result:
            print "The following files have conflicts:"
            print "\n".join(result)
            sys.exit(1)

    except GitCommandError, error:
        print "Failed to run git command."
        print str(error)
        sys.exit(1)

    # Check linter before running other tests.
    lint()


@task
@consume_args
def merge_commit(args):
    """
    Commit the merge and push changes.
    """
    if len(args) < 3:
        print "Usage: TOKEN GITHUB_PULL_ID AUTHOR"
        sys.exit(1)

    # Paver or bash has a bug so we rejoin author name.
    author = ' '.join(args[2:])

    from git import GitCommandError, Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branc_name = repo.head.ref.name

    if branc_name not in ['master', 'production']:
        print "You can not commit the merge outside of main branches."
        sys.exit(1)

    (pull_request, message) = _review_properties(
        token=args[0], pull_id=args[1])

    try:
        git.commit(author=author, message=message)
        origin = repo.remotes.origin
        origin.push()
    except GitCommandError, error:
        print "Failed to run git commit."
        print str(error)
        sys.exit(1)


@task
@consume_args
def pqm(args):
    """
    Submit the branch to pqm.

    test_remote PULL_ID
    """
    if len(args) != 1:
        print 'Please specify the pull request id for this branch.'
        sys.exit(1)

    result = pave.git.status()
    if result:
        print 'Please commit all files and get review approval.'
        print 'PQM canceled.'
        sys.exit(1)

    try:
        pull_id = int(args[0])
    except:
        print "Pull id in bad format. It must be an integer."
        sys.exit(1)

    repo_name = SETUP['repository']['name'].lower()

    builder = '--builder=%s-pqm' % (repo_name)
    pull_id = '--properties=pull_id=%s' % (args[0])
    new_args = [builder, pull_id]
    environment.args = new_args
    buildbot_try(new_args)
