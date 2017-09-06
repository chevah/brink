# Copyright (c) 2014 Adi Roiban.
# See LICENSE for details.
"""
Elevated tests for `BrinkFilesystem`.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
from brink.testing import BrinkTestCase

from brink.filesystem import BrinkFilesystem


class TestBrinkFilesystem(BrinkTestCase):
    """
    Tests for the filesystem running as elevated user.
    """

    def test_placeholder(self):
        """
        This is a simple test which will always pass.

        You can update the code to have it fail, to test the behaviour
        for a failed test.
        """
        BrinkFilesystem()

    def test_other_placeholder(self):
        """
        This is a another test which will always pass.
        """
        BrinkFilesystem()
