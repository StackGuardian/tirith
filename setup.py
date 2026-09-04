#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")) as file_handle:
        return file_handle.read()


setup(
    name="py-tirith",
    version="1.2.0",
    license="Apache",
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
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    # Declared explicitly as well as in MANIFEST.in: MANIFEST governs the sdist, but a wheel
    # built straight from the tree takes its data files from here. Without this the TUI
    # installs with no stylesheet and no examples -- it starts, and every playground pane is
    # empty, which is a worse failure than not starting at all.
    package_data={
        "tirith.tui": ["*.css"],
        "tirith.tui.examples": ["*/*.json", "*/*.md"],
        # The bundled policy packs. Without these `--pack` finds nothing and `--list-packs`
        # prints an empty list, which is the same silent-empty failure the TUI had.
        "tirith.packs": ["*/pack.json", "*/policies/*.json"],
    },
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        # 'Operating System :: Microsoft :: Windows',
        "Programming Language :: Python",
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        # 'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        "Topic :: System",
    ],
    project_urls={
        "Changelog": "https://github.com/stackguardian/tirith/blob/main/CHANGELOG.md",
        "Issue Tracker": "https://github.com/stackguardian/tirith/issues",
    },
    keywords=["iac", "policy", "terraform", "policy as code"],
    python_requires=">=3.8",
    install_requires=["simplejson==3.17.2", "pydash==6.0.0", "PyYAML==6.0.1"],
    extras_require={
        # `pip install py-tirith[tui]` adds the interactive interface (`tirith ui`).
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
    setup_requires=[
        "pytest-runner",
    ],
    entry_points={
        "console_scripts": [
            "tirith=tirith.__main__:main",
        ]
    },
)
