# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import with_statement
import os


class ProjectPaths(object):
    """
    Container for common path used by the build system.
    """

    def __init__(self, os_name, build_folder_name, folders, filesystem):
        self.fs = filesystem
        self._os_name = os_name
        self.project = self._getProjectPath()
        self.product = os.path.abspath('.')
        self.build = self.fs.join([self.product, build_folder_name])
        self.deps = self.fs.join([self.project, folders['deps']])
        self.brink = self.fs.join([self.project, folders['brink']])
        self.pypi = self.fs.join([self.brink, 'cache', 'pypi'])
        self.dist = self.fs.join([self.product, folders['dist']])
        self.publish = self.fs.join([self.product, folders['publish']])
        self.python_executable = self.getPythonExecutable(os_name=os_name)
        self.python_scripts = self.getPythonScripts()
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

    def getPythonExecutable(self, os_name=None):
        """
        Return the path to the Python executable for an OS.
        """
        if os_name is None:
            os_name = os.name

        if os_name == 'windows':
            return self.fs.join(['lib', 'python.exe'])
        else:
            return self.fs.join(['bin', 'python'])

    def getPythonScripts(self, os_name=None):
        """
        Return the path to the Python scripts folder for an OS.
        """
        if os_name is None:
            os_name = os.name

        if os_name == 'nt':
            return self.fs.join(['lib', 'Scripts'])
        else:
            return self.fs.join(['bin'])


def which(command, extra_paths=None):
    """
    Locate the path to `command`.
    """
    from twisted.python.procutils import which

    paths = which(command)
    if extra_paths:
        paths.extend(extra_paths)

    if not paths:
        return None
    elif len(paths) > 1:
        if os.name == 'nt':
            # On Windows we only return the first file with an "executable"
            # extension.
            for path in paths:
                if (path.lower().endswith('.exe') or
                        path.lower().endswith('.cmd') or
                        path.lower().endswith('.bat')
                ):
                    return path
        else:
            # On Unix we return the first path.
            return paths[0]
    else:
        # Only one path found.
        return paths[0]
