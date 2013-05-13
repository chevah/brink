# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
"""
PQM related targets for paver.
"""
import os
import sys

from paver.easy import task
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
    from chevah.github_hooks_server.handler import Handler
    handler = Handler(trac_url='mock')
    try:
        repo_name = SETUP['github']['repo']
        github = Github(token, user_agent='pygithub/chevah-pqm')
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
        int(pave.getTicketIDFromBranchName(branch_name))
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
    from brink.pavement_commons import lint
    lint()


@task
@consume_args
def merge_commit(args):
    """
    Commit the merge and push changes.

    Exit code:
    * 0 - ok
    * 1 - failure
    * 2 - warning
    """
    if len(args) < 3:
        print "Usage: TOKEN GITHUB_PULL_ID AUTHOR"
        sys.exit(1)

    token = args[0]
    pull_id = args[1]
    # Paver or bash has a bug so we rejoin author name.
    author = ' '.join(args[2:])

    from git import GitCommandError, Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branch_name = repo.head.ref.name

    if branch_name not in ['master', 'production']:
        print "You can not commit the merge outside of main branches."
        sys.exit(1)

    (pull_request, message) = _review_properties(
        token=token, pull_id=pull_id)

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
    Submit the branch to PQM.

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

    arguments = ['pqm', '--properties=pull_id=%s' % (pull_id)]
    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)


@task
@cmdopts([
    ('target=', None, 'Base repository URI.'),
    ])
@task
def rqm(options):
    """
    Submit the branch to RQM.
    """
    result = pave.git.status()
    if result:
        print 'Please commit all files before requesting the release.'
        print 'RQM cancelled.'
        sys.exit(1)

    target = pave.getOption(options, 'rqm', 'target', default_value=None)
    if target != 'production':
        target = 'staging'

    arguments = ['rqm', '--properties=target=' + target]
    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)
