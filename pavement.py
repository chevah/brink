# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Build script for Chevah brink repository.

This is here to help with review, buildbot, and other tasks.
"""
import os
import sys

from brink.pavement_commons import (
    buildbot_list,
    buildbot_try,
    coverage_prepare,
    coverage_publish,
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
    test_coverage,
    test_os_dependent,
    test_os_independent,
    test_python,
    test_remote,
    test_review,
    test_normal,
    test_super,
    )
from brink.sphinx import test_documentation
from paver.easy import call_task, consume_args, needs, no_help, pushd, task

# Make pylint shut up.
buildbot_list
buildbot_try
coverage_prepare
coverage_publish
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
test_coverage
test_documentation
test_os_dependent
test_os_independent
test_python
test_remote
test_review
test_normal
test_super

RUN_PACKAGES = [
    'zope.interface==3.8.0',
    'twisted==15.1.0.c1',
    ]

BUILD_PACKAGES = [
    'sphinx==1.1.3-chevah1',
    'repoze.sphinx.autointerface==0.7.1-chevah2',
    # Docutils is required for RST parsing and for Sphinx.
    'docutils>=0.9.1-chevah2',

    # Buildbot is used for try scheduler
    'buildbot==0.8.11.c7',

    'configparser==3.5.0b2',
    'towncrier==16.0.0.chevah4',

    # For PQM
    'smmap==0.8.2',
    'async==0.6.1',
    'gitdb==0.6.4',
    'gitpython==1.0.0',
    'pygithub==1.10.0',
    ]

TEST_PACKAGES = [
    # Required for seesaw testing.
    'chevah-compat==0.34.0',
    'chevah-empirical==0.38.1',

    # Requried by empirical.
    'wmi==1.4.9',

    'pocketlint==1.4.4.c12',
    'pyflakes>=1.0.0',
    'closure-linter==2.3.13',
    'pep8>=1.6.2',

    # Never version of nose, hangs on closing some tests
    # due to some thread handling.
    'nose==1.3.6',
    'mock',

    'coverage==4.0.3',
    'codecov==2.0.3',

    # Test SFTP service using a 3rd party client.
    'paramiko',

    # Required for some unicode handling.
    'unidecode',

    'bunch',
    ]


SETUP['product']['version'] = None
SETUP['product']['version_major'] = None
SETUP['product']['version_minor'] = None

SETUP['repository']['name'] = u'brink'
SETUP['repository']['github'] = 'https://github.com/chevah/brink'
SETUP['pocket-lint']['include_files'] = [
    'msys-console.js',
    'pavement.py',
    'release-notes.rst',
    'paver.sh',
    ]
SETUP['pocket-lint']['include_folders'] = [
    'brink',
    'documentation',
    'release-notes',
    ]
# We don't use the managed release notes for this project.
SETUP['pocket-lint']['release_notes_folder'] = None
SETUP['folders']['source'] = u'brink'
SETUP['test']['package'] = 'brink.tests'
SETUP['test']['elevated'] = 'brink.tests.elevated'
SETUP['test']['cover_package'] = 'brink'
SETUP['test']['nose_options'] = ['--with-run-reporter', '--with-timer']
SETUP['website_package'] = 'brink.website'
SETUP['buildbot']['server'] = 'buildbot.chevah.com'
SETUP['buildbot']['web_url'] = 'https://buildbot.chevah.com:10443'
SETUP['pypi']['index_url'] = 'http://pypi.chevah.com/simple'


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
@needs('coverage_prepare')
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

    # Copy generated DEFAULT_VALUES file.
    pave.fs.copyFile(['DEFAULT_VALUES'], [pave.path.build, 'DEFAULT_VALUES'])

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
    Updating of version at runtime for testing.
    """
    SETUP['product']['version'] = '0.55.13'
    SETUP['product']['version_major'] = '0'
    SETUP['product']['version_minor'] = '55'


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
        call_task('test_os_independent')
    else:
        call_task('test_os_dependent', args=args)


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


@task
@consume_args
def publish(args):
    """
    Placeholder to test the whole publish process.
    """
    print "Publishing: %s" % (args,)


@task
@needs('update_setup')
def release_notes():
    """
    Update the release notes.
    """
    from pkg_resources import load_entry_point
    args = [
        '--yes',
        '--version=%s' % (SETUP['product']['version'],),
        '--package=brink',
        '--filename=release-notes.rst',
        ]
    towncrier_main = load_entry_point(
        'towncrier', 'console_scripts', 'towncrier')

    with pushd('brink/tests'):
        return sys.exit(towncrier_main(prog_name='towncrier', args=args))
