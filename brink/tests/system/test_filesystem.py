# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
System tests for `BrinkFilesystem`.
"""
import os

from brink.testing import BrinkTestCase, mk

from brink.filesystem import BrinkFilesystem


class TestBrinkFilesystem(BrinkTestCase):
    """
    System tests for `BrinkFileSystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()

        self.brink_fs = BrinkFilesystem()

    def test_which_file_exists_posix(self):
        """
        Returns the full path to the specified command if the file is
        found.
        """
        if os.name == 'nt':
            raise self.skipTest("Unix specific test.")

        self.test_segments = mk.fs.createFileInTemp()
        file_name = self.test_segments[-1:][0]
        folder_segments = self.test_segments[:-1]
        folder = mk.fs.getRealPathFromSegments(folder_segments)
        folder = folder.encode('utf-8')
        extra_paths = [mk.ascii(), folder]
        command = file_name.encode('utf-8')
        full_path = mk.fs.getRealPathFromSegments(self.test_segments)
        full_path = full_path.encode('utf-8')

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertEqual(full_path, result)

    def test_which_file_exists_nt(self):
        """
        Returns the full path to the specified command if a valid executable
        file is found.
        """
        if os.name != 'nt':
            raise self.skipTest("Windows specific test.")

        self.test_segments = mk.fs.createFileInTemp(suffix='.bat')
        file_name = self.test_segments[-1:][0]
        folder_segments = self.test_segments[:-1]
        folder = mk.fs.getRealPathFromSegments(folder_segments)
        extra_paths = [mk.string(), folder]
        command = file_name.replace('.bat', '')
        full_path = mk.fs.getRealPathFromSegments(self.test_segments)

        result = self.brink_fs.which(command, extra_paths=extra_paths)

        self.assertEqual(full_path, result)

    def test_which_not_exist(self):
        """
        Returns `None` if the specified command could not be found.
        """
        unknown_command = mk.string()

        result = self.brink_fs.which(unknown_command)

        self.assertIsNone(result)
