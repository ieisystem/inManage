#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup for inmanage_sdk."""

import ast
import io
import setuptools
from setuptools import setup

INSTALL_REQUIRES = (
    ['pycryptodome >= 3.5.0', 'PyYAML', 'requests >= 2.9.1', 'Jpype1', 'requests-toolbelt']
)


def version():
    """Return version string."""
    with io.open('inmanage.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s


with io.open('README.md') as readme:
    setup(
        name='inmanage',
        version=version(),
        description='ieisystem server manager api',
        long_description=readme.read(),
        license='Expat License',
        author='Wangbaoshan',
        author_email='wangbaoshan@ieisystem.com',
        url='https://github.com/ieisystem/inManage',
        classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
        ],
		install_requires=INSTALL_REQUIRES,
        py_modules=['inmanage'],
		packages=setuptools.find_packages(),
		include_package_data=True
    )
