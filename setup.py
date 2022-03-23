#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup

import ekbuild


dist_name = "ekbuild"
description = "Endless Key build system"


setup(
    name=dist_name,
    description=description,
    version=ekbuild.VERSION,
    author="EndlessOS",
    author_email="danigm@endlessos.org",
    packages=["ekbuild"],
    entry_points={
        "console_scripts": "ekbuild = ekbuild:main.main",
    },
    package_dir={"ekbuild": "ekbuild"},
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
)
