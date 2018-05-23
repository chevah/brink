# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Helpers for testing the project.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )

from chevah.compat.testing import ChevahTestCase, conditionals, mk

# Shut up the linter.
conditionals
mk


class BrinkTestCase(ChevahTestCase):
    """
    TestCase dedicated to brink project.
    """
