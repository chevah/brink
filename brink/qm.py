# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
"""
PQM related targets for paver.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )

import os
import re
import sys

from paver.easy import call_task, needs, task
from paver.tasks import environment, consume_args, cmdopts

from brink.utils import BrinkPaver
from brink.configuration import SETUP

pave = BrinkPaver(SETUP)

RE_REVIEWERS = '.*reviewers{0,1}:{0,1} @.*'
RE_NEEDS_CHANGES = '.*needs{0,1}[\-_]changes{0,1}.*'
RE_CHANGES_APPROVED = '.*changes{0,1}[\-_]approved{0,1}.*'

_REQUIRED = object()


@task
@consume_args
def github(args):
    """
    Helpers for interacting with GitHub website.

    Admin commands:

    * token PASSWORD - Get a new token to be used by PQM."
    """
    def github_help():
        print("Usage: github COMMNAND ARGUMENTS.")
        print("")
        print("List of commands:")
        print("    open - Open the repository in githuh.")
        print("    review  - Open the page for creating a new pull request")

    if not len(args):
        github_help()
        sys.exit(1)

    import webbrowser

    if args[0] == 'open':
        webbrowser.open_new_tab(SETUP['repository']['github'])
        sys.exit(0)

    if args[0] == 'new':
        pave.git.publish()
        url = "%s/compare/%s?expand=1" % (
            SETUP['repository']['github'], pave.git.branch_name)
        webbrowser.open_new_tab(url)
        sys.exit(0)

    if args[0] == 'token':
        print(_github_token(username='chevah-robot', password=args[1]))
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
        note_url='https://buildbot.chevah.com')
    return authorization.token


def _get_repo(token):
    """
    Return GitHub repository.
    """
    from github import Github
    repo = SETUP['repository']['github'].split('/')
    repo = repo[-2] + '/' + repo[-1]
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
        print("Failed to get PR details")
        print(str(error))
        sys.exit(1)


def _get_protected_branch(repo, branch):
    """
    Return the branch details.
    """
    from github import GithubException
    try:
        return repo.get_protected_branch(branch)

    except GithubException as error:
        print("Failed to get protected branch details")
        print(str(error))
        sys.exit(1)


def _check_review_properties(token, pull_id):
    """
    Helper for calling this task from multiple places, without messing
    with paver arguments.
    """
    from github import GithubException
    try:
        repo = _get_repo(token=token)
        pull_request = _get_pull(repo, pull_id=pull_id)

        branch_name = pull_request.head.ref
        branch_sha = pull_request.head.sha.lower()

        # Fail early if branch can not be merged.
        if not pull_request.mergeable:
            print("\n> GitHub said that branch can not be merged.")
            print("Check PR %s for %s.\n" % (pull_id, branch_name))
            sys.exit(1)

        master = _get_protected_branch(repo, 'master')
        if master.protected and pull_request.mergeable_state == u'blocked':

            branch_commit = repo.get_commit(branch_sha)
            combined_status = branch_commit.get_combined_status().statuses
            if not combined_status:
                print('No branch status recorded by GitHub.')
            else:
                print('GitHub said that branch status is:')
                for status in combined_status:
                    print(" %s: %s (%s)" % (
                        status.context, status.state, status.description))

            print('The branch merge is blocked.')
            print('Check GitHub PR page for more details.')
            sys.exit(1)

        comments = []
        for comment in pull_request.get_issue_comments():
            comments.append((
                comment.user.login, comment.body, comment.updated_at))

        reviews = []
        for review in pull_request.get_reviews():
            # For now the GitHub review has no modified/update date.
            # We hope they are listed as they are made.
            reviews.append((review.user.login, review.state))

    except GithubException as error:
        print("Failed to get GitHub details")
        print(str(error))
        sys.exit(1)

    def getReviewTitle(content, ticket_id=None):
        """
        Parse line and return merge commit message.
        """
        result = content.strip()

        if len(result.split('\n')) > 1:
            print("Commit merge message should be single line.")
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

    def checkReviewApproval(comments, reviews, reviewers, sha):
        """
        Check comments to see if review was approved by all reviewers.
        """
        # We sort all comments in reverse order as they were updated.
        comments = sorted(
            comments, key=lambda comment: comment[2], reverse=True)

        # This is iterated multiple times.
        reviews = list(reversed(reviews))

        # Get last comment of each review and check that the review was
        # approved.
        pending_approval = []
        for reviewer in reviewers:
            if _approvedByReviewer(reviewer, comments, reviews):
                # All good.
                continue

            pending_approval.append((reviewer, 'Not approved yet.'))

        if pending_approval:
            print("Review not approved. See list below")
            for reason in pending_approval:
                print(reason)
            sys.exit(1)

    ticket_id = pave.getTicketIDFromBranchName(branch_name)

    reviewers = _getGitHubReviewers(pull_request.body)
    checkReviewApproval(
        comments=comments,
        reviews=reviews,
        reviewers=reviewers,
        sha=branch_sha,
        )

    review_title = getReviewTitle(pull_request.title, ticket_id)
    commit_message = "[#%s] %s" % (ticket_id, review_title)

    return (repo, pull_request, commit_message)


def _getGitHubReviewers(description):
    """
    Return a list of reviewers from review request description.
    """
    results = []
    for line in description.splitlines():
        result = re.match(RE_REVIEWERS, line)
        if not result:
            continue
        for word in line.split(' '):
            if word.startswith('@'):
                results.append(word[1:].strip())
    return results


def _approvedByReviewer(reviewer, comments, reviews):
    """
    Return `True` if reviewer has approved the changes.

    Approvals can come from multiple sources
    * GitHub comment
    * GitHub review actions
    """
    reviewer_approval = False

    # First try to see if the marker is in the comments.
    for author, content, updated_at in comments:
        action = _getActionFromComment(content)

        if reviewer != author:
            # Not a comment from reviewer.
            continue

        if action in ['needs-changes']:
            # We have a needs-changes, before an approval.
            reviewer_approval = False
            break

        if action == 'changes-approved':
            reviewer_approval = True
            break

    for author, state in reviews:
        if state == u'COMMENTED':
            # Just a comment. Can be ignored.
            continue

        if reviewer != author:
            # Not a review from reviewer.
            continue

        if state == u'CHANGES_REQUESTED':
            # Change requested before an approval.
            return False

        if state == u'APPROVED':
            return True

    # If we are hear, it means that we don't a review action from the author,
    # so we return the value from the comment action.
    return reviewer_approval


def _getActionFromComment(comment):
    """
    Return action associated with comment.

    Supported commands:
    * changes-approved - all good
    * needs-changes - more work
    """
    for line in comment.splitlines():
        line = line.lower()
        if re.match(RE_CHANGES_APPROVED, line):
            return 'changes-approved'
        if re.match(RE_NEEDS_CHANGES, line):
            return 'needs-changes'

    return 'no-action'


def _get_environment(name, default=_REQUIRED):
    """
    Get environment variable.
    """
    value = os.environ.get(name, default)
    if value is _REQUIRED:
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
    except Exception:
        print("Invalid pull_id: %s" % str(pull_id))
        sys.exit(1)

    token = _get_environment('GITHUB_TOKEN', default='')
    if token is '':
        token = None

    return {
        'token': token,
        'pull_id': pull_id,
        }


@task
def merge_init():
    """
    Check if current branch can be merged.

    Environment variables:
    * GITHUB_PULL_ID
    * GITHUB_TOKEN
    """
    github_env = _get_github_environment()

    from git import Repo
    repo = Repo(os.getcwd())
    git = repo.git

    branch_name = _get_environment('BRANCH', repo.head.ref.name)
    if branch_name in 'master' or branch_name.startswith('series-'):
        print("You can not merge the main branches.")
        sys.exit(1)

    try:
        int(pave.getTicketIDFromBranchName(branch_name))
    except Exception:
        print("Branch name '%s' does not start with ticket id." % (
            branch_name))
        sys.exit(1)

    # Check pull request details on Github.
    (_, pull_request, message) = _check_review_properties(
        token=github_env['token'], pull_id=github_env['pull_id'])

    pr_branch_name = pull_request.head.ref
    remote_sha = pull_request.head.sha.lower()
    local_sha = repo.head.commit.hexsha

    if remote_sha != local_sha:
        print("Local branch and review branch are at different revision.")
        print("Local sha:  %s %s" % (local_sha, branch_name))
        print("Review sha: %s %s" % (remote_sha, pr_branch_name))
        sys.exit(1)

    # Clear any unused files from this repo as this might be done
    # before a release.
    print('Clean repo')
    print(git.clean(force=True, quiet=True))


def _pr_merge(pr, commit_title, commit_message=None, merge_method=None):
    """
    Merge the PR.
    """
    from github import PullRequestMergeStatus
    post_parameters = dict()
    post_parameters["commit_title"] = commit_title

    if commit_message:
        post_parameters["commit_message"] = commit_message

    if merge_method:
        post_parameters["merge_method"] = merge_method

    headers, data = pr._requester.requestJsonAndCheck(
        "PUT",
        pr.url + "/merge",
        input=post_parameters,
        )
    return PullRequestMergeStatus.PullRequestMergeStatus(
        pr._requester, headers, data, completed=True)


@task
@needs('update_setup', 'deps')
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
    """
    from github import GithubException

    github_env = _get_github_environment()

    (repo, pull_request, message) = _check_review_properties(
        token=github_env['token'], pull_id=github_env['pull_id'])

    branch_name = pull_request.head.ref
    remote_sha = pull_request.head.sha.lower()

    try:
        print(_pr_merge(
            pr=pull_request,
            commit_title=pull_request.title,
            merge_method='squash',
            ))
        print(repo.create_git_tag(
            tag=SETUP['product']['version'],
            message='Tag created by RQM',
            object=remote_sha,
            type='commit',
            ))
        print("\n> PR Merged for %s. Tag created at %s.\n" % (
            branch_name, remote_sha,))

    except GithubException as error:
        print("\n> Failed to merge PR and create tag.\n")
        print(str(error))
        sys.exit(1)


@task
def pqm():
    """
    Submit the branch to PQM.

    Arguments AFTER all options: PULL_ID [--force-clean]
    """
    args = sys.argv[2:]

    if len(args) < 1:
        print('Please specify the pull request id for this branch.')
        sys.exit(1)

    result = pave.git.status()
    if result:
        print('Please commit all files and get review approval.')
        print('PQM canceled.')
        sys.exit(1)

    try:
        pull_id = int(args[0])
    except Exception:
        print("Pull id in bad format. It must be an integer.")
        sys.exit(1)

    pull_id_property = '--properties=github_pull_id=%s' % (pull_id)
    arguments = ['gk-merge', pull_id_property]

    if '--force-purge' in args:
        arguments.append('--properties=force_purge=yes')

    environment.args = arguments
    from brink.pavement_commons import test_remote
    test_remote(arguments)


@task
@cmdopts([
    ('target=', None, 'Base repository URI.'),
    ('latest=', None, '`no` if this release is not for latest version.'),
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
        print('Please commit all files before requesting the release.')
        print('RQM cancelled.')
        sys.exit(1)

    target = pave.getOption(options, 'rqm', 'target', default_value=None)
    if target == 'production':
        target = 'gk-release'
    else:
        target = 'gk-release-staging'

    test_arguments = 'latest=%s' % pave.getOption(
        options, 'rqm', 'latest', default_value='yes')

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
