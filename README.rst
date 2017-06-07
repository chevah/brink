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

Run `./paver.sh test_review` to trigger the tests required before merge.

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


Paver Script
============

The paver.sh script we use is taken from chevah/python-package repository.

If modifications to paver.sh file are required, they should be done on a
branch on that repository.
