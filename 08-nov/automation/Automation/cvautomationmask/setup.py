# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright ©2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Setup file for the CVAutomationMask Python package."""

import os
import re
import ssl
import sys
import socket
import subprocess
import datetime
import getpass

from setuptools import setup
from setuptools import find_packages


ssl._create_default_https_context = ssl._create_unverified_context
ROOT = os.path.dirname(__file__)
VERSION = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')


def get_version():
    """Gets the version of the cvautomationmask python package from __init__.py file."""
    init = open(os.path.join(ROOT, 'cvautomationmask', '__init__.py')).read()
    return VERSION.search(init).group(1)


def readme():
    """Reads the README.rst file and returns its contents."""
    with open(os.path.join(ROOT, 'README.rst')) as file_object:
        return file_object.read()


def get_license():
    """Reads the LICENSE.txt file and returns its contents."""
    with open(os.path.join(ROOT, 'License.txt')) as file_object:
        return file_object.read()


def is_connected():
    """ Checks whether pypi.org is reachable from the machine """
    try:
        socket.create_connection(("Autocenter.automation.commvault.com", 80))
        return True
    except OSError:
        try:
            socket.create_connection(("engweb.commvault.com", 80))
            return True
        except OSError:
            pass
    return False


def execute_command(command):
    """ Executes command on the machine

    Args:
         command    (str)   -- Command to be executed on the machine

    """
    try:
        os.chdir(packages_directory)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output, error = process.communicate()

        if output:
            print(f"Command output: {output.decode()}")

        if error:
            print(f"Error: {error.decode()}")

    except Exception as exp:
        print(f"Exception occurred: {exp}")


# remove previous cvautomationmask installations
def remove_previous_versions():
    """Uninstalls the older installed versions of cvautomationmask before installing the latest version."""
    process = subprocess.Popen(
        [PYTHON_PATH, '-m', 'pip', 'uninstall', '-y', "cvautomationmask"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output, error = process.communicate()

    if output:
        print(output.decode())
    else:
        print(error.decode())

def cvautomationmask_setup():
    """setuptools parameters as a function for reusability"""
    setup(
        name='cvautomationmask',
        version=get_version(),
        author='Commvault Systems Inc.',
        author_email='Dev-Automation@commvault.com',
        description='Place holder package for Commvault Automation - Internal use only',
        license=get_license(),
        long_description=readme(),
        scripts=[],
        packages=find_packages(),
        keywords='commvault',
        include_package_data=True,
        zip_safe=False,
    )


PYTHON_PATH = sys.executable
FILE_PATH = os.path.abspath(__file__)

remove_previous_versions()

if 'win' in sys.platform.lower(): # retrying install to avoid Windows Access Denied Error
    try:
        cvautomationmask_setup()
    except:
        print("\nRetrying the set up of cvautomationmask as an error occured")
        cvautomationmask_setup() 
else:
    cvautomationmask_setup()


# run pip install for wheel files only if the platform is Windows
# packages are installed along with python by the Commvault installer
if 'win' in sys.platform.lower():
    print('\n Installation user: "{0}"\n'.format(getpass.getuser()))
    PIP_PATH = f'"{PYTHON_PATH}" -m pip'

    packages_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'packages')

    # Install base libraries
    print(f"{datetime.datetime.now()} Installing base requirements")
    base_requirements = os.path.join(packages_directory, 'base_requirements.txt')
    with open(base_requirements, 'r') as file_content:
        packages = file_content.readlines()

    for package_name in packages:
        package = package_name.strip()
        print(f"\n{datetime.datetime.now()} started installing package {package}")
        package_command = f'{PIP_PATH} install --upgrade --no-index --find-links="{packages_directory}"' \
                          f' --no-warn-script-location "{package}" --disable-pip-version-check'
        print(f'\nPackages install command: {package_command}')
        execute_command(package_command)

    # Install other libraries if internet connection is present
    if is_connected():
        print('\nInternet connection is available')
        print('Installing other third party libraries')
        other_requirements = os.path.join(packages_directory, 'other_requirements.txt')
        with open(other_requirements, 'r') as file_content:
            packages = file_content.readlines()

        for package_name in packages:
            package = package_name.strip()
            print(f"\n{datetime.datetime.now()} started installing package {package}")
            package_command = f'{PIP_PATH} install --upgrade --no-warn-script-location "{package}"' \
                              f' --disable-pip-version-check'
            print(f'Packages install command: {package_command}')
            execute_command(package_command)
    else:
        print('Internet connection is not available')
        print('Skipping other third party library installation')

    print("******Install completed******")

PATH = os.path.join(
    os.path.dirname(os.path.dirname(FILE_PATH)), 'CoreUtils', 'config_generator.py'
)

PROCESS = subprocess.Popen([PYTHON_PATH, PATH])
PROCESS.communicate()

PATH = os.path.join(
    os.path.dirname(os.path.dirname(FILE_PATH)), 'CoreUtils', 'problematic_data.py'
)

PROCESS = subprocess.Popen([PYTHON_PATH, PATH])
PROCESS.communicate()
