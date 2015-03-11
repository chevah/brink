chevah-brink release notes
==========================

Here are the release notes for past brink version.


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
