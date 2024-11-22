# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    GmailUsername   --  Username for the Gmail account

    GmailPassword   --  Password for the Gmail account

    CloudUsername   --  Username to login to commvault cloud

    CloudPassword   --  Commvault cloud password

    TrialCloudUsername --  Username to perform Trial related operations

    TrialCloudPassword --  Password for the Trial account

"""

import json

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from CVTrials.trial_helper import TrialHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for downloading commvault trial package"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express trial package download from cloud"
        self.helper = None
        self.browser = None
        self.driver = None
        self.machine = None
        self.download_directory = None

        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            "GmailUsername": None,
            "GmailPassword": None,
            "CloudUsername": None,
            "CloudPassword": None,
            "TrialCloudUsername": None,
            "TrialCloudPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        # To create a machine class object for the local machine
        self.machine = Machine()

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()

        # To generate download directory
        self.download_directory = self.machine.join_path(
            constants.AUTOMATION_DIRECTORY,
            'CVTrials',
            'TrialPackage'
        )

        # To delete Trial package folder if it exists
        if self.machine.check_directory_exists(self.download_directory):
            self.machine.remove_directory(self.download_directory)
            self.log.info('Directory: %s removed successfully', self.download_directory)

        # To create download directory for downloading the files
        self.machine.create_directory(self.download_directory)
        self.log.info('Directory: %s created successfully')

        # To set download directory for downloading files in the browser
        self.browser.set_downloads_dir(self.download_directory)
        self.browser.open()
        self.driver = self.browser.driver

        # To initialize the Trial helper file
        self.helper = TrialHelper(self)

        # To login to Gmail account
        self.helper.gmail.navigate_to_gmail()
        self.helper.gmail.login(self.tcinputs.get('GmailUsername'), self.tcinputs.get('GmailPassword'))

        # To delete all the mail from the given sender
        self.helper.gmail.delete_all_mail_from_sender('cloudservices@commvault.com')
        self.helper.gmail.delete_all_mail_from_sender('support@commvault.com')

        # To delete the trial user entries
        self.helper.delete_commvaultone_trial_user(cloud_username=self.tcinputs.get('CloudUsername'),
                                                   cloud_password=self.tcinputs.get('CloudPassword'))

        # To delete the trials text file if exists
        file_path = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
        if self.machine.check_file_exists(file_path):
            self.machine.delete_file(file_path)
        self.log.info('Successfully removed the trial temporary files')

    def run(self):
        """Main function for test case execution"""
        try:
            # To register for the commvault trial package in commvault home page
            self.helper.register_for_free_trial(
                username=self.tcinputs.get('TrialCloudUsername'),
                password=self.tcinputs.get('TrialCloudPassword'),
                first_name='Commvaultone',
                last_name='Trial',
                phone='0999999999',
                postal_code='560075',
                company='commvault',
                email=self.tcinputs.get('GmailUsername'),
                country='India')

            # To download the commvault trial software
            self.helper.download_trial_package_from_cloud(
                sender='cloudservices@commvault.com',
                path=self.download_directory)

            # To store the mail contents in a Temp text file
            contents = self.helper.trial_details
            contents['status'] = 'passed'

            # File path to save the contents
            file_path = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
            self.log.info('Mail contents are stored in the path: "%s"', file_path)

            with open(file_path, 'w') as file:
                file.write(json.dumps(contents))

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        Browser.close_silently(self.browser)
