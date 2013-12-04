# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Helpers for testing the project.
"""

from chevah.empirical import EmpiricalTestCase, mk

# Shut up the linter.
mk


class BrinkTestCase(EmpiricalTestCase):
    """
    TestCase dedicated to brink project.
    """
