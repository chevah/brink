# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Brink build system.
"""
from __future__ import absolute_import, unicode_literals

import os


def get_module_path():
    """
    Return the path to this module.
    """
    return os.path.dirname(__file__)
