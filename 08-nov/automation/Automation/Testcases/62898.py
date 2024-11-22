# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from datetime import datetime, timedelta

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.DisasterRecovery.drmanagement_helper import DRCommvaultCloudManagement, CreateCommcellInstance


class TestCase(CVTestCase):
    """Check in the download report that for a specified user, the user is able to view DR download history
    of Commcell ID's he is part of
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "View DR download history on cloud"
        self.tcinputs = {
            "CloudUser1UserName": None,
            "CloudUser1Password": None,
            "CloudUser2UserName": None,
            "CloudUser2Password": None,
            "DatasetParameters": {"datasetGuid": "None", "duration":"None"}
        } #duration is in days
        self.cloud_user1_commcell = None
        self.cloud_user2_commcell = None
        self.helper_cloud_user1 = None
        self.helper_cloud_user2 = None
        self.helper_cloud_admin = None
        self.CommentsForAccess = "Please, give download access!"
        self.CommentsForApproveDenyRevoke = "Yes, you may."
        self.cloud_user1_username = ''
        self.cloud_user2_username = ''
        self.UserCommcellAssociation = dict()
        self.local_machine = Machine()

    def setup(self):
        """Setup function of this test case"""
        self.cloud_user1_commcell = CreateCommcellInstance(self.commcell.webconsole_hostname,
                                                           self.tcinputs.get('CloudUser1UserName'),
                                                           self.tcinputs.get('CloudUser1Password'))()
        self.cloud_user2_commcell = CreateCommcellInstance(self.commcell.webconsole_hostname,
                                                           self.tcinputs.get('CloudUser2UserName'),
                                                           self.tcinputs.get('CloudUser2Password'))()
        self.helper_cloud_user1 = DRCommvaultCloudManagement(self.cloud_user1_commcell)
        self.helper_cloud_user2 = DRCommvaultCloudManagement(self.cloud_user2_commcell)
        self.helper_cloud_admin = DRCommvaultCloudManagement(self.commcell)
        self.utility = OptionsSelector(self.commcell)
        self.cloud_user1_username = self.tcinputs.get('CloudUser1UserName')
        self.cloud_user2_username = self.tcinputs.get('CloudUser2UserName')

    def run(self):
        """Run function of this test case"""
        try:
            companyname_companyid_commcellguid_commcellid = self.helper_cloud_user1.get_companyname_companyid_commcellguid_commcellid()
            self.helper_cloud_user1.company_name, self.helper_cloud_user1.company_id, \
            self.helper_cloud_user1.commcell_guid, self.helper_cloud_user1.commcell_id = companyname_companyid_commcellguid_commcellid[0]
            request_id = self.helper_cloud_user1.request_access(self.CommentsForAccess)
            self.log.info('Request for Access of .dmp files for commcell %s was sent successfully'
                          % self.helper_cloud_user1.commcell_guid)
            self.helper_cloud_admin.company_id = self.helper_cloud_user1.company_id
            validity = datetime.now()
            validity = validity + timedelta(days=1)
            validity = validity.strftime("%Y-%m-%d-%H-%M-%S")
            _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                    2,
                                                                    validity=validity,
                                                                    comments=self.CommentsForApproveDenyRevoke)
            self.log.info("Approve of access request was done successfully")
            set_folder_name = self.helper_cloud_user1.get_available_set_folders_of_a_commcell()[-1]
            custom_set_path = self.local_machine.join_path(self.utility.get_drive(self.local_machine),
                                                           "DownloadDRDumpPath")
            try:
                self.local_machine.create_directory(custom_set_path, force_create=True)
                self.log.info('Download folder creation is successful for {}'.format(self.helper_cloud_user1.commcell_guid))
            except Exception as exception:
                self.log.info('Download folder creation is not successful for {}'.format(self.helper_cloud_user1.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise exception
            try:
                self.helper_cloud_user1.download_from_cvcloud(set_folder_name, custom_set_path)
                self.log.info('Download was successful for {}'.format(self.helper_cloud_user1.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
            except:
                self.log.info('Download was not successful for {}'.format(self.helper_cloud_user1.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise Exception('Download was not successful for {}. Test case has failed'.format(self.helper_cloud_user1.commcell_guid))

            #Do the same process as above for CloudUser2 for a different commcell
            companyname_companyid_commcellguid_commcellid = self.helper_cloud_user2.get_companyname_companyid_commcellguid_commcellid()
            self.helper_cloud_user2.company_name, self.helper_cloud_user2.company_id, \
            self.helper_cloud_user2.commcell_guid,  self.helper_cloud_user2.commcell_id = companyname_companyid_commcellguid_commcellid[0]
            request_id = self.helper_cloud_user2.request_access(self.CommentsForAccess)
            self.log.info('Request for Access of .dmp files for commcell %s was sent successfully'
                          % self.helper_cloud_user2.commcell_guid)
            self.helper_cloud_admin.company_id = self.helper_cloud_user2.company_id
            validity = datetime.now()
            validity = validity + timedelta(days=1)
            validity = validity.strftime("%Y-%m-%d-%H-%M-%S")
            _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                    2,
                                                                    validity=validity,
                                                                    comments=self.CommentsForApproveDenyRevoke)
            self.log.info("Approving of access request was done successfully for {}".format(self.helper_cloud_user2.commcell_guid))
            set_folder_name = self.helper_cloud_user2.get_available_set_folders_of_a_commcell()[-1]
            custom_set_path = self.local_machine.join_path(self.utility.get_drive(self.local_machine),
                                                           "DownloadDRDumpPath")
            try:
                self.local_machine.create_directory(custom_set_path, force_create=True)
                self.log.info('Download folder creation is successful for {}'.format(self.helper_cloud_user2.commcell_guid))
            except Exception as exception:
                self.log.info('Download folder creation is not successful for {}'.format(self.helper_cloud_user2.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise exception
            try:
                self.helper_cloud_user2.download_from_cvcloud(set_folder_name, custom_set_path)
                self.log.info('Download was successful for {}'.format(self.helper_cloud_user2.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
            except Exception as exception:
                self.log.info('Download was not successful for {}'.format(self.helper_cloud_user2.commcell_guid))
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise exception

            companyname_companyid_commcellguid_commcellid = self.helper_cloud_user1.get_companyname_companyid_commcellguid_commcellid()
            self.UserCommcellAssociation[self.tcinputs.get("CloudUser1UserName")] = [i[-1] for i in companyname_companyid_commcellguid_commcellid]
            companyname_companyid_commcellguid_commcellid = self.helper_cloud_user2.get_companyname_companyid_commcellguid_commcellid()
            self.UserCommcellAssociation[self.tcinputs.get("CloudUser2UserName")] = [i[-1] for i in companyname_companyid_commcellguid_commcellid]
            for user in self.UserCommcellAssociation:
                allowedCommcells = self.UserCommcellAssociation.get(user)
                if len(allowedCommcells) == 0:
                    self.log.info("No Commcells found for user {}".format(user))
                    raise Exception
                if user.lower() == self.cloud_user1_username:
                   self.helper_cloud_user1.validate_drbackup_download_history_report(self.tcinputs.get("DatasetParameters"), allowedCommcells)
                elif user.lower() == self.cloud_user2_username:
                    self.helper_cloud_user2.validate_drbackup_download_history_report(self.tcinputs.get("DatasetParameters"), allowedCommcells)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED