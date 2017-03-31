common
======

[![Build Status](https://travis-ci.org/CampbellGroup/common.svg?branch=166_include_travis)](https://travis-ci.org/CampbellGroup/common)



Shared campbell lab code.

# Installation
To install dependent modules, double click on ```install_dependencies.py```. Alternatively, you can run it in a terminal:

```bash
>>> python install_dependencies.py
```

Please note that you might have to change the LABRADHOST environmental variable after installation. For instructions on how to do this, look up on CampbellGroup wiki.

To install the ok module, you need to go the software folder on the Campbell server and install the corresponding package.

# Conventions
New code should...  
* Be Python 2 & 3 compatible  
* Follow pep8  
* Have default config files in the config directory, with local users specifying configuration settings via an external "config" directory at the  same level as this repository.    
* Minimize functional code in guis, i.e. have the GUIs import   functions/objects that perform calculations whenever reasonable.  
* Test code for all new (and old) but GUIs is highly encouraged.    


# Contributing

## Process

1. User iHaveIssues makes an issue in the issue tracker.  This issue explains what feature is to be added or what bug is to be fixed.

2. User c0der creates a new branch for development regarding this issue. The branch name is `XX-description-of-issue` where `XX` is the issue number and the remainder is a brief description of the issue.

3. Development is done in the branch via a series of commits.

4. When the feature is nearly complete or the bug is fixed, a pull request is filed by a user iPullRequest (usually iPullRequest is the same person as c0der).  This notifies other users that some new code is ready for review. iPullRequests can and should call out specific users who are qualified to review the code. Those users review the code by reading the changes and running the new (and old) tests.

5. Users may add more commits to address outstanding issues with the code.

6. Once user iDoReviews thinks the code is in good shape, they comment "LGTM" (looks good to me) in the pull request comments. iPullRequest can now merge the feature branch into master. Writing LGTM on a pull requests indicates that you are convinced the code works as expected and that you now share responsibility with the author for any problems arising from the change. **Only iPullRequests may actually merge the pull request**.  For larger or more critical changes, such as refactoring functional code, several reviewers should sign off LGTM on the pull request.

7. Tests are highly encouraged for any new functionality.  
* Tests should stand alone as much as possible.  
* Tests should run from the terminal and not change the users environment, by for example opening windows that the user would have to manually close. For functions that generate plots, use plt.switch_backend('PDF') to switch off the generation of plot windows, which prevent tests from running while open.  
* When in doubt, testing something is better than testing nothing.  

* Any changes should pass all existing tests. Run the test code with    
```
$ nosetests -w common\tests
```  
from the command line.

### Commits

* Commits should focus on precisely one issue.  
* Group pep8 changes to existing code into their own commits.  

#### Commit messages

Your commit message documents your changes for all time. Take pride in it. Commits should follow this format:

* Brief one sentence description of the change, using the active present tense.
* One blank line
* A paragraph describing the change in more detail. For small changes, this may not be needed if the brief description captures the essence of the change.


### Small fixes

For small fixes, there is no need to open an issue. The contributor must still create a new branch and make a PR for code review. The branch name should be prefixed with `minor` instead of an issue number.

    Examples of small fixes include:
     * Changing an error (or success) message to be more descriptive.
     * Updating docstrings.
