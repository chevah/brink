# Copyright (c) 2012 Adi Roiban.
# See LICENSE for details.
"""
Tests for Brink build system.
"""
from __future__ import (
    absolute_import,
    print_function,
    with_statement,
    unicode_literals,
    )
from chevah.compat.testing import mk


def setup_package():
    """
    Called before running all tests.
    """
    # Prepare the main testing filesystem.
    mk.fs.setUpTemporaryFolder()


def teardown_package():
    """
    Called after all tests were run.
    """
    # Remove main testing folder.
    mk.fs.tearDownTemporaryFolder()
    mk.fs.checkCleanTemporaryFolders()
