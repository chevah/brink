brink
=====

.. image:: https://github.com/chevah/brink/workflows/GitHub-CI/badge.svg
  :target: https://github.com/chevah/brink/actions


Reinventing paver, distribute and other build system and distribution tools.

There is a package generated for brink, called `chevah-brink`.

paver.sh will check the source code for `pavement.py` and will install the
required chevah-brink version.

paver.sh will also update the chevah-brink package each time `paver deps` is
called.

It will read the private configuration from ~/.config/chevah-brink.ini.

This repo is also used as a testing ground for the general build system for the
Chevah project.


Development
===========

Each change needs a dedicated branch::

    $ git checkout -b short-name

Create a PR and request a review.

Once all the required tests are green and you have a review,
you can merge from GitHub's merge button.

The merge button will tell you if something is not right.


Configuration file
==================

Configuration file used by commands in this repo should be saved as
`~/.config/chevah-brink.ini` with the following format::

    [actions]
    token = GITHUB_PERSONAL_TOKEN

    [buildbot]
    server = YOUR.BUILDMASTER.ADDRESS
    port = YOUR_BUILDMASTER_PORT
    web_url = YOUR_BUILDMASTER_HTTP_STATUS_URL
    username = BUILDMASTER_TRY_USERNAME
    password = BUILDMASTER_TRY_PASSWORD


GitHub Token Permissions
========================

Part of the brink script will interact with GitHub and will need special
permissions.

Get a new token from https://github.com/settings/tokens/new.

Permissions required for each part:

* `actions-try`: repo (all)


Release Process
===============

Each change in chevah/brink should be done under a different version number.

Record the version number in `setup.py`.

Every change must be documented under release-notes.rst following the same
format as earlier releases (see the file contents).

Note: The release-notes fragment files are only used on chevah/server, so the
fragments folder was moved to brink/tests/release-notes on this package.

Once a new version is merged, publish it to our package index server::

    ./build-brink/bin/python setup.py bdist_wheel upload -r chevah


Brink Script
============

The brink.sh script should be kept in sync with the version from the
chevah/python-package repository.

Changes to brink.sh do not need an update in version as they are not
versioned.
