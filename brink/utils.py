# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Utility code for Brink.
"""
from __future__ import with_statement

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
from brink.git import BrinkGit
from brink.filesystem import BrinkFilesystem
from brink.paths import ProjectPaths
from brink.sphinx_tools import BrinkSphinx


def _p(path):
    '''
    Shortcut for converting a list to a path using os.path.join.
    '''
    result = os.path.join(*path)
    if os.name == 'posix':
        result = result.encode('utf-8')
    return result


class BrinkPaver(object):
    """
    Collection of methods to help with build system.
    """

    def __init__(self, setup):
        self.setup = setup
        self._default_values = self._getDefaultValues()
        self.os_name = self._default_values['os_name']
        self.cpu = self._default_values['platform']

        self.path = ProjectPaths(
            os_name=self.os_name,
            build_folder_name=self._default_values['build_folder'],
            folders=self.setup['folders'],
            )
        self.git = BrinkGit()
        self.fs = BrinkFilesystem()
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

    def updateRepositories(self, projects, uri):
        print('Updating dependencies from "%s".' % uri)

        for project_name in projects:
            repo_uri = uri + project_name + '.git'

            project_folder = _p([self.path.project, project_name])
            # Do the initial clone if the repo does not exists.
            if not os.path.exists(project_folder):
                with self.fs.changeFolder([self.path.project]):
                    self.git.clone(
                        repo_uri=repo_uri, project_name=project_name)
            else:
                with self.fs.changeFolder([project_folder]):
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
                '-r', _p([self.path.brink_package, 'static', 'requirements',
                            'requirements-runtime.txt']),
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
                '-r', _p([self.path.brink_package, 'static', 'requirements',
                            'requirements-buildtime.txt']),
                ],
            )

    def uninstallBuildDependencies(self):
        """
        Unintall the required packages to build environment.
        """
        self.pip(
            command='uninstall',
            arguments=[
                '-r', _p([self.path.brink_package, 'static', 'requirements',
                            'requirements-buildtime.txt']),
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
                builder = args[index + 1]
                break
            if arg.startswith('--builder='):
                builder = arg[10:]

        base_url = (
            self.setup['buildbot']['web_url'] +
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

        target = _p([self.path.dist, folder_name])
        target_nsis_path = _p([target, 'windows-installer.nsi'])
        template_nsis_path = _p([
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

        make_nsis_command = ['makensis', 'windows-installer.nsi']

        try:
            with self.fs.changeFolder([target]):
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
                    self.setup['folders']['source'],
                    self.setup['folders']['static'],
                    self.setup['folders']['configuration'],
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

    def createDownloadPage(self,
            introduction, changelog, base_name, create_index=True):
        """
        Create a download page for product based on information from `data`.
        """
        from brink.pavement_commons import DIST_EXTENSION

        target_folder = self.path.dist

        self.fs.createFolder([target_folder])

        # Set download site.
        if self.git.branch_name == 'production':
            download_hostname = (
                self.setup['publish']['download_production_hostname'])
        else:
            download_hostname = (
                self.setup['publish']['download_staging_hostname'])
        base_url = "http://%s/%s/%s/%s" % (
            download_hostname,
            self.setup['product']['name'].lower(),
            self.setup['product']['version_major'],
            self.setup['product']['version_minor'],
            )
        data = {
            'introduction': introduction,
            'changelog': changelog,
            'base_url': base_url,
            'version': self.setup['product']['version'],
            'extensions': DIST_EXTENSION,
            'base_name': base_name,
            'page_title': "%s %s Download" % (
                self.setup['product']['name'],
                self.setup['product']['version'],
                ),
            'distributables': self.setup['product']['distributables'],
        }

        website_package = self.setup['website_package']
        website_path = self.importAsString(
            website_package).get_module_path()
        page_name = 'release-' + data['version'] + ".html"
        download_page = [target_folder, page_name]
        self.fs.copyFile(
            source=[website_path, 'templates', 'one_column.html'],
            destination=download_page,
            )

        print "Creating download page..."
        content = self.renderJinja(
            package=website_package,
            folder='jinja2',
            template='download_product.j2',
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

    def pocketLint(self,
            folders=None, excluded_folders=None,
            files=None, excluded_files=None,
            ):
        """
        Run pocketlint on `folders` and `files`.

        Files from `excluded_folders` and `excluded_files` list will be
        ignored.

        `excluded_folders` and `excluded` files contains regular expression
        which will match full folder names or file names.
        """
        from pocketlint.formatcheck import (
            check_sources,
            JavascriptChecker,
            JS,
            )
        from pocketlint.contrib import cssccc
        import pocketlint
        import mimetypes

        # These types are not recognized by Windows.
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

        class PocketLintOptions(object):
            """
            Holds the options used by pocket lint for chevah project.
            """
            def __init__(self):
                self.max_line_length = 79

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

        if self.os_name is 'ubuntu' and JS is None:
            print 'Install "seed" or "gjs" to enable JS linting on Ubuntu.'
            sys.exit(1)

        sources = []
        for folder in folders:
            for root, member_folders, member_files in os.walk(folder):
                if is_excepted_folder(root):
                    continue
                for file_name in member_files:
                    if not is_excepted_file(file_name):
                        sources.append(os.path.join(root, file_name))

        for file_name in files:
            sources.append(file_name)

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

    def getPythonLibPath(self, platform=None, python_version=None):
        """
        Return the path to python library folder relative to build folder.
        """
        if platform is None:
            os_name = self.os_name
        else:
            os_name = platform.split('-')[0]

        if python_version is None:
            python_version = self.setup['python']['version']

        if os_name == 'windows':
            segments = ['lib', 'Lib']
        else:
            segments = ['lib', 'python' + python_version]

        segments.append('site-packages')
        return _p(segments)
