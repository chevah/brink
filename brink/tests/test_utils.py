# Copyright (c) 2013 Adi Roiban.
# See LICENSE for details.
"""
Tests for brink utilities.
"""
from brink.testing import BrinkTestCase

from brink.utils import BrinkPaver


class TestBrinkPaver(BrinkTestCase):
    """
    Tests for BrinkPaver.
    """

    def test_initialization(self):
        """
        It is initialized with a setup dictionary.
        """
        setup = {
            'folders': {
                'source': 'brink',
                'dist': 'dist',
                'publish': 'publish',
                }
            }

        result = BrinkPaver(setup=setup)

        self.assertEqual(setup, result.setup)
