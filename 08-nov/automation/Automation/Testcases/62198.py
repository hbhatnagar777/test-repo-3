# -*- coding: utf-7 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    tear_down()         --  tear down function of this test case.

    init_tc()           --  Initialization function for the test case.
"""

from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper


class TestCase(CVTestCase):
    """Class for executing the test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "TAPE_IMPORT_WITH_UNSUPPORTED_IDA"
        self.sp_client_object = None
        self.tcinputs = {
            "TapeLibrary": None,
            "ClientName": None,
            "PseudoClientName": None,
            "IndexServer": None,
            "AccessNodes": None,
            "TenantUrl": None,
            "UserName": None,
            "Password": None,
            "AzureAppId": None,
            "AzureAppKeyValue": None,
            "AzureDirectoryId": None,
            "AzureUserName": None,
            "AzureSecret": None,
            "SiteUrl": None,
            "Office365Plan": None
        }

    def init_tc(self):
        """ Initialization function for the test case. """
        self.log.info('Creating SharePoint client object.')
        self.sp_client_object = SharePointOnline(self)
        self.sp_client_object.initialize_sp_v2_client_attributes()
        self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                  int(self.sp_client_object.cvoperations.get_plan_obj
                                                      (self.tcinputs.get('Office365Plan')).plan_id))]
        self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
        self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
        self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
        self.log.info('SharePoint client object created.')

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.CCM_helper = CCMHelper(self)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])
            self.sp_client_object.cvoperations.run_backup()

            self.CCM_helper.create_entities(tape_library=self.tcinputs["TapeLibrary"])
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"])
            media_list = self.CCM_helper.get_barcode_list(new_subclient.subclient_id)
            self.CCM_helper.clean_entities()
            self.commcell.run_data_aging()
            self.CCM_helper.tape_import(media_list)
            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(self.tcinputs["ClientName"])
            job = new_backupset.restore_out_of_place(client=self.client,
                                                     destination_path=self.tcinputs["RestoreFolder"],
                                                     paths=[],
                                                     fs_options={"index_free_restore": True},
                                                     restore_jobs=self.CCM_helper.get_jobs_for_subclient(new_subclient))
            if not job.wait_for_completion():
                raise Exception("Restore Job with id {} failed with message {}".format(job.job_id,
                                                                                       job.delay_reason))

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(
                self.sp_client_object.pseudo_client_name)
