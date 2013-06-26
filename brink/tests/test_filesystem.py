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

    def test_which_extra_paths_not_defined(self):
        """
        Returns `None` if the command could not be found in system path or
        in the `extra_paths` argument.
        """
        folder = mk.string()
        command = mk.string()
        extra_paths = [mk.string()]

        def _folderListing(path):
            result = []
            if folder == path:
                result.append(command)
            return result

        self.brink_fs._getFolderListing = _folderListing

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)

    def test_which_extra_paths_file_found(self):
        """
        Returns the full path to the specified command if found and the
        executable file exists.
        """
        folder = mk.string()
        command = mk.string()
        full_path_to_command = os.path.join(folder, command)
        extra_paths = [mk.string(), folder]

        def _folderListing(path):
            result = []
            if folder == path:
                result.append(command)
            return result

        self.brink_fs._getFolderListing = _folderListing

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertEqual(full_path_to_command, result)

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

    def test_parseUnixPaths(self):
        """
        It uses : to separate path entries.
        """
        path1 = mk.string()
        path2 = mk.string()
        paths = u'%s:%s' % (path1, path2)

        result = self.brink_fs._parseUnixPaths(paths)

        self.assertEqual(2, len(result))
        self.assertContains(path1, result)
        self.assertContains(path2, result)

    def test_parseWindowsPaths(self):
        """
        It uses ; to separate path entries.
        """
        path1 = mk.string()
        path2 = mk.string()
        paths = u'%s;%s' % (path1, path2)

        result = self.brink_fs._parseWindowsPaths(paths)

        self.assertEqual(2, len(result))
        self.assertContains(path1, result)
        self.assertContains(path2, result)

    def test_findCommand_ok_posix(self):
        """
        On Unix systems it does not validate Windows type executable files
        as valid commands.
        """
        if os.name == 'nt':
            raise self.skipTest("Unix specific test.")

        command = mk.string()
        path = mk.string()
        full_path = '%s/%s' % (path, command)
        exe_command = '%s.exe' % command
        bat_command = '%s.exe' % command
        cmd_command = '%s.exe' % command
        files = [exe_command, bat_command, cmd_command]
        self.brink_fs._isValidSystemPath = self.Mock(return_value=True)
        self.brink_fs._getFolderListing = self.Mock(return_value=files)

        result = self.brink_fs._findCommand(command, path)

        self.assertIsNone(result)

        files.append(command)

        result = self.brink_fs._findCommand(command, path)

        self.assertEqual(full_path, result)

    def test_findCommand_ok_windows(self):
        """
        On Windows systems it validates files with .exe/.bat/.cmd extensions
        as valid commands.
        """
        if os.name != 'nt':
            raise self.skipTest("Windows specific test.")

        command = mk.string()
        path = mk.string()
        exe_command = '%s.exe' % command
        bat_command = '%s.exe' % command
        cmd_command = '%s.exe' % command
        full_path = '%s\%s' % (path, exe_command)
        files = [exe_command, bat_command, cmd_command]
        self.brink_fs._isValidSystemPath = self.Mock(return_value=True)
        self.brink_fs._getFolderListing = self.Mock(return_value=files)

        result = self.brink_fs._findCommand(command, path)

        self.assertEqual(full_path, result)

    def test_findCommand_checks_folders_only(self):
        """
        Returns `None` if the path argument is not a folder.
        """
        command = mk.string()
        path = mk.string()
        self.brink_fs._isValidSystemPath = self.Mock(return_value=False)

        result = self.brink_fs._findCommand(command, path)

        self.assertIsNone(result)

    def test_findCommand_no_result(self):
        """
        Returns `None` if the command could not be found in the specified
        path.
        """
        command = mk.string()
        path = mk.string()
        files = [mk.string(), mk.string()]
        self.brink_fs._isValidSystemPath = self.Mock(return_value=True)
        self.brink_fs._getFolderListing = self.Mock(return_value=files)

        result = self.brink_fs._findCommand(command, path)

        self.assertIsNone(result)
