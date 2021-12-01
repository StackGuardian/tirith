[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

# StackGuardian Policy Framework

StackGuardian Policy Framework scans declarative Infrastructure as Code (IaC) configurations like Terraform against policies defined using JSON.

## Features
- A simple interface to define compliance policies as declarative config, which can be enforced proactively on Infrastructure as Code to detect breaches.
- Pluggable architecture allows to integrate into policy engines like OPA for policy evaluation.
- Summarizes evaluation output and provides brief output formatting.
- Cli support with data and input as arguments

## Feature Road-map
This is only a list of approved features that will be included in the StackGuardian Policy Framework over the next few months.
- Support for CloudFormation config scanning
- Support for ARM config scanning
- Extended library of evaluator functions

## Publish Package on test.pypi.org
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
  ```

