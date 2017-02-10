# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import with_statement

from contextlib import contextmanager
import os
import re
import shutil
import stat
import sys
import unicodedata


class BrinkFilesystem(object):
    """
    Filesystem handling.
    """

    @staticmethod
    def getEncodedPath(path):
        """
        Return the encoded representation of the path, use in the lower
        lever API for accessing the filesystem.
        """
        if os.name == 'nt':
            return path
        else:
            return path.encode(u'utf-8')

    def join(self, paths):
        """
        Join paths.

        It also converts all paths to backslash paths.
        """
        if os.name == 'posix':
            # Make sure we don't mix unicode
            new_paths = []
            for path in paths:
                if isinstance(path, unicode):
                    path = path.encode('utf-8')
                new_paths.append(path)
            paths = new_paths
        elif os.name == 'nt':
            if paths[0].startswith('/') and not paths[1].endswith(":"):
                # Try figuring out if this is an absolute path and fix it.
                paths = [paths[1] + u':', os.sep] + paths[2:]

        result = os.path.join(*paths)
        return result.replace('\\', '/')

    def readFile(self, destination):
        content = []
        with open(self.join(destination), 'r') as opened_file:
            for line in opened_file:
                content.append(line.rstrip())
        return content

    def exists(self, destination):
        """
        Try if destination exists as file or as folder or as symlink.
        """
        return os.path.exists(self.join(destination))

    def isFile(self, destination):
        """
        Try if destination is a file.
        """
        return os.path.isfile(self.join(destination))

    def isFolder(self, destination):
        """
        Try if destination is a folder.
        """
        return os.path.isdir(self.join(destination))

    def getFileContentAsString(self, target):
        """
        Return the string representation of the file.
        """
        with open(self.join(target), 'r+') as opened_file:
            content = opened_file.read()
        return content

    def getFileContentAsList(self, target, strip_newline=True):
        """
        Return the string representation of the file.

        If `strip_newline` is True, the trailing newline will be not included.
        """
        content = []
        with open(self.join(target), 'r') as opened_file:
            for line in opened_file:
                if strip_newline:
                    line = line.rstrip()
                content.append(line)
        return content

    def createEmptyFile(self, target):
        """
        Create empty file.
        """
        path = self.join(target)
        with file(path, 'w'):
            os.utime(path, None)

    def createFolder(self, destination, recursive=False):
        """
        Create a folder

        If 'recursive' is True it will create parent folders if they don't
        exists.

        It ignores already exists errors.
        """
        path = self.join(destination)
        try:
            if recursive:
                os.makedirs(path)
            else:
                os.mkdir(path)
        except OSError, error:
            if error.errno == 17:
                pass
            else:
                raise

    def copyFile(self, source, destination):
        """
        Copy file from `source` to `destination`.
        """
        shutil.copyfile(self.join(source), self.join(destination))

    def copyFolder(
            self, source, destination,
            excepted_folders=None, excepted_files=None,
            overwrite=True,
            ):
        """
        Copy `source` folder to `destination`.

        The copy is done recursive.
        If folder already exists the content will be merged.

        `excepted_folders` and `excepted_files` is a list of regex with
        folders and files that will not be copied.
        """
        source = self.join(source)
        destination = self.join(destination)

        if excepted_folders is None:
            excepted_folders = []

        if excepted_files is None:
            excepted_files = []

        if not os.path.exists(source):
            raise AssertionError(
                u'Source folder does not exists: %s' % (source))

        for source_folder, dirs, files in os.walk(source):
            destination_folder = destination + source_folder[len(source):]

            # Check if we need to skip this folder.
            skip_folder = False
            for excepted_folder in excepted_folders:
                if re.match(excepted_folder, source_folder):
                    skip_folder = True
                    break
            if skip_folder:
                continue

            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder)

            for file_ in files:
                destination_file = self.join([destination_folder, file_])
                source_file = self.join([source_folder, file_])

                # Check if we need to skip this file.
                skip_file = False
                for excepted_file in excepted_files:
                    if re.match(excepted_file, file_):
                        skip_file = True
                        break

                destination_file = self.join([destination_folder, file_])
                source_file = self.join([source_folder, file_])

                if not overwrite and os.path.exists(destination_file):
                    skip_file = True

                if skip_file:
                    continue

                if os.path.exists(destination_file):
                    os.remove(destination_file)

                if os.path.islink(source_file):
                    linkto = os.readlink(source_file)
                    os.symlink(linkto, destination_file)
                else:
                    shutil.copyfile(source_file, destination_file)
                    shutil.copystat(source_file, destination_file)

    def copyFolderContent(self, source, destination, mask='.*'):
        """
        Copy folder content. cp source/* destination/
        """
        source = self.join(source)
        destination = self.join(destination)
        names = os.listdir(source)
        for name in names:
            file_source_path = self.join([source, name])
            file_destination_path = self.join([destination, name])
            try:
                if os.path.isfile(file_source_path) and re.search(mask, name):
                    shutil.copyfile(file_source_path, file_destination_path)
                    shutil.copymode(file_source_path, file_destination_path)
            except re.error:
                pass

    def concatenateFiles(self, sources, destination):
        """
        Concatenate sources files to destination.
        """
        with open(self.join(destination), 'wb') as destination_file:
            for source in sources:
                shutil.copyfileobj(
                    open(self.join(source), 'rb'), destination_file)

    def deleteFile(self, path):
        """
        Delete a file.

        Ignores errors if it does not exists.
        """
        try:
            os.unlink(self.join(path))
        except OSError, error:
            if error.errno == 2:
                pass
            else:
                raise

    def deleteFolder(self, target):
        """
        Delete a folder.

        Ignores errors if it does not exists.
        """

        def on_error(func, path, exc_info):
            """
            Error handler for ``shutil.rmtree``.

            If the error is due to an access error (read only file)
            it attempts to add write permission and then retries.

            If the error is for another reason it re-raises the error.
            """
            os.chmod(path, stat.S_IWRITE)
            func(path)

        try:
            shutil.rmtree(
                self.join(target), ignore_errors=False, onerror=on_error)
        except OSError, error:
            if error.errno == 2:
                pass
            else:
                raise

    def createLink(self, source, destination):
        """
        Create a symlink on Unix or copy folder on Windows.

        createLink requires using absolute paths for source.
        """
        if os.name != 'nt':
            os.symlink(self.join(source), self.join(destination))
        else:
            self.copyFolder(
                source=source,
                destination=destination)

    def appendContentToFile(self, destination, content):
        """
        Append content to file.
        """
        with open(self.join(destination), 'a') as opened_file:
            opened_file.write(content)

    def writeContentToFile(self, destination, content):
        """
        Write content to file.
        """
        with open(self.join(destination), 'w') as opened_file:
            opened_file.write(content)

    def replaceFileContent(self, target, rules):
        """
        Replace the file content.

        It takes a list for tuples [(pattern1, substitution1), (pat2, sub2)]
        and applies them in order.
        """
        with open(self.join(target), 'r') as source_file:
            altered_lines = []
            for line in source_file:
                new_line = line
                for rule in rules:
                    pattern = rule[0]
                    substitution = rule[1]
                    new_line = re.sub(
                        pattern.encode('utf-8'),
                        substitution.encode('utf-8'),
                        new_line)
                altered_lines.append(new_line)

        with open(self.join(target), 'w') as source_file:
            for line in altered_lines:
                source_file.write(line)

    @contextmanager
    def changeFolder(self, destination):
        """
        Context manager (Python 2.5+ only) for stepping into a
        directory and automatically coming back to the previous one.
        The original directory is returned. Usage is like this::

            from __future__ import with_statement
            # the above line is only needed for Python 2.5

            from paver.easy import *

            @task
            def my_task():
                with changeFolder('new/directory') as old_dir:
                    ...do stuff...
        """
        path = self.join(destination)
        old_dir = os.getcwd()
        os.chdir(path)
        try:
            yield old_dir
        finally:
            os.chdir(old_dir)

    def which(self, command, extra_paths=None):
        """
        Find and return the full path to `command`.
        """
        paths = self._getSearchPaths(extra_paths)

        for path in paths:
            result = self._findCommand(command, path)
            # Return the first result.
            if result:
                return result

    def _getSearchPaths(self, extra_paths=None):
        """
        Return the list of all paths as defined in the environment.
        """
        if extra_paths is None:
            extra_paths = []
        environment_paths = os.environ['PATH']

        result = extra_paths[:]

        if os.name == 'posix':
            os_paths = self._parseUnixPaths(environment_paths)
        else:
            os_paths = self._parseWindowsPaths(environment_paths)

        result.extend(os_paths)
        return result

    def _parseUnixPaths(self, paths):
        """
        Parse paths stored in Unix environment format.
        """
        return paths.split(':')

    def _parseWindowsPaths(self, paths):
        """
        Parse paths stored in Windows environment format.
        """
        return paths.split(';')

    def listFolder(self, path):
        """
        Returns the contents of the specified `path` as a list.
        """
        if sys.platform.startswith('darwin') or os.name == 'nt':
            # On Windows and OSX we force Unicode as low filesystem is Unicode.
            if not isinstance(path, unicode):
                path = path.decode('utf-8')

        try:
            result = os.listdir(path)
        except OSError as error:
            if error.errno == 13:
                return []
            else:
                raise

        if sys.platform.startswith('darwin'):
            # On OSX we need to normalize the Unicode result
            result = [
                unicodedata.normalize('NFC', name)
                for name in result]
        return result

    def _isValidSystemPath(self, path):
        """
        Only folders are valid system path items.

        Method is a helper for testing.
        """
        return os.path.isdir(path)

    def _findCommand(self, command, path):
        """
        Search path for command executable.

        Return the first path found.

        On Windows, it will find executable even if extension is not
        provided.
        """
        if not self._isValidSystemPath(path):
            return None

        targets = [command]
        if os.name == 'nt':
            windows_targets = [
                '%s.exe' % (command),
                '%s.bat' % (command),
                '%s.cmd' % (command),
                ]
            windows_targets.extend(targets)
            targets = windows_targets

        files = self.listFolder(path)
        for target in targets:
            for candidate in files:
                if candidate == target:
                    result = os.path.join(path, candidate)
                    return result
