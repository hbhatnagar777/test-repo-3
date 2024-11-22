# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper module for downloading additional problematic test data from the
internal repository for advanced internal testing.

This module tries to connect to the internal repository, and downloads and stores
the file under TestData folder inside the AutomationUtils directory
with the name problematicdata.tar.gz & windows_problematicdata.7z

This module is ran as part of the Post Install script during installation of the Test Automation
package using the Commvault Installer.

**ProblematicData:**    Class to connect to and download the problematic data from
the internal repository

    __init__()              --  initializes an instance of the problematic data helper class

    _download_package()     --  downloads the problematic data package from the given URL and
    writes under the AutomationUtils\\TestData directory

    download_test_data()    --  initiates the job to download the problematic test data package
    from the internal repository

"""


import os
import requests


class ProblematicData(object):
    """Helper class to download problematic data from autocenter"""

    UNIX_TEST_DATA_URL = ("http://autocenter.automation.commvault.com:1983/"
                          "TESTDATA/UNIX/problematicdata.tar.gz")

    WINDOWS_TEST_DATA_URL = ("http://autocenter.automation.commvault.com:1983/"
                             "TESTDATA/WINDOWS/windows_problematicdata.7z")

    def __init__(self):
        """Initializes the problematic data attributes"""
        self._download_location = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'AutomationUtils', 'TestData'
        )

        if not os.path.exists(self._download_location):
            os.makedirs(self._download_location)

    def _download_package(self, download_url):
        """Downloads the problematic data package from the internal repository and
            writes under the AutomationUtils\\TestData directory

            Args:
                download_url     (str)     --   url where the package is to be downloaded from

        """
        downloaded_file_location = os.path.join(
            self._download_location, download_url.split('/')[-1]
        )

        if os.path.exists(downloaded_file_location):
            return

        try:
            download_stream = requests.get(download_url, stream=True)

            if download_stream.status_code == 200:
                with open(downloaded_file_location, 'wb') as file:
                    for chunk in download_stream.iter_content(chunk_size=1024**2):
                        if chunk: # filter out keep-alive new chunks
                            file.write(chunk)
            else:
                print("Failed to download the file. Please check repository.")

        except requests.exceptions.ConnectionError:
            print("Problematic data download not required. Skipping it.")
        except Exception as excep:
            print("Failed to download file from: ", download_url)
            print(excep)

    def download_test_data(self):
        """Downloads the problematic data package from the internal repository"""
        self._download_package(ProblematicData.UNIX_TEST_DATA_URL)
        self._download_package(ProblematicData.WINDOWS_TEST_DATA_URL)


if __name__ == '__main__':
    PROBLEMATIC_DATA = ProblematicData()
    PROBLEMATIC_DATA.download_test_data()
