#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup for autopyre."""

import ast
import io

from setuptools import setup

# read the contents of your README file
with open("README.md", "r") as fh:
    long_description = fh.read()

INSTALL_REQUIRES = (
    ['tomli; python_version < "3.11"']
)


def version():
    """Return version string."""
    with io.open('autopyre.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s

with io.open('README.md') as readme:
    setup(
        name='autopyre',
        version=version(),
        description='A tool that automatically formats Python code to conform '
                    'to the PEP 8 style guide and This project based on autopep8',
        long_description=long_description,
        long_description_content_type = "text/markdown",
        license='MIT',
        author='Hideo Hattori, 2023-1-OPPS1-CGS-08',
        author_email='kys00919@gmail.com',
        url='https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Software Development :: Quality Assurance',
        ],
        keywords='automation, pep8, format, pycodestyle, autopyre, pyrestyle',
        install_requires=INSTALL_REQUIRES,
        python_requires=">=3.6",
        test_suite='test.test_autopyre',
        py_modules=['autopyre'],
        zip_safe=False,
        entry_points={'console_scripts': ['autopyre = autopyre:main', 'pyrestyle = pyrestyle:main'],},
    )