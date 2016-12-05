brink
=====

Reinventing, paver, distribute and other build system and distribution tools.

There is a package generated for brink, called `chevah-brink`.

paver.sh will check the source code for `pavement.py` and will install the
required chevah-brink version.

paver.sh will also update the chevah-brink package each time `paver deps` is
called.


TODO
====

* Update python, pip and setuptool. Right now we need to clean the build
  folder to update python pip or setuptools.
* Add support to install binary packages.


Development
===========

Each change needs a dedicated ticket and a dedicated branch::

    $ git checkout -b TICKET_ID-short-name


Release Notes
=============

Each change in chevah/brink should be done under a different version number.

Record the version number in `setup.py`.

Every change must be documented under release-notes.rst following the same
format as earlier releases (see the file contents).

Note: The release-notes fragment files are only used on chevah/server, so the
fragments folder was moved to test/release-notes on this package.
