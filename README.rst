brink
=====

Reinventing, paver, distribute and other build system and distribution tools.

For now paver, distribute and pip are stored inside the repo. Hope we can
find a way to distribute them in another way.

There is a Python package generated for brink, called `chevah-brink`.

paver.sh will check the source code for `pavement.py` and will install the
required chevah-brink version.

paver.sh will also update the chevah-brink package each time `paver deps` is
called.
