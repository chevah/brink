"""
Configuration of a brink project.

This is the basic public configuration.
Private data is loaded from ~/.config/chevah-brink.ini
"""

SETUP = {
    'product': {
        'name': 'ChevahProduct',
        'version': '0.0.1',
        'version_major': '0',
        'version_minor': '0',
        'copyright_holder': 'Chevah Project',
        'distributables': {}
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
        'github': 'NO GitHub URI defined',
        },
    'buildbot': {
        'vcs': 'git',
        'builders_filter': None,
        },
    'actions': {
        'token': '',
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
    'scame': {
        'scope': {
            'include': [],
            'exclude': [],
            },
        'towncrier': {
            'fragments_directory': '',
            'excluded_fragments': ['readme', 'readme.rst'],
            },
        },
    'website_package': 'chevah.website',
    'test': {
        'package': 'chevah.product.tests',
        # Module inside the test-package where elevated test are located.
        'elevated': None,
        # List of nose arguments passed to all tests.
        'nose_options': [],
        # URL for publishing the coverage reports to coverator.
        'coverator_url': ''
        },
    }

DIST_TYPE = {
    'ZIP': 0,
    'NSIS': 1,
    'TAR_GZ': 2,
    'NSIS_RENAMED': 3,
    'TAR_GZ_LINK': 4,
    }

DIST_EXTENSION = {
    DIST_TYPE['ZIP']: 'zip',
    DIST_TYPE['NSIS']: 'exe',
    DIST_TYPE['TAR_GZ']: 'tar.gz',
    DIST_TYPE['TAR_GZ_LINK']: 'tar.gz',
    DIST_TYPE['NSIS_RENAMED']: 'rename_to_exe',
    }
