# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
import os
import subprocess
import sys


def execute(command, input_text=None, output=None,
        ignore_errors=False, verbose=False,
        extra_environment=None):
    if verbose:
        print 'Calling: %s' % command

    if output is None:
        output = subprocess.PIPE

    if extra_environment is not None:
        execute_environment = os.environ.copy()
        execute_environment.update(extra_environment)
    else:
        execute_environment = None

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=output,
            env=execute_environment,
            )
    except OSError, error:
        if error.errno == 2:
            print 'Failed to execute: %s' % ' '.join(command)
            print 'Missing command: %s' % command[0]
            sys.exit(1)
        else:
            raise

    try:
        (stdoutdata, stderrdata) = process.communicate(input_text)
    except KeyboardInterrupt:
        # Don't print stack trace on keyboard interrupt.
        # Just exit.
        sys.exit(1)

    exit_code = process.returncode
    if exit_code != 0:
        if verbose:
            print u'Failed to execute %s\n%s' % (command, stderrdata)
        if not ignore_errors:
            sys.exit(exit_code)

    return (exit_code, stdoutdata)
