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

    def test_expanded_paths_file_exists(self):
        """
        Returns the full path to the specified command if found and the
        executable file exists.
        """
        paths.path_exists = lambda x: x == self.command_bat_path

        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(self.command_exe_path)
        extra_paths.append(self.command_bat_path)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertEqual(self.command_bat_path, result)

    def test_expanded_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is found but the file does
        not exist.
        """
        paths.path_exists = lambda x: False

        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(self.command_exe_path)
        extra_paths.append(self.command_bat_path)

        result = paths.which(self.command, extra_paths=extra_paths)

        self.assertIsNone(result)

    def test_expanded_paths_invalid(self):
        """
        Returns `None` if the specified command is not found in the
        `expanded_paths` list.
        """
        paths.path_exists = lambda x: True

        command = mk.string()
        extra_paths = []
        extra_paths.append(u'bogus/path/')
        extra_paths.append(u'bogus')
        extra_paths.append(mk.string())

        result = paths.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)
