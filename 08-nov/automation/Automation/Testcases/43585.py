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

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper


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
        self.destination_cs = None
        self.ccm_helper = None
        self.client1 = None
        self.name = "POST CCM NAME CHANGE VALIDATION"
        self.tc = self.inputJSONnode["testsets"]["testCases"]["43585"]

    def backup_client(self):
        """Create entities required and run a backup job for a client on source cs."""
        mountpath_location = self.tc["mountpath_location"]
        mountpath_username = self.tc["mountpath_username"]
        mountpath_password = self.tc["mountpath_password"]
        self.ccm_helper.create_entities(mountpath_location,
                                        mountpath_username,
                                        mountpath_password)

    def ccm_export(self):
        """Run ccm export for a client on source cs."""
        export_location = self.tc["export_location"]
        export_location_username = self.tc["export_location_username"]
        export_location_password = self.tc["export_location_password"]
        options = {
            "pathType": "Network",
            "userName": export_location_username,
            "password": export_location_password
        }

        export_job = self.ccm_helper.run_ccm_export(export_location,
                                                    [self.client1],
                                                    options=options)

        if not export_job.wait_for_completion():
            self.log.info("CCM Export Job {} completed successfully".format(export_job.job_id))

        else:
            raise Exception("CCM Export job {} failed with error: {}".format(export_job.job_id,
                                                                             export_job.error_msg))

    def ccm_import(self):
        """Run ccm import on destination cs."""
        destination_cs_name = self.tc["destination_cs_name"]
        destination_cs_username = self.tc["destination_cs_username"]
        destination_cs_password = self.tc["destination_cs_password"]
        self.destination_cs = self.ccm_helper.create_destination_commcell(destination_cs_name,
                                                                          destination_cs_username,
                                                                          destination_cs_password)
        import_location = self.tc["import_location"]
        import_job = self.ccm_helper.run_ccm_import(import_location)

        if not import_job.wait_for_completion():
            self.log.info("CCM Export Job {} completed successfully".format(import_job.job_id))

        else:
            raise Exception("CCM Export job {} failed with error: {}".format(import_job.job_id,
                                                                             import_job.error_msg))

    def name_change(self):
        """Perform name change for imported clients on destination cs."""
        parameters_dict = {
            "sourceCommcellHostname": self.commcell.commserv_name,
            "destinationCommcellHostname": self.destination_cs.commserv_name,
            "clientIds": [self.destination_cs.clients.get(self.client1).client_id]
        }
        if self.commcell.name_change.name_change_post_ccm(parameters_dict):
            self.log.info("Name change for client {} completed successfully".format(self.client1))

        else:
            raise Exception("Name Change failed for client {}".format(self.client1))

    def restore_on_source(self):
        """Perform restore for the client on source cs post ccm name change."""
        subclient, bkpset = self.ccm_helper.get_latest_subclient(client_name=self.client1)
        restore_job = self.ccm_helper.restore_by_job(bkpset, self.ccm_helper.get_jobs_for_subclient(subclient))
        if not restore_job.wait_for_completion():
            self.log.info("Restore job {} completed successfully for client {} on source cs".format(restore_job.job_id,
                                                                                                    self.client1))
        else:
            raise Exception("Restore job {} failed on source cs".format(restore_job.job_id))

    def backup_on_dest(self):
        """Perform new backup on the migrated client on destination cs post ccm name change."""
        mountpath_location_dest = None
        self.destination_cs.disk_libraries.add("new_lib_on_dst",
                                               self.destination_cs.commserv_name,
                                               mountpath_location_dest)
        self.destination_cs.storage_policies.add("new_sp_on_dst",
                                                 "new_lib_on_dst")
        subclient = self.destination_cs.subclients.add("sub1", "new_sp_on_dst")
        backup_job = subclient.backup()
        if not backup_job.wait_for_completion():
            self.log.info("Restore job {} completed successfully for client {} on source cs".format(backup_job.job_id,
                                                                                                    self.client1))
        else:
            raise Exception("Restore job {} failed on source cs".format(backup_job.job_id))

    def setup(self):
        """Setup function of this test case"""
        self.ccm_helper = CCMHelper(self)

    def run(self):
        """Run function of this test case"""
        try:
            self.backup_client()
            self.ccm_export()
            self.ccm_import()
            self.name_change()
            self.restore_on_source()
            self.backup_on_dest()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
