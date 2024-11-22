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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    create_sql_object()     --  creates SQL object for the commcell

    enable_v2_indexing()    --  enables or disables v2 indexing

    create_pseudo_client()  --  creates a vmware client

    get_media_list()        --  Retrieves media list from tape library created.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from cvpysdk.constants import VSAObjects
from datetime import datetime, timezone
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "TAPE_IMPORT_FOR_MISSING_VSA_JOBS"
        self.time = None
        self.tcinputs = {
            "proxy_client": None,
            "tape_library": None,
            "vcenter_hostname": None,
            "vcenter_username": None,
            "vcenter_password": None,
            "vm1": None,
            "vm2": None
        }

    @property
    def get_time(self):
        """Function to get current time."""
        if not self.time:
            self.time = datetime.now()
            self.time = self.time.replace(tzinfo=timezone.utc).timestamp()
        return self.time

    def enable_v2_indexing(self, bool):
        """Enables or Disables V2 indexing."""
        self.commcell.add_additional_setting('CommServDB.GxGlobalParam', 'UseIndexingV2forNewVSAClient', 'BOOLEAN',
                                             'true' if bool else 'false')

    def get_media_list(self, subclient):
        """
        Retrieves media list from tape library created.
                subclient       (object)        --  subclient object created
        """
        return self.CCM_helper.get_barcode_list(subclient.subclient_id)

    def create_pseudo_client_1(self):
        """Creates a VMware pseudo client."""
        self.pseudo_client_1_name = "pseudo_client_1_{}".format(self.get_time)
        self.pseudo_client_1 = self.commcell.clients.add_vmware_client(self.pseudo_client_1_name,
                                                                       self.tcinputs["vcenter_hostname"],
                                                                       self.tcinputs["vcenter_username"],
                                                                       self.tcinputs["vcenter_password"],
                                                                       [self.tcinputs["proxy_client"]])
        self.subclients_1 = self.pseudo_client_1.agents.get('Virtual Server').instances.get('VMware').backupsets.get(
            'defaultBackupSet').subclients
        storage_policy = self.tape_storage_policy
        self.subclient_1 = self.subclients_1.add_virtual_server_subclient('sub-1',
                                                                          [{
                                                                              'equal_value': True,
                                                                              'allOrAnyChildren': True,
                                                                              'display_name': self.tcinputs["vm1"],
                                                                              'type': VSAObjects.VMName
                                                                          }],
                                                                          storage_policy=storage_policy)

    def create_pseudo_client_2(self):
        """Creates a VMware pseudo client."""
        self.pseudo_client_2_name = "pseudo_client_2_{}".format(self.get_time)
        self.pseudo_client_2 = self.commcell.add_vmware_client(self.pseudo_client_2_name,
                                                               self.tcinputs["vcenter_hostname"],
                                                               self.tcinputs["vcenter_username"],
                                                               self.tcinputs["vcenter_password"],
                                                               [self.tcinputs["proxy_client"]])
        self.subclients_2 = self.pseudo_client_2.agents.get('Virtual Server').instances.get('VMware').backupsets.get(
            'defaultBackupSet').subclients
        storage_policy = self.tape_storage_policy
        self.subclient_2 = self.subclients_2.add_virtual_server_subclient('sub-2',
                                                                          [{
                                                                              'equal_value': True,
                                                                              'allOrAnyChildren': True,
                                                                              'display_name': self.tcinputs["vm2"],
                                                                              'type': VSAObjects.VMName
                                                                          }],
                                                                          storage_policy=storage_policy)

    def setup(self):
        """Setup function of this test case"""
        self.CCM_helper = CCMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        tape_library = self.tcinputs["tape_library"]
        query = """select top 1 DrivePoolName from MMdrivepool where MasterPoolId in 
                        (select MasterPoolId from MMMasterPool where libraryid in
                            (select LibraryId from MMLibrary where AliasName  ='{0}'))""".format(tape_library)

        result = self.options_selector.exec_commserv_query(query)
        drivepool_name = str(result[1][0][0])
        self.tape_storage_policy = self.commcell.storage_policies.add_tape_sp("tape_sp_{}".format(self.get_time),
                                                                              tape_library,
                                                                              self.CCM_helper.get_active_mediaagent(),
                                                                              drivepool_name,
                                                                              'Default Scratch')

    def run(self):
        """Run function of this test case"""
        try:
            self.enable_v2_indexing(False)
            self.create_pseudo_client_1()
            job1 = self.subclient_1.backup()
            if not job1.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
                )
            else:
                self.log.info("Backup job: %s completed successfully", job1.job_id)

            self.enable_v2_indexing(True)
            self.create_pseudo_client_2()
            job2 = self.subclient_2.backup()
            if not job2.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job2.delay_reason)
                )
            else:
                self.log.info("Backup job: %s completed successfully", job2.job_id)

            media_list_1 = self.get_media_list(self.subclient_1)
            media_list_2 = self.get_media_list(self.subclient_2)

            self.subclients_1.delete("sub-1")
            self.subclients_2.delete("sub-2")
            self.commcell.run_data_aging()
            self.CCM_helper.tape_import(media_list_1 + media_list_2)

            new_subclient, new_backupset = self.CCM_helper.get_latest_subclient(client_name=self.pseudo_client_2_name,
                                                                                agent=constants.Agents.VIRTUAL_SERVER)
            new_subclient.full_vm_restore_in_place()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
