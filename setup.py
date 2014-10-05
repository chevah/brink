
# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Package for chevah-brink.

These are the extensions build around paver.
"""
from setuptools import setup, find_packages, Command
import os

VERSION = u'0.47.0'


class PublishCommand(Command):
    """
    Publish the source distribution to local pypi cache and remote
    Chevah PyPi server.
    """

    description = "copy distributable to Chevah cache folder"
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, (
            'Must be in package root: %s' % self.cwd)
        self.run_command('sdist')

        # Upload package to Chevah PyPi server.
        upload_command = self.distribution.get_command_obj('upload')
        upload_command.repository = u'chevah'
        self.run_command('upload')


distribution = setup(
    name='chevah-brink',
    version=VERSION,
    maintainer="Adi Roiban",
    maintainer_email="adi.roiban@chevah.com",
    license='BSD',
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
