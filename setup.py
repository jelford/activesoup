#! /usr/bin/env python3
# coding=utf-8
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# Get the long description from the README file
with open('README.md', 'r') as f:
    long_description = f.read()


class UseToxError(TestCommand):

    def run_tests(self):
        raise RuntimeError('Run tests with tox')

setup(
    name='activesoup',
    version='0.0.1',
    description='A pure-python headless browser',
    long_description=long_description,
    url='https://github.com/jelford/activesoup',
    author='James Elford',
    author_email='james.p.elford@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ],

    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'beautifulsoup4>=4.4.1',
        'requests>=2.9.0',
        'html5lib>=0.9',
    ],
    cmdclass={'test': UseToxError}
)
