#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import os
import subprocess

def parse_requirements(filename):
    return list(filter(lambda line: (line.strip())[0] != '#',
                       [line.strip() for line in open(filename).readlines()]))


def calculate_version():
    # Fetch version from git tags, and write to version.py.
    # Also, when git is not available (PyPi package), use stored version.py.
    version_py = os.path.join(os.path.dirname(__file__), 'version.py')
    try:
        version_git = subprocess.check_output(["git", "describe"]).rstrip()
    except Exception:
        with open(version_py, 'r') as fh:
            version_git = (open(version_py).read()
                           .strip().split('=')[-1].replace('"', ''))
    version_msg = ('# Do not edit this file, pipeline versioning is '
                   'governed by git tags')
    with open(version_py, 'w') as fh:
        fh.write(version_msg + os.linesep + "__version__=" + version_git)
    return version_git


REQUIREMENTS = parse_requirements('requirements.txt')
VERSION_GIT = calculate_version()


def get_long_description():
    readme_file = 'README.md'
    if not os.path.isfile(readme_file):
        return ''
    # Try to transform the README from Markdown to reStructuredText.
    try:
        import pandoc
        pandoc.core.PANDOC_PATH = 'pandoc'
        doc = pandoc.Document()
        doc.markdown = open(readme_file).read()
        description = doc.rst
    except Exception:
        description = open(readme_file).read()
    return description


setup(
    name='populartwitterbot',
    version=VERSION_GIT,
    author='Limie',
    author_email='limie.ar@gmail.com',
    packages=['populartwitterbot'],
    url='https://github.com/limiear/populartwitterbot',
    license='MIT',
    description=('A python bot that try to find some kind of popularity in the '
                 'twitter community.'),
    long_description=get_long_description(),
    zip_safe=True,
    install_requires=REQUIREMENTS,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
)
