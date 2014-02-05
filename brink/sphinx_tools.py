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
            source = [self.paver.path.build, 'doc']

        if target is None:
            target = [self.paver.path.build, 'doc_build']

        sphinx_command.extend([
            '-b', 'html', self.fs.join(source), self.fs.join(target)])

        sys_argv = sys.argv
        try:
            sys.argv = sphinx_command
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

    def createConfiguration(
            self, destination, project, version, themes_path,
            theme_name='standalone', intersphinx_mapping=None,
            copyright='Chevah Team', experimental=True,
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
    'repoze.sphinx.autointerface',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
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
experimental = %(experimental)s

from docutils.parsers.rst import Directive
from sphinx import addnodes
from sphinx.util.nodes import set_source_info

class Only(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):

        if not tags.has(self.arguments[0]):
            return []

        node = addnodes.only()
        node.document = self.state.document
        set_source_info(self, node)
        node['expr'] = self.arguments[0]

        # Same as util.nested_parse_with_titles but try to handle nested
        # sections which should be raised higher up the doctree.
        surrounding_title_styles = self.state.memo.title_styles
        surrounding_section_level = self.state.memo.section_level
        self.state.memo.title_styles = []
        self.state.memo.section_level = 0
        try:
            result = self.state.nested_parse(
                self.content,
                self.content_offset,
                node,
                match_titles=1,
                )
            title_styles = self.state.memo.title_styles
            if (not surrounding_title_styles
                or not title_styles
                or title_styles[0] not in surrounding_title_styles
                or not self.state.parent):
                # No nested sections so no special handling needed.
                return [node]
            # Calculate the depths of the current and nested sections.
            current_depth = 0
            parent = self.state.parent
            while parent:
                current_depth += 1
                parent = parent.parent
            current_depth -= 2
            title_style = title_styles[0]
            nested_depth = len(surrounding_title_styles)
            if title_style in surrounding_title_styles:
                nested_depth = surrounding_title_styles.index(title_style)
            # Use these depths to determine where the nested sections should
            # be placed in the doctree.
            n_sects_to_raise = current_depth - nested_depth + 1
            parent = self.state.parent
            for i in xrange(n_sects_to_raise):
                if parent.parent:
                    parent = parent.parent

            # Insert child of only.
            new_node = node.children[0]
            new_node.parent = parent
            parent.append(new_node)

            return []
        finally:
            self.state.memo.title_styles = surrounding_title_styles
            self.state.memo.section_level = surrounding_section_level

def setup(app):
    if experimental:
        tags.add('experimental')
    else:
        tags.add('production')
    app.add_directive('conditional', Only)

""" % (  # Indentation here is strange, since we use multi-line string.
            {
                'theme_name': theme_name,
                'project': project,
                'version': version,
                'intersphinx_mapping': intersphinx_mapping,
                'copyright': copyright,
                'themes_path': themes_path,
                'experimental': experimental,
                }
            )

        with open(self.fs.join(destination), 'w') as conf_file:
            conf_file.write(content)
