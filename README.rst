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


Static code analysis
====================

The project make use of various static code analysis tools via pocket-lint.

To check the files changes since `master`, use::

    $ ./paver.sh lint

To check all files, use::

    $ ./paver.sh lint --all


Testing
=======


Python Testing
--------------

'Nose' is used as a testrunner. More info about python-nose here:
http://somethingaboutorange.com/mrl/projects/nose/0.11.3/usage.html

To run the tests::

    $ ./paver.sh test 'nose args'

To get the testrunner help::

    $ ./paver.sh test --help

You can call a test in the following way::

    $ ./paver.sh test chevah.server.tests.package.test_module

You can also use the shorthand form and `./paver.sh` will prepend
the test package::

    $ ./paver.sh test package.test_module

In the unfortunate case in which you will need to repeat a test until it
fails use::

    $ paver test_loop 12 TEST-ARGUMENTS

To test the server part as a system service (Unix and Windows) we have a
set of 'elevated' tests which will create OS accounts to run test against.
On Unix, this means running test using `sudo`.


Skipping elevated and functional tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run only the unit and system tests, skipping elevated and functional
tests altogether.

For this, use the following command::

    $ ./paver.sh test normal


Skipping slow tests
^^^^^^^^^^^^^^^^^^^

During development you might want to run the tests in the shortest amount of
time possible.

You can run only the tests that are not known to be slow by issuing the
following command::

    $ ./paver.sh test --attr="!slow"

The attribute can be applied to any target. For instance if you want to
execute only unit and system tests but skip the slow ones you will type the
following::

    $ ./paver.sh test normal --attr='!slow'

There is also a helper to run all `fast` tests. It will run about 80% of the
tests::

    $ ./paver.sh test_quick


Testing using the build slaves
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also run tests against a number of pre-configured systems:
Windows 2003/2008, Linux 32/64 bit, AIX, etc.

To obtain an up-to-date list of existing buildbots run the following command::

    $ ./paver.sh test_remote

You should specify the builder name to run all tests::

    $ ./paver.sh test_remote ubuntu-1204-32 --wait

This will create a patch for local changes and apply the patch on remote
machine before running the tests.
You don't need to commit your changes.
If you add or remove files, make sure to add them to the git staging area.

Just as when running tests on the local machine you can specify a particular
test, an entire test case, or a package. The same syntax applies::

    $ ./paver.sh test_remote linux-x64 normal.commons.test_configuration --wait
    $ ./paver.sh test_remote linux-x64 normal.location --wait


Using a python binary dist from testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a new Python binary distribution is available, before moving it in
production, you can run a test with the version located in the testing area.

In paver.conf change::

    BINARY_DIST_URI='http://binary.chevah.com/testing'

Then run tests on slave by forcing a cleanup.

Either by using raw `buildbot --properties`::

    $ ./paver.sh test_remote rhel-6 --properties=purge_clean=yes

Or by using our sugar wrapper::

    $ ./paver.sh test_remote group-all --force-purge

You don't need to commit the changes form paver.conf as test_remote will
send the diff.


Memory leaks testing
^^^^^^^^^^^^^^^^^^^^

While running test code or production code object references might be left
behind either to circular references or being kept as references to a class.

Checking for memory leaks is a **slow** process and it needs to be explicitly
enabled using the `CHEVAH_GC` environment variable.

A set of tests are targeted for leaks::

    $ CHEVAH_GC=1 ./paver.sh test_leaks

Any test can be run with memory leaks check. For example to run all quick
tests do::

    $ CHEVAH_GC=1 ./paver.sh test normal.transfer.test_job
    $ CHEVAH_GC=1 ./paver.sh test_quick

There is also a builder::

    $ ./paver.sh test_remote leaks


UI/JavaScript/Web Testing
-------------------------

Our UI is implemented in HTML/CSS/JavaScript... the dynamic trio.

We have both JS unit testing and general functional testing for the
web applications.

All web/js/html/CSS tests are driven by Python Selenium and we have a helper
to auto-generate tests for each supported browser.


Unit Testing
^^^^^^^^^^^^

Launch automated JS unit test using::

    $ ./paver.sh test selenium.test_unit

You can filter to run tests only on a specific browser::

    $ ./paver.sh test selenium.test_unit --attr=browser_chrome

You can run a specific test case, but for now there is no option to
filter a single test or a set of tests.::

    $ ./paver.sh test selenium.test_unit:TestJSCommonsChrome

You can filter tests from debugger. Run test case with --pdb::

    $ ./paver.sh test selenium.test_unit:TestJSCommonsChrome --pdb

the browser window will stay open after all tests are run. In the browser
windows you can remove the `?reporter=selenium` marker and load the page.
In the new runner, you can click on a suite or test to filter only that one.


Functional Testing
^^^^^^^^^^^^^^^^^^

We are using Selenium with Python binding for functional testing of
HTML/CSS/JS.

You need to install Firefox and Chrome.

On Windows, only the 32bit Internet Explorer version is used.

To run the functional tests, use::

    $ ./paver.sh test selenium

To run only tests for a specific browser, use::

    $ ./paver.sh test selenium.test_login --attr=browser_firefox

For IE testing you will need to enable "Protected mode" for **all** zone from
Internet Options -> Security.


Debugging JavaScript in browsers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With modern web browsers, you can insert ``debugger`` line in your JS
code and the browser will stop at that breakpoint. Make sure the browser is
running with active development tools.

To run only tests for a specific browser, use::

    $ ./paver.sh test selenium.test_unit --attr=browser_firefox --pdb

When tests fail, it will stop before exit leaving the browser windows active.
By default, the `selenium` minimal JS unit test reporter is used. Remove
the arguments from the URL, open the dev tools and load the page again.
It should not be stopped at the `debugger` breakpoint.


Hunting memory / circular references
------------------------------------

The leaks assertion will give you a list with class **names** which were
still present after test.
For example it can say::

    [('FileConfigurationProxy', 2, 1), ('OrderedDict', 13, 7),
    ('weakproxy', 2, 1)]

You will need to import that class, get all objects from that class

        objs = self._getObjectsByTypeName('LogHandlersConfiguration')
        # Pick one object and see what links to it.
        refs = gc.get_referrers(objs[1])
        refs[-1]

When you see that `Method, Attribute, InterfaceClass` are leaks, this most
probably mean that an import is done inside the test.
For other types, check what objects refer to them and try to see why the
memory was not release.
Under exceptional conditions, you can manually force freeing that object
by setting its reference to `None`. When you do that, leave a comment.


Test user
=========

The default test configuration together with the execution of './paver.sh run'
command will create a set of account to help with manual testing::

    username: user
    password: pass
    ssh key : test-ssh-rsa-1024 / test-ssh-dsa-1024
    home    : BUILD_FOLDER/users_files/test_user

    username: ssl_user
    password: password
    home    : /tmp  # Only Unix for SSL password-less authentication.


Testing CA, PKI, X.509 certificates
===================================

The testing CAs are managed using XCA http://xca.sourceforge.net/

Launch it using::

    xca -d test_data/pki/xca-chevah.xdb

The password for the db is `chevah`.

It has:

* 3 Root CAs

It has 2 CRLs which are advertised over CDP as:

* URI:http://localhost:8080/some-child/ca.crl
* URI:http://localhost:8080/some-child/ca-other.crl

test_data/ssl/ is the path where old X.509 certificates, generated using TinyCA
were stored.


FTP/FTPS testing
================

Explicit FTPS with password::
    curl -v --ftp-ssl --cacert test_data/pki/ca-cert.pem \
        -E test_data/pki/client-cert-and-key.pem \
        ftp://user:pass@localhost:10021/

Explicit FTPS with no password::
    curl -v --ftp-ssl --cacert test_data/pki/ca-cert.pem \
        -E test_data/pki/client-ssl_user-cert-and-key.pem \
        ftp://ssl_user@localhost:10021/

Explicit FTPS with CCC::
    curl -v --ftp-ssl --cacert test_data/pki/ca-cert.pem \
        -E test_data/pki/client-ssl_user-cert-and-key.pem \
        ftp://ssl_user@localhost:10021/ --ftp-ssl-ccc

Implicit FTPS::
    curl -v --cacert test_data/pki/ca-cert.pem \
        -E test_data/pki/client-ssl_user-cert-and-key.pem \
        ftps://ssl_user@localhost:10990/


Test code coverage
==================

No code coverage tools is used yet :(


Documentation
=============

Documentation is located in ``server/static/documentation`` and is using
ReStructuredText format.

It is converted into HTML using Python Sphynx.

We generate documentation for 2 use cases:

* website integrated into public website.
* standalone, include into distributable for offline and LM access.

For standalone version, static files (images, fonts, css) are copied from the
website package.
The integrated version is triggered by the publish process.
The standalone version is triggered by the distributable build process.


The following adnotation classes are available:

* seealso - green
* tip - green
* note - blue
* danger - strong red
* warning - red
* attention - yellow

Documentation is generated in 2 versions: production and experimental.
By default the experimental version is generated. To generated the production
version run `documenation_website --experimental`.

You can build the documentation using the following command. Files are
generated in build/doc/html::

    $ ./paver.sh documentation_standalone

The version design to integrate into website can be generated using this
command, but it is much harder to test. To test, you will need to publish it::

    $ ./paver.sh documentation_website

You can check that documentation is successfully built using::

    $ ./paver.sh test_documentation


Download page
=============

Download page is generated together with 'dist' target.
It is build using Jinja2 template from ``server/static/download`` together
with Release Notes file from the documentation.

Data for release notes files is taken from different locations:
 * general page layout from website package
 * general download content from Jinja2 template
 * OS and download notes from pavement.py
 * release notes from release notes file.

Media files are not included in the download page and it uses the
one published on the website.


Project distributable files
===========================

End user distributable files (aka installation kit) are generated using
the `./paver.sh dist` command.

When running on Ubuntu or Windows, `./paver.sh dist` can generate distributable
files for all operating systems (not only for the current one).

Documentation is generated only once and then copied inside each
distributable folder.

When executing `./paver.sh dist` the process will uninstall all packages that
are required only for building and testing, leaving only packages required
for runtime. The removed packages are re-installed at the end of the process.


External dependencies
---------------------

The following external dependencies are required:
 * working Posix environment (msys on Windows)
 * tar (pax format)
 * gzip
 * nsis package on Ubuntu or upstream NullSoft Installer on Windows.

.. note::
    **pax** should be installed in order to create tar.gz archives in pax
    format. Never version of GNU Tar format is not supported on AIX and
    on non-GNU/Linux systems.


Usage
-----

Generate the distributable files for all supported operating system::

    $ ./paver.sh dist

Generate distributable for a specific operating system::

    $ ./paver.sh dist -p linux-x64
    $ ./paver.sh dist -p windows-x86
    $ ./paver.sh dist -p raspbian7-armv7l


Releasing the product
=====================

The work required for a new release is done in a dedicated branch, just like
for any other change.

The release branch should be named: TICKED_ID-release-VERSION

Releasing a new version of the product involves:

* Updating the version number in the release branch
* Updating the release notes based on release-notes/* in the release branch
* building the distributable files
* creating documentation
* creating download page
* copying documentation, download page and files on a public server.

To update the release notes, first update the version and then run this
in the release branch::

    $ ./paver.sh release_notes

It will update the release notes file and remove all release notes fragment
files without a commit.

The documentation is published in both production and experimental version.
Each version is published inside it's own folder on the server
(ex /documentation/sftpplus/v/1.2.3/).
For the latest version, the documentation is also copied to the
`/documentation/sftpplus/latest/` folder.

`./paver.sh publish` is the command use for publishing a new version.
We don't use the `publish` command directly, but rather use the
Release Queue Manager (rqm) to help with a release.

The RQM should check that all test pass and then generate and publish
distributable and documentation.

RQM will publish a tag for the release branch and merge a release branch into
master, once the release was successful.

For more details use::

    $ ./paver.sh rqm --help

To release the current branch on the staging server use::

    $ ./paver.sh rqm

To force the creation of a `latest` version use::

    $ ./paver.sh rqm --latest=yes

To release the current branch in production and have it
merged use the following example::

    $ ./paver.sh rqm --target=production --pull_id=123

The GitHub pull id is required to check that branch was approved and is
mergeable.
It will be merged in the branch specified by the PR.
If it is going to be merged in master, it will also be released as a `latest`
release.


Release blocker and merging into the release branch
---------------------------------------------------

During the release process, new bugs might be found either as a direct result
of the release tests or as external tests.

These bugs will block the release.

The bugs will first need to be fixed in independent branches and merged into
master.

Once merged into master, the release branch will either merge master or
cherry pick the bugfix merge.
Cherry picking is required in the case that master contains other changes
which should not be part of the release.

The release notes need to be manually updated and the release notes fragments
manually removed.

Once the fix is in the release branch, it is ready for release.


Re-releasing
------------

Under some circumstances you might want to re-release a code which was
already merged into master or the release series.

To re-release a product in production, without merging it use the low level
`re-release` gatekeeper (update `latest` flag as suitable for this
re-release). Use this with caution and only in exceptional cases::

    $ ./paver.sh test_remote gk-re-release latest=yes


Doing maintenance bugfix releases
---------------------------------

In some cases we need do to a bugfix release for an older release (which
is not the latest release).

Start the bugfix release based on the normal release process by creating
a ticket and a branch.

The branch should be created from the parent tag. For example to create a
branch for release 1.2.1, create the branch based on tag 1.2.0::

    git checkout -b 1234-release-1.2.1 1.2.0

For bugs which also affect the latest/current release, it is assumed that the
bugfix was already merged in master.

On the release branch, either cherry pick the bugfix merge from master or
in some way update the release branch to include the bugfix.

Updating the version and run `paver release_notes` or manually edit the
release notes.

Create the PR as usual, request a review and send it to RQM using::

    $ ./paver.sh rqm --latest=no

The test might fail to execute at this later date and with the latest
build matrix. Is up to you to update or skip the tests.

Once the RQM was successfull, files are on staging and the PR was approved,
you can do the release using::

    $ ./paver.sh test_remote gk-re-release latest=no

After the files are on the production server, you can manually close the PR,
create a tag (and push it) based on the release branch and manually remove the
release branch.