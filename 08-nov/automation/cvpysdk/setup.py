# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ---------------------------------------------------------------------------

"""Setup file for the CVPySDK Python package."""

import os
import re
import ssl
import shutil

from setuptools import setup, find_packages


ssl._create_default_https_context = ssl._create_unverified_context

ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')


def get_version():
    """Gets the version of the CVPySDK python package from __init__.py file."""
    init = open(os.path.join(ROOT, 'cvpysdk', '__init__.py')).read()
    return VERSION.search(init).group(1)


def readme():
    """Reads the README.rst file and returns its contents."""
    with open(os.path.join(ROOT, 'README.rst')) as file_object:
        return file_object.read()

os.chdir(ROOT)

setup(
    name='cvpysdk',
    version=get_version(),
    author='Commvault Systems Inc.',
    author_email='Dev-PythonSDK@commvault.com',
    description='Commvault SDK for Python',
    license='Apache 2.0',
    long_description=readme(),
    url='https://github.com/Commvault/cvpysdk',
    scripts=[],
    packages=find_packages(),
    keywords='commvault, python, sdk, cv, simpana, commcell, cvlt, webconsole',
    include_package_data=True,
    install_requires=['requests==2.31.0', 'xmltodict==0.13.0', 'pycryptodomex==3.20.0'],
    zip_safe=False,
    project_urls={
        'Bug Tracker': 'https://github.com/Commvault/cvpysdk/issues',
        'Documentation': 'https://commvault.github.io/cvpysdk/',
        'Source Code': 'https://github.com/Commvault/cvpysdk/tree/master'
    }
)

# Remove temp files created during setup install
shutil.rmtree(os.path.join(ROOT, 'build'), ignore_errors=True)
shutil.rmtree(os.path.join(ROOT, 'dist'), ignore_errors=True)
shutil.rmtree(os.path.join(ROOT, 'cvpysdk.egg-info'), ignore_errors=True)