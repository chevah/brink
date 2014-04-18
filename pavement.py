# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Build script for Chevah brink repository.

The main script is 'make-it-happen.sh'.

This is here just to help with review, buildbot and other tasks.
"""
import os
import sys

from brink.pavement_commons import (
    buildbot_list,
    buildbot_try,
    default,
    github,
    harness,
    help,
    lint,
    merge_init,
    merge_commit,
    pave,
    pqm,
    publish_distributables,
    publish_documentation,
    publish,
    rqm,
    SETUP,
    test_documentation,
    test_python,
    test_remote,
    test_review,
    test_normal,
    test_super,
    )
from paver.easy import call_task, consume_args, needs, no_help, task

# Make pylint shut up.
buildbot_list
buildbot_try
default
github,
harness
help
lint
merge_init
merge_commit
pqm
publish_distributables
publish_documentation
publish
rqm
test_documentation
test_python
test_remote
test_review
test_normal
test_super

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
    # Required for seesaw testing.
    'chevah-compat==0.8.4',
    'chevah-empirical==0.18.2',

    'pyflakes==0.7.3',
    'pocketlint==1.4.4.c4',


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

NODE_PACKAGES = [
    'karma@0.10.2',
    'karma-firefox-launcher',
    'karma-jasmine'
    ]

SETUP['repository']['name'] = u'brink'
SETUP['github']['repo'] = 'chevah/brink'
SETUP['github']['url'] = 'https://github.com/chevah/brink'
SETUP['pocket-lint']['include_files'] = [
    'msys-console.js',
    'pavement.py',
    'release-notes.rst',
    ]
SETUP['pocket-lint']['include_folders'] = [
    'brink',
    'documentation',
    ]
SETUP['folders']['source'] = u'brink'
SETUP['test']['package'] = 'brink.tests'
SETUP['test']['elevated'] = 'brink.tests.elevated'
SETUP['website_package'] = 'brink.website'
SETUP['buildbot']['server'] = 'build.chevah.com'
SETUP['buildbot']['web_url'] = 'http://build.chevah.com:10088'
SETUP['pypi']['index_url'] = 'http://pypi.chevah.com:10042/simple'

if os.name == 'nt':
    # Fix temp folder
    import tempfile
    tempfile.tempdir = "c:\\temp"


@task
@needs('deps_testing', 'deps_build')
def deps():
    """
    Install all dependencies.
    """


@task
def deps_testing():
    """
    Get dependencies for running the tests.
    """
    print('Installing testing dependencies to %s.' % (pave.path.build))
    pave.pip(
        command='install',
        arguments=RUN_PACKAGES,
        )
    pave.pip(
        command='install',
        arguments=TEST_PACKAGES,
        )


@task
@needs('deps_testing')
def deps_build():
    """
    Get dependencies for building the project.
    """
    print('Installing build dependencies to %s.' % (pave.path.build))
    pave.pip(
        command='install',
        arguments=BUILD_PACKAGES,
        )


@task
@needs('deps_build')
def deps_web():
    """
    Install all dependencies required to run web tests.
    """
    for package in NODE_PACKAGES:
        pave.npm(command="install", arguments=[package])


@task
def build():
    """
    Copy new source code to build folder.
    """
    build_target = pave.fs.join([pave.path.build, 'setup-build'])

    # Delete 1-st stage of build use by Python packaging.
    pave.fs.deleteFolder([build_target])
    # Delete brink package from site-packages.
    pave.fs.deleteFolder([
        pave.path.build, pave.getPythonLibPath(), 'brink'])

    sys.argv = ['setup.py', 'build', '--build-base', build_target]
    print "Building in " + build_target

    pave.fs.deleteFolder(
        [pave.path.build, 'doc_source'])
    pave.fs.copyFolder(
        source=['documentation'],
        destination=[pave.path.build, 'doc_source'])
    pave.fs.createFolder([pave.path.build, 'doc_source', '_static'])

    import setup
    setup.distribution.run_command('install')
    pave.fs.copyFile(
        ['DEFAULT_VALUES'], [pave.path.build, 'DEFAULT_VALUES'])


@task
def doc_html():
    """
    Create documentation as html.
    """
    pave.fs.createFolder([pave.path.build, 'doc'])
    pave.fs.createFolder([pave.path.build, 'doc', 'html'])


@task
def dist():
    """
    Create distributables files.
    """
    # Create a fake file.
    pave.fs.createEmptyFile([pave.path.dist, '1.2.0.html'])


@no_help
@task
def update_setup():
    """
    Fake updating of versions for testing.
    """
    SETUP['product']['version'] = '1.2.0'
    SETUP['product']['version_major'] = '1'
    SETUP['product']['version_minor'] = '2'


@task
@consume_args
@needs('test_python')
def test(args):
    """
    Run Python tests.
    """


@task
@consume_args
def test_ci(args):
    """
    Run tests in continous integration environment.
    """
    env = os.environ.copy()

    test_type = env.get('TEST_TYPE', 'normal')
    if test_type == 'os-independent':
        return call_task('test_os_independent')

    return call_task('test_os_dependent', args=args)


@task
@consume_args
@needs('deps_testing')
def test_os_dependent(args):
    """
    Run os dependent tests in buildbot.
    """
    call_task('test_python')


@task
@needs('deps_build')
def test_os_independent():
    """
    Run os independent tests in buildbot.
    """
    call_task('lint', options={'all': True})
    call_task('test_documentation')


@task
@consume_args
def test_web(args):
    """
    Run JavaScript tests.

    Right now it does nothing.
    """


@task
@consume_args
def test_web_functional(args):
    """
    Run functional web tests.

    Right now it does nothing.
    """
