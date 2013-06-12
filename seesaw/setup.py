from distutils import log
from setuptools import Command, find_packages, setup
import os
import shutil

VERSION = '0.1.0'


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
            "Distributables files copied to %s " % (self.destination_base))

        # Upload package to Chevah PyPi server.
        upload_command = self.distribution.get_command_obj('upload')
        upload_command.repository = u'chevah'
        self.run_command('upload')


distribution = setup(
    name="chevah-seesaw",
    version=VERSION,
    maintainer='Adi Roiban',
    maintainer_email='adi.roiban@chevah.com',
    license='Public Domain',
    platforms='any',
    description="Testing project Chevah project.",
    long_description=open('README.rst').read(),
    url='http://www.chevah.com',
    namespace_packages=['chevah'],
    packages=find_packages('.'),
    install_requires=[
        'chevah-compat',
        'chevah-empirical',
        'twisted==12.1.0-chevah3',
        ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        ],
    cmdclass={
        'publish': PublishCommand,
        },
    )