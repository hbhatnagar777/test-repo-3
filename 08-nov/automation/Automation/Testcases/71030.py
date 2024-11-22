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
from Application.GoogleWorkspace.GoogleWorkspace import GoogleMail
from Application.GoogleWorkspace.solr_helper import SolrHelper
from Web.Common.exceptions import CVTestStepFailure
from Application.GoogleWorkspace import constants


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.incremental_user = None
        self.solr_helper = None
        self.users = None
        self.google_object = None
        self.name = "Google Mail Basic Acceptance Case"
        self.client_name = None
        self.backup_count = 0
        self.input_count = 0
        self.incr_count = 0
        self.solr_count = 0
        self.tcinputs = {
            'ServerPlan': None,
            'IndexServer': None,
            'AccessNodeGroup': None,
            'GoogleWorkspacePlan': None,
            'ServiceAccountDetails': None,
            'CredentialName': None,
            'JobResultsDir': None,
            'Users': None,
            'InputCount': None,
            'IncrementalCount': None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.google_object = GoogleMail(self.commcell)
            self.google_object.client_name = f"{constants.GMAIL_CLIENT_NAME}_{self._id}"

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
            self.input_count = self.tcinputs['InputCount']
            self.incr_count = self.tcinputs['IncrementalCount']
            self.solr_helper = SolrHelper(self, self.google_object)
        except Exception as exp:
            self.log.info(f'Error Occurred : {exp}')
            raise Exception

    def verify_backup(self,job_details,incremental=False):
        """
        Runs backup for the associated users.
        """
        try:
            if job_details.summary['status'].lower() != 'completed':
                self.log.info(f"Backup Job didn't completed successfully. Job Status : {job_details.summary['status']}")
                raise Exception

            self.log.info("Job completed Successfully!")
            self.log.info(f"Job details are : {job_details.summary}")
            self.backup_count = int(job_details.summary['totalNumOfFiles'])


            self.log.info(f"Documents Count from Backup : {self.backup_count}")
            self.log.info(f"Documents Count from Index : {self.solr_count}")

            if incremental:
                if int(self.solr_count) != self.backup_count or self.backup_count!=self.incr_count:
                    self.log.info(f"Count Mismatch in Incremental Backup Job")
                    raise Exception
                self.log.info(f"Incremental Backup Job Count Matched!")
            else:
                if int(self.solr_count) != self.backup_count or self.backup_count!=self.input_count:
                    self.log.info(f"Count Mismatch in Backup Job")
                    raise Exception
                self.log.info(f"Backup Job Count Matched!")

        except:
            raise CVTestStepFailure(f"Client Level Backup failed")

    def verify_restore(self,job_details):
        """
        Runs restore for the client
        """
        try:
            if job_details.status.lower() != 'completed':
                self.log.info(f"Restore Job didn't completed successfully. Job Status : {job_details.summary['status']}")
                raise Exception

            job_details = job_details.details['jobDetail']
            self.log.info("Job completed Successfully!")
            self.log.info(f"Job details are : {job_details}")

            if self.backup_count != int(job_details['detailInfo']['numOfObjects']):
                self.log.info(f"Backup count and Restore count is not matched!!")
                raise Exception

            self.log.info('Restore Job Successful!')
        except Exception as err:
            self.log.error(f'Exception occured : {str(err)}')
            raise CVTestStepFailure(f"Restore operation unsuccessful. Error : {err}")

    def run(self):
        """Run function of this test case"""
        try:
            self.google_object.create_association(users=self.users, plan=self.tcinputs['GoogleWorkspacePlan'])
            self.log.info("Running Backup")
            full_job_details = self.google_object.run_backup()
            full_job_details.wait_for_completion()
            self.solr_count = self.solr_helper.check_all_items_played_successfully(select_dict={'JobId': full_job_details.job_id,
                                                                                           'DocumentType': 2})
            self.verify_backup(full_job_details)
            self.google_object.create_association(users=self.incremental_user,
                                                  plan=self.tcinputs['GoogleWorkspacePlan'])
            self.log.info("Running Incremental Backup")
            incr_job_details = self.google_object.run_backup()
            incr_job_details.wait_for_completion()
            self.solr_count = self.solr_helper.check_all_items_played_successfully(select_dict={'JobId': incr_job_details.job_id,
                                                                                           'DocumentType': 2})
            self.verify_backup(incr_job_details,incremental=True)
            self.log.info("Running Restore")
            restore_job_details = self.google_object.run_restore(self.incremental_user, **{'overwrite': True})
            restore_job_details.wait_for_completion()

            self.verify_restore(restore_job_details)


        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = 'FAILED'

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')
            if self.status == 'PASSED':
                # Delete the client if test case is successful
                self.google_object.delete_client(self.google_object.client_name)
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
