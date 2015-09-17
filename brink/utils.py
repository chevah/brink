# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Utility code for Brink.
"""
from __future__ import absolute_import, with_statement

from contextlib import closing
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import md5
import os
import re
import socket
import subprocess
import sys
import urllib2

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
            index_url = self.setup['pypi']['index_url']

        if arguments is None:
            arguments = []

        pip_arguments = [command]

        if command == 'install':
            if only_cache:
                pip_arguments.extend(['--no-index'])
            else:
                pip_arguments.extend(
                    ['--index-url=' + index_url])

            if install_hook:
                pip_arguments.extend([
                    '--install-hook=%s' % (install_hook)])

            pip_arguments.extend(
                ['--download-cache=' + self.path.cache])

            pip_arguments.extend(
                ['--build=' + self.fs.join(pip_build_path)])

            pip_arguments.extend(
                ['--find-links=file://' + self.path.cache])

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
        try:
            import simplejson as json
            json  # Shut the linter.
        except ImportError:
            import json

        result = json.load(self.openPage(url))
        return result

    def buildbotShowLastStep(self, builder):
        """
        Show logs for last step from last build for builder.
        """
        base_url = (
            self.setup['buildbot']['web_url'] +
            '/json/builders/' +
            builder)
        result = self.getJSON(url=base_url)
        last_build = str(result['cachedBuilds'][-1])

        result = self.getJSON(url=base_url + '/builds/' + last_build)
        for line in self.openPage(result['logs'][-1][1] + '/text'):
            print line,

    def buildbotShowProgress(self, builder):
        """
        Show interactive progess of builder activity.
        """
        # Wait a bit for the new build to start.
        import time
        time.sleep(2)

        # How to data to read and print from status stream.
        CHUNK = 2 * 1024

        base_url = (
            self.setup['buildbot']['web_url'] +
            '/json/builders/' +
            builder)
        builder_status = self.getJSON(url=base_url)
        if builder_status['currentBuilds']:
            last_build = str(builder_status['currentBuilds'][0])
        else:
            # This build was was... no progress to list so we get
            # the last build status.
            self.buildbotShowLastStep(builder)
            return

        while builder_status['state'] == 'building':
            last_step = self.getJSON(url=base_url + '/builds/' + last_build)
            last_step_url = last_step['logs'][-1][1] + '/text'

            req = urllib2.urlopen(last_step_url)
            while True:
                chunk = req.read(CHUNK)
                if not chunk:
                    break
                print chunk,

            # Wait a bit for next step to start
            time.sleep(0.1)
            builder_status = self.getJSON(url=base_url)

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
                print 'It is required to provide option "%s".' % (option_name)
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
                    foldername = root + '/'
                    zip_info = ZipInfo(foldername)
                    zip_info.external_attr = 16
                    z.writestr(zip_info, "")

    def createMD5Sum(self, source):
        '''
        Returns an MD5 hash for the file specified by file_path.
        '''
        md5hash = md5.new()

        with open(self.fs.join(source), 'rb') as input_file:
            while True:
                read_buffer = input_file.read(8096)
                if not read_buffer:
                    break
                md5hash.update(read_buffer)

            result = md5hash.hexdigest()

        return result

    def createNSIS(
            self, folder_name, product_name, product_version,
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
            print (
                'NullSoft Installer is not installed. '
                'On Ubuntu you can install it using '
                '"sudo apt-get install nsis".'
                )
            sys.exit(1)

        make_nsis_command = [make_nsis_path, '-V2', 'windows-installer.nsi']

        try:
            with self.fs.changeFolder([target]):
                print "Executing %s" % make_nsis_command
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
            print "Failed to convert some bat files."
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
            print "Failed to convert some configuration files."
            sys.exit(1)

    def _convertToDOSNewlines(self, file_path):
        """
        Convert the file to DOS newlines.
        """
        file_path = self.fs.getEncodedPath(file_path)
        tmp_file_path = file_path + '.tmp'
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
        command = ['rsync', '-acz', '-e', "'ssh'"]
        if verbose:
            command.append('-v')
        command.append(self.fs.join(source))
        command.append(destination_uri)
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

    def createDownloadPage(
            self, introduction, changelog, base_name, hostname,
            create_index=True, product_name=None, page_title=None):
        """
        Create a download page for product based on information from `data`.

        * introduction - a text/description for the top of the page.
        * changelog - the whole changelog of this release
          (and previous releases).
        * base_name - Name used to construct the URL path to the download file.
        * product_name - Name used to describe the product which is downloaded.
        * hostname - FQDN for the host where the files are stored.
        * create_index - When `True` will create the index.html
        """
        from brink.pavement_commons import DIST_EXTENSION

        if not product_name:
            product_name = base_name

        if not page_title:
            page_title = "%s %s Downloads" % (
                product_name,
                self.setup['product']['version'],
                )

        target_folder = self.path.dist

        self.fs.createFolder([target_folder])

        base_url = "http://%s/%s/%s/%s" % (
            hostname,
            base_name.lower(),
            self.setup['product']['version_major'],
            self.setup['product']['version_minor'],
            )
        data = {
            'introduction': introduction,
            'changelog': changelog,
            'base_url': base_url,
            'version': self.setup['product']['version'],
            'extensions': DIST_EXTENSION,
            'base_name': product_name.replace(' ', '-').lower(),
            'page_title': page_title,
            'distributables': self.setup['product']['distributables'],
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

        print "Creating download page..."
        content = self.renderJinja(
            package=website_package,
            folder='jinja',
            template='download_page_content.j2',
            data=data
            )
        changelog_html = self.renderRST(source=data['changelog'])
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

    def pocketLint(
            self,
            folders=None, excluded_folders=None,
            files=None, excluded_files=None,
            quick=False, dry=False,
            branch_name=None,
            ):
        """
        Run pocketlint on `folders` and `files`.

        Files from `excluded_folders` and `excluded_files` list will be
        ignored.

        `excluded_folders` and `excluded` files contains regular expression
        which will match full folder names or file names.
        """
        from pocketlint.formatcheck import check_sources, PocketLintOptions
        from pocketlint.contrib import cssccc
        import mimetypes

        # These types are not recognized by various OS.
        mimetypes.add_type('text/plain', '.bat')
        mimetypes.add_type('application/json', '.json')
        mimetypes.add_type('image/x-icon', '.ico')

        if files is None:
            files = []

        if folders is None:
            folders = []

        if excluded_files is None:
            excluded_files = []

        if excluded_folders is None:
            excluded_folders = []

        regex_files = [
            re.compile(expression) for expression in excluded_files]
        regex_folders = [
            re.compile(expression) for expression in excluded_folders]

        def is_excepted_folder(folder_name):
            for expresion in regex_folders:
                if expresion.match(folder_name):
                    return True
            return False

        def is_excepted_file(file_name):
            for expresion in regex_files:
                if expresion.match(file_name):
                    return True
            return False

        if quick:
            changes = self.git.diffFileNames()

            quick_files = []
            for change in changes:
                # Filter deleted changes since we can not lint then.
                if change[0] == 'd':
                    continue

                # Add files which are explicitly requested.
                if change[1] in files:
                    quick_files.append(change[1])
                    continue

                # Filter files in excluded folders.
                folder_name = os.path.dirname(change[1])
                if is_excepted_folder(folder_name):
                    continue

                # Filter files is in excluded files.
                file_name = os.path.basename(change[1])
                if is_excepted_file(file_name):
                    continue

                # Filter files outside of requested folders.
                excluded_file = True
                for folder in folders:
                    if change[1].startswith(folder):
                        excluded_file = False

                if not excluded_file:
                    quick_files.append(change[1])
                    continue

            # We only lint specific files in quick mode.
            files = quick_files
            folders = []

        if dry:
            print "\n---\nFiles\n---"
            for name in files:
                print name
            print "\n---\nFolders\n---"
            for name in folders:
                print name
            print "\n---\nExcluded files\n---"
            for name in excluded_files:
                print name
            print "\n---\nExcluded folders\n---"
            for name in excluded_folders:
                print name
            return 0

        sources = []
        for folder in folders:
            for root, member_folders, member_files in os.walk(folder):
                if is_excepted_folder(root):
                    continue
                for file_name in member_files:
                    if not is_excepted_file(file_name):
                        sources.append(self.fs.join([root, file_name]))

        for file_name in files:
            sources.append(file_name)

        count = -1
        initial_ignore = cssccc.IGNORED_MESSAGES
        options = PocketLintOptions()
        options.max_line_length = 80
        options.jslint['enabled'] = False
        options.closure_linter['enabled'] = True
        options.closure_linter['ignore'] = [1, 10, 11, 110, 220]

        ticket = branch_name.split('-', 1)[0]

        # Strings are broken to not match the own rules.
        options.regex_line = [
            ('FIX' + 'ME:%s:' % (ticket), 'FIX' + 'ME for current branch.'),
            ('(?i)FIX' + 'ME$', 'FIXME:123: is the required format.'),
            ('(?i)FIX' + 'ME:$', 'FIXME:123: is the required format.'),
            ('FIX' + 'ME[^:]', 'FIXME:123: is the required format.'),
            ('(?i)FIX' + 'ME:[^0-9]', 'FIXME:123: is the required format.'),
            ('(?i)FIX' + 'ME:[0-9]+[^:]$',
                'FIXME:123: is the required format.'),
            ('(?i)TO' + 'DO ', 'No TO' + 'DO markers are allowed.'),
            ('(?i)TO' + 'DO$', 'No TO' + 'DO markers are allowed.'),
            ('\[#' + '%s\] ' % (ticket), 'Branch should fix this issue.'),
            ]
        options.pep8['hang_closing'] = True

        try:
            cssccc.IGNORED_MESSAGES = ['I005', 'I006']
            count = check_sources(sources, options=options)
        finally:
            cssccc.IGNORED_MESSAGES = initial_ignore

        return count

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

        if os_name == 'windows':
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

    def getBinaryDistributionFolder(self, target, platform=None):
        """
        Return segments for binary distribution folder.

        It download binary distribution if it does not exists.
        """
        if platform is None:
            platform = "%s-%s" % (self.os_name, self.cpu)

        distribution = "%s-%s" % (target, platform)
        distribution_segments = ['cache', distribution]

        if self.fs.isFolder(distribution_segments):
            return distribution_segments

        if os.name == 'posix':
            command = []
        else:
            command = ['C:\\MinGW\\msys\\1.0\\bin\\sh.exe']
        command.extend(['./paver.sh'])

        if target == 'agent-1.5':
            command.append('get_agent')
        else:
            command.append('get_python')

        command.append(distribution)

        (exit_code, output) = self.execute(command, output=sys.stdout)

        return distribution_segments

    def node(self, command, arguments):
        """
        Execute a command in node-js environment.
        """
        prefix_segments = [self.path.build, 'npm-packages']
        prefix_path = self.fs.join(prefix_segments)

        command_path = self.fs.which(command, extra_paths=[
            prefix_path, self.fs.join([prefix_path, 'bin'])])
        if not command_path:
            print "Could not find node command %s" % (command)
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
            print "npm not found. Are nodejs and npm installed."
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
