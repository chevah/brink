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


Development process
===================

Each change needs a dedicated ticket and a dedicated branch::

    $ git checkout -b TICKET_ID-short-name

After code is committed and branch is published run the test for review::

    $ git push --set-upstream origin TICKET-short-name
    $ ./paver.sh test_review

Each branch should have a release note fragment, which is a simple text file
located in 'release-notes' folder and named based on TICKET_ID.CATEGORY.

Supported categories are:

* .feature - for new features visible to end users
* .bugfix - for bug /  defect fixes
* .removal - for removing / deprecating things
* .ignore - for branch which doesn't affect the end users

Release note fragment files can contain multiple lines.
The lines are concatenated and wrapped when the final notes are generated.


Create a review request using::

    $ ./paver.sh github new

If changes are required after review, change code, commit and re-rerun
review tests (will push changes for you)::

    $ ./paver.sh test_review

After code was approved, request the branch to merge::

    $ ./paver.sh pqm PULL_REQUEST_ID

`master` branch is a protected branch on GitHub. Only repo administrators
and the buildmaster is allowed to push changes to master.
