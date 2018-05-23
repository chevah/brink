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


class TestBrinkPaver(BrinkTestCase):
    """
    Tests for BrinkPaver.
    """

    MINIMAL_SETUP = {
        'folders': {
            'source': 'brink',
            'dist': 'dist',
            'publish': 'publish',
            }
        }

    def setUp(self):
        super(TestBrinkPaver, self).setUp()
        self.utils = BrinkPaver(setup=self.MINIMAL_SETUP)

    def test_initialization(self):
        """
        It is initialized with a setup dictionary.
        """
        result = BrinkPaver(setup=self.MINIMAL_SETUP)

        self.assertEqual(self.MINIMAL_SETUP, result.setup)

    def test_convertToDOSNewlines(self):
        """
        Convert unix newlines to dos newlines.
        """
        content = (
            u'one line\t \n'
            u' \tspaces\n'
            )
        self.test_segments = mk.fs.createFileInTemp(content=content)
        path = mk.fs.getRealPathFromSegments(self.test_segments)

        self.utils._convertToDOSNewlines(path)

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
        content = (
            u'one line\t \n'
            u' \tspaces\n'
            )
        self.test_segments = mk.fs.createFileInTemp(content=content)
        name = self.test_segments[-1]

        result = self.utils.createMD5Sum([mk.fs.temp_path, name])

        expected = hashlib.md5(content).hexdigest()
        self.assertEqual(expected, result)

    @conditionals.onOSFamily('posix')
    def test_rsync_unix(self):
        """
        On Unix it used the default SSH.
        """
        command = []
        self.utils.execute = (
            lambda **kwargs: not command.append(kwargs) and (0, ''))

        self.utils.rsync(
            username='some-user',
            hostname='some-host',
            source=['source', 'folder'],
            destination='path/on/server',
            )

        self.assertEqual([{
            'command': [
                'rsync',
                '-acz',
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
        command = []
        self.utils.execute = (
            lambda **kwargs: not command.append(kwargs) and (0, ''))

        self.utils.rsync(
            username='some-user',
            hostname='some-host',
            source=['source', 'folder'],
            destination='path/on/server',
            )

        self.assertEqual([{
            'command': [
                'rsync',
                '-acz',
                '-e',
                'ssh-rsync -F %s\\.ssh\\config' % os.getenv('USERPROFILE'),
                'source/folder',
                'some-user@some-host:path/on/server',
                ],
            'output': sys.stdout,
            }], command)
