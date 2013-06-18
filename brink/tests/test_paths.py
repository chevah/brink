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
    Unit tests for `which` brink command.
    """

    def setUp(self):
        self.command = mk.string()
        self.command_exe_path = u'bogus/path/%s.exe' % self.command
        self.command_bat_path = u'bogus/path/%s.bat' % self.command

        self._path_exists = paths.path_exists

        super(TestWhich, self).setUp()

    def tearDown(self):
        paths.path_exists = self._path_exists

        super(TestWhich, self).tearDown()

    def test_which_expanded_paths_file_not_exists(self):
        """
        """
        def path_exists(path):
            return False

        paths.path_exists = path_exists

        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(self.command_exe_path)
        extra_paths.append(self.command_bat_path)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)

    def test_which_expanded_paths_not_found(self):
        """
        """
        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(u'bogus')
        extra_paths.append(mk.string())

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)

    def test_which_expanded_paths_exits(self):
        """
        """
        def path_exists(path):
            return path == self.command_bat_path

        paths.path_exists = path_exists

        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(self.command_exe_path)
        extra_paths.append(self.command_bat_path)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertEqual(self.command_bat_path, result)
