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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.array_helper import ArrayHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log, subclient_initialize
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing Acceptance test case for Add/Edit/Delete Array in the Array Management for
        Kaminario sStorage array from Command Center"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[ARRAY MANAGEMENT] Delete snapshot from array management"
        self.admin_console = None
        self.arrayhelper_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "ArrayName": None,
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "ResourceGroup": None,
            "StorageAccount": None,
            "Region": None,
            "BackupType":None,
        }

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.arrayhelper_obj = ArrayHelper(self.admin_console, self.csdb)
        self.arrayhelper_obj.array_name = self.tcinputs['ArrayName']
        self.log.info("Login completed successfully")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj_inputs = {
            'hypervisor': self.tcinputs['ClientName'],
            'instance': self.tcinputs['InstanceName'],
            'subclient': self.tcinputs['SubclientName'],
            'resource_group': self.tcinputs.get('ResourceGroup', None),
            'region': self.tcinputs.get('Region', None),
            'backup_type': self.tcinputs.get("BackupType",'FULL'),
            'snapshot_rg': self.tcinputs.get('SnapshotRG', None),
            'subclient_obj': self.subclient,
            'testcase_obj': self,
            'auto_vsa_subclient': subclient_initialize(self)
        }

    def run(self):
        """Main function for test case execution"""

        try:
            set_inputs(self.vsa_obj_inputs, self.vsa_obj)
            self.log.info("Created VSA object successfully.")
            decorative_log("Backup")
            self.vsa_obj.backup()

            self.get_child_job_obj()

            # check for backup snapshot
            res1, res1_dict = self.vm_obj.check_disk_snapshots_by_jobid(self.child_job_obj)
            if not res1:
                raise Exception("no snap found for job {0}".format(self.child_job_obj.job_id))

            self.delete_snap()  # deleting snap from array management

            # checking if snapshot is deleted
            res2, res2_dict = self.vm_obj.check_disk_snapshots_by_jobid(self.child_job_obj)

            # validating deletion
            if res1 and not res2:
                self.log.info("Snap deletion Validated")
            else:
                raise Exception("Snap deletion failed")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def get_child_job_obj(self):
        for vm in self.vsa_obj.hvobj.VMs:
            self.vm = vm
        self.vm_obj = self.vsa_obj.auto_vsa_subclient.hvobj.VMs[self.vm]
        self.child_job_obj = Job(self.commcell, self.vsa_obj.auto_vsa_subclient.get_childjob_foreachvm(
            self.vsa_obj.backup_job)[self.vm])

    def delete_snap(self):
        decorative_log("Deleting snap for {0}".format(self.child_job_obj.job_id))
        delete_job = self.arrayhelper_obj.delete_snap_by_job(self.child_job_obj.job_id)
        del_job_obj = Job(self.commcell, delete_job)
        self.log.info("Waiting for deletion to complete")
        del_job_obj.wait_for_completion()

    def tear_down(self):
        try:
            self.log.info("In teardown")
            # self.arrayhelper_obj.action_delete_array()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
