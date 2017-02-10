# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Helpers for testing the project.
"""

from chevah.compat.testing import ChevahTestCase, mk

# Shut up the linter.
mk


class BrinkTestCase(ChevahTestCase):
    """
    TestCase dedicated to brink project.
    """
