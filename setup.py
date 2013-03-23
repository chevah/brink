# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Package for chevah-brink.

These are the extensions build around paver.
"""
from distutils import log
from setuptools import setup, find_packages, Command
import os
import shutil

VERSION = u'0.17.0'


class PublishCommand(Command):
    """
    Publish the source distribution to local pypi cache and remote
    Chevah PyPi server.
    """

    description = "copy distributable to Chevah cache folder"
    user_options = []

    def initialize_options(self):
        self.cwd = None
        self.destination_base = '~/chevah/brink/cache/pypi/'

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, (
            'Must be in package root: %s' % self.cwd)
        self.run_command('sdist')
        sdist_command = self.distribution.get_command_obj('sdist')
        for archive in sdist_command.archive_files:
            source = os.path.join(archive)
            destination = os.path.expanduser(
                self.destination_base + os.path.basename(archive))
            shutil.copyfile(source, destination)
        log.info(
            "Distributable(s) files copied to %s " % (self.destination_base))

        # Upload package to Chevah PyPi server.
        upload_command = self.distribution.get_command_obj('upload')
        upload_command.repository = u'chevah'
        self.run_command('upload')


setup(
    name='chevah-brink',
    version=VERSION,
    maintainer="Adi Roiban",
    maintainer_email="adi.roiban@chevah.com",
    license='BSD (3 clause) License',
    platforms='any',
    description='Chevah build system.',
    long_description=open('README.rst').read(),
    url='http://www.chevah.com',
    packages=find_packages('.'),
    package_data={'brink': [
        'static/requirements/*',
        ]},
    cmdclass={'publish': PublishCommand},
)
