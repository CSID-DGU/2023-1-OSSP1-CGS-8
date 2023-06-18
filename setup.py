#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup for autopyre."""

import ast
import io

from setuptools import setup

# read the contents of your README file

INSTALL_REQUIRES = (
    ['tomli; python_version < "3.11"']
)


def version():
    """Return version string."""
    with io.open('autopyre.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s

with io.open('README.rst') as readme:
    setup(
        name='autopyre',
        version=version(),
        description='A tool that automatically formats Python code to conform '
                    'to the PEP 8 style guide and This project based on autopep8',
        long_description=readme.read(),
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
        py_modules=['autopyre', 'pyrestyle'],
        zip_safe=False,
        entry_points={'console_scripts': ['autopyre = autopyre:main']},
    )


def get_version():
    with open('pyrestyle.py') as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])

with io.open('README.rst') as readme:
    setup(
        name='pyrestyle',
        version=get_version(),
        description="Python style guide checker",
        long_description=readme.read(),
        keywords='pyrestyle, pep8, PEP 8, PEP-8, PEP8',
        author='Johann C. Rocholl',
        author_email='johann@rocholl.net',
        maintainer='Ian Lee',
        maintainer_email='IanLee1521@gmail.com',
        url='https://github.com/CSID-DGU/2023-1-OPPS1-CGS-08',
        license='Expat license',
        py_modules=['pyrestyle'],
        include_package_data=True,
        zip_safe=False,
        python_requires='>=3.7',
        entry_points={
            'console_scripts': [
                'pyrestyle = pyrestyle:_main',
            ],
        },
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )