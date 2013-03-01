#
# Configuration of a brink project.
#
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
        'base_uri': 'http://172.20.0.11/git/',
        'push_uri': 'git@git.chevah.com:'
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
        'exclude_files': [],
        'exclude_folders': [],
        'include_files': ['pavement.py'],
        'include_folders': [],
    },
    'website_package': 'chevah.website',
    'test': {
        'package': 'chevah.product.tests',
        # Module inside the test-package where elevated test are located.
        'elevated': None,
    },
    'github': {
        'base_url': 'https://github.com',
        'repo': 'chevah',
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
