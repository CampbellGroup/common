common
======

[![Build Status](https://travis-ci.org/CampbellGroup/common.svg?branch=166_include_travis)](https://travis-ci.org/CampbellGroup/common)

Shared campbell lab code.

# Installation

## Dependencies

There are a number of packages that should be installed:

* `pylabrad`
* `pyqt5`       - GUI package
* `pyqt5-stubs` - Linter hints for `pyqt5` (nonfunctional, but useful in IDEs for code inspection)
* `qt5reactor`  - needed for compatibility between LabRAD's backend (based on `twisted`) and `pyqt5`
* `numpy`
* `scipy`
* `ok`          - This is a package provided by OpalKelly to interface with its FPGAs. We have several versions
  in the group's share drive

## Environment Variables

The first thing that needs to happen to make this work is to set the environment variables that Labrad expects to have.
These tell it what settings to use, and are consistent throughout our lab:

| Name            | Setting              | Description                                                                                                                                   |
|-----------------|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| LABRADHOST      | localhost (or an IP) | The hostname or IP address where the manager is running. If you want this computer to connect to another one, use that computer's IP address. |
| LABRADPORT      | 7682                 | TCP port to use when connecting to the labrad manager.                                                                                        |
| LABRADPASSWORD  | lab                  | Password to use for connecting to the manager. If left blank, you'll be prompted for a password every time.                                   |
| LABRAD_TLS      | off                  | Transport Level Security (TLS) mode to use for securing connections to the manager.                                                           |
| LABRAD_TLS_PORT | 7643                 | TCP port to use when connecting to the labrad manager with a connection initially secured by TLS.                                             |
| LABRADNODE      | \<name of the node\> | Used by the node server as the name of the labrad node running on this machine.                                                               |

# Issues

See issue templates located at https://github.com/CampbellGroup/common/tree/master/.github/ISSUE_TEMPLATE before
submitting issues

# Conventions

New code should...

* Be Python 2 & 3 compatible, using
    ```python
    print(str)
    ```
  and
    ```python
    try:
        ...
    except Exception as e:
        ...
    ```
* Follow pep8
* Write code that obviates the need for configuration files.
* If necessary, have default configuration files in the config directory, with local users specifying configuration
  settings via an external "config" directory at the same level as this repository.
* Minimize computrational code in guis, i.e. GUI's should be able to run stand-alone on any computer in this sense they
  should be "dumb" and able to be imported into code and buttons etc. attached to functions.
* Test code for all new (and old) but GUIs is highly encouraged.

# Contributing

Adapted from [pylabrad contribution guidelines](https://github.com/labrad/labrad/blob/master/contributing.md)

## Process

1. User iHaveIssues posts an issue. The issue explains the desired feature or bug to be fixed.

2. User c0der creates a new branch for development regarding the issue. The branch name is
   `XX-brief-description-of-issue` where `XX` is the issue number.

3. Development is done in the branch via a series of commits.

4. When the feature is nearly complete or the bug is fixed, a pull request is filed by a user iPullRequest (usually
   iPullRequest is the same person as c0der). This notifies other users that new code is ready for review. iPullRequests
   should ask for a code reviews from qualified users. Those users review the code by reading the changes and running
   the test code.

5. Users may add more commits to address outstanding issues with the code.

6. Once user iDoReviews thinks the code is in good shape, they comment "LGTM" (looks good to me) in the pull request
   comments.

- **Writing LGTM on a pull requests indicates that you are convinced the code works as expected and that you now share
  responsibility with the author for any problems arising from the change.**

- iPullRequest can now merge the feature branch into master. Only iPullRequests may actually merge the pull request.

- For larger or more critical changes, such as refactoring functional code, several reviewers should sign off LGTM on
  the pull request.

7. Tests are highly encouraged for any new functionality.

- Tests should stand alone as much as possible.
- Tests should run from the terminal and not change the users environment, by for example opening windows that the user
  would have to manually close. For functions that generate plots, use plt.switch_backend('PDF') to switch off the
  generation of plot windows, which prevent tests from running while open.
- When in doubt, testing something is better than testing nothing.

- Any changes should pass all existing tests. Run the test code from a terminal with

```
$ nosetests -w common\tests
```  

### Commits

* Commits should focus on precisely one issue.
* Group pep8 changes to existing code into their own commits.

#### Commit messages

Your commit message documents your changes for all time. Take pride in it. Commits should follow this format:

* Brief one sentence description of the change, using the active present tense.
* One blank line
* A paragraph describing the change in more detail. For small changes, this may not be needed if the brief description
  captures the essence of the change.

### Small fixes

For small fixes, there is no need to open an issue. The contributor must still create a new branch and make a PR for
code review. The branch name should be prefixed with `minor` instead of an issue number.

    Examples of small fixes include:
     * Changing an error (or success) message to be more descriptive.
     * Updating docstrings.
