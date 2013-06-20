# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Unit tests for brink filesystem.
"""
import os

from chevah.utils.testing import UtilsTestCase
from chevah.utils.testing.mockup import manufacture as mk

from brink.filesystem import BrinkFilesystem


class TestBrinkFilesystem(UtilsTestCase):
    """
    Unit tests for `BrinkFilesystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()

        self.fs = BrinkFilesystem()

    def test_which_extra_paths_file_found(self):
        """
        Returns `None` if the command could not be found in system path or
        in the `extra_paths` argument.

        Returns the full path to the specified command if found and the
        executable file exists.
        """
        if os.name != 'nt':
            raise self.skipTest("Functionality implemented only on Windows.")

        command = mk.string()
        path_bat_file = '%s.bat' % command
        path_exe_file = '%s.exe' % command
        extra_paths = [mk.string(), path_exe_file]

        def path_exists(path):
            """
            Dummy method that will validate only the .bat file path as
            existing.
            """
            return path_bat_file == path

        self.fs._pathExists = path_exists

        result = self.fs.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)

        extra_paths.append(path_bat_file)

        result = self.fs.which(command, extra_paths=extra_paths)

        self.assertEqual(path_bat_file, result)

    def test_which_extra_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is defined in `extra_paths`
        but the actual, executable, file does not exist.
        """
        if os.name != 'nt':
            raise self.skipTest("Functionality implemented only on Windows.")

        self.fs._pathExists = mk.makeMock()
        self.fs._pathExists.return_value = False

        command = mk.string()
        path_exe_file = '%s.exe' % command

        extra_paths = [mk.string(), path_exe_file]

        result = self.fs.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)
