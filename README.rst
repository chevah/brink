brink
=====

Reinventing, paver, distribute and other build system and distribution tools.

There is a package generated for brink, called `chevah-brink`.

paver.sh will check the source code for `pavement.py` and will install the
required chevah-brink version.

paver.sh will also update the chevah-brink package each time `paver deps` is
called.


TODO
----

* Update python, pip and setuptool. Right now we need to clean the build
  folder to update python pip or setuptools.
* Add support to install binary packages.
