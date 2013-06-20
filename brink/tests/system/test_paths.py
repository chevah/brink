# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Test for paths classes and helpers.
"""
import os

from chevah.utils.testing import UtilsTestCase
from chevah.utils.testing.mockup import manufacture as mk

from brink import paths


class TestPathsWhichWindows(UtilsTestCase):
    """
    System tests for `which` brink command.
    """

    @classmethod
    def setUpClass(cls):
        super(TestPathsWhichWindows, cls).setUpClass()

        if os.name != 'nt':
            message = 'Feature is implemented only on Windows platforms.'
            raise cls.skipTest(message)

    def setUp(self):
        super(TestPathsWhichWindows, self).setUp()

        self.command = mk.string()
        self.fs = mk.makeLocalTestFilesystem()
        self.test_segments = self.fs.createFileInTemp(
            content='@echo off', suffix='.bat'
            )
        self.path = self.fs.getRealPathFromSegments(self.test_segments)

    def test_which_extra_paths_file_exists(self):
        """
        Returns `None` if the command could not be found in system path or
        in the `extra_paths` argument.

        Returns the full path to the specified command if found and the
        executable file exists.
        """
        path_bat_file = self.path
        path_exe_file = self.path.replace('.bat', '.exe')

        extra_paths = []
        extra_paths.append(mk.string())
        extra_paths.append(path_exe_file)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)

        extra_paths.append(path_bat_file)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertEqual(path_bat_file, result)

    def test_which_extra_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is defined in `extra_paths`
        but the actual, executable, file does not exist.
        """
        path_exe_file = self.path.replace('.bat', '.exe')

        extra_paths = []
        extra_paths.append(mk.string())
        extra_paths.append(path_exe_file)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)
