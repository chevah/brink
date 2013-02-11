# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import with_statement
import sys


class BrinkSphinx(object):
    '''
    Collection of Python Sphinx operations.
    '''

    def __init__(self, paver):
        # This is here for filesystem access.
        # For the future, we should only pass paths and each path is a
        # filesystem.
        self.paver = paver
        self.fs = paver.fs

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

        sphinx_command.extend([
            '-b', 'html', self.fs.join(source), self.fs.join(target)])

        sys_argv = sys.argv
        try:
            sys.argv = sphinx_command
            with self.paver.fs.changeFolder([self.paver.path.build]):
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
        self.paver.fs.createFolder(destination=destination, recursive=True)
        sys.argv = [
            'apidoc', '--maxdepth=4', '-f',
            '-o', self.fs.join(destination), module]
        apidoc_main(sys.argv)

    def createConfiguration(self, destination, project, version, themes_path,
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

        with open(self.fs.join(destination), 'w') as conf_file:
            conf_file.write(content)
