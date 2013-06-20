# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
System tests for `BrinkFilesystem`.
"""
from chevah.utils.testing import UtilsTestCase

from brink.filesystem import BrinkFilesystem
from chevah.utils.testing.mockup import manufacture as mk


class TestBrinkFilesystem(UtilsTestCase):
    """
    System tests for `BrinkFileSystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()

        self.brink_fs = BrinkFilesystem()
        self.fs = mk.makeLocalTestFilesystem()
        self.test_segments = self.fs.createFileInTemp(
            content='@echo off', suffix='.bat'
            )
        self.path = self.fs.getRealPathFromSegments(self.test_segments)
        self.file_name = self.test_segments[-1:][0]

    def test_exists_file_exists(self):
        """
        Returns the full path to the specified command if found and the
        executable file exists.
        """
        command = self.file_name.replace('.bat', '')
        command = command.encode('utf-8')
        path_bat_file = self.path
        path_exe_file = self.path.replace('.bat', '.exe')
        extra_paths = [mk.string(), path_exe_file, path_bat_file]

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertEqual(path_bat_file, result)

    def test_exists_file_not_exists(self):
        """
        Returns `None` if the specified command is defined in `extra_paths`
        but the actual, executable, file does not exist.
        """
        unknown_command = mk.string()
        unknown_command = unknown_command.encode('utf-8')
        extra_paths = [mk.string(), mk.string(), mk.string()]

        result = self.brink_fs.which(unknown_command, extra_paths=extra_paths)

        self.assertIsNone(result)
