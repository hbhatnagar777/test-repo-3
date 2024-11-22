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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.DisasterRecovery.drmanagement_helper import DRCommvaultCloudManagement, CreateCommcellInstance


class TestCase(CVTestCase):
    """Check that user is able to download the database dump files once the access is granted.
       Also check that user is able to download dumps from only the Commcell he has access to.
       User should be able to download database dump files for the granted Commcell.
       User should have access to download database dumps for the Commcell he has access to.
       If request is denied, download should fail.
       """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Download from only approved Commcell"
        self.tcinputs = {
            "CloudAdminUserName": None,
            "CloudAdminPassword": None,
            "ApprovalStatus": None,
        }
        self.cloud_admin_commcell = None
        self.helper_cloud_admin = None
        self.helper_cloud_user = None
        self.CommentsForAccess = "Please, give download access!"
        self.CommentsForApproveDenyRevoke = "Yes, you may."
        self.local_machine = Machine()

    def setup(self):
        """Setup function of this test case"""
        self.cloud_admin_commcell = CreateCommcellInstance(self.commcell.webconsole_hostname,
                                                           self.tcinputs.get('CloudAdminUserName'),
                                                           self.tcinputs.get('CloudAdminPassword'))()
        self.helper_cloud_user = DRCommvaultCloudManagement(self.commcell)
        self.helper_cloud_admin = DRCommvaultCloudManagement(self.cloud_admin_commcell)
        self.utility = OptionsSelector(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            companyname_companyid_commcellguid = self.helper_cloud_user.get_companyname_companyid_commcellguid()
            self.helper_cloud_user.company_name, self.helper_cloud_user.company_id, \
            self.helper_cloud_user.commcell_guid = companyname_companyid_commcellguid[0]
            request_id = self.helper_cloud_user.request_access(self.CommentsForAccess)
            self.log.info('Request for Access of .dmp files for commcell %s was sent successfully'
                          % self.helper_cloud_user.commcell_guid)
            self.helper_cloud_admin.company_id = self.helper_cloud_user.company_id
            _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                    self.tcinputs.get("ApprovalStatus"),
                                                                    comments=self.CommentsForApproveDenyRevoke)
            self.log.info("Approve/Deny/Revoke of access request was done successfully")
            set_folder_name = self.helper_cloud_user.get_available_set_folders_of_a_commcell()[-1]
            custom_set_path = self.local_machine.join_path(self.utility.get_drive(self.local_machine),
                                                           "DownloadDRDumpPath")
            try:
                self.local_machine.create_directory(custom_set_path, force_create=True)
                self.log.info('Download folder creation is successful')
            except Exception as exception:
                self.log.info('Download folder creation is not successful')
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise exception
            try:
                self.helper_cloud_user.download_from_cvcloud(set_folder_name, custom_set_path)
                self.log.info('Download was successful')
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
            except:
                self.log.info('Download was not successful')
                _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                        4,
                                                                        comments=self.CommentsForApproveDenyRevoke)
                raise Exception('Download was not successful. Test case has failed')

            self.helper_cloud_user.company_name, self.helper_cloud_user.company_id, \
            self.helper_cloud_user.commcell_guid = companyname_companyid_commcellguid[1]
            request_id = self.helper_cloud_user.request_access(self.CommentsForAccess)
            self.log.info('Request for Access of .dmp files for commcell %s was sent successfully'
                          % self.helper_cloud_user.commcell_guid)
            self.helper_cloud_admin.company_id = self.helper_cloud_user.company_id
            _ = self.helper_cloud_admin.approve_deny_revoke_request(int(request_id),
                                                                    3,
                                                                    comments=self.CommentsForApproveDenyRevoke)
            self.log.info("Approve/Deny/Revoke of access request was done successfully")
            set_folder_name = self.helper_cloud_user.get_available_set_folders_of_a_commcell()[-1]
            try:
                self.local_machine.create_directory(custom_set_path, force_create=True)
                self.log.info('Download folder creation is successful')
            except Exception as exception:
                self.log.info('Download folder creation is not successful')
                raise exception
            try:
                self.helper_cloud_user.download_from_cvcloud(set_folder_name, custom_set_path)
            except:
                self.log.info('Download was not successful. Test case is successful')
            else:
                self.log.info('Download was successful. Test case has failed')
                raise Exception("Download was successful. Test case has failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
