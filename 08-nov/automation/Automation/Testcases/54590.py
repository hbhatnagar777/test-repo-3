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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    set_v1_indexing()           -- sets v1 indexing

    create_proxy_client_source  --  Creates a vcenter client on source commcell

    create_proxy_client_dest    --  Creates a vcenter client on destination commcell

    ccm_export()                --  Function to perform CCM Export.

    import_setup()              --  Function to setup import options for CCM Import.

    ccm_import()                --  Function to perform CCM Import.

    verify_import()             --  Function to verify entities migrated during Commcell Migration.

    tear_down()                 --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from datetime import datetime, timezone
from cvpysdk.constants import VSAObjects
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
        self.name = "VSA V1 : CCM validation for VSA client"
        self.time = None
        self.tcinputs = {
            "vcenter_hostname": None,
            "vcenter_username": None,
            "vcenter_password": None,
            "vm_name": None,
            "storage_policy": None,
            "exportLocation": None,
            "exportPathType": None,
            "exportUserName": None,
            "exportPassword": None,
            "importLocation": None,
            "disk_restore_path": None,
            "destinationCommcellHostname": None,
            "destinationCommcellUsername": None,
            "destinationCommcellPassword": None,
        }

    @property
    def get_time(self):
        """Function to get current time."""
        if not self.time:
            self.time = datetime.now()
            self.time = self.time.replace(tzinfo=timezone.utc).timestamp()
        return self.time

    def set_v1_indexing(self):
        """Set v1 indexing"""
        self.commcell.add_additional_setting('CommServDB.GxGlobalParam', 'UseIndexingV2forNewVSAClient', 'BOOLEAN',
                                             'false')

    def ccm_export(self):
        """Function to run CCM Export."""
        options = {
            "pathType": self.tcinputs["exportPathType"],
            "userName": self.tcinputs["exportUserName"],
            "password": self.tcinputs["exportPassword"],
            "captureMediaAgents": False
        }

        export_job = self.CCM_helper.run_ccm_export(self.tcinputs["exportLocation"],
                                                    [self.pseudo_client_source_name], options=options)

        self.log.info("Started CCM Export Job: %s", export_job.job_id)

        if export_job.wait_for_completion():
            self.log.info("CCM Export Job id %s "
                          "completed successfully", export_job.job_id)
        else:
            self.log.error("CCM Export Job id %s "
                           "failed/ killed", export_job.job_id)
            raise Exception("CCM Export job failed")

    def import_setup(self):
        """Function to setup import options requried to perform CCM import."""
        self.destination_cs = self.CCM_helper.create_destination_commcell(
            self.tcinputs["destinationCommcellHostname"],
            self.tcinputs["destinationCommcellUsername"],
            self.tcinputs["destinationCommcellPassword"]
        )
        self.log.info("Successfully created and logged into destination commcell {}".format(
            self.destination_cs.commserv_name))

    def ccm_import(self):
        """Function to perform CCM Import."""
        options = {
            'forceOverwrite': True
        }

        import_job = self.CCM_helper.run_ccm_import(
            self.tcinputs["importLocation"],
            options=options
        )
        self.log.info("Started CCM Import Job: %s", import_job.job_id)

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id %s "
                          "completed successfully", import_job.job_id)
        else:
            self.log.error("CCM Import Job id %s "
                           "failed/ killed", import_job.job_id)
            raise Exception("CCM Import job failed")

        self.CCM_helper.set_libary_mapping(self.commcell.commserv_name)
        self.log.info("Library Mapping successfully completed")

    def create_pseudo_client_source(self):
        self.pseudo_client_source_name = "pseudo_client_source_{}".format(self.get_time)
        self.pseudo_client_source = self.commcell.clients.add_vmware_client(self.pseudo_client_source_name,
                                                                            self.tcinputs["vcenter_hostname"],
                                                                            self.tcinputs["vcenter_username"],
                                                                            self.tcinputs["vcenter_password"],
                                                                            [self.commcell.commserv_hostname])
        self.subclients_source = self.pseudo_client_source.agents.get('Virtual Server').instances.get(
            'VMware').backupsets.get(
            'defaultBackupSet').subclients
        storage_policy = self.tcinputs["storage_policy"]
        self.subclients_source = self.subclients_source.add_virtual_server_subclient('sub-1',
                                                                                     [{
                                                                                         'equal_value': True,
                                                                                         'allOrAnyChildren': True,
                                                                                         'display_name': self.tcinputs[
                                                                                             "vm_name"],
                                                                                         'type': VSAObjects.VMName
                                                                                     }],
                                                                                     storage_policy=storage_policy)

    def create_pseudo_client_destination(self):
        """Creates a VMware pseudo client on destination commcell."""
        self.pseudo_client_dest_name = "pseudo_client_dest_{}".format(self.get_time)
        self.pseudo_client_dest = self.destination_cs.clients.add_vmware_client(self.pseudo_client_dest_name,
                                                                                self.tcinputs["vcenter_hostname"],
                                                                                self.tcinputs["vcenter_username"],
                                                                                self.tcinputs["vcenter_password"],
                                                                                [self.destination_cs.commserv_hostname])

    def verify_import(self):
        """Verifies CCM Import was successful."""
        subclient_dest, backupset_dest = self.CCM_helper.get_latest_subclient(self.pseudo_client_source_name,
                                                                              destination_commcell=True,
                                                                              agent=constants.Agents.VIRTUAL_SERVER)
        job2 = subclient_dest.full_vm_restore_out_of_place(vcenter_client=self.pseudo_client_dest_name,
                                                           proxy_client=self.destination_cs.commserv_hostname)
        if not job2.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup with error: {0}".format(job2.delay_reason)
            )
        else:
            self.log.info("Backup job: %s completed successfully", job2.job_id)

        job3 = subclient_dest.disk_restore(vm_name=self.tcinputs["vm_name"],
                                           destination_path=self.tcinputs["disk_restore_path"],
                                           proxy_client=self.destination_cs.commserv_hostname)

        if not job3.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup with error: {0}".format(job3.delay_reason)
            )
        else:
            self.log.info("Backup job: %s completed successfully", job3.job_id)

    def setup(self):
        """Setup function of this test case"""
        self.CCM_helper = CCMHelper(self)

    def run(self):
        """Run function of this test case"""
        try:
            self.set_v1_indexing()
            self.create_pseudo_client_source()
            self.log.info("Successfully created pseudo client {}".format(self.pseudo_client_source_name))
            self.log.info("Setting V1 indexing for the pseudo client")
            job1 = self.subclients_source.backup()
            self.log.info("Started backup job {}".format(job1.job_id))
            if not job1.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(job1.delay_reason)
                )
            else:
                self.log.info("Backup job: %s completed successfully", job1.job_id)

            self.ccm_export()
            self.import_setup()
            self.ccm_import()
            self.create_pseudo_client_destination()
            self.log.info("Successfully created pseudo client {}".format(self.pseudo_client_dest_name))
            self.verify_import()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.commcell.clients.has_client(self.pseudo_client_source_name):
            self.commcell.clients.delete(self.pseudo_client_source_name)

        if self.destination_cs.clients.has_client(self.pseudo_client_source_name):
            self.destination_cs.clients.delete(self.pseudo_client_source_name)

        if self.destination_cs.clients.has_client(self.pseudo_client_dest_name):
            self.destination_cs.clients.delete(self.pseudo_client_dest_name)

        self.machine_object = OptionsSelector(self.commcell).get_machine_object(self.destination_cs.commserv_client)
        self.machine_object.delete_file("{}\\*".format(self.tcinputs["disk_restore_path"]))
