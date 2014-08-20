# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
"""
PQM related targets for paver.
"""
import os
import sys

from paver.easy import call_task, task
from paver.tasks import environment, consume_args, cmdopts

from brink.utils import BrinkPaver
from brink.configuration import SETUP

pave = BrinkPaver(SETUP)


@task
@consume_args
def github(args):
    """
    Helpers for interacting with GitHub website.

    Admin commands:

    * token PASSWORD - Get a new token to be used by PQM."
    """
    def github_help():
        print "Usage: github COMMNAND ARGUMENTS."
        print ""
        print "List of commands:"
        print "    open - Open the repository in githuh."
        print "    review  - Open the page for creating a new pull request"

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

    if args[0] == 'token':
        print _github_token(username='chevah-robot', password=args[1])
        sys.exit(0)


def _github_token(username, password):
    """
    Return an authorization token from GitHub for chevah-robot account.
    """
    from github import Github

    github = Github(username, password, user_agent='pygithub/chevah-pqm')
    user = github.get_user()
    authorization = user.create_authorization(
        scopes=['repo'],
        note='Chevah PQM',
        note_url='http://build.chevah.com/waterfall')
    return authorization.token


def _get_repo(token, repo):
    """
    Return GitHub repository.
    """
    from github import Github
    github = Github(token, user_agent='pygithub/chevah-pqm')
    return github.get_repo(repo)


def _get_pull(repo, pull_id):
    """
    Return the pull request details.
    """
    from github import GithubException
    try:
        return repo.get_pull(pull_id)

    except GithubException, error:
        print "Failed to get GitHub details"
        print str(error)
        sys.exit(1)


def _review_properties(token, pull_id):
    """
    Helper for calling this task from multiple places, without messing
    with paver arguments.
    """
    from github import GithubException
    from chevah.github_hooks_server.handler import Handler
    handler = Handler(trac_url='mock')
    try:
        repo = _get_repo(token=token, repo=SETUP['github']['repo'])
        pull_request = _get_pull(repo, pull_id=pull_id)

        # Fail early if branch can not be merged.
        if not pull_request.mergeable:
            print "GitHub said that branch can not be merged."
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

        # Make sure first letter is upper case.
        result = result[0].upper() + result[1:]

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
                    reviewer, 'Approved at "%s". Branch at "%s".' % (
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

            sha = handler._getApprovedSHA(content)
            if sha:
                return sha

        return None

    branch_name = pull_request.head.ref
    branch_sha = pull_request.head.sha.lower()
    ticket_id = pave.getTicketIDFromBranchName(branch_name)

    reviewers = handler._getGitHubReviewers(pull_request.body)
    checkReviewApproval(
        comments=comments, reviewers=reviewers, sha=branch_sha)

    review_title = getReviewTitle(pull_request.title, ticket_id)
    commit_message = "[#%s] %s" % (ticket_id, review_title)

    return (pull_request, commit_message)


def _get_environment(name, default=None):
    """
    Get environment variable.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise AssertionError(
            'Variable %s not found in environment !' % (name))
    return value


def _get_github_environment():
    """
    Get GitHub data from environment.
    """

    pull_id = _get_environment('GITHUB_PULL_ID')
    try:
        pull_id = int(pull_id)
    except:
        print "Invalid pull_id: %s" % str(pull_id)
        sys.exit(1)

    return {
        'token': _get_environment('GITHUB_TOKEN'),
        'pull_id': pull_id,
        }


@task
def merge_init():
    """
    Merge the current branch into master, without a commit.

    Environment variables:
    * GITHUB_PULL_ID
    * GITHUB_TOKEN
    """
    github_env = _get_github_environment()

    from git import GitCommandError, Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branch_name = _get_environment('BRANCH', repo.head.ref.name)
    if branch_name in ['master', 'production']:
        print "You can not merge the main branches."
        sys.exit(1)

    try:
        int(pave.getTicketIDFromBranchName(branch_name))
    except:
        print "Branch name '%s' does not start with ticket id." % (
            branch_name)
        sys.exit(1)

    # Check pull request details on Github.
    (pull_request, message) = _review_properties(
        token=github_env['token'], pull_id=github_env['pull_id'])

    pr_branch_name = pull_request.head.ref
    remote_sha = pull_request.head.sha.lower()
    local_sha = repo.head.commit.hexsha

    if remote_sha != local_sha:
        print "Local branch and review branch are at different revision."
        print "Local sha:  %s %s" % (local_sha, branch_name)
        print "Review sha: %s %s" % (remote_sha, pr_branch_name)
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
            print "Switch to master branch"
            print repo.heads['master'].checkout()
            print "Update master"
            print git.pull()
        except IndexError:
            print "We don't have a master branch."
            print "Let's get it."
            print repo.remotes['origin'].fetch()
            print git.checkout('origin/master', b='master')

        print "Merge original branch with squash and no commit."
        print git.merge(
            local_sha, no_commit=True, squash=True)

        print "Check for merge conflicts."
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
    finally:
        print "Go back to initial branch."
        # Since we merge with squash... we don't have a real merge so we
        # can not use merge --abort here.
        print git.reset(hard=True)
        print repo.heads[branch_name].checkout()


@task
@consume_args
def merge_commit(args):
    """
    Commit the merge and push changes.

    Exit code:
    * 0 - ok
    * 1 - failure
    * 2 - warning

    Environment variables:
    * GITHUB_PULL_ID
    * GITHUB_TOKEN
    * TEST_AUTHOR
    """
    github_env = _get_github_environment()

    # Paver or bash has a bug so we rejoin author name.
    author = _get_environment('TEST_AUTHOR')

    from git import GitCommandError, Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branch_name = repo.head.ref.name

    (_, message) = _review_properties(
        token=github_env['token'], pull_id=github_env['pull_id'])

    try:
        # Merge branch into master.
        print "Go to master"
        repo.heads['master'].checkout()
        print "Update master"
        print git.pull()
        print "Merge branch"
        print git.merge(branch_name, squash=True, no_commit=True)
        print "Commit message"
        print git.commit(author=author, message=message)
        # Push merged changes.
        for state in repo.remotes.origin.push():
            print state.summary
            if '[rejected]' in state.summary:
                print 'Failed to push changes.'
                sys.exit(1)
        # Delete original branch.
        print repo.remotes.origin.push(branch_name, delete=True)
    except GitCommandError, error:
        print "Failed to run git commit."
        print str(error)
        sys.exit(1)


@task
@consume_args
def pqm(args):
    """
    Submit the branch to PQM.

    Arguments: PULL_ID
    """
    if len(args) != 1:
        print 'Please specify the pull request id for this branch.'
        sys.exit(1)

    result = pave.git.status()
    if result:
        print 'Please commit all files and get review approval.'
        print 'PQM cancelled.'
        sys.exit(1)

    try:
        pull_id = int(args[0])
    except:
        print "Pull id in bad format. It must be an integer."
        sys.exit(1)

    pull_id_property = '--properties=github_pull_id=%s' % (pull_id)
    arguments = ['gk-merge', pull_id_property]
    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)


@task
@cmdopts([
    ('target=', None, 'Base repository URI.'),
    ('latest=', None, '`yes` if this release is for latest version.'),
    (
        'pull-id=', None,
        'ID of GitHub pull request for release. Required only for production.'
        ),
    ])
@task
def rqm(options):
    """
    Submit the branch to release manager.
    """
    result = pave.git.status()
    if result:
        print 'Please commit all files before requesting the release.'
        print 'RQM cancelled.'
        sys.exit(1)

    target = pave.getOption(options, 'rqm', 'target', default_value=None)
    if target == 'production':
        target = 'gk-release'
    else:
        target = 'gk-release-staging'

    test_arguments = 'latest=%s' % pave.getOption(
        options, 'rqm', 'latest', default_value='no')

    pull_id_property = '--properties=github_pull_id=%s' % pave.getOption(
        options, 'rqm', 'pull_id', default_value='not-defined')

    arguments = [target, pull_id_property, test_arguments]
    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)


@task
@cmdopts([
    ('target=', None, 'production | staging'),
    ])
def publish(options):
    """
    Publish download files and documentation.

    Environment variables:
    * TEST_ARGUMENTS - [latest=yes|latest=no]
    """

    target = pave.getOption(
        options, 'publish', 'target', default_value='staging')

    latest = _get_environment('TEST_ARGUMENTS', default='latest=no')
    if latest == 'latest=yes':
        latest = 'yes'
    else:
        latest = 'no'

    arguments = [target, latest]
    call_task('publish_documentation', args=arguments)
    call_task('publish_distributables', args=arguments)
