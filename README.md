[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

# StackGuardian Policy Framework

StackGuardian Policy Framework scans declarative Infrastructure as Code (IaC) configurations like Terraform against policies defined using JSON.

## Content

- [Features](#features)
- [Feature Road-Map](#feature-road-map)
- [How to use it?](#how-to-use-it)
- [A basic mind-map of the repository](#a-basic-mind-map-of-the-repository)
- [Local Development Environment](#local-development-environment)
- [Want to contribute?](#want-to-contribute)
    * [Getting an issue assigned](#getting-an-issue-assigned)
    * [A bug report](#a-bug-report)
    * [Opening a Pull Request and getting it merged](#opening-a-pull-request-and-getting-it-merged)
- [Submitting a feedback](#submitting-a-feedback) 
- [Support](#support)
- [License](#license)



## Features
- A simple interface to define compliance policies as declarative config, which can be enforced proactively on Infrastructure as Code to detect breaches.
- Pluggable architecture allows to integrate into policy engines like OPA for policy evaluation.
- Summarizes evaluation output and provides brief output formatting.
- Cli support with data and input as arguments.
- Very easy to use.
- Works on Mac, Linux and Windows.

## Feature Road-map
This is only a list of approved features that will be included in the StackGuardian Policy Framework over the next few months.
- Support for CloudFormation config scanning
- Support for ARM config scanning
- Extended library of evaluator functions

## How to use it?

## A basic mind-map of the repository

## Local Development Environment

- Any operating system is supported(Windows, Mac, or Linux).
- Python 3.6 or higher is required.
- [pip](https://pip.pypa.io/en/stable/) is required.

And leave the rest to us!!!
<!-- ## Publish Package on test.pypi.org
* Use the following command to install the latest version of the setuptools package.
  ```
    python -m pip install --user --upgrade setuptools
  ```
  
* Make sure you are at the same directory where setup.py is located and run this command.
  ```
    python setup.py sdist
  ```
* Visit <a href="https://test.pypi.org/">test.pypi.org</a> and create a new account if not already.
* Install Twine package using following command.
  ```
    pip install twine
  ```
* Upload you package to test.pypi using following command.
  ```
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
  ``` -->

## Want to contribute?
### Getting an issue assigned

Go to the <a href="https://github.com/StackGuardian/policy-framework">StackGuardian Policy Framework Repository</a> and in the <a href="https://github.com/stackguardian/policy-framework/issues">issues</a> tab describe any bug or feature you want to add. If found relevant, the maintainers will assign the issue to you and you may start working on it as mentioned in the next section.
<p>The kinds of issues a contributor can open:</p>
 <ul>
	<li>Report Bugs</li>
	<li>Feature Enhancement</li>
	<li>If any "help" is needed with the policy framework</li>
 </ul>

### A bug report

Head over to the <a href="https://github.com/StackGuardian/policy-framework">StackGuardian Policy Framework Repository</a> and in the <a href="https://github.com/stackguardian/policy-framework/issues">issues</a> tab describe the bug you encountered and we will be happy to take a look into it.
### Opening a Pull Request and getting it merged?

 1. Go to the <a href ="https://github.com/StackGuardian/policy-framework">repository</a> and fork it.
 2. Clone the repository in your local machine.
 3. Open your terminal and ```cd policy-framework```
 4. Create your own branch to work on the changes you intend to perform. For e.g. if you want some changes or bug fix to any function in the evaluators, name your branch with something relevant like, ```git branch bug-fix-equals-evaluator```
 5. After necessary changes, ```git push --set-upstream origin bug-fix-equals-evaluator```, ```git checkout main``` and ```git merge bug-fix-equals-evaluator``` or use the GUI to create a "Pull Request" after pushing it in the respective branch.
 6. A review request will be sent to the repository maintainers and your changes will be merged if found relevant.

## Submitting a Feedback

Wanna submit a feedback? It's as simple as writing and posting it in the <a href="https://github.com/StackGuardian/feedback/discussions/8">feedback section</a>.
<p>Your feedback will help us improve</p>

## Support

## License

<i>Apache License 2.0</i>
<p>The Apache License is a permissive free software license written by the Apache Software Foundation (ASF). It allows all users to use the software for any purpose, to distribute it, to modify it, and to distribute modified versions of the software under the terms of the license, without concern for royalties.</p>
