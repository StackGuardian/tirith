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
