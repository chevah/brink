# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import with_statement

from contextlib import contextmanager
import os
import re
import shutil


class BrinkFilesystem(object):
    """
    Filesystem handling.
    """

    def join(self, paths):
        """
        Join paths.

        It also converts all paths to backslash paths.
        """
        result = os.path.join(*paths)
        if os.name == 'posix':
            result = result.encode('utf-8')
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
        Retrun the string represenation of the file.
        """
        with open(self.join(target), 'r+') as opened_file:
            content = opened_file.read()
        return content

    def getFileContentAsList(self, target, strip_newline=True):
        """
        Retrun the string represenation of the file.

        If `strip_newline` is True, the trailing newline will be not included.
        """
        content = []
        with open(self.join(target), 'r') as opened_file:
            for line in opened_file:
                if strip_newline:
                    line = line.rstrip()
                content.append(line)
        return content

    def createEmtpyFile(self, target):
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

    def copyFolder(self, source, destination,
            excepted_folders=None, excepted_files=None):
        """
        Copy `source` folder to `destination`.

        The copy is done recursive.
        If folder already exitst the content will be merged.

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

                # Check if we need to skip this file.
                skip_file = False
                for excepted_file in excepted_files:
                    if re.match(excepted_file, file_):
                        skip_file = True
                        break
                if skip_file:
                    continue

                source_file = self.join([source_folder, file_])
                destination_file = self.join([destination_folder, file_])

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
        try:
            shutil.rmtree(self.join(target))
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
        Appened content to file.
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
