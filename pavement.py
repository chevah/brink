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
from paver.easy import consume_args, task

# Make pylint shut up.
help
default


@task
def deps():
    '''Copy external dependencies.'''
    pave.installBuildDependencies()


@task
@consume_args
def pypi_mirror(args):
    """
    Create a local mirror of required pypi packages.
    """
    pave.fs.deleteFolder([pave.path.pypi])
    pave.fs.createFolder([pave.path.pypi])

    arguments = [
            '-d', pave.path.pypi,
            '--no-install',
            ]

    if args:
        arguments.extend(args)
    else:
        arguments.extend(['-r', 'requirements.txt'])

    pave.pip(
        command='install',
        arguments=arguments,
        )


@task
@consume_args
def pypi_download(args):
    """
    Download package from central PyPI mirror.
    """
    pave.fs.createFolder([pave.path.pypi])

    arguments = [
            '-d', pave.path.pypi,
            '--no-install',
            ]
    if not args:
        print "You must specify at least one package to be downloaded."
        return
    arguments.extend(args)

    pave.pip(
        command='install',
        arguments=arguments,
        only_cache=False,
        index_url='http://pypi.python.org/simple',
        )


@task
@consume_args
def pypi_install(args):
    """
    Install the package from local cache.
    """
    arguments = ['--upgrade']

    if not args:
        print "You must specify one package to be installed."
        return

    arguments.extend(args)

    pave.pip(
        command='install',
        arguments=arguments,
        )
