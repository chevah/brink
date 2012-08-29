# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Build script for Chevah brink repository.

The main script is 'make-it-happen.sh'.

This is here just to help with review, buildbot and other tasks.
"""
from __future__ import with_statement

from pavement_lib import (
    default,
    pave,
    )
from paver.easy import task

# Make pylint shut up.
help
default


@task
def deps():
    '''Copy external dependencies.'''
    pave.installBuildDependencies()


@task
def pypi_mirror():
    """
    Create a mirror of required pypi packages.
    """
    pave.fs.deleteFolder([pave.path.pypi])
    pave.fs.createFolder([pave.path.pypi])
    pave.pip(
        command='install',
        arguments=[
            '-d', pave.path.pypi,
            '-r', 'requirements.txt',
            ],
        )
