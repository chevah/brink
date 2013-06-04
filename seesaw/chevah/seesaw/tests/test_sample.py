"""
A simple sample tests.
"""

try:
    from unittest2 import TestCase
    TestCase  # Shut the linter.
except ImportError:
    from unittest import TestCase


class TestSample(TestCase):
    """
    Sample test case.
    """

    def test_sample(self):
        """
        Sample test.
        """
        self.assertEqual(2, 1 + 1)
