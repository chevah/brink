# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Helpers for testing the project.
"""

from chevah.utils.testing import UtilsTestCase, manufacture as mk

# Shut up the linter.
mk


class BrinkTestCase(UtilsTestCase):
    """
    TestCase dedicated to brink project.
    """
