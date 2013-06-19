# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Test for paths classes and helpers.
"""
import os

from brink import paths

from chevah.utils.testing import UtilsTestCase
from chevah.utils.testing.mockup import manufacture as mk


class TestWhich(UtilsTestCase):
    """
    System tests for `which` brink command.
    """

    @classmethod
    def setUpClass(cls):
        if os.name != 'nt':
            raise cls.skipTest('Only Windows systems supported.')

    def setUp(self):
        super(TestWhich, self).setUp()

        self.command = mk.string()
        self.fs = mk.makeLocalTestFilesystem()
        self.segments = self.fs.createFileInTemp(
            content='@echo off', suffix='.bat'
            )
        path = self.fs.getRealPathFromSegments(self.segments)

        self.path_bat_file = path
        self.path_exe_file = path.replace('.bat', '.exe')

        self.extra_paths = []
        self.extra_paths.append(mk.string())
        self.extra_paths.append(self.path_exe_file)

    def tearDown(self):
        self.fs.deleteFile(self.segments)

        super(TestWhich, self).tearDown()

    def test_expanded_paths_file_exists(self):
        """
        Returns the full path to the specified command if found and the
        executable file exists.
        """
        self.extra_paths.append(self.path_bat_file)

        result = paths.which(self.command, extra_paths=self.extra_paths)

        self.assertEqual(self.path_bat_file, result)

    def test_expanded_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is found but the file does
        not exist.
        """
        result = paths.which(self.command, extra_paths=self.extra_paths)

        self.assertIsNone(result)

    def test_expanded_paths_invalid(self):
        """
        Returns `None` if the specified command is not found in the
        `expanded_paths` list.
        """
        extra_paths = []
        extra_paths.append(mk.string())
        extra_paths.append(mk.string())

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)
