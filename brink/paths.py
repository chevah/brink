# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import with_statement
import os


def _p(path):
    '''
    Shortcut for converting a list to a path using os.path.join.
    '''
    result = os.path.join(*path)
    if os.name == 'posix':
        result = result.encode('utf-8')
    return result


class ProjectPaths(object):
    """
    Container for common path used by the build system.
    """

    def __init__(self, os_name, build_folder_name, folders):
        self._os_name = os_name
        self.project = self._getProjectPath()
        self.product = os.path.abspath('.')
        self.build = _p([self.product, build_folder_name])
        self.deps = _p([self.project, folders['deps']])
        self.brink = _p([self.project, folders['brink']])
        self.pypi = _p([self.brink, 'cache', 'pypi'])
        self.dist = _p([self.product, folders['dist']])
        self.publish = _p([self.product, folders['publish']])
        self.python_executable = self.getPythonExecutable(os_name=os_name)
        self.brink_package = os.path.dirname(__file__)

    def _getProjectPath(self):
        '''Return the root of Chevah project.'''
        cwd = os.getcwd()
        parent_folder, curent_folder = os.path.split(cwd)
        while (parent_folder and not parent_folder.endswith('chevah')):
            parent_folder, curent_folder = os.path.split(parent_folder)
        if not parent_folder:
            print 'Failed to get project root.'
            exit()
        return parent_folder

    def getPythonExecutable(self, os_name):
        '''Return the path to pyhon bin for target.'''
        if os_name == 'windows':
            return _p(['lib', 'python.exe'])
        else:
            return _p(['bin', 'python'])
