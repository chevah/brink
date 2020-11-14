# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
from optparse import make_option
import sys

from paver.easy import cmdopts, needs, task
from paver.tasks import BuildFailure


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
            source = [self.paver.path.build, 'doc_source']

        if target is None:
            target = [self.paver.path.build, 'doc']

        sphinx_command.extend([
            '-d', self.fs.join([self.paver.path.build, 'doc_build'])])

        sphinx_command.extend([
            '-b', 'html', self.fs.join(source), self.fs.join(target)])

        sys_argv = sys.argv
        try:
            sys.argv = sphinx_command
            return sphinx_main(sys.argv)
        finally:
            sys.argv = sys_argv

    def apidoc(self, module, destination):
        from chevah.commons.utils.apidoc import main as apidoc_main
        self.paver.fs.createFolder(destination=destination, recursive=True)
        sys.argv = [
            'apidoc', '--maxdepth=4', '-f',
            '-o', self.fs.join(destination), module]
        apidoc_main(sys.argv)

    def createConfiguration(
            self, destination, project, version, themes_path,
            theme_name='standalone', intersphinx_mapping=None,
            copyright='Chevah Team', extra_configuration=''
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
    ]
suppress_warnings = ['toc.secnum']
source_suffix = '.rst'
# Ignore included files in root and in child folders from being reported
# as not part of the toctree.
exclude_patterns = ['**.include.rst', '**/*.include.rst']
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

pdf_documents = [(
    'index',
    u'%(project)s-%(version)s',
    u'%(project)s Documentation',
    u'%(copyright)s',
    )]
pdf_stylesheets = ['sphinx', 'kerning', 'a4']
pdf_use_toc = False
pdf_toc_depth = 2

%(extra_configuration)s
""" % (  # Indentation here is strange, since we use multi-line string.
            {
                'theme_name': theme_name,
                'project': project,
                'version': version,
                'intersphinx_mapping': intersphinx_mapping,
                'copyright': copyright,
                'themes_path': themes_path,
                'extra_configuration': extra_configuration,
                }
            )

        with open(self.fs.join(destination), 'w') as conf_file:
            conf_file.write(content)

    def generateProjectDocumentation(
        self, arguments=None, theme='standalone',
        extra_configuration='',
            ):
        """
        Generate project documentation and return exit code.
        """
        if arguments is None:
            arguments = []

        product_name = self.paver.setup['product']['name']
        version = self.paver.setup['product']['version']

        website_path = self.paver.importAsString(
            self.paver.setup['website_package']).get_module_path()

        self.createConfiguration(
            destination=[self.paver.path.build, 'doc_source', 'conf.py'],
            project=product_name,
            version=version,
            copyright=self.paver.setup['product']['copyright_holder'],
            themes_path=self.paver.fs.join([website_path, 'sphinx']),
            theme_name=theme,
            extra_configuration=extra_configuration,
            )

        destination = [self.paver.path.build, 'doc', 'html']
        exit_code = self.createHTML(
            arguments=arguments,
            source=[self.paver.path.build, 'doc_source'],
            target=destination,
            )

        print("Documentation files generated in %s" % (
            self.paver.fs.join(destination)))
        print("Exit with %d." % (exit_code))
        return exit_code


@task
@cmdopts([
    make_option(
        "-c", "--check",
        help="Check all pages.",
        default=False,
        action="store_true"
        ),
    ('all', None, 'Create all files.'),
    ('theme', None, 'Theme of the generated pages.'),
    ])
@needs('build', 'update_setup')
def doc_html(options):
    """
    Generates the documentation.
    """
    # Avoid recursive import.
    from brink.pavement_commons import pave

    arguments = []
    if pave.getOption(options, 'doc_html', 'all'):
        arguments.extend(['-a', '-E', '-n'])
    theme = pave.getOption(options, 'doc_html', 'theme', 'standalone')

    return pave.sphinx.generateProjectDocumentation(
        arguments, theme=theme)


@task
@needs('build', 'update_setup')
def test_documentation():
    """
    Generates the documentation in testing mode.

    Any warning are treated as errors.
    """
    # Avoid recursive import.
    from brink.pavement_commons import pave

    exit_code = pave.sphinx.generateProjectDocumentation(
        ['-a', '-E', '-W', '-N', '-n'])
    if exit_code:
        raise BuildFailure('Documentation test failed.')
