# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Brink build system.
"""
import os


def get_module_path():
    """
    Return the path to this module.
    """
    return os.path.dirname(__file__)


# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
