# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
# We don't want to depende on six/future so we have our own unicode handling.
# pylint: disable=unicode-builtin
"""
Unit tests for brink filesystem.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
import os

from brink.filesystem import BrinkFilesystem
from brink.testing import BrinkTestCase, mk

try:
    bool(type(unicode))
except NameError:
    unicode = str


class TestBrinkFilesystem(BrinkTestCase):
    """
    Unit tests for `BrinkFilesystem`.
    """

    def setUp(self):
        super(TestBrinkFilesystem, self).setUp()

        self.sut = BrinkFilesystem()
        self.sut._isValidSystemPath = self.Mock(return_value=True)

    def test_which_extra_paths_not_defined(self):
        """
        Returns `None` if the command could not be found in system path or
        in the `extra_paths` argument.
        """
        command = mk.string()
        extra_paths = [mk.string()]
        self.sut.listFolder = self.Mock(return_value=[])

        result = self.sut.which(command, extra_paths=extra_paths)

        self.assertIsNotNone(result)

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

        self.sut.listFolder = _folderListing

        result = self.sut.which(command, extra_paths=extra_paths)

        self.assertEqual(full_path_to_command, result)

    def test_which_extra_paths_file_not_exists(self):
        """
        Returns `None` if the specified command is defined in `extra_paths`
        but the actual, executable, file does not exist.
        """
        command = mk.string()
        path_exe_file = '%s.exe' % command
        self.sut.listFolder = self.Mock(return_value=[])
        extra_paths = [mk.string(), path_exe_file]

        result = self.sut.which(command, extra_paths=extra_paths)

        self.assertIsNone(result)

    def test_parseUnixPaths(self):
        """
        It uses : to separate path entries.
        """
        path1 = mk.string()
        path2 = mk.string()
        paths = u'%s:%s' % (path1, path2)

        result = self.sut._parseUnixPaths(paths)

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

        result = self.sut._parseWindowsPaths(paths)

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
        bat_command = '%s.bat' % command
        cmd_command = '%s.cmd' % command
        files = [
            exe_command,
            bat_command,
            cmd_command,
            ]
        self.sut.listFolder = self.Mock(return_value=files)

        result = self.sut._findCommand(command, path)

        self.assertIsNone(result)

        files.append(command)

        result = self.sut._findCommand(command, path)

        self.assertEqual(full_path, result)

    def test_findCommand_ok_windows(self):
        """
        On Windows systems it validates files with .exe extension before
        checking files without extension.
        """
        if os.name != 'nt':
            raise self.skipTest("Windows specific test.")

        command = mk.string()
        path = mk.string()
        exe_command = '%s.exe' % command
        full_path = '%s\%s' % (path, exe_command)
        files = [
            command,
            exe_command,
            ]
        self.sut.listFolder = self.Mock(return_value=files)

        result = self.sut._findCommand(command, path)

        self.assertEqual(full_path, result)

    def test_findCommand_ok_windows_with_extension(self):
        """
        On Windows systems it validates files with .exe extension, even
        when the command is specified with explicit .exe extension.
        """
        if os.name != 'nt':
            raise self.skipTest("Windows specific test.")

        command = mk.string()
        path = mk.string()
        exe_command = '%s.exe' % command
        full_path = '%s\%s' % (path, exe_command)
        files = [
            command,
            exe_command,
            ]
        self.sut.listFolder = self.Mock(return_value=files)

        result = self.sut._findCommand(exe_command, path)

        self.assertEqual(full_path, result)

    def test_findCommand_checks_folders_only(self):
        """
        Returns `None` if the path argument is not a folder.
        """
        command = mk.string()
        path = mk.string()
        self.sut._isValidSystemPath = self.Mock(return_value=False)

        result = self.sut._findCommand(command, path)

        self.assertIsNone(result)

    def test_findCommand_no_result(self):
        """
        Returns `None` if the command could not be found in the specified
        path.
        """
        command = mk.string()
        path = mk.string()
        files = [mk.string(), mk.string()]
        self.sut.listFolder = self.Mock(return_value=files)

        result = self.sut._findCommand(command, path)

        self.assertIsNone(result)

    def test_getSearchPaths_default(self):
        """
        It returns a list of paths from operating system environment
        variable.
        """
        if os.name == 'posix':
            paths = self.sut._parseUnixPaths(os.environ['PATH'])
        else:
            paths = self.sut._parseWindowsPaths(os.environ['PATH'])

        result = self.sut._getSearchPaths()

        self.assertEqual(paths, result)

    def test_getSearchPaths_with_extra(self):
        """
        If a list of extra paths if provided, it return a list with paths
        defined in the operating system, but with the list of extra paths
        prepended to the result.
        """
        path1 = mk.string
        path2 = mk.string
        if os.name == 'posix':
            path3 = self.sut._parseUnixPaths(os.environ['PATH'])[0]
        else:
            path3 = self.sut._parseWindowsPaths(os.environ['PATH'])[0]

        result = self.sut._getSearchPaths(extra_paths=[path1, path2])

        self.assertEqual(path1, result[0])
        self.assertEqual(path2, result[1])
        self.assertEqual(path3, result[2])

    def test_copyFolder_no_overwrite(self):
        """
        It can copy the folder without overwriting existing files.
        """
        source_segments = mk.fs.createFolderInTemp(prefix=u'src-')
        destination_segments = mk.fs.createFolderInTemp(prefix=u'dst-')
        self.addCleanup(lambda: mk.fs.deleteFolder(source_segments))
        self.addCleanup(lambda: mk.fs.deleteFolder(destination_segments))
        existing_name = mk.makeFilename()
        existing_source_segments = source_segments + [existing_name]
        existing_destination_segments = destination_segments + [existing_name]
        mk.fs.createFile(existing_source_segments, content=b'source-exist')
        mk.fs.createFile(
            existing_destination_segments, content=b'destination-exist')
        mk.fs.createFile(source_segments + [u'other-file'], content=b'other')

        self.sut.copyFolder(
            source=[u'/'] + source_segments,
            destination=[u'/'] + destination_segments,
            overwrite=False,
            )

        self.assertTrue(
            mk.fs.exists(destination_segments + [u'other-file']))
        self.assertTrue(
            mk.fs.exists(existing_destination_segments))
        self.assertEqual(
            b'destination-exist',
            mk.fs.getFileContent(existing_destination_segments, utf8=False))

    def test_join_rejoin_unicode(self):
        """
        It can join and re-join the result from unicode path.
        """
        first_join = self.sut.join([mk.makeFilename(), mk.makeFilename()])
        second_join = self.sut.join([first_join, mk.makeFilename()])

        if os.name == 'posix':
            self.assertIsInstance(str, second_join)
        else:
            self.assertIsInstance(unicode, second_join)
