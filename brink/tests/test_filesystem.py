# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Unit tests for brink filesystem.
"""
import os

from brink.testing import BrinkTestCase, mk

from brink.filesystem import BrinkFilesystem


class TestBrinkFilesystem(BrinkTestCase):
    """
    Unit tests for `BrinkFilesystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()

        self.brink_fs = BrinkFilesystem()
        self.brink_fs._isValidSystemPath = self.Mock(return_value=True)

    def test_which_extra_paths_file_found(self):
        """
        Returns `None` if the command could not be found in system path or
        in the `extra_paths` argument.

        Returns the full path to the specified command if found and the
        executable file exists.
        """
        folder = mk.string()
        command = mk.string()
        bat_file = '%s.bat' % command
        path_bat_file = os.path.join(folder, bat_file)
        extra_paths = [mk.string()]

        def _folderListing(path):
            if folder == path:
                return [bat_file]
            return []

        self.brink_fs._getFolderListing = _folderListing

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)

        extra_paths.append(folder)

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertEqual(path_bat_file, result)

    def test_which_extra_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is defined in `extra_paths`
        but the actual, executable, file does not exist.
        """
        command = mk.string()
        path_exe_file = '%s.exe' % command
        self.brink_fs._getFolderListing = self.Mock(return_value=[])
        extra_paths = [mk.string(), path_exe_file]

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)
