# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Git support for brink.
"""
from __future__ import with_statement

import os
import sys

from brink.execute import execute


def _p(path):
    '''
    Shortcut for converting a list to a path using os.path.join.
    '''
    result = os.path.join(*path)
    if os.name == 'posix':
        result = result.encode('utf-8')
    return result


class BrinkGit(object):
    '''
    Helpers for calling external git command.
    '''

    def __init__(self):
        self.git = self._getGitPath()

    def _getGitPath(self):
        if os.name == 'posix':
            return 'git'
        elif os.name == 'nt':
            git_locations = [
                'c:\\Program Files\\Git\\bin\\git.exe',
                'c:\\Program Files (x86)\\Git\\bin\\git.exe',
                ]
            for git_try in git_locations:
                if os.path.exists(git_try):
                    return git_try
            raise AssertionError('Failed to find Git.')
        else:
            raise AssertionError('OS not supported.')

    def push(self, remote='origin'):
        '''Push current changes.'''
        exit_code, output = execute([self.git, 'push', remote])
        return output.strip()

    def publish(self, remote='origin'):
        """
        Publish new branch to remote repo.
        """
        exit_code, output = execute([
            self.git, 'push', '--set-upstream', remote, self.branch_name])
        return output.strip()

    def status(self):
        """
        Publish new branch to remote repo.
        """
        exit_code, output = execute([self.git, 'status', '-s'])
        return output.strip()

    @property
    def revision(self):
        '''Return the revision of the current git branch.'''
        command = [self.git, 'show', '-s', '--pretty=format:%t']
        exit_code, output = execute(command)
        return output.strip()

    @property
    def branch_name(self):
        """
        Return the name of the current git branch.

        $ git symbolic-ref HEAD
        refs/heads/production
        """
        exit_code, output = execute([self.git, 'symbolic-ref', 'HEAD'])
        return output.strip().split('/')[-1]

    @property
    def account(self):
        '''Return the name and email of the current git user.'''
        exit_code, output = execute([self.git, 'config', 'user.name'])
        name = output.strip()

        exit_code, output = execute([self.git, 'config', 'user.email'])
        email = output.strip()

        return '%s <%s>' % (name, email)

    @property
    def last_commit(self):
        '''Return the comment of the last commit.'''
        command = [
            self.git, 'log', "--pretty=format:'%h - %s'",
            '--date=short', '-1',
            ]
        exit_code, output = execute(command)
        return output.strip()

    def clone(self, repo_uri, project_name):
        '''Clone the repository if it does not already exists.'''
        command = [self.git, 'clone', repo_uri, project_name]
        exit_code, output = execute(command)
        if exit_code != 0:
            print 'Failed to clone "%s".' % repo_uri
            sys.exit(1)

    def pull(self, repo_uri=None, branch='master'):
        '''Run git pull on the branch.'''
        if repo_uri:
            command = [self.git, 'pull', repo_uri, branch]
        else:
            command = [self.git, 'pull', 'origin', branch]

        exit_code, output = execute(command)
        if exit_code != 0:
            print 'Failed to update repo "%s".' % repo_uri
            sys.exit(1)

    def copyFile(self, source, destination, branch='master'):
        command = ['git', 'show', '%s:%s' % (branch, _p(source))]
        with open(_p(destination), 'w') as output_file:
            execute(command, output=output_file)
