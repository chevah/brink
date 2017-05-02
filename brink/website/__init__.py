"""
Helper for testing brink documentation tasks.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
import os


def get_module_path():
    """
    Return the path to this module.
    """
    return os.path.abspath(os.path.dirname(__file__))
