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


Input Example:
"testcases":    {     "71027":

                    {   "ClientName": "",
                         "SubclientName": "",
                         "Replication Target": "",
                         "BackupsetName": "",
                         "AgentName": "Virtual Server",
                         "InstanceName": "",
                         "Host": "",
                         "MediaAgent": "",
                         "Datastore": "",
                         "SnapAutomationOutput": "",
                         "Network": "VM Network",
                         "Destination network": "Original network"
                         }
                }

"""
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSAVSClient, AutoVSACommcell
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Automation of Live Mount using backupcopy for vm-ware from command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tcinputs = {
            "RecoveryTarget": None
        }
        self.tpath = None
        self.tstamp = None

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)

        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)

    def run(self):
        """Run function of this test case"""
        try:
            target = self.tcinputs['RecoveryTarget']

            auto_subclient = self.vsa_obj.auto_vsa_subclient

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if "skip_pre_backup_config" in self.tcinputs.keys():
                self.vsa_obj.run_pre_backup_config_checks = not self.tcinputs['skip_pre_backup_config']
            backup_jobid= auto_subclient.backup(backup_options)
            parent_jobid = self.vsa_obj.backup_job

            self.tpath = auto_subclient.testdata_path
            self.tstamp = auto_subclient.timestamp
            self.vsa_obj.testdata_path = self.tpath
            self.vsa_obj.timestamp = self.tstamp
            self.vsa_obj.generate_testdata = False
            self.vsa_obj.skip_testdata = True
            self.vsa_obj.cleanup_testdata_before_backup = False
            self.vsa_obj.backup_method = "SNAP"

            self.vsa_obj.vsa_discovery()

            AutoVSACommcell_obj = AutoVSACommcell(self.commcell, self.csdb)
            client = self.commcell.clients.get(self.vsa_obj.hypervisor)
            AutoVSAVSClient_obj = AutoVSAVSClient(AutoVSACommcell_obj, client)
            self.vsa_obj.auto_vsa_client = AutoVSAVSClient_obj
            AutoVSAVSClient_obj.timestamp = self.vsa_obj.timestamp
            AutoVSAVSClient_obj.backup_folder_name = self.vsa_obj.backup_folder_name


            target_summary = self.vsa_obj.get_target_summary(target)
            target_client_DN = target_summary['Destination hypervisor']
            target_client = self.vsa_obj.get_client_name_from_display_name(target_client_DN)
            destination_hvobj = self.vsa_obj._create_hypervisor_object(target_client)[0]
            self.vsa_obj.rep_target_dict = target_summary
            self.vsa_obj.restore_destination_client = destination_hvobj

            vm_names, live_mount_jobs = self.vsa_obj.live_mount(target)

            AutoVSAVSClient_obj.live_mount_validation(None,
                                                      destination_hvobj,
                                                      live_mount_jobs,
                                                      vm_names,
                                                      rep_target_summary=self.vsa_obj.rep_target_dict,
                                                      source_hvobj=self.vsa_obj.hvobj)
            self.vsa_obj.delete_snap_array(parent_jobid)
        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.log.info('Failed with error: ' + str(exp))

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
