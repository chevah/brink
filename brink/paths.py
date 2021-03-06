# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
import os


class ProjectPaths(object):
    """
    Container for common path used by the build system.
    """

    def __init__(self, os_name, build_folder_name, folders, filesystem):
        build_folder_name = build_folder_name.rstrip(b'/')
        build_folder_name = build_folder_name.rstrip(b'\\')
        self.fs = filesystem
        self._os_name = os_name
        self.product = os.path.abspath(b'.')
        self.build = self.fs.join([self.product, build_folder_name])
        self.dist = self.fs.join([self.product, folders['dist']])
        self.publish = self.fs.join([self.product, folders['publish']])
        self.python_executable = self.getPythonExecutable(os_name=os_name)
        self.python_scripts = self.getPythonScripts()
        self.brink_package = os.path.dirname(__file__)

    def getPythonExecutable(self, os_name=None):
        """
        Return the path to the Python executable for an OS.
        """
        if os_name is None:
            os_name = os.name

        if os_name == 'win':
            return self.fs.join(['lib', 'python.exe'])
        else:
            return self.fs.join(['bin', 'python'])

    def getPythonScripts(self, os_name=None):
        """
        Return the path to the Python scripts folder for an OS.
        """
        if os_name is None:
            os_name = os.name

        if os_name in ['nt', 'win']:
            return self.fs.join(['lib', 'Scripts'])
        else:
            return self.fs.join(['bin'])
