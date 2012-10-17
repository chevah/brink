# Copyright (c) 2011 Adi Roiban.
# See LICENSE for details.
"""
Shared pavement methods used in Chevah project.

This file is copied into the root of each repo as pavement_lib.py

Brace yoursef for watching how wheels are reinvented.

Do not modify this file inside the branch.


A `product` is a repository delived to customers or a library.
A `project` is a collection of products.

This scripts assume that you have dedicated folder for the project, and
inside the project folder, there is one folder for each products.
"""
from __future__ import with_statement
from contextlib import closing
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import getpass
import md5
import os
import re
import shutil
import socket
import sys
import subprocess
import urllib2

from paver.easy import cmdopts, task, pushd, needs
from paver.tasks import environment, help, consume_args


def _p(path):
    '''Shortcut for converting a list to a path using os.path.join.'''
    result = os.path.join(*path)
    if os.name == 'posix':
        result = result.encode('utf-8')
    return result


SETUP = {
    'product': {
        'name': 'ChevahProduct',
        'version': '0.0.1',
        'version_major': '0',
        'version_minor': '0',
        'copyright_holder': 'Chevah Project',
    },
    'python': {
        'version': '2.5',
    },
    'folders': {
        'source': None,
        'static': u'static',
        'dist': u'dist',
        'publish': u'publish',
        'configuration': u'configuration',
        'deps': u'deps',
        'brink': u'brink',
        'test_data': u'test_data',
        'nsis': 'nsis'
    },
    'repository': {
        'name': None,
        'base_uri': 'http://172.20.0.11/git/',
    },
    'buildbot': {
        'vcs': 'git',
        'server': '172.20.0.11',
        'port': 10087,
        'username': 'chevah_buildbot',
        'password': 'chevah_password',
        'web_url': 'http://172.20.0.11:10088',
        'builders_filter': None,
    },
    'publish': {
        'download_production_hostname': 'download.chevah.com',
        'download_staging_hostname': 'staging.download.chevah.com',
        'website_production_hostname': 'chevah.com',
        'website_staging_hostname': 'staging.chevah.com'
    },
    'pypi': {
        'index_url': 'http://172.20.0.1:10042/simple',
    },
    'pocket-lint': {
        'exclude_files': [
            'ftplib.py',
            'reset.css',
            'default.css',
            'state.sqlite',
            ],
        'exclude_folders': [],
        'include_files': ['pavement.py'],
        'include_folders': [],
    },
    'sphinx': {
        # Images, CSS and other HTML relates files,
        'html_templates_package': 'chevah.htmltemplates',
        # Sphinx themes.
        'themes_package': 'chevah.sphinxthemes',
        # Media files used by sphinx themes.
        'media_package': 'chevah.website',
    },
    'test': {
        'package': 'chevah.product.tests',
    },

}

DIST_TYPE = {
    'ZIP': 0,
    'NSIS': 1,
    'TAR_GZ': 2,
    'NSIS_RENAMED': 3,
    }

DIST_EXTENSION = {
    DIST_TYPE['ZIP']: 'zip',
    DIST_TYPE['NSIS']: 'exe',
    DIST_TYPE['TAR_GZ']: 'tar.gz',
    DIST_TYPE['NSIS_RENAMED']: 'rename_to_exe'
}


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


def get_python_lib_path(platform=None, python_version=None):
    """
    Return the path to python library folder relative to build folder.
    """
    if platform is None:
        os_name = pave.os_name
    else:
        os_name = platform.split('-')[0]

    if python_version is None:
        python_version = SETUP['python']['version']

    if os_name == 'windows':
        segments = ['lib', 'Lib']
    else:
        segments = ['lib', 'python' + python_version]

    segments.append('site-packages')
    return _p(segments)


class MD5SumFile(object):
    """
    A file storing md5 checksums for files.
    """

    def __init__(self, segments):
        """
        Initialize by creating an empty file.
        """
        self._segments = segments
        pave.fs.createEmtpyFile(target=self._segments)

    def addFile(self, file_path):
        """
        Add file to file listed in md5 file.
        """
        content = pave.createMD5Sum([file_path]) + '  ' + file_path + '\n'
        pave.fs.appendContentToFile(
            destination=self._segments, content=content)


class PaverGit(object):
    '''Helpers for calling external git command.'''

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


class PaverFilesystem(object):

    def readFile(self, destination):
        content = []
        with open(_p(destination), 'r') as opened_file:
            for line in opened_file:
                content.append(line.rstrip())
        return content

    def getFileContentAsString(self, target):
        """
        Retrun the string represenation of the file.
        """
        with open(_p(target), 'r+') as opened_file:
            content = opened_file.read()
        return content

    def getFileContentAsList(self, target, strip_newline=True):
        """
        Retrun the string represenation of the file.

        If `strip_newline` is True, the trailing newline will be not included.
        """
        content = []
        with open(_p(target), 'r') as opened_file:
            for line in opened_file:
                if strip_newline:
                    line = line.rstrip()
                content.append(line)
        return content

    def createEmtpyFile(self, target):
        """
        Create empty file.
        """
        path = _p(target)
        with file(path, 'w'):
            os.utime(path, None)

    def createFolder(self, destination, recursive=False):
        """
        Create a folder

        If 'recursive' is True it will create parent folders if they don't
        exists.

        It ignores already exists errors.
        """
        path = _p(destination)
        try:
            if recursive:
                os.makedirs(path)
            else:
                os.mkdir(path)
        except OSError, error:
            if error.errno == 17:
                pass
            else:
                raise

    def copyFile(self, source, destination):
        """
        Copy file from `source` to `destination`.
        """
        shutil.copyfile(_p(source), _p(destination))

    def copyFolder(self, source, destination,
            excepted_folders=None, excepted_files=None):
        """
        Copy `source` folder to `destination`.

        The copy is done recursive.
        If folder already exitst the content will be merged.

        `excepted_folders` and `excepted_files` is a list of regex with
        folders and files that will not be copied.
        """
        source = _p(source)
        destination = _p(destination)

        if excepted_folders is None:
            excepted_folders = []

        if excepted_files is None:
            excepted_files = []

        if not os.path.exists(source):
            raise AssertionError(
                u'Source folder does not exists: %s' % (source))

        for source_folder, dirs, files in os.walk(source):
            destination_folder = destination + source_folder[len(source):]

            # Check if we need to skip this folder.
            skip_folder = False
            for excepted_folder in excepted_folders:
                if re.match(excepted_folder, source_folder):
                    skip_folder = True
                    break
            if skip_folder:
                continue

            if not os.path.exists(destination_folder):
                os.mkdir(destination_folder)

            for file_ in files:

                # Check if we need to skip this file.
                skip_file = False
                for excepted_file in excepted_files:
                    if re.match(excepted_file, file_):
                        skip_file = True
                        break
                if skip_file:
                    continue

                source_file = os.path.join(source_folder, file_)
                destination_file = os.path.join(destination_folder, file_)

                if os.path.exists(destination_file):
                    os.remove(destination_file)

                if os.path.islink(source_file):
                    linkto = os.readlink(source_file)
                    os.symlink(linkto, destination_file)
                else:
                    shutil.copyfile(source_file, destination_file)
                    shutil.copystat(source_file, destination_file)

    def copyFolderContent(self, source, destination, mask='.*'):
        """
        Copy folder content. cp source/* destination/
        """
        source = _p(source)
        destination = _p(destination)
        names = os.listdir(source)
        for name in names:
            file_source_path = _p([source, name])
            file_destination_path = _p([destination, name])
            try:
                if os.path.isfile(file_source_path) and re.search(mask, name):
                    shutil.copyfile(file_source_path, file_destination_path)
                    shutil.copymode(file_source_path, file_destination_path)
            except re.error:
                pass

    def concatenateFiles(self, sources, destination):
        """
        Concatenate sources files to destination.
        """
        with open(_p(destination), 'wb') as destination_file:
            for source in sources:
                shutil.copyfileobj(
                    open(_p(source), 'rb'), destination_file)

    def deleteFile(self, path):
        """
        Delete a file.

        Ignores errors if it does not exists.
        """
        try:
            os.unlink(_p(path))
        except OSError, error:
            if error.errno == 2:
                pass
            else:
                raise

    def deleteFolder(self, target):
        """
        Delete a folder.

        Ignores errors if it does not exists.
        """
        try:
            shutil.rmtree(_p(target))
        except OSError, error:
            if error.errno == 2:
                pass
            else:
                raise

    def createLink(self, source, destination):
        """
        Create a symlink on Unix or copy folder on Windows.

        createLink requires using absolute paths for source.
        """
        if os.name != 'nt':
            os.symlink(_p(source), _p(destination))
        else:
            self.copyFolder(
                source=source,
                destination=destination)

    def appendContentToFile(self, destination, content):
        """
        Appened content to file.
        """
        with open(_p(destination), 'a') as opened_file:
            opened_file.write(content)

    def writeContentToFile(self, destination, content):
        """
        Write content to file.
        """
        with open(_p(destination), 'w') as opened_file:
            opened_file.write(content)

    def replaceFileContent(self, target, rules):
        """
        Replace the file content.

        It takes a list for tuples [(pattern1, substitution1), (pat2, sub2)]
        and applies them in order.
        """
        with open(_p(target), 'r') as source_file:
            altered_lines = []
            for line in source_file:
                new_line = line
                for rule in rules:
                    pattern = rule[0]
                    substitution = rule[1]
                    new_line = re.sub(
                        pattern.encode('utf-8'),
                        substitution.encode('utf-8'),
                        new_line)
                altered_lines.append(new_line)

        with open(_p(target), 'w') as source_file:
            for line in altered_lines:
                source_file.write(line)


class ProjectPaths(object):

    def __init__(self, os_name, build_folder_name):
        self._os_name = os_name
        self.project = self._getProjectPath()
        self.product = os.path.abspath('.')
        self.build = _p([
            self.product, build_folder_name])
        self.deps = _p([
            self.project, SETUP['folders']['deps']])
        self.brink = _p([
            self.project, SETUP['folders']['brink']])
        self.pypi = _p([self.brink, 'cache', 'pypi'])
        self.dist = _p([
            self.product, SETUP['folders']['dist']])
        self.publish = _p([
            self.product, SETUP['folders']['publish']])

        self.python_executable = self.getPythonExecutable(os_name=os_name)

    def _getProjectPath(self):
        '''Return the root of Chevah project.'''
        cwd = os.getcwd()
        parent_folder, curent_folder = os.path.split(cwd)
        while (parent_folder and not parent_folder.endswith('chevah')):
            parent_folder, curent_folder = os.path.split(parent_folder)
        if not parent_folder:
            print 'Failed to get project root.'
            exit()
        return parent_folder

    def getPythonExecutable(self, os_name):
        '''Return the path to pyhon bin for target.'''
        if os_name == 'windows':
            return _p(['lib', 'python.exe'])
        else:
            return _p(['bin', 'python'])


class PaverSphinx(object):
    '''Collection of Python Sphinx operations.'''

    def call(self, arguments):
        from sphinx import main as sphinx_main
        sys.argv = ['sphinx']
        sys.argv.extend(arguments)
        sys.exit(sphinx_main(sys.argv))

    def createHTML(self, arguments=None, source=None, target=None):
        """
        Execute the command for building the documentation in HTML format.

        This is used by the documentation and APIdoc projects.
        The Sphinx command is executed inside the build folder, and all
        paths are relative to the build folder.
        """
        from sphinx import main as sphinx_main
        sphinx_command = ['sphinx', '-n']
        if arguments:
            sphinx_command.extend(arguments)

        if source is None:
            source = ['doc']

        if target is None:
            target = ['doc_build']

        sphinx_command.extend(['-b', 'html', _p(source), _p(target)])

        sys_argv = sys.argv
        try:
            sys.argv = sphinx_command
            with pushd(pave.path.build):
                return sphinx_main(sys.argv)
        finally:
            sys.argv = sys_argv

    def createPDF(self):
        '''Generates a PDF file for the documentation.'''
        from sphinx import main as sphinx_main
        sys.argv = ['sphinx', '-b', 'pdf', 'doc', 'doc_build']
        return sphinx_main(sys.argv)

    def apidoc(self, module, destination):
        from chevah.commons.utils.apidoc import main as apidoc_main
        pave.fs.createFolder(destination=destination, recursive=True)
        sys.argv = [
            'apidoc', '--maxdepth=4', '-f', '-o', _p(destination), module]
        apidoc_main(sys.argv)

    def makeConfiguration(self, destination, project, version, themes_path,
            theme_name='standalone', intersphinx_mapping=None,
            copyright='Chevah Team',
        ):
        """
        Generates the configuration files for creating Sphinx based
        documentation.

        Configuration file is stored in 'destination' file, and should
        be named 'conf.py'.
        """
        if intersphinx_mapping is None:
            intersphinx_mapping = "{}"

        content = """

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'repoze.sphinx.autointerface',
    ]
source_suffix = '.rst'
exclude_patterns = ['**/*.include.rst']
master_doc = 'index'
pygments_style = 'sphinx'
intersphinx_mapping = %(intersphinx_mapping)s
templates_path = ['%(themes_path)s']
html_static_path = ['_static']
html_theme_path = ['%(themes_path)s']
html_theme = '%(theme_name)s'
project = "%(project)s"
copyright = "%(copyright)s"
version = "%(version)s"
release = "%(version)s"
autodoc_default_flags = ['members']
primary_domain = 'py'

""" % ({
    'theme_name': theme_name,
    'project': project,
    'version': version,
    'intersphinx_mapping': intersphinx_mapping,
    'copyright': copyright,
    'themes_path': themes_path,
    })

        with open(_p(destination), 'w') as conf_file:
            conf_file.write(content)


class ChevahPaver(object):

    def __init__(self):
        self._default_values = self._getDefaultValues()
        self.os_name = self._default_values['os_name']
        self.cpu = self._default_values['platform']

        self.path = ProjectPaths(
            os_name=self.os_name,
            build_folder_name=self._default_values['build_folder'],
            )
        self.git = PaverGit()
        self.fs = PaverFilesystem()
        self.sphinx = PaverSphinx()

        self.python_command_normal = [self.path.python_executable]
        if self.os_name == 'windows':
            self.python_command_super = [self.path.python_executable]
        else:
            self.python_command_super = ['sudo', self.path.python_executable]

    def _getDefaultValues(self):
        '''Get the default build folder and python version.'''
        with open('DEFAULT_VALUES') as default_values:
            output = default_values.read()
        results = output.strip().split(' ')
        default_values = {
            'build_folder': results[0],
            'python_version': results[1],
            'os_name': results[2],
            'platform': results[3],
        }
        return default_values

    def updateRepositories(self, projects, uri):
        print('Updating dependencies from "%s".' % uri)

        for project_name in projects:
            repo_uri = uri + project_name + '.git'

            project_folder = _p([self.path.project, project_name])
            # Do the initial clone if the repo does not exists.
            if not os.path.exists(project_folder):
                with pushd(self.path.project):
                    self.git.clone(
                        repo_uri=repo_uri, project_name=project_name)
            else:
                with pushd(project_folder):
                    self.git.pull(repo_uri=repo_uri)

    def execute(self, *args, **kwargs):
        return execute(*args, **kwargs)

    def installRunDependencies(self, extra_packages=None):
        """
        Install the required packages for runtime environemnt.
        """
        if extra_packages is None:
            extra_packages = []

        self.pip(
            command='install',
            arguments=[
                '-r', _p([pave.path.brink, 'requirements-runtime.txt']),
                ],
            )

        for package in extra_packages:
            self.pip(
                command='install',
                arguments=[package],
                )

    def installBuildDependencies(self):
        """
        Intall the required packages to build environment.
        """
        self.pip(
            command='install',
            arguments=[
                '-r', _p([pave.path.brink, 'requirements-buildtime.txt']),
                ],
            )

    def uninstallBuildDependencies(self):
        """
        Unintall the required packages to build environment.
        """
        self.pip(
            command='uninstall',
            arguments=[
                '-r', _p([pave.path.brink, 'requirements-buildtime.txt']),
                '-y',
                ],
            )

    def pip(self, command='install', arguments=None,
            exit_on_errors=True, index_url=None, only_cache=False,
            silent=False):
        """
        Execute the pip command.
        """

        # Reset packages state before each run.
        # Pip does not support multiple runs from a single instances,
        # so installed packages are cached per instance.
        from pkg_resources import working_set
        working_set.entries = []
        working_set.entry_keys = {}
        working_set.by_key = {}
        map(working_set.add_entry, sys.path)

        from pip import log, main

        # Fix multiple log consumers.
        # pip does not support multiple runs from a single python instance
        # so at start, it just appends the log consumers.
        # Here we reset them as a python instance was just started.
        log.logger.consumers = []

        pip_build_path = [self.path.build, 'pip-build']
        self.fs.deleteFolder(pip_build_path)

        if index_url is None:
            index_url = SETUP['pypi']['index_url']

        if arguments is None:
            arguments = []

        pip_arguments = [command]

        if command == 'install':
            if only_cache:
                pip_arguments.extend(['--no-index'])
            else:
                pip_arguments.extend(
                    ['--index-url=' + index_url])
            pip_arguments.extend(
                ['--download-cache=' + self.path.pypi])

            pip_arguments.extend(
                ['--build=' + _p(pip_build_path)])

            pip_arguments.extend(
                ['--find-links=file://' + self.path.pypi])

        if silent:
            pip_arguments.extend(['-q'])

        pip_arguments.extend(arguments)

        result = main(initial_args=pip_arguments)

        if result != 0 and exit_on_errors:
            print "Failed to run:\npip %s" % (' '.join(pip_arguments))
            sys.exit(result)

        return result

    def openPage(self, url):
        open_url = urllib2.build_opener()
        request = urllib2.Request(url)
        try:
            result = open_url.open(request)
            return result
        except:
            print 'Failed to open ' + url
            sys.exit(1)

    def getJSON(self, url):
        """
        Get URL as JSON and return the dict representations.
        """
        import simplejson
        result = simplejson.load(self.openPage(url))
        return result

    def buildbotShowLastStep(self, args):

        if not '--wait' in args:
            return

        for index, arg in enumerate(args):
            if arg == '-b':
                break

        builder = args[index + 1]

        base_url = (
            SETUP['buildbot']['web_url'] +
            '/json/builders/' +
            builder)
        result = self.getJSON(url=base_url)
        last_build = str(result['cachedBuilds'][-1])

        result = self.getJSON(url=base_url + '/builds/' + last_build)
        for line in self.openPage(result['logs'][-1][1] + '/text'):
            print line,

    def getOption(self, options, option_name,
            default_value=None, required=False):
        '''Return the paver option_name passed to task_name.'''
        try:
            value = options[option_name]
        except KeyError:
            if required:
                print 'It is required to provide option "%s".' % (option_name)
                sys.exit(1)
            value = default_value
        return value

    def copyPython(self, destination, python_version, platform):
        """
        Create a base Python environment.
        """
        python_binary_dist = 'python' + python_version + '-' + platform
        source = [self.path.brink, 'cache', python_binary_dist]
        self.fs.deleteFolder(destination)
        self.fs.copyFolder(source, destination)

    def getIPAddress(self, gateway='172.20.0.1'):
        '''Return the local public IP address.'''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((gateway, 80))
        address = s.getsockname()[0]
        s.close()
        return address

    def getHostname(self):
        '''Return the hostname of the local computer.'''
        hostname = socket.gethostname()
        if hostname.startswith('buildslave-'):
            hostname = hostname[11:]
        if hostname.startswith('bs-'):
            hostname = hostname[3:]
        return hostname

    def createTarGZArchive(self, folder_name):
        tar_name = folder_name + '.tar'
        tar_command = [
            'pax', '-wf', tar_name, folder_name]
        execute(tar_command)
        gzip_command = ['gzip', '-f', tar_name]
        execute(gzip_command)

    def createZipArchive(self, source, destination, exclude=None):
        """
        Create a zip file at `destination` based on files from `source`.
        """
        """
        Create a zip file at `destination` based on files from `source`.
        """
        if exclude is None:
            exclude = []

        source_path = _p(source)
        parent_path = os.path.dirname(source_path)
        archivename = _p(destination)
        with closing(ZipFile(archivename, 'w', ZIP_DEFLATED)) as z:
            for root, dirs, files in os.walk(source_path):
                # Write all files.
                for fn in files:
                    if fn in exclude:
                        continue
                    absolute_filename = os.path.join(root, fn)
                    zip_filename = absolute_filename[len(parent_path):]
                    # FIXME
                    # See http://bugs.python.org/issue1734346
                    # for adding unicode support.
                    z.write(str(absolute_filename), str(zip_filename))

                # For empty folders, we need to create a special ZipInfo
                # entry.
                # 16 works, but some places suggest using 48.
                if not files and not dirs:
                    foldername = root + '/'
                    zip_info = ZipInfo(foldername)
                    zip_info.external_attr = 16
                    z.writestr(zip_info, "")

    def createMD5Sum(self, source):
        '''
        Returns an MD5 hash for the file specified by file_path.
        '''
        md5hash = md5.new()

        with open(_p(source), 'rb') as input_file:
            while True:
                read_buffer = input_file.read(8096)
                if not read_buffer:
                    break
                md5hash.update(read_buffer)

            result = md5hash.hexdigest()

        return result

    def createNSIS(self, folder_name, product_name, product_version,
                  product_url, product_publisher):
        '''Generate a self extracted install file using NSIS.'''
        defines = (
            '!define PRODUCT_NAME "%s"\n'
            '!define PRODUCT_VERSION "%s"\n'
            '!define PRODUCT_PUBLISHER "%s"\n'
            '!define PRODUCT_URL "%s"\n'
            '!define DISTRIBUTABLE_NAME "%s"\n' % (
                product_name,
                product_version,
                product_publisher,
                product_url,
                folder_name,
                ))

        target = _p([pave.path.dist, folder_name])
        target_nsis_path = _p([target, 'windows-installer.nsi'])
        template_nsis_path = _p([
            pave.path.product,
            SETUP['folders']['source'],
            SETUP['folders']['static'],
            SETUP['folders']['nsis'],
            'windows-installer.nsi.in',
            ])

        with open(target_nsis_path, 'w') as nsis_file:
            # Write constants file.
            nsis_file.write(defines)
            # Append template nsis file
            for line in open(template_nsis_path):
                nsis_file.write(line)

        make_nsis_command = ['makensis', 'windows-installer.nsi']

        try:
            with pushd(target):
                subprocess.call(make_nsis_command)
        except OSError, os_error:
            if os_error.errno != 2:
                raise
            print (
                'NullSoft Installer is not installed. '
                'On Ubuntu you can install it using '
                '"sudo apt-get install nsis".'
                )
            sys.exit(1)
        pave.fs.deleteFile(target_nsis_path)

    def fixDosEndlines(self, target_path, python_lib):
        '''Convert all bat and config files to dos newlines.'''

        def convert_to_dos_newlines(file_path):
            '''Convert the file to dos newlines.'''
            tmp_file_path = file_path + '.tmp'
            write_file = open(tmp_file_path, 'wb')
            read_file = open(file_path, 'rU')
            for line in read_file:
                line = line.strip()
                write_file.write(line + '\r\n')
            write_file.close()
            read_file.close()
            os.remove(file_path)
            os.rename(tmp_file_path, file_path)

        root_files = os.listdir(target_path)
        files_fixed = 0
        for filename in root_files:
            if filename.endswith('.bat'):
                file_path = os.path.join(target_path, filename)
                convert_to_dos_newlines(file_path)
                files_fixed += 1

        if files_fixed == 0:
            print "Failed to convert any bat files."
            sys.exit(1)

        source_folder = _p([python_lib,
                    'chevah',
                    SETUP['folders']['source'],
                    SETUP['folders']['static'],
                    SETUP['folders']['configuration'],
                    ])
        config_files = os.listdir(source_folder)
        files_fixed = 0
        for filename in config_files:
            if '.config' in filename:
                file_path = os.path.join(source_folder, filename)
                convert_to_dos_newlines(file_path)
                files_fixed += 1

        if files_fixed == 0:
            print "Failed to convert any configuration files."
            sys.exit(1)

    def copyDependencyFile(self, project, version, source, destination):
        """
        Copy a dependency file to destination.
        """
        deps_source = [
            pave.path.deps, 'src', project, project + '-' + version]
        deps_source.extend(source)
        self.fs.copyFile(source=deps_source, destination=destination)

    def rsync(self, username, hostname, source, destination):
        """
        Executes the external rsync command using SSH.

        `source` is specified as local path segments.
        `destination` is path as string.
        """
        destination_uri = '%s@%s:%s' % (username, hostname, destination)
        command = [
            'rsync', '-acz', '-e', "'ssh'",
            _p(source),
            destination_uri,
            ]
        exit_code, result = self.execute(
            command=command, output=sys.stdout)
        if exit_code:
            print "Failed to execute rsync."
            sys.exit(exit_code)

    def importAsString(self, module_name):
        """
        Import the module as dotted path string.
        """
        __import__(module_name)
        return sys.modules[module_name]


pave = ChevahPaver()


@task
@cmdopts([
    ('uri=', None, 'Base repository URI.'),
])
def deps_update(options):
    '''Update dependencies source.'''

    projects = [
        'agent',
        'agent-1.5',
        'commons',
        'deps',
        'server',
        'webadmin-1.6',
        ]
    default_uri = SETUP['repository']['base_uri']
    base_uri = pave.getOption(
        options.deps_update, 'uri', default_value=default_uri)
    pave.updateRepositories(projects=projects, uri=base_uri)


def _pocketlint_check(folder=None, files=None):
    '''Run pocketlint on all .js, .html and .css files from `folder`.

    Files from `excepted_folders` list will not be checked.
    '''
    from pocketlint.formatcheck import (
        check_sources,
        JavascriptChecker,
        JS,
        )
    from pocketlint.contrib import cssccc
    import pocketlint

    class PocketLintOptions(object):
        """
        Holds the options used by pocket lint for chevah project.
        """
        def __init__(self):
            self.max_line_length = 79

    if pave.os_name is 'ubuntu' and JS is None:
        print 'Install "seed" or "gjs" to enable JS linting on Ubuntu.'
        sys.exit(1)

    def is_excepted_folder(root):
        excludes = SETUP['pocket-lint']['exclude_folders']
        for exception in excludes:
            if re.match(exception, root):
                return True
        return False

    sources = []
    if folder:
        for root, member_folders, member_files in os.walk(folder):
            if is_excepted_folder(root):
                continue
            for file_name in member_files:
                check_file = True
                excludes = (
                    SETUP['pocket-lint']['exclude_files'])
                if file_name in excludes:
                    check_file = False
                if check_file:
                    sources.append(os.path.join(root, file_name))

    if files is None:
        files = []
    for file in files:
        sources.append(file)

    count = -1
    pocketlint_path = os.path.dirname(pocketlint.__file__)
    jslint = _p([pocketlint_path, 'pocketlint', 'jshint', 'jshint.js'])
    jsreporter = _p([
        pocketlint_path, 'pocketlint', 'jshint', 'jshintreporter.js'])

    initial_jslint = JavascriptChecker.FULLJSLINT
    initial_jsreporter = JavascriptChecker.JSREPORTER
    initial_ignore = cssccc.IGNORED_MESSAGES
    try:
        JavascriptChecker.FULLJSLINT = jslint
        JavascriptChecker.JSREPORTER = jsreporter
        cssccc.IGNORED_MESSAGES = ['I005', 'I006']
        count = check_sources(sources, PocketLintOptions())
    finally:
        JavascriptChecker.FULLJSLINT = initial_jslint
        JavascriptChecker.JSREPORTER = initial_jsreporter
        cssccc.IGNORED_MESSAGES = initial_ignore

    return count


@task
def lint():
    '''Run static codse checks.'''
    pocketlint_reports_count = _pocketlint_check(
        folder=SETUP['folders']['source'])

    # Check for additional files outside of source folder.
    pocketlint_reports_count += _pocketlint_check(
        files=SETUP['pocket-lint']['include_files'])

    for folder in SETUP['pocket-lint']['include_folders']:
        pocketlint_reports_count += _pocketlint_check(folder=folder)

    if pocketlint_reports_count > 0:
            raise SystemExit(True)

    return 0


@task
def default():
    '''Default task. Shows this help.'''
    environment.args = []
    help()


@task
def deps():
    """Copy external dependencies.

    Each project should define custom deps_runtime and deps_builtime
    targets.
    """
    pave.installBuildDependencies()


@task
@needs('build')
@consume_args
def test(args):
    '''Run the test suite.'''
    exit_code = run_test(
        python_command=pave.python_command_normal,
        switch_user='-',
        arguments=args,
        )

    if exit_code != 0:
        sys.exit(exit_code)
    return exit_code


@task
@needs('build')
@consume_args
def test_super(args):
    '''Run the test suite using root. On Windows is runs as a normal user.'''
    exit_code = run_test(
        python_command=pave.python_command_super,
        switch_user=getpass.getuser(),
        arguments=args,
        )

    if exit_code != 0:
        sys.exit(exit_code)
    return exit_code


def run_test(python_command, switch_user, arguments):
    test_command = python_command[:]
    test_command.extend([_p(['bin', 'nose_runner.py']), switch_user])

    test_args = arguments[:]

    if '--pdb' in test_args:
        test_args.append('--pdb-failures')

    have_explicit_tests = False
    source_folder = SETUP['folders']['source']
    test_module = u'chevah.' + source_folder + '.tests'

    test_module = SETUP['test']['package']
    for index, item in enumerate(test_args):
        # Look for appending package name to test module name.
        # Add explicit test package to shorthand tests.
        if (not item.startswith(test_module) and not item.startswith(u'-')):
            have_explicit_tests = True
            test_args[index] = test_module + '.' + item

        # Add generic regex to match if they are missing
        if item.startswith(u'--match'):
            rule = item[8:]
            test_args[index] = '--match=.*' + rule + '.*'

    if not have_explicit_tests:
        # Add all test if no particular test was asked.
        test_args.append(test_module)

    test_command.extend(test_args)
    with pushd(pave.path.build):
        print test_command
        exit_code = subprocess.call(test_command)
        print 'Exit code is: %d' % (exit_code)
        return exit_code


@task
@needs('build')
def harness():
    '''Start a Python shell.'''
    with pushd(pave.path.build):
        import code
        shell = code.InteractiveConsole(globals())
        shell.interact()


@task
@consume_args
def sphinx(args):
    '''Call the Sphinx command line tool.'''
    with pushd(pave.path.build):
        pave.sphinx.call(arguments=args)


@task
@needs('build')
def apidoc():
    '''Generates automatic API documentation files..'''

    module = 'chevah.' + SETUP['folders']['source']
    with pushd(pave.path.build):
        pave.sphinx.apidoc(module=module, destination=['doc', 'api'])

    pave.fs.copyFile(
        source=['apidoc_conf.py'],
        destination=[pave.path.build, 'doc', 'conf.py'],
        )
    pave.sphinx.createHTML()


@task
@consume_args
def buildbot_try(args):
    '''Launch a try job on buildmaster.'''

    if not len(args):
        print 'User "-b builder_name" to run the try on builder_name.'
        print 'You can use multiple builders by using multiple -b args.'
        buildbot_list()
        sys.exit(1)

    # Add -b in front of the last argument if no builder where specified
    if not '-b' in args:
        builder_name = args[-1]
        args[-1] = '-b'
        args.append(builder_name)

    from buildbot.scripts import runner
    from unidecode import unidecode

    # Push the latest changes to remote repo, as otherwise the diff will
    # not be valide.
    pave.git.push()

    new_args = [
        'buildbot', 'try',
        '--connect=pb',
        '--master=%s:%d' % (
            SETUP['buildbot']['server'],
            SETUP['buildbot']['port']
            ),
        '--username=%s' % (SETUP['buildbot']['username']),
        '--passwd=%s' % (SETUP['buildbot']['password']),
        '--vc=%s' % (SETUP['buildbot']['vcs']),
        '--who="%s"' % (unidecode(pave.git.account)),
        '--branch=%s' % (pave.git.branch_name),
        ]

    if not ('--no-wait' in args):
        print ('Use "--no-wait" if you only want to trigger the build'
                'without waiting for result.')
        args.append('--wait')
    else:
        args.remove('--no-wait')

    new_args.extend(args)
    sys.argv = new_args
    try:
        runner.run()
    finally:
        pave.buildbotShowLastStep(args)


@task
@consume_args
def buildbot_list(args):
    '''List builder names available on the remote buildbot master.

    To get the list of all remote builder, call this target with 'all'
    argument.
    '''
    from buildbot.scripts import runner

    new_args = [
        'buildbot', 'try',
        '--connect=pb',
        '--master=%s:%d' % (
            SETUP['buildbot']['server'],
            SETUP['buildbot']['port']
            ),
        '--username=%s' % (SETUP['buildbot']['username']),
        '--passwd=%s' % (SETUP['buildbot']['password']),
        '--get-builder-names',
        ]
    sys.argv = new_args

    print 'Running %s' % new_args

    new_out = None
    if not 'all' in args:
        from StringIO import StringIO
        new_out = StringIO()
        sys.stdout = new_out

    try:
        runner.run()
    finally:
        if new_out:
            sys.stdout = sys.__stdout__
            if SETUP['buildbot']['builders_filter']:
                selector = (
                    SETUP['buildbot']['builders_filter'])
            elif SETUP['folders']['source']:
                selector = SETUP['folders']['source']
            else:
                selector = ''
            for line in new_out.getvalue().split('\n'):
                if selector in line:
                    print line


@task
@cmdopts([
    ('username=', None, 'Username for which to request review.'),
    ('review_id=', 'r', 'Review ID to update.'),
    ('name=', 'n', 'The name of this review.'),
    ('description=', 'd', 'Description of changes.'),
])
def review(options):
    '''Creates and updates reviews hosted on ReviewBoard.'''
    from rbtools.postreview import main as postreview_main

    branch_name = pave.git.branch_name

    print "Pushing changes..."
    git_push = ['git', 'push', '--set-upstream', 'origin', branch_name]
    pave.execute(git_push)

    username = pave.getOption(options.review, 'username', default_value=None)

    if not username:
        # Get the ReviewBoard username based on git account.
        # Translate: Name Surname <name@domain.tld>
        # As: namesurname
        from unidecode import unidecode
        username = unidecode(pave.git.account)
        username = username.split('<')[0].strip().lower()
        username = username.replace(' ', '')

    review_id = pave.getOption(options.review, 'review_id')

    # Try to get the bug number from branch name as 23-some_description.
    # If it is not number, set it to None.
    bug = branch_name.split('-')[0]
    try:
        int(bug)
    except ValueError:
        bug = None

    name = pave.getOption(options.review, 'name')
    if name is None:
        name = branch_name

    description = pave.getOption(options.review, 'description')

    module = SETUP['repository']['name']

    new_args = ['rbtools']
    new_args.extend([
        '--server=http://review.chevah.com/',
        '--repository-url=/srv/git/' + module + '.git',
        '--username=%s' % username,
        ])

    if review_id:
        new_args.append('--review-request-id=%s' % review_id)

        if description is None:
            description = pave.git.last_commit
        new_args.append('--change-description=' + description)

        # We don't want to update the summary when posting an updated diff.
        name = None
        description = None
        bug = None

    if name:
        new_args.append('--summary=' + name)

    if description:
        new_args.append('--description=' + description)

    if bug:
        new_args.append('--bugs-closed=' + bug)

    sys.argv = new_args
    print 'Posting review as user: ' + username
    postreview_main()


@task
@needs('build', 'update_setup')
def doc_html():
    """
    Generates the documentation.
    """
    product_name = SETUP['product']['name']
    version = SETUP['product']['version']

    themes_path = pave.importAsString(
        SETUP['sphinx']['themes_package']).get_module_path()
    pave.sphinx.makeConfiguration(
        destination=[pave.path.build, 'doc_source', 'conf.py'],
        project=product_name,
        version=version,
        copyright=SETUP['product']['copyright_holder'],
        themes_path=themes_path,
        theme_name='standalone'
        )
    destination = [pave.path.build, 'doc', 'html']
    exit_code = pave.sphinx.createHTML(
        arguments=[],
        source=['doc_source'],
        target=destination,
        )

    media_path = pave.importAsString(
        SETUP['sphinx']['media_package']).get_module_path()
    pave.fs.copyFolder(
        source=[media_path, 'media'],
        destination=[pave.path.build, 'doc', 'html', 'media'])

    print "Documentation files generated in %s" % _p(destination)
    return exit_code


@task
@needs('update_setup', 'dist', 'doc_html')
def publish():
    """
    Publish download files and documentation.

    publish/downloads/PRODUCT_NAME will go to download website
    publish
    """
    product_name = SETUP['product']['name'].lower()
    version = SETUP['product']['version']
    version_major = SETUP['product']['version_major']
    version_minor = SETUP['product']['version_minor']

    publish_downloads_folder = [pave.path.publish, 'downloads']
    publish_website_folder = [pave.path.publish, 'website']
    product_folder = [_p(publish_downloads_folder), product_name]
    release_publish_folder = [
        _p(publish_downloads_folder),
        product_name, version_major, version_minor]

    # Create publising content for download site.
    pave.fs.deleteFolder(publish_downloads_folder)
    pave.fs.createFolder(release_publish_folder, recursive=True)
    pave.fs.writeContentToFile(
        destination=[_p(product_folder), 'LATEST'], content=version)
    pave.fs.createEmtpyFile([_p(product_folder), 'index.html'])
    pave.fs.copyFolderContent(
        source=[pave.path.dist],
        destination=release_publish_folder,
        )

    # Create publising content for presentation site.
    pave.fs.deleteFolder(publish_website_folder)
    pave.fs.createFolder(publish_website_folder)
    pave.fs.createFolder([_p(publish_website_folder), 'downloads'])
    pave.fs.copyFolder(
        source=[pave.path.build, 'doc', 'html/'],
        destination=[pave.path.publish, 'website', 'documentation'],
        )
    release_html_name = 'release-' + version + '.html'
    pave.fs.copyFile(
        source=[pave.path.dist, release_html_name],
        destination=[
            pave.path.publish, 'website', 'downloads', release_html_name],
        )
    pave.fs.copyFile(
        source=[pave.path.dist, release_html_name],
        destination=[pave.path.publish, 'website', 'downloads', 'index.html'],
        )

    publish_config = SETUP['publish']
    if pave.git.branch_name == 'production':
        download_hostname = publish_config['download_production_hostname']
        documentation_hostname = publish_config['website_production_hostname']
    else:
        download_hostname = publish_config['download_staging_hostname']
        documentation_hostname = publish_config['website_staging_hostname']

    print "Publishing distributables to %s ..." % (download_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=download_hostname,
        source=[pave.path.publish, 'downloads', product_name + '/'],
        destination=download_hostname + '/' + product_name
        )

    print "Publishing documentation to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'documentation/'],
        destination=documentation_hostname + '/documentation/' + product_name
        )

    print "Publishing download pages to %s..." % (documentation_hostname)
    pave.rsync(
        username='chevah_site',
        hostname=documentation_hostname,
        source=[pave.path.publish, 'website', 'downloads/'],
        destination=documentation_hostname + '/downloads/' + product_name
        )

    print "Publish done."


@task
def clean():
    '''Clean build and dist folders.

    This is just a placeholder, since clean is handeld by the outside
    paver.sh scripts.
    '''
