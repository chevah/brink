# Copyright (c) 2013 Adi Roiban.
# See LICENSE for details.
"""
Tests for brink utilities.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
import hashlib
import os
import sys
from brink.testing import BrinkTestCase, conditionals, mk

from brink.utils import BrinkPaver


MINIMAL_SETUP = {
    'folders': {
        'source': 'brink',
        'dist': 'dist',
        'publish': 'publish',
        }
    }


class TestBrinkPaver(BrinkTestCase):
    """
    Tests for BrinkPaver.
    """

    def test_initialization(self):
        """
        It is initialized with a setup dictionary.
        """
        result = BrinkPaver(setup=MINIMAL_SETUP)

        self.assertEqual(MINIMAL_SETUP, result.setup)

    def test_convertToDOSNewlines(self):
        """
        Convert unix newlines to dos newlines.
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)
        content = (
            u'one line\t \n'
            u' \tspaces\n'
            )
        self.test_segments = mk.fs.createFileInTemp(content=content)
        path = mk.fs.getRealPathFromSegments(self.test_segments)

        sut._convertToDOSNewlines(path)

        result = mk.fs.getFileContent(self.test_segments)

        self.assertEqual((
            u'one line\t \r\n'
            u' \tspaces\r\n'
            ),
            result)

    def test_createMD5Sum(self):
        """
        Return the MD5 of file at path, which is specified as segments
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)
        content = (
            u'one line\t \n'
            u' \tspaces\n'
            )
        self.test_segments = mk.fs.createFileInTemp(content=content)
        name = self.test_segments[-1]

        result = sut.createMD5Sum([mk.fs.temp_path, name])

        expected = hashlib.md5(content).hexdigest()
        self.assertEqual(expected, result)

    @conditionals.onOSFamily('posix')
    def test_rsync_unix(self):
        """
        On Unix it used the default SSH.
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)
        command = []
        sut.execute = (
            lambda **kwargs: not command.append(kwargs) and (0, ''))

        sut.rsync(
            username='some-user',
            hostname='some-host',
            source=['source', 'folder'],
            destination='path/on/server',
            )

        self.assertEqual([{
            'command': [
                'rsync',
                '-cza',
                '-e',
                'ssh',
                'source/folder',
                'some-user@some-host:path/on/server',
                ],
            'output': sys.stdout,
            }], command)

    @conditionals.onOSFamily('nt')
    def test_rsync_windows(self):
        """
        On Windows it used the dedicated SSH with a dedicated config file.
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)
        command = []
        sut.execute = (
            lambda **kwargs: not command.append(kwargs) and (0, ''))

        sut.rsync(
            username='some-user',
            hostname='some-host',
            source=['source', 'folder'],
            destination='path/on/server',
            )

        self.assertEqual([{
            'command': [
                'rsync',
                '-rcz',
                '-no-p',
                '--chmod=D755,F644',
                '--chown=some-user:www-data',
                '-e',
                'ssh-rsync -F %s\\.ssh\\config' % os.getenv('USERPROFILE'),
                'source/folder',
                'some-user@some-host:path/on/server',
                ],
            'output': sys.stdout,
            }], command)

    def test_getPythonLibPath_default(self):
        """
        It will return a path which exists.
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)

        result = sut.getPythonLibPath()

        # We test `chevah` which should be a package specific to this
        # build... to make sure we don't get a generic Python path.
        self.assertContains(b'chevah', os.listdir(result))

    def test_default_values(self):
        """
        It will make the runtime information and path available.

        To check brink.sh we also test the environment variables
        """
        sut = BrinkPaver(setup=MINIMAL_SETUP)

        self.assertEqual(b'python2.7', sut.python_version)

        if os.getenv('CHEVAH_BUILD', b'') != b'':
            # We run with custom builddir
            build_dir = b'build-brink-\xc8\x9b'
        else:
            build_dir = b'build-brink'

        # On Windows, brink path is always with backslashes.
        expected_path = os.path.join(
            os.getcwd(), build_dir).decode('utf-8').replace('\\', '/')

        self.assertEqual(expected_path.encode('utf-8'), sut.path.build)

        self.assertEqual(build_dir, os.environ['PYTHONPATH'])
        self.assertEqual(b'python2.7', os.environ['CHEVAH_PYTHON'])
