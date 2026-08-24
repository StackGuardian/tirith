#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from os.path import dirname
from os.path import join

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")) as file_handle:
        return file_handle.read()


def read_version():
    """
    Single source of truth: `src/tirith/__init__.py`.

    Read rather than imported, because importing the package at build time would execute its
    imports before its dependencies are installed. `tirith --version` reports this same value
    (`cli.py` reads `tirith.__version__`), so a duplicate literal here is a version the CLI can
    contradict -- which is exactly what a hardcoded copy invites, and nothing asserted otherwise.
    """
    match = re.search(r'^__version__ = "([^"]+)"', read("src", "tirith", "__init__.py"), re.M)
    if not match:
        raise RuntimeError("could not find __version__ in src/tirith/__init__.py")
    return match.group(1)


setup(
    name="tirith-iac-governance",
    version=read_version(),
    license="Apache-2.0",
    license_files=["LICENSE"],
    description="Tirith simplifies defining Policy as Code.",
    long_description_content_type="text/markdown",
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub("", read("README.md")),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.md")),
    ),
    author="StackGuardian",
    author_email="team@stackguardian.io",
    url="https://github.com/stackguardian/tirith",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    # Declared explicitly as well as in MANIFEST.in: MANIFEST governs the sdist, but a wheel
    # built straight from the tree takes its data files from here. Without this the TUI
    # installs with no stylesheet and no examples -- it starts, and every playground pane is
    # empty, which is a worse failure than not starting at all.
    package_data={
        "tirith.tui": ["*.css"],
        "tirith.tui.examples": ["*/*.json", "*/*.md"],
    },
    zip_safe=False,
    classifiers=[
        # The matrix in .github/workflows/build_test.yml is the source of truth for what is
        # actually supported; these must not claim less than it tests, which they did -- 3.10
        # through 3.12 were tested on every push and advertised nowhere.
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Quality Assurance",
    ],
    project_urls={
        "Changelog": "https://github.com/stackguardian/tirith/blob/main/CHANGELOG.md",
        "Issue Tracker": "https://github.com/stackguardian/tirith/issues",
    },
    keywords=["iac", "policy", "terraform", "policy as code"],
    python_requires=">=3.8",
    install_requires=["simplejson==3.17.2", "pydash==6.0.0", "PyYAML==6.0.1"],
    extras_require={
        # `pip install tirith-iac-governance[tui]` adds the interactive interface (`tirith ui`).
        #
        # An extra rather than a dependency, for two reasons. The UI toolkit requires Python
        # >=3.9 while tirith supports >=3.8, so a hard dependency would drop 3.8 support for
        # everyone; the environment markers below let 3.8 users install the extra and simply
        # get nothing rather than an error. And tirith's main use is as a CI gate, where every
        # dependency is install time on every run -- people gating a pipeline should not pay
        # for an interface they never open.
        # textual>=8.0 rather than a looser floor: `Select.NULL` (the unselected sentinel the
        # Playground and Builder both test against) only exists from 8.0. Before that it was
        # named Select.BLANK, so on 0.60-7.x the example picker raises AttributeError the first
        # time the prompt row is chosen. `Select(compact=...)` is likewise newer than 0.60.
        "tui": [
            'textual>=8.0; python_version >= "3.9"',
            'textual-serve>=1.0; python_version >= "3.9"',
        ],
    },
    entry_points={
        "console_scripts": [
            "tirith=tirith.__main__:main",
        ]
    },
)
