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
    github,
    lint,
    SETUP
    )
from paver.easy import task

# Make pylint shut up.
help
default
github
lint


# Brink version is defined here and used by paver.sh script.
BRINK_VERSION = '0.20.1'
PYTHON_VERSION = '2.7'


RUN_PACKAGES = [
    'zope.interface==3.8.0',
    'twisted==12.1.0-chevah3',
    ]

BUILD_PACKAGES = [
    'sphinx==1.1.3-chevah1',
    'repoze.sphinx.autointerface==0.7.1-chevah2',
    # Docutils is required for RST parsing and for Sphinx.
    'docutils>=0.9.1-chevah2',

    # Buildbot is used for try scheduler
    'buildbot',

    # For PQM
    'chevah-github-hooks-server==0.1.6',
    'smmap==0.8.2',
    'async==0.6.1',
    'gitdb==0.5.4',
    'gitpython==0.3.2.RC1',
    'pygithub==1.10.0',
    ]

TEST_PACKAGES = [
    'pyflakes>=0.5.0-chevah2',
    'closure_linter==2.3.9',
    'pocketlint==0.5.31-chevah7',
    'pocketlint-jshint',

    # Never version of nose, hangs on closing some tests
    # due to some thread handling.
    'nose==1.1.2-chevah1',
    'mock',

    # Test SFTP service using a 3rd party client.
    'paramiko',

    # Required for some unicode handling.
    'unidecode',

    'bunch',
    ]


SETUP['github']['url'] = 'https://github.com/chevah/brink'
SETUP['pocket-lint']['include_files'] = [
    'pavement.py',
    ]
SETUP['pocket-lint']['include_folders'] = [
    'brink',
    ]


@task
def deps():
    """
    Copy external dependencies.
    """
    pave.pip(
        command='install',
        arguments=RUN_PACKAGES,
        )
    pave.pip(
        command='install',
        arguments=TEST_PACKAGES,
        )

    pave.pip(
        command='install',
        arguments=BUILD_PACKAGES,
        )
