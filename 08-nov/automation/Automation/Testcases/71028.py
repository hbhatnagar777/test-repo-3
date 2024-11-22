# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  sets up the variables required for running the testcase

    run()                       --  run function of this test case

    teardown()                  --  tears down the things created for running the testcase

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from Application.GoogleWorkspace.GoogleWorkspace import GoogleDrive
from Application.GoogleWorkspace import constants


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.incremental_user = None
        self.users = None
        self.google_object = None
        self.name = "Google Drive Basic Operations Case"
        self.client_name = None
        self.backup_count = -1
        self.tcinputs = {
            'ServerPlan': None,
            'IndexServer': None,
            'AccessNodeGroup': None,
            'GoogleWorkspacePlan': None,
            'ServiceAccountDetails': None,
            'CredentialName': None,
            'JobResultsDir': None,
            'Users': None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.google_object = GoogleDrive(self.commcell)
            self.google_object.client_name = f"{constants.GDRIVE_CLIENT_NAME}_{self._id}"

            self.log.info(f'Creating Google client : {self.google_object.client_name}')
            self.google_object.create_client(plan_name=self.tcinputs['ServerPlan'],
                                             client_name=self.google_object.client_name,
                                             client_group_name=self.tcinputs['AccessNodeGroup'],
                                             indexserver=self.tcinputs['IndexServer'],
                                             service_account_details=self.tcinputs['ServiceAccountDetails'],
                                             credential_name=self.tcinputs['CredentialName'],
                                             jr_path=self.tcinputs['JobResultsDir'])
            self.google_object.validate_discovered_users()
            self.users = self.tcinputs['Users'].split(",")
            self.incremental_user = self.tcinputs['IncrementalUser'].split(",")
        except Exception as exp:
            self.log.info(f'Error Occurred : {exp}')
            raise Exception

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("********************* RUNNING FIRST BACKUP *****************************")
            self.google_object.create_association(users=self.users,
                                                  plan=self.tcinputs['GoogleWorkspacePlan'])
            self.google_object.run_backup()
            self.log.info("********************* RUNNING INCREMENTAL BACKUP ***********************")
            self.google_object.create_association(users=self.incremental_user,
                                                  plan=self.tcinputs['GoogleWorkspacePlan'])
            self.google_object.run_backup()
            self.log.info("**************** RUNNING RESTORE FOR INCREMENTAL USERS *****************")
            self.google_object.run_restore(self.incremental_user, **{'overwrite': True})
            self.google_object.delete_client(self.google_object.client_name)

        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = 'FAILED'

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == 'PASSED':
                self.log.info(f'Test case status: {self.status}')
                # Delete the client if test case is successful
                self.google_object.delete_client(self.google_object.client_name)
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
