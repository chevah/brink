# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Build script for Chevah brink repository.

This is here to help with review, buildbot, and other tasks.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import sys
import warnings

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

# These are the hard dependencies needed by the library itself.
RUN_PACKAGES = [
    'zope.interface==3.8.0',
    'twisted==15.5.0.chevah4',
    ]

# Packages required to use the dev/build system.
BUILD_PACKAGES = [
    # Buildbot is used for try scheduler
    'buildbot==0.8.11.c7',

    'configparser==3.5.0b2',
    'towncrier==16.0.0.chevah4',

    # For PQM
    'smmap==0.8.2',
    'async==0.6.1',
    'gitdb==0.6.4',
    'gitpython==1.0.0',
    'pygithub==1.34',
    ]

# Packages required by the static analysis tests.
LINT_PACKAGES = [
    'scame==0.1.0',
    'pyflakes>=1.5.0',
    'closure-linter==2.3.13',
    'pycodestyle==2.3.1',
    'bandit==1.4.0',
    'pylint==1.7.1',
    'astroid==1.5.3',
    'enum34>=1.1.6',

    # These are build packages, but are used for testing the documentation.
    'sphinx==1.1.3-chevah1',
    'repoze.sphinx.autointerface==0.7.1-chevah2',
    # Docutils is required for RST parsing and for Sphinx.
    'docutils>=0.9.1-chevah2',
    ]

# Packages required to run the test suite.
TEST_PACKAGES = [
    'chevah-compat==0.43.2',

    # We need a newer future to work with pylint/astoid.
    'future>=0.16.0',
    'wmi==1.4.9',

    # Never version of nose, hangs on closing some tests
    # due to some thread handling.
    'nose==1.3.7',
    'mock',

    'coverage==4.0.3',
    'codecov==2.0.3',

    # Test SFTP service using a 3rd party client.
    'paramiko',

    # Required for some unicode handling.
    'unidecode',

    'bunch',
    ]


try:
    from scame.formatcheck import ScameOptions
    options = ScameOptions()
    options.max_line_length = 80

    options.scope = {
        'include': [
            'msys-console.js',
            'pavement.py',
            'release-notes.rst',
            'paver.sh',
            'brink/',
            'documentation/',
            ],
        'exclude': [],
        }

    # We don't use the managed release notes for this project.
    options.towncrier = {'enabled': False}

    options.pyflakes['enabled'] = True

    options.pycodestyle['enabled'] = True
    options.pycodestyle['hang_closing'] = True

    options.closure_linter['enabled'] = True
    options.closure_linter['ignore'] = [1, 10, 11, 110, 220]

    # For now these are disabled, as there are to many errors.
    options.bandit['enabled'] = False
    options.pylint['enabled'] = False
    options.pylint['disable'] = ['C0103', 'C0330', 'R0902', 'W0212']

except ImportError:
    # This will fail before we run `paver deps`
    options = None


SETUP['product']['version'] = None
SETUP['product']['version_major'] = None
SETUP['product']['version_minor'] = None

SETUP['repository']['name'] = u'brink'
SETUP['repository']['github'] = 'https://github.com/chevah/brink'
SETUP['scame'] = options
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
def deps():
    """
    Install all dependencies.
    """
    print('Installing dependencies to %s...' % (pave.path.build,))
    packages = RUN_PACKAGES + TEST_PACKAGES

    env_ci = os.environ.get('CI', '').strip()
    if env_ci.lower() != 'true':
        packages += BUILD_PACKAGES + LINT_PACKAGES
    else:
        builder = os.environ.get('BUILDER_NAME', '')
        if 'os-independent' in builder or '-py3' in builder:
            packages += LINT_PACKAGES
            print('Installing only lint and test dependencies.')
        elif '-gk-' in builder:
            packages += BUILD_PACKAGES + LINT_PACKAGES
            print('Installing only build, lint and test dependencies.')
        else:
            print('Installing only test dependencies.')

    pave.pip(
        command='install',
        arguments=packages,
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
    print("Building in " + build_target)

    pave.fs.deleteFolder(
        [pave.path.build, 'doc_source'])
    pave.fs.copyFolder(
        source=['documentation'],
        destination=[pave.path.build, 'doc_source'])
    pave.fs.createFolder([pave.path.build, 'doc_source', '_static'])

    import setup
    setup.DISTRIBUTION.run_command('install')


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
    Run tests in continuous integration environment.
    """
    # Show some info about the current environment.
    from OpenSSL import SSL, __version__ as pyopenssl_version
    from coverage.cmdline import main as coverage_main

    print('PYTHON %s' % (sys.version,))
    print('%s (%s)' % (
        SSL.SSLeay_version(SSL.SSLEAY_VERSION), SSL.OPENSSL_VERSION_NUMBER))
    print('pyOpenSSL %s' % (pyopenssl_version,))
    coverage_main(argv=['--version'])

    env = os.environ.copy()

    test_type = env.get('TEST_TYPE', 'normal')
    if test_type == 'os-independent':
        return call_task('test_os_independent')

    if test_type == 'py3':
        return call_task('test_py3', args=args)

    return call_task('test_os_dependent', args=args)


@task
def test_py3():
    """
    Run checks for py3 compatibility.
    """
    from pylint.lint import Run
    from nose.core import main as nose_main
    arguments = ['--py3k', SETUP['folders']['source']]
    linter = Run(arguments, exit=False)
    stats = linter.linter.stats
    errors = (
        stats['info'] + stats['error'] + stats['refactor'] +
        stats['fatal'] + stats['convention'] + stats['warning']
        )
    if errors:
        print('Pylint failed')
        sys.exit(1)

    print('Compiling in Py3 ...',)
    command = ['python3', '-m', 'compileall', '-q', 'chevah']
    pave.execute(command, output=sys.stdout)
    print('done')

    sys.argv = sys.argv[:1]
    pave.python_command_normal.extend(['-3'])

    captured_warnings = []

    def capture_warning(
        message, category, filename,
        lineno=None, file=None, line=None
            ):
        if not filename.startswith('chevah'):
            # Not our code.
            return
        line = (message.message, filename, lineno)
        if line in captured_warnings:
            # Don't include duplicate warnings.
            return
        captured_warnings.append(line)

    warnings.showwarning = capture_warning

    sys.args = ['nose', 'brink.tests.normal']
    runner = nose_main(exit=False)
    if not runner.success:
        print('Test failed')
        sys.exit(1)
    if not captured_warnings:
        sys.exit(0)

    print('\nCaptured warnings\n')
    for warning, filename, line in captured_warnings:
        print('%s:%s %s' % (filename, line, warning))
    sys.exit(1)


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
    print("Publishing: %s" % (args,))


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
