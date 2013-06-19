# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Test for paths classes and helpers.
"""
from brink import paths

from chevah.utils.testing import UtilsTestCase
from chevah.utils.testing.mockup import manufacture as mk


class TestWhich(UtilsTestCase):
    """
    System tests for `which` brink command.
    """

    def setUp(self):
        super(TestWhich, self).setUp()

        content = '@echo off'
        self.command = mk.string()
        self.fs = mk.makeLocalTestFilesystem()
        self.segments = self.fs.createFileInTemp(
            content=content, suffix='.bat'
            )
        path = self.fs.getPath(self.segments)

        self.path_bat_file = path
        self.path_exe_file = path.replace('.bat', '.exe')

        self.extra_paths = []
        self.extra_paths.append(mk.string())
        self.extra_paths.append(self.path_exe_file)

        def path_exists(path):
            segments = self.fs.getSegmentsFromRealPath(path)
            return self.fs.isFile(segments)

        # patch path_exists method to work in testing environment
        paths.path_exists = path_exists

    def tearDown(self):
        self.fs.deleteFile(self.segments)

        super(TestWhich, self).tearDown()

    def test_expanded_paths_file_exists(self):
        """
        Returns the full path to the specified command if found and the
        executable file exists.
        """
        self.extra_paths.append(self.path_bat_file)

        import pdb,sys; sys.stdout=sys.__stdout__;pdb.set_trace();
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
