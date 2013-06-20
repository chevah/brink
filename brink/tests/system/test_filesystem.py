# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
System tests for `BrinkFilesystem`.
"""
from chevah.brink.testing import BrinkTestCase, mk

from brink.filesystem import BrinkFilesystem


class TestBrinkFilesystem(BrinkTestCase):
    """
    System tests for `BrinkFileSystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()
        self.brink_fs = BrinkFilesystem()
        self.test_segments = mk.fs.createFileInTemp(
            content='something', suffix='.bat')
        self.path = mk.fs.getRealPathFromSegments(self.test_segments)
        self.file_name = self.test_segments[-1:][0]

    def test_which_file_exists(self):
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

    def test_which_not_exist(self):
        """
        Returns `None` if the specified command could not be found.
        """
        unknown_command = mk.string()
        extra_paths = [mk.string(), mk.string(), mk.string()]

        result = self.brink_fs.which(unknown_command)

        self.assertIsNone(result)
