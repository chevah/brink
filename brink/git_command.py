# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Git support for brink.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )


import os
import sys

from brink.execute import execute


class BrinkGit(object):
    """
    Helpers for calling external git command.
    """

    def __init__(self, filesystem):
        self.fs = filesystem
        self.git = self._getGitPath()

    def _getGitPath(self):
        """
        Return path to git executable.
        """
        extra_paths = []

        if os.name == 'nt':
            # Some Windows systems don't have Git in PATH so we use the
            # hard-coded paths from c:\Program Files.
            extra_paths = [
                'c:\\Program Files\\Git\\bin\\',
                'c:\\Program Files (x86)\\Git\\bin\\',
                ]

        path = self.fs.which('git', extra_paths)

        if path:
            return path

        raise AssertionError('Failed to find Git.')

    def push(self, remote='origin'):
        '''Push current changes.'''
        _, output = execute([self.git, 'push', remote])
        return output.strip()

    def publish(self, remote='origin'):
        """
        Publish new branch to remote repo.
        """
        _, output = execute([
            self.git, 'push', '--set-upstream', remote, self.branch_name])
        return output.strip()

    def status(self):
        """
        Publish new branch to remote repo.
        """
        _, output = execute([self.git, 'status', '-s'])
        return output.strip()

    @property
    def revision(self):
        '''Return the revision of the current git branch.'''
        command = [self.git, 'show', '-s', '--pretty=format:%H']
        _, output = execute(command)
        return output.strip()

    @property
    def origin(self):
        '''Return the origin of the current git branch.'''
        command = [self.git, 'config', '--get', 'remote.origin.url']
        _, output = execute(command)
        return output.strip()

    @property
    def branch_name(self):
        """
        Return the name of the current git branch.

        $ git symbolic-ref HEAD
        refs/heads/production
        """
        _, output = execute([self.git, 'symbolic-ref', 'HEAD'])
        return output.strip().split('/')[-1]

    @property
    def account(self):
        '''Return the name and email of the current git user.'''
        _, output = execute([self.git, 'config', 'user.name'])
        name = output.strip().decode('utf-8')

        _, output = execute([self.git, 'config', 'user.email'])
        email = output.strip().decode('utf-8')

        return '%s <%s>' % (name, email)

    @property
    def last_commit(self):
        '''Return the comment of the last commit.'''
        command = [
            self.git, 'log', "--pretty=format:'%h - %s'",
            '--date=short', '-1',
            ]
        _, output = execute(command)
        return output.strip()

    def clone(self, repo_uri, project_name):
        '''Clone the repository if it does not already exists.'''
        command = [self.git, 'clone', repo_uri, project_name]
        exit_code, _ = execute(command)
        if exit_code != 0:
            print('Failed to clone "%s".' % repo_uri)
            sys.exit(1)

    def pull(self, repo_uri='origin', branch='master'):
        '''Run git pull on the branch.'''
        command = [self.git, 'pull', repo_uri, branch]

        exit_code, _ = execute(command)
        if exit_code != 0:
            print('Failed to update repo "%s".' % repo_uri)
            sys.exit(1)

    def copyFile(self, source, destination, branch='master'):
        """
        Copy file from branch.
        """
        command = ['git', 'show', '%s:%s' % (branch, self.fs.join(source))]
        with open(self.fs.join(destination), 'w') as output_file:
            execute(command, output=output_file)

    @staticmethod
    def diffFileNames(ref='master'):
        """
        Return a list of (action, filename) that have changed in
        comparison with `ref`.
        """
        result = []
        command = ['git', 'diff', '--name-status', '%s' % (ref)]
        exit_code, output = execute(command)
        if exit_code != 0:
            print('Failed to diff files.')
            sys.exit(1)

        for line in output.splitlines():
            action, name = line.split('\t')
            action = action.lower()
            result.append((action, name))

        return result

    @staticmethod
    def diff(ref='master'):
        """
        Return a list of (action, filename) that have changed in
        comparison with `ref`.
        """
        result = []
        if ref:
            command = ['git', 'diff', '%s' % (ref)]
        else:
            command = ['git', 'diff']

        exit_code, output = execute(command)
        if exit_code != 0:
            print('Failed to diff repo.')
            sys.exit(1)

        return output
