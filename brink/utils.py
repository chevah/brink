# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Utility code for Brink.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )

from contextlib import closing
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from hashlib import md5, sha256
import os
import socket
import subprocess
import sys

from brink.execute import execute
from brink.git_command import BrinkGit
from brink.filesystem import BrinkFilesystem
from brink.paths import ProjectPaths
from brink.sphinx import BrinkSphinx


class BrinkPaver(object):
    """
    Collection of methods to help with build system.
    """

    def __init__(self, setup):
        self.setup = setup
        self._default_values = self._getDefaultValues()
        self.os_name = self._default_values['os_name']
        self.cpu = self._default_values['platform']
        self.python_version = self._default_values['python_version']

        self.fs = BrinkFilesystem()
        self.path = ProjectPaths(
            os_name=self.os_name,
            build_folder_name=self._default_values['build_folder'],
            folders=self.setup['folders'],
            filesystem=self.fs,
            )
        self.git = BrinkGit(filesystem=self.fs)

        self.sphinx = BrinkSphinx(paver=self)

        self.python_command_normal = [self.path.python_executable]
        if self.os_name == 'win':
            self.python_command_super = [self.path.python_executable]
        elif self.os_name == 'sles10':
            self.python_command_super = [
                'sudo',
                self.path.python_executable,
                ]
        else:
            CODECOV_TOKEN = os.getenv('CODECOV_TOKEN', '')
            self.python_command_super = [
                'sudo',
                'CODECOV_TOKEN=%s' % (CODECOV_TOKEN,),
                self.path.python_executable,
                ]

    def _getDefaultValues(self):
        '''Get the default build folder and python version.'''
        default_values = {
            'build_folder': os.environ['PYTHONPATH'],
            'python_version': os.environ['CHEVAH_PYTHON'],
            'os_name': os.environ['CHEVAH_OS'],
            'platform': os.environ['CHEVAH_ARCH'],
            }
        return default_values

    def execute(self, *args, **kwargs):
        """
        Shortcut to execute function.

        This is here to avoid importing the execute function and also help
        with testing.
        """
        return execute(*args, **kwargs)

    def pip(self, command='install', arguments=None,
            exit_on_errors=True, index_url=None, only_cache=False,
            install_hook=None, silent=False):
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
        list(map(working_set.add_entry, sys.path))

        from pip import main

        pip_build_path = [self.path.build, 'pip-build']
        self.fs.deleteFolder(pip_build_path)

        if index_url is None:
            index_url = self.setup['pypi']['index_url']

        if arguments is None:
            arguments = []

        pip_arguments = [command]

        if command == 'install':
            pip_arguments.extend([
                '--trusted-host', 'pypi.chevah.com',
                '--trusted-host', 'deag.chevah.com:10042',
                ])
            if only_cache:
                pip_arguments.extend([b'--no-index'])
            else:
                pip_arguments.extend(
                    [b'--index-url=' + index_url])

            if install_hook:
                pip_arguments.extend([
                    b'--install-hook=%s' % (install_hook)])

            pip_build = self.fs.join(pip_build_path)
            pip_arguments.extend(['--build', pip_build])

        if silent:
            pip_arguments.extend(['-q'])

        pip_arguments.extend(arguments)

        result = main(args=pip_arguments)

        if result != 0 and exit_on_errors:
            print("Failed to run:\npip %s" % (' '.join(pip_arguments)))
            sys.exit(result)

        return result

    def getOption(
            self, options, task_name, option_name,
            default_value=None, required=False):
        '''Return the paver option_name passed to task_name.'''
        try:
            task_options = options[task_name]
        except KeyError:
            return default_value

        try:
            value = task_options[option_name]
        except KeyError:
            if required:
                print('It is required to provide option "%s".' % (option_name))
                sys.exit(1)
            value = default_value
        return value

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

        source_path = self.fs.join(source)
        parent_path = os.path.dirname(source_path)
        archivename = self.fs.join(destination)
        with closing(ZipFile(archivename, 'w', ZIP_DEFLATED)) as z:
            for root, dirs, files in os.walk(source_path):
                # Write all files.
                for fn in files:
                    if fn in exclude:
                        continue
                    absolute_filename = os.path.join(root, fn)
                    zip_filename = absolute_filename[len(parent_path):]
                    # See http://bugs.python.org/issue1734346
                    # for adding unicode support.
                    z.write(str(absolute_filename), str(zip_filename))

                # For empty folders, we need to create a special ZipInfo
                # entry.
                # 16 works, but some places suggest using 48.
                if not files and not dirs:
                    foldername = root[len(parent_path):] + '/'
                    zip_info = ZipInfo(foldername)
                    zip_info.external_attr = 16
                    z.writestr(zip_info, "")

    def createMD5Sum(self, source):
        '''
        Returns an MD5 hash for the file specified by file_path.
        '''
        md5hash = md5()

        with open(self.fs.join(source), 'rb') as input_file:
            while True:
                read_buffer = input_file.read(8096)
                if not read_buffer:
                    break
                md5hash.update(read_buffer)

            result = md5hash.hexdigest()

        return result

    def createSHA256Sum(self, source):
        '''
        Returns an SHA256 hash for the file specified by file_path.
        '''
        shahash = sha256()

        with open(self.fs.join(source), 'rb') as input_file:
            while True:
                read_buffer = input_file.read(8096)
                if not read_buffer:
                    break
                shahash.update(read_buffer)

            result = shahash.hexdigest()

        return result

    def createNSIS(
            self, folder_name, product_name, product_version,
            product_url, product_publisher, platform='win-x86'):
        """
        Generate a self extracted install file using NSIS.
        """
        defines = (
            '!define PRODUCT_NAME "%s"\n'
            '!define PRODUCT_VERSION "%s"\n'
            '!define PRODUCT_PUBLISHER "%s"\n'
            '!define PRODUCT_URL "%s"\n'
            '!define PLATFORM "%s"\n'
            '!define DISTRIBUTABLE_NAME "%s"\n' % (
                product_name,
                product_version,
                product_publisher,
                product_url,
                platform,
                folder_name,
                ))

        target = self.fs.join([self.path.dist, folder_name])
        target_nsis_path = self.fs.join([target, 'windows-installer.nsi'])
        template_nsis_path = self.fs.join([
            self.path.product,
            self.setup['folders']['source'],
            self.setup['folders']['static'],
            self.setup['folders']['nsis'],
            'windows-installer.nsi.in',
            ])

        with open(target_nsis_path, 'w') as nsis_file:
            # Write constants file.
            nsis_file.write(defines)
            # Append template nsis file
            for line in open(template_nsis_path):
                nsis_file.write(line)

        nsis_locations = [
            r'C:\Program Files (x86)\NSIS',
            r'C:\Program Files\NSIS',
            ]
        make_nsis_path = self.fs.which('makensis', nsis_locations)
        if not make_nsis_path:
            print(
                'NullSoft Installer is not installed. '
                'On Ubuntu you can install it using '
                '"sudo apt-get install nsis".'
                )
            sys.exit(1)

        make_nsis_command = [make_nsis_path, '-V2', 'windows-installer.nsi']

        try:
            with self.fs.changeFolder([target]):
                print("Executing %s" % make_nsis_command)
                subprocess.call(make_nsis_command)
        except OSError as os_error:
            if os_error.errno != 2:
                raise
            print(
                'NullSoft Installer is not installed. '
                'On Ubuntu you can install it using '
                '"sudo apt-get install nsis".'
                )
            sys.exit(1)
        self.fs.deleteFile(target_nsis_path)

    def fixDosEndlines(self, target_path, python_lib):
        '''Convert all bat and config files to dos newlines.'''

        root_files = os.listdir(target_path)
        files_fixed = 0
        for filename in root_files:
            if filename.endswith('.bat'):
                file_path = self.fs.join([target_path, filename])
                self._convertToDOSNewlines(file_path)
                files_fixed += 1

        if files_fixed == 0:
            print("Failed to convert some bat files.")
            sys.exit(1)

        source_folder = self.fs.join([
            python_lib,
            self.setup['folders']['source'],
            self.setup['folders']['static'],
            self.setup['folders']['configuration'],
            ])
        config_files = os.listdir(source_folder)
        files_fixed = 0
        for filename in config_files:
            if '.ini' in filename or '.config' in filename:
                file_path = self.fs.join([source_folder, filename])
                self._convertToDOSNewlines(file_path)
                files_fixed += 1

        if files_fixed == 0:
            print("Failed to convert some configuration files.")
            sys.exit(1)

    def _convertToDOSNewlines(self, file_path):
        """
        Convert the file to DOS newlines.
        """
        tmp_file_path = self.fs.getEncodedPath(file_path + '.tmp')
        file_path = self.fs.getEncodedPath(file_path)
        write_file = open(tmp_file_path, 'wb')
        read_file = open(file_path, 'rU')
        for line in read_file:
            # Only discard newline from the end.
            line = line.rstrip('\n')
            write_file.write(line + '\r\n')
        write_file.close()
        read_file.close()
        os.remove(file_path)
        os.rename(tmp_file_path, file_path)

    def rsync(self, username, hostname, source, destination, verbose=False):
        """
        Executes the external rsync command using SSH.

        `source` is specified as local path segments.
        `destination` is path as string.
        """
        destination_uri = '%s@%s:%s' % (username, hostname, destination)
        if self.os_name == 'win':
            # On Windows we use the cygwin ssh, and not the git ssh.
            # It needs an explicit config file.
            home_path = os.getenv('USERPROFILE')
            ssh_command = 'ssh-rsync -F %s' % (os.path.join(
                home_path, '.ssh', 'config'),)
            arguments = [
                '-rcz',
                '-no-p', '--chmod=D755,F644',
                '--chown=%s:www-data' % (username,),
                '-e', ssh_command,
                ]
        else:
            # On Linux we can just archive.
            arguments = ['-cza', '-e', 'ssh']

        command = ['rsync'] + arguments
        if verbose:
            command.append('-v')
        command.append(self.fs.join(source))
        command.append(destination_uri)
        exit_code, result = self.execute(
            command=command, output=sys.stdout)
        if exit_code:
            print("Failed to execute rsync.")
            sys.exit(exit_code)

    def importAsString(self, module_name):
        """
        Import the module as dotted path string.
        """
        __import__(module_name)
        return sys.modules[module_name]

    def createDownloadPage(
            self, introduction, changelog, base_url, product_name,
            version=None, create_index=True, page_title=None):
        """
        Create a download page for product based on information from `data`.

        * introduction - a text/description for the top of the page.
        * changelog - the whole changelog of this release
          (and previous releases).
        * product_name - Name used to describe the product which is downloaded.
        * base_url - URL without the trailing slash.
        * create_index - When `True` will create the index.html
        """
        from brink.pavement_commons import DIST_EXTENSION

        if not version:
            version = self.setup['product']['version']

        if not page_title:
            page_title = "%s %s Downloads" % (
                product_name,
                version,
                )

        target_folder = self.path.dist

        self.fs.createFolder([target_folder])

        # We create a deep copy of distributables so that when we update the
        # URLs the original copy is not affected.
        resolved_distributables = []

        for name, distributables in self.setup['product']['distributables']:
            all_distributables = [distributables[0].copy()]

            for release in distributables[1:]:
                resolved_release = release.copy()
                all_distributables.append(resolved_release)

                url = resolved_release.get('url', '')
                if url:
                    continue

                resolved_release['url'] = (
                    base_url + '/' +
                    product_name.lower() + '-' +
                    release['platform'] + '-' +
                    version + '.' +
                    DIST_EXTENSION[release['type']]
                    )

            resolved_distributables.append((name, all_distributables))

        data = {
            'introduction': introduction,
            'base_url': base_url,
            'version': version,
            'page_title': page_title,
            'distributables': resolved_distributables,
            }

        website_package = self.setup['website_package']
        website_path = self.importAsString(
            website_package).get_module_path()
        page_name = data['version'] + ".html"
        download_page = [target_folder, page_name]
        self.fs.copyFile(
            source=[website_path, 'placeholders', 'simple.html'],
            destination=download_page,
            )

        print("Creating download page for %s..." % (version,))
        content = self.renderJinja(
            package=website_package,
            folder='jinja',
            template='download_page_content.j2',
            data=data
            )
        changelog_html = self.renderRST(source=changelog)
        content = content.replace(
            'CHANGELOG-CONTENT-PLACEHOLDER', changelog_html)

        rules = [
            ['PAGE-TITLE-PLACEHOLDER', data['page_title']],
            ['PAGE-CONTENT-PLACEHOLDER', content],
            ]
        self.fs.replaceFileContent(target=download_page, rules=rules)

        if create_index:
            index_page = [target_folder, 'index.html']
            self.fs.copyFile(
                source=download_page, destination=index_page)

    def renderRST(self, source):
        """
        Return the HTML rendering for RST.
        """
        from docutils.core import publish_parts

        content = publish_parts(
            source=source, writer_name='html',)['html_body']
        return content

    def renderJinja(self, folder, template, data, package=None):
        """
        Return the string representation of Jinja2 template using data.
        """
        from docutils.core import publish_parts
        from jinja2 import (
            Environment,
            FileSystemLoader,
            Markup,
            PackageLoader,
            )

        if package:
            templates_loader = PackageLoader(package, folder)
        else:
            templates_loader = FileSystemLoader(folder)

        jinja_environment = Environment(loader=templates_loader)

        # Add rst filter.
        def rst_filter(s):
            return Markup(
                publish_parts(source=s, writer_name='html')['html_body'])
        jinja_environment.filters['rst'] = rst_filter

        template = jinja_environment.get_template(template)

        content = template.render(data=data)
        return content

    def getPythonLibPath(self, platform=None, python_version=None):
        """
        Return the path to python library folder relative to build folder.
        """
        if platform is None:
            os_name = self.os_name
        else:
            os_name = platform.split('-')[0]

        if python_version is None:
            python_version = self.python_version

        if os_name == 'win':
            segments = ['lib', 'Lib']
        else:
            segments = ['lib', python_version]

        segments.append('site-packages')
        return self.fs.join(segments)

    def getTicketIDFromBranchName(self, branch_name):
        """
        Extract the ticket id as string from branch name.
        """
        return branch_name.split('-')[0]

    def node(self, command, arguments):
        """
        Execute a command in node-js environment.
        """
        prefix_segments = [self.path.build, 'npm-packages']
        prefix_path = self.fs.join(prefix_segments)

        command_path = self.fs.which(command, extra_paths=[
            prefix_path, self.fs.join([prefix_path, 'bin'])])
        if not command_path:
            print("Could not find node command %s" % (command))
            return 1

        node_command = [command_path]
        node_command.extend(arguments)

        node_modules_path = os.pathsep.join([
            self.fs.join([prefix_path, 'node_modules']),  # Windows
            self.fs.join([prefix_path, 'lib', 'node_modules']),  # Unix
            ])

        extra_environment = {
            'NODE_PATH': node_modules_path,
            }

        (exit_code, output) = self.execute(
            node_command,
            output=sys.stdout,
            extra_environment=extra_environment,
            )
        return exit_code

    def npm(self, command="install", arguments=None):
        """
        Run the npm command.

        Node modules are installed in build/npm-packages.
        """
        prefix_segments = [self.path.build, 'npm-packages']
        cache_segments = [self.path.build, 'npm-cache']
        self.fs.createFolder(prefix_segments)
        self.fs.createFolder(cache_segments)

        if arguments is None:
            arguments = ['--help']

        npm_path = self.fs.which('npm')
        if not npm_path:
            print("npm not found. Are nodejs and npm installed.")
            sys.exit(1)

        npm_command = [npm_path]

        if command == 'install':
            npm_command.extend(['install', '-g'])

        npm_command.extend(arguments)
        npm_command.extend([
            '--cache-min', '999999',
            '--cache-max', '999999',
            '--prefix', self.fs.join(prefix_segments),
            '--cache', self.fs.join(cache_segments),
            ])

        self.execute(npm_command, output=sys.stdout)
