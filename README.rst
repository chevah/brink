brink
=====

Reinventing, paver, distribute and other build system and distribution tools.

There is a package generated for brink, called `chevah-brink`.

paver.sh will check the source code for `pavement.py` and will install the
required chevah-brink version.

paver.sh will also update the chevah-brink package each time `paver deps` is
called.


Development
===========

Each change needs a dedicated ticket and a dedicated branch::

    $ git checkout -b TICKET_ID-short-name

Create a PR and request a review.

Once all the required tests are green and you have a review,
you can merge from GitHub's merge button.

The merge button will tell you if something is not right.


Release Notes
=============

Each change in chevah/brink should be done under a different version number.

Record the version number in `setup.py`.

Every change must be documented under release-notes.rst following the same
format as earlier releases (see the file contents).

Note: The release-notes fragment files are only used on chevah/server, so the
fragments folder was moved to brink/tests/release-notes on this package.

Once a new version is merged, publish it to our package index server.


Paver Script
============

The paver.sh script should be kept in sync with the version from the
chevah/python-package repository.

Changes to paver.sh do not need an update in version as they are not
versioned yet.


Rsync on Windows
================

msys-console.js will download the msys version for the Unix tool, with the
exception or rsync.
rsync is the cygwin version and uses a dedicated ssh-rsync.
It will also not find the config file, so you need to explicitly specify it.

You will need to call it with `rsync -e 'ssh-rsync -F c:\path\to\.ssh\config`

brink.utils.BrinkPaver.rsync loads the SSH configuration file
from `%USERPROFILE%\.ssh\config`.

It will not find the known host file, so on the SSH client config file you
will need to add: `UserKnownHostFiles: c:\path\to\.ssh\known_hosts`.
