# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
"""

from chevah.empirical.testcase import ChevahTestCase

from brink.qm import (
    _close_pull,
    _get_pull,
    _get_repo,
    _open_pull,
    )


class TestQMGitHub(ChevahTestCase):
    """
    Test for QM GitHub operations.

    These are manual tests since a token need to be provided.
    """

    # Please set this token, otherwise all tests are skipped.
    # We don't commit it since this repo is public.
    TOKEN = None
    REPO_NAME = 'chevah/seesaw'

    def setUp(self):
        if not self.TOKEN:
            raise self.skipTest()
        self.repo = _get_repo(repo=self.REPO_NAME, token=self.TOKEN)
        super(TestQMGitHub, self).setUp()

    def test_get_pull(self):
        """
        Return pull request details.
        """
        result = _get_pull(self.repo, pull_id=1)

        self.assertEqual(u'seesaw', result.base.repo.name)

    def test_close_pull(self):
        """
        Closes the pull request.
        """
        # Make sure the pull is opened.
        message = u'Test close message.'
        _open_pull(self.repo, pull_id=1)

        result = _close_pull(self.repo, pull_id=1, message=message)

        self.assertEqual(u'closed', result.state)
        # Get the pull again to check state.
        pull = _get_pull(self.repo, pull_id=1)
        self.assertEqual(u'closed', pull.state)
        last_comment = list(pull.get_issue_comments())[-1]
        self.assertEqual(message, last_comment.body)
