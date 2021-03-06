chevah-brink release notes
==========================

Here are the release notes for past brink version.


Version 0.78.1, 2020-11-14
--------------------------

* Reduce the list of extension from Sphinx.
* Remove support for PDF doc generation.


Version 0.78.0, 2020-11-04
--------------------------

* Refactor the publishing of the download and documentation pages.


Version 0.77.2, 2020-11-03
--------------------------

* Fix trial download page create.


Version 0.77.1, 2020-11-03
--------------------------

* Allow creating download page with custom versions. Done to help with trial
  download page creation.


Version 0.77.0, 2020-11-01
--------------------------

* Allow creating download page with external links.


Version 0.76.0, 2020-10-28
--------------------------

* Allow adding custom configuration to Sphinx config file.


Version 0.75.0, 2020-07-19
--------------------------

* Add support for GitHub actions try.


Version 0.74.2, 2020-07-01
--------------------------

* Allow pip from Chevah private pypi server.


Version 0.74.1, 2020-07-01
--------------------------

* Update for latest pip version.


Version 0.74.0, 2020-06-23
--------------------------

* ProjectPaths.cache was removed. The cache is now handled outside of the
  Python code.
* BrinkPaver.getBinaryDistributionFolder was removed.
* The paver.sh script was renamed to brink.sh
* The DEFAULT_VALUES file is no longer used.
  It was replaced by environment variables.


Version 0.73.0, 2020-06-22
--------------------------

* Add support for using with Unicode paths.
* Use global cache for pip.


Version 0.72.0, 2020-02-27
--------------------------

* Add NSIS support for win-x64.


Version 0.71.1, 2018-08-22
--------------------------

* Fix utils.getPythonLibPath() with new short names.


Version 0.71.0, 2018-08-21
--------------------------

* Use shorter OS names: win, amzn, obsd, fbsd, sol.


Version 0.70.3, 2018-07-24
--------------------------

* On Windows store the config in %APPDATA% path.


Version 0.70.2, 2018-07-20
--------------------------

* User config now has default values.


Version 0.70.1, 2018-07-20
--------------------------

* Fix test_remote.


Version 0.70.0, 2018-07-19
--------------------------

* Read buildbot credentials from local file.


Version 0.69.4, 2018-06-23
--------------------------

* Use fixed chmod for sync on Windows.
* Add SHA256 checksum file.


Version 0.69.3, 2018-05-23
--------------------------

* Fix rsync command line.


Version 0.69.2, 2018-05-23
--------------------------

* Use dedicated ssh on Windows for rsync.
* Document the rsync/ssh configuration for windows.


Version 0.69.1, 2018-05-08
--------------------------

* Fix publish with rsync on Windows.


Version 0.69.0, 2018-05-05
--------------------------

* Add support for rsync on Windows.
* Documentation is now published using a relative path to work around rsync
  issues on Windows path handling.
* Update sys-console.js


Version 0.68.0, 2017-12-19
--------------------------

* Add support for publishing trial versions.


Version 0.66.0, 2017-09-04
--------------------------

* Add test_diff helper.
* Fix test when running with specific elevated tests or with arguments.
* Fix test argument parsing when executed via buildbot.


Version 0.65.0, 2017-09-04
--------------------------

* Remove support for experimental documentation version.


Version 0.64.0, 2017-08-13
--------------------------

* For RQM use GitHub API to do the merge.


Version 0.63.4, 2017-07-26
--------------------------

* Exclude *.include.rst include files located in the root folder of the
  documentation.


Version 0.63.3, 2017-06-15
--------------------------

* Make coverage publish less verbose.


Version 0.63.2, 2017-06-13
--------------------------

* Fix `paver lint` when using branch diff.


Version 0.63.1, 2017-06-06
--------------------------

* coverage_publish will not use the BRANCH env var to advertise the branch,
  as on CI system we can run on a bare repo and the branch names might be
  messed.


Version 0.63.0, 2017-06-06
--------------------------

* Update lint target to latest pocket-lint.


Version 0.62.0, 2017-06-06
--------------------------

* PQM merge_commit task will not check that it has the right dependencies
  before running the command.
* Support Raspbian 8 specifically.
* Iterate smarter through version_configuration.
* paver.conf now has a simplified method for installing the base requirements.


Version 0.61.3, 2017-05-18
--------------------------

 Fix PQM when reviews are done using both comments and actions.


Version 0.61.2, 2017-05-11
--------------------------

* Revert Unicode names in test_remote.


Version 0.61.1, 2017-05-11
--------------------------

* Fix Unicode error in test_remote.


Version 0.61.0, 2017-05-09
--------------------------

* Update PQM to use the GitHub latest API to check reviews and
  branch protection.


Version 0.60.5, 2017-05-08
--------------------------

* No longer use --find-links as pip is no longer making a compatible cache.
  pip is now caching wheel files in its own hashed cache.


Version 0.60.4, 2017-05-08
--------------------------

* Fix pip build folder path Unicode handling for Unix/Linux.


Version 0.60.2, 2017-05-08
--------------------------

* Fix distributable publishing.


Version 0.60.0, 2017-05-05
--------------------------

* Fix getBinaryDistributionFolder for new paver.sh
* Update paver.sh for netbsd.


Version 0.59.0, 2017-04-28
--------------------------

* Use pip and setuptools directly from the python package.
* Initial steps for py3 tests.


Version 0.58.1, 2017-04-20
--------------------------

* Add support for Solaris 10 versions older than u8, based on u3.


Version 0.58.0, 2017-02-10
--------------------------

* Add an non overwrite option to BrinkFilesystem.copyFolder.


Version 0.57.0, 2017-01-31
--------------------------

* Update paver.sh from python-package to add support for macOS 10.12.
* Test runner can now be configured with a list of default nose arguments.
* Test runner will pass the right token when using sudo.


Version 0.56.0, 2015-08-10
--------------------------

* Release reserved for the new python-distribution.


Version 0.55.28, 2017-01-08
---------------------------

* Add support for OpenBSD 6.0 and newer.


Version 0.55.27, 2016-12-08
---------------------------

* Update msys-console.js to use latest Git for Windows distribution.


Version 0.55.26, 2016-12-05
---------------------------

* Update README to include release notes creation process
* Move 'release-notes' folder to 'test/release-notes' to avoid confusion,
  as the feature files are used on chevah/server only.


Version 0.55.25, 2016-07-20
---------------------------

* Fix creation of empty folder in zip archive.


Version 0.55.24, 2016-06-02
---------------------------

* Add support for SLES 10.
* Skip CODECOV_TOKEN variable passing in test_super on SLES 10 as it has an
  old sudo without support for preserving environment variables.


Version 0.55.23, 2016-05-03
---------------------------

* Fix CODECOV_TOKEN variable passing in test_super.


Version 0.55.22, 2016-05-03
---------------------------

* Add test_os_dependent and test_os_independent tasks.


Version 0.55.21, 2016-05-01
---------------------------

* Don't publish .coveragerc file


Version 0.55.20, 2016-05-01
---------------------------

* Build .coveragerc file under standard name.


Version 0.55.19, 2016-05-01
---------------------------

* Add task to run local tests with coverage and produce stdout, xml and
  html reports.


Version 0.55.18, 2016-05-01
---------------------------

* Remove support for coverage using nose, as coverage is now provided by
  empirical.


Version 0.55.17, 2016-04-30
---------------------------

* Allow disabling coverage from pavement.py.
* Make PR publish option so that coverage can also be published for the
  `master` repo post-merge.
* Fix package under coverage target.


Version 0.55.16, 2016-04-30
---------------------------

* Add support for generating code coverage and sending report to Codecov
  and having Codecov send reports back to GitHub PR.


Version 0.55.15, 2016-03-19
---------------------------

* Add nicer CLI for forcing steps in test_remote.
  You can now use --force-purge.


Version 0.55.14, 2016-03-19
---------------------------

* Fix log output in test_remote --wait to use the logs retrieved over PB.


Version 0.55.13, 2016-02-03
---------------------------

* Add code to build PDF documentation.
* Fix release notes fragment linter on release series branches.
* Publish latest release by default.


Version 0.55.12, 2016-02-03
---------------------------

* Fix merge_commit.


Version 0.55.11, 2016-02-01
---------------------------

* Update RQM to publish the tag on a release.
* Update lint to check that the release branch has no unpublished release
  notes.
* Update lint to check for release notes fragments.


0.55.10 - 02/12/2015
--------------------

* Support FreeBSD.


0.55.9 - 17/11/2015
-------------------

* Publish on staging under different username.


0.55.8 - 08/11/2015
-------------------

* Prefer wheels in pip.


0.55.7 - 07/11/2015
-------------------

* Allow custom url fragment for download and documentation.
* Allow passing PocketLint options.
* Prevent PQM of release series.


0.55.6 - 24/09/2015
-------------------

* Revert to using the DEFAULTS_VALUE file because of issues with python-package.


0.55.5 - 22/09/2015
-------------------

* Get rid of the DEFAULTS_VALUE temp file and the unused 'make-it-happen.sh'.


0.55.4 - 17/09/2015
-------------------

* Support Raspbian.


0.55.3 - 17/09/2015
-------------------

* Allow custom page title for the the download page.


0.55.2 - 17/09/2015
-------------------

* Allow fine grained customization of the download page.


0.55.1 - 08/09/2015
-------------------

* Create Sphinx build files outside of the output dir.


0.55.0 - 09/08/2015
-------------------

* Fix loading of paver.conf variables.
* Add support for linked tar.gz download files.


0.54.4 - 16/04/2015
-------------------

* Fix merge_init and merge_commit step.


0.54.1 - 16/04/2015
-------------------

* Improve error messages for git set remote.
* Set remote automatically from GitHub url.


0.54.0 - 16/04/2015
-------------------

* Update PQM to work with GitHub push.
* Update URL used in new GitHub pull requests.
* Update test_remote to allow `--force_*` commands.


0.53.1 - 02/04/2015
-------------------

* Fix approval of a review if there is a `needs-changes` before a
  `changes-approved` marker.
* Fix `which` on OSX for Unicode paths.


0.53.0 - 11/03/2015
-------------------

* Remove compiler options from paver.sh, they are no longer needed here.
* Use an updated buildbot that doesn't require bz2 support.


0.52.0 - 04/03/2015
-------------------

* Add support for `changes-approved` command in PQM.


0.51.0 - 24/02/2015
-------------------

* Add ARM64 support.
* Add HP-UX support.
* Fix OS detection for Solaris 9 and OS X 10.10.
* Allow unreadable directories in PATH.


0.50.0 - 13/02/2015
-------------------

* Refactored OS detection.


0.49.3 - 07/01/2015
-------------------

* Fix execution of python elevated test.


0.49.2 - 07/01/2015
-------------------

* Really fix publishing versioned documentation.


0.49.1 - 07/01/2015
-------------------

* Fix publishing versioned documentation.


0.49.0 - 06/01/2015
-------------------

* Update publish task to put versioned documentation into dedicated folder.


0.48.1 - 08/01/2015
-------------------

* Fix paver clean on RHEL 4.


0.48.0 - 18/12/2014
-------------------

* Update linter to check for ticket id of current branch. This should make
  sure known issues are kept in sync.


0.48.0 - 18/12/2014
-------------------

* Update linter to check for ticket id of current branch. This should make
  sure known issues are kept in sync.


0.47.1 - 04/11/2014
-------------------

* Fix removing folders with read-only files on Windows.


0.47.0 - 04/10/2014
-------------------

* Add support for OS X 10.8.
* Rename `get_default_values` to `detect_os`.
* Add /usr/local/bin to the default PATHs.


0.46.3 - 22/09/2014
-------------------

* Revert changes from 0.46.2 as they were bad.


0.46.2 - 22/09/2014
-------------------

* Fix PQM merge_init when branch name is not available on repo. Use only
  branch SHA instead of branch name.


0.46.1 - 22/09/2014
-------------------

* Fix OS detection for RHEL 7.
* Accidentally releases with code from 0.46.2


0.46.0 - 14/08/2014
-------------------

* Add support for RHEL 7.


0.45.2 - 05/09/2014
-------------------

* Fix PQM merge which was not explicitly pushing to origin:master.


0.45.1 - 18/08/2014
-------------------

* Fix PQM merge which was not updating master before merge and so failing
  to push finale changes to origin.


0.45.0 - 14/08/2014
-------------------

* Add support for Ubuntu 14.04.


0.44.1 - 29/07/2014
-------------------

* Fix PQM merge_init to not depend on branch name, but use commit SHA
  instead.


0.44.0 - 13/07/2014
-------------------

* Undo removal of download page generation, since this method is used by
  multiple projects.


0.43.0 - 13/07/2014
-------------------

* Update documentation publish script to also copy latest version.
* To publish documentation, users need to define a `documentation_website`
  task.


0.42.0 - 13/07/2014
-------------------

* Remove functionality to created download page.
* Update Sphinx docs generation to create with different themes.


0.41.0 - 27/06/2014
-------------------

* Fix arch detection on Solaris.


0.40.1 - 16/04/2014
-------------------

* Sync with latest master.
* Fix release notes dates.


0.40.0 - 15/04/2014
-------------------

* Update release helpers to latest build system.
* Rename 'release',  to 'publish' and move it in qm.py.


0.39.2 - 25/03/2014
-------------------

* Fix QM merge_init.
* Add dedicated test_review task.


0.39.1 - 11/03/2014
-------------------

* Update lint task to latest buildbot changes.


0.39.0 - 10/03/2014
-------------------

* Update steps for latest buildbot changes.


0.38.1 - 06/03/2014
-------------------

* Fix PQM merge_init step.


0.38.0 - 05/03/2014
-------------------

* Add support to specify branch name for linter from command line.


0.37.1 - 06/02/2014
-------------------

* Add case insensitive search for markers.


0.37.0 - 05/02/2014
-------------------

* Add linter for FIXME:123: and TO DO markers.


0.36.0 - 05/02/2014
-------------------

* Update to latest pocket-lint and pep8 and fix newly discovered errors.
* Remove support for jslint/jshint as we now use closure-linter.


0.35.0 - 05/02/2014
-------------------

* Add default quick linter. Use -a / --all to lint all files.
* Remove support for JSHint as we now use google-closure-linter.


0.34.0 - 13/01/2014
-------------------

* Add support for legacy client 1.5.


0.33.7 - 24/12/2013
-------------------

* Update release managers parsing to latest buildbot.


0.33.6 - 23/12/2013
-------------------

* Revert 'elevated' exclusion from default test.


0.33.5 - 19/12/2013
-------------------

* Fix test arguments for buildslave.


0.33.4 - 15/12/2013
-------------------

* Fix conversion to Windows new lines.


0.33.3 - 12/12/2013
-------------------

* Fix rendering of RST files so that it is always called from project root.
  docutils has an ugly template loading behaviour. Templates path is resolved
  at module load time and is relative to current working directory.
* Update paver.sh to bootstrap python packages from a PyPi index.


0.33.2 - 12/12/2013
-------------------

* Fix fixDosEndlines to support old `.config` files.


0.33.1 - 12/12/2013
-------------------

* Clean pyc files in `clean` command.
* Use native windows command for removing folders. This gives a big
  performance boots.


0.33.0 - 12/12/2013
-------------------

* Remove paver.sh specific scripts from pavement.py and move script
  configuration variables in a dedicated file.
* Fix downloading binary distribution into local cache.


0.32.0 - 30/11/2013
-------------------

* Use self contained repository by removing all dependencies to local
  brink repository and keeping cached data in repository build folder.


0.31.1 - 19/11/2013
-------------------

* Exit with non-zero result when documentation test failed.


0.31.0 - 06/11/2013
-------------------

* PQM merges the branch with squash and manually closes the GitHub pull
  request.


0.30.0 - 09/10/2013
-------------------

* Add `lint --quick` option to check only changed files since master.
* Add `lint --dry` option to show what files and folders are linted.


0.29.0 - 03/10/2013
-------------------

* Add verbose mode for rsync.
* Use verbose rsync for publishing documentation and distributables.
* Fix creation of download page for production.


0.28.0 - 24/09/2013
-------------------

* Exclude selenium tests from default python tests.


0.26.0 - 03/09/2013
-------------------

* On Windows, make a priority finding paths with extensions.
* Add node-js and npm commands.


0.24.0 - 03/06/2013
-------------------

* Rename 'paver test' into 'paver test_python' and don't run lint tests.


0.23.0 - 03/06/2013
-------------------

* Add fully functional build support system.
* Fix sending test arguments in `paver test_remote`.


0.22.0 - 03/06/2013
-------------------

* Added msys-console script.


0.21.7 - 17/05/2013
-------------------

* Remove copyPython as we now use getBinaryDistributionFolder.
* add '--latest' option to `paver pqm`.


0.21.6 - 13/05/2013
-------------------

* Allow getOption to work even when task options were not defined.
* Reduce logging for makensis command.


0.21.5 - 12/05/2013
-------------------

* Add pave.getBinaryDistributionFolder().


0.21.4 - 12/05/2013
-------------------

* Add RQM and PQM tasks in brink.qm.


0.21.3 - 12/05/2013
-------------------

* Publish according to target argument.


0.21.2 - 12/05/2013
-------------------

* By default, don't wait for test_remote tasks.


0.21.1 - 12/05/2013
-------------------

* Add support for custom properties in test_remote.


0.21.0 - 12/05/2013
-------------------

* Add support for Python 2.7 where simplejson is not available.


0.20.1 - 23/04/2013
-------------------

* Add User Agent for github api requests.


0.20.0 - 24/04/2013
-------------------

* Remove usage of shared requirements file.
* Add versioned documentation and download pages.
