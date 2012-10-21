# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Build script for Chevah brink repository.

The main script is 'make-it-happen.sh'.

This is here just to help with review, buildbot and other tasks.
"""
from __future__ import with_statement

from brink.pavement_commons import (
    default,
    pave,
    )
from paver.easy import task

# Make pylint shut up.
help
default


# Brink version is defined here and used by paver.sh script.
BRINK_VERSION = '0.3.0'

EXTRA_PACKAGES = []


@task
def deps():
    '''Copy external dependencies.'''
    pave.installRunDependencies(extra_packages=EXTRA_PACKAGES)
    pave.installBuildDependencies()
