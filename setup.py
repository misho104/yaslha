#!env python
from setuptools import setup
import ast
import pathlib
import re


with (pathlib.Path('yaslha') / '__init__.py').open('rb') as f:
    version_match = re.search(r'__version__\s+=\s+(.*)', f.read().decode('utf-8'))
    version = str(ast.literal_eval(version_match.group(1))) if version_match else '0.0.0'

setup(
    name='yaslha',
    version=version,
    author='Sho Iwamoto / Misho',
    author_email='webmaster@misho-web.com',
    url='https://github.com/misho104/yaslha',
    description='A Python package to convert data files in SLHA and similar formats to Python objects, JSON, or YAML.',
    license='MIT',
    packages=['yaslha'],
    package_data={
        'yaslha': [
            'tests/data/*',
        ]},
    install_requires=['click', 'ruamel.yaml'],
    entry_points={
        'console_scripts': ['yaslha-convert=yaslha.script:convert']
    },
    tests_require=['nose', 'coverage', 'mypy', 'flake8'],
    test_suite='nose.collector',
)
