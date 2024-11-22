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

    setup()         --  initial setup for testcase

    start_preupgrade()  executes steps that need to run before upgrade

    perform_backup()--  performs backups

    write_to_json() --  constructs/edits dictionary to save in json

    postupgrade_setup()-- setup for postupgrade section of testcase

    start_postupgrade()-- runs postupgrade testcase

    perform_restore()--  performs restores for jobs saved in json

    run()           --  run function of this test case
"""
import os, json
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log, subclient_initialize
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing basic testcase for Backup and restore for Azure RM in admin Console"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Upgrade Testcase"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.jsondata = {}

    def setup(self):
        """settingup tc variables"""
        if self.tcinputs['preupgrade'] or self.tcinputs['preupgrade'] == 'true':
            self.preupgrade = True
        else:
            self.preupgrade = False

        if self.tcinputs['postupgrade'] or self.tcinputs['postupgrade'] == 'true':
            self.postupgrade = True
        else:
            self.postupgrade = False

    def start_preupgrade(self):
        """ runs pre upgrade case"""
        try:
            VirtualServerUtils.decorative_log("Starting pre-ugrade case")
            path_to_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.file_path = path_to_file + "\\" + self.commcell.commserv_name + "upgrade_case.json"
            if os.path.isfile(self.file_path):
                with open(self.file_path, 'r+') as file:
                    self.jsondata = json.load(file)
                    file.close()
            else:
                self.jsondata = {}

            self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
            self.perform_backup("FULL")
            self.write_to_json(backup_type=self.backup_options.backup_type,
                               backup_job_id=self.backup_options.backup_job.job_id,
                               testpath=self.auto_subclient.testdata_path)
            self.auto_subclient.testdata_path = None
            self.auto_subclient.testdata_paths = []
            self.perform_backup("INCREMENTAL")
            self.write_to_json(backup_type=self.backup_options.backup_type,
                               backup_job_id=self.backup_options.backup_job.job_id,
                               testpath=self.auto_subclient.testdata_path)
            self.auto_subclient.testdata_path = None
            self.auto_subclient.testdata_paths = []
            self.perform_backup("SYNTHETIC_FULL")
            self.write_to_json(backup_type=self.backup_options.backup_type,
                               backup_job_id=self.auto_subclient.backup_job.job_id,
                               testpath=self.auto_subclient.testdata_path)
            ofile = open(self.file_path, 'w+')
            ofile.write(json.dumps(self.jsondata, indent=4))
            ofile.close()

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def perform_backup(self, backup_type):
        """ performs backup given backup type
        backup_type (str) -- FULL/INCREMENTAL/SYNTHETIC FULL
        """

        VirtualServerUtils.decorative_log("Backup")
        self.backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
        _adv = {"create_backup_copy_immediately": True,
                'backup_copy_type': 'USING_LATEST_CYLE'}
        self.backup_options.advance_options = _adv
        self.backup_options.backup_method = "SNAP"
        self.backup_options.backup_type = backup_type
        self.auto_subclient.backup(self.backup_options)
        self.log.info("backup job id {0}, testdatapath{1}".format(self.backup_options.backup_job.job_id,
                                                                  self.backup_options.testdata_path))
        self.log.info(self.auto_subclient.testdata_path)
        # self.auto_subclient.post_backup_validation(validate_workload=False, skip_snapshot_validation=False,
        #                                            validate_cbt=False)

    def write_to_json(self, backup_type, backup_job_id, testpath):
        """ constructs/edits json entries
        input:
            backup_type     (str)
            backup_job_id   (str)
            testpath        (str)
        """

        try:
            if self.jsondata.get("Agent"):
                if self.jsondata.get("Agent", {}).get(self.instance.name.replace(" ", "")):
                    self.jsondata['Agent'][self.instance.name.replace(" ", "")][backup_type] = {
                        'jobid': backup_job_id, 'testpath': testpath}
                else:
                    self.jsondata['Agent'][self.instance.name.replace(" ", "")] = {backup_type: {}}
                    self.write_to_json(backup_type, backup_job_id, testpath)
            else:
                self.jsondata = {"Agent": {self.instance.name.replace(" ", ""): {backup_type: {}}}}
                self.write_to_json(backup_type, backup_job_id, testpath)
        except Exception as err:
            self.log.exception("JSON writing error, check file")

    def postupgrade_setup(self):
        """ sets up post upgrade case basics"""
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open(maximize=True)
            self.log.info("Creating the login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                self.inputJSONnode['commcell']['commcellPassword'])

            self.log.info("Login completed successfully")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            self.vsa_obj_inputs = {
                'hypervisor': self.tcinputs['ClientName'],
                'instance': self.tcinputs['InstanceName'],
                'subclient': self.tcinputs['SubclientName'],
                'storage_account': self.tcinputs.get('StorageAccount', None),
                'resource_group': self.tcinputs.get('ResourceGroup', None),
                'region': self.tcinputs.get('Region', None),
                'managed_vm': self.tcinputs.get('ManagedVM', False),
                'disk_type': self.tcinputs.get('DiskType', None),
                'availability_zone': self.tcinputs.get('AvailabilityZone', "Auto"),
                'snapshot_rg': self.tcinputs.get('SnapshotRG', None),
                'subclient_obj': self.subclient,
                'testcase_obj': self,
                'auto_vsa_subclient': subclient_initialize(self),
                "destination_datastore": self.tcinputs.get('destination_datastore', None),
                "destination_host": self.tcinputs.get('destination_host', None),
                "restore_network": self.tcinputs.get('network', None),  # for nutanix
                "storage_container": self.tcinputs.get('storageContainer', None),  # for nutanix
                "restore_proxy_input": self.tcinputs.get('restoreProxy', None)  # for nutanix
            }
            self.log.info("Reading upgrade json")
            path_to_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.file_path = path_to_file + "\\" + self.commcell.commserv_name + "upgrade_case.json"
            f = open(self.file_path, "r")
            self.jsondata = json.loads(f.read())
            self.log.info("Json read done")
        except Exception as err:
            handle_testcase_exception(self, err)

    def start_postupgrade(self):
        """ runs post upgrade case"""
        try:
            VirtualServerUtils.decorative_log("Starting post upgrade testcase")
            self.postupgrade_setup()
            self.perform_restore("FULL")
            self.perform_restore("FULL", snap_restore=True)
            self.perform_restore("INCREMENTAL")
            self.perform_restore("INCREMENTAL", snap_restore=True)
            self.perform_restore('SYNTHETIC_FULL', snap_restore=None)
        except Exception as exp:
            handle_testcase_exception(self, exp)

        try:
            VirtualServerUtils.decorative_log("Final Incremental")
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup_method = "SNAP"
            self.vsa_obj.cleanup_testdata_before_backup = True
            self.vsa_obj.generate_testdata = True
            self.vsa_obj.skip_testdata = False
            self.vsa_obj.backup()
            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.full_vm_in_place = False
            self.vsa_obj.restore_from_job = self.vsa_obj.backup_job
            self.vsa_obj.snap_restore = False
            self.vsa_obj.full_vm_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def perform_restore(self, backup_type, snap_restore=False):
        """ performs restore from jobs stored in json"""
        VirtualServerUtils.decorative_log("Performing restore from job type {0}".format(backup_type))
        set_inputs(self.vsa_obj_inputs, self.vsa_obj)
        self.vsa_obj.backup_type = backup_type
        self.vsa_obj.testdata_path = self.jsondata["Agent"][self.instance.name.replace(" ", "")][backup_type][
            'testpath']
        self.vsa_obj.backup_job = self.jsondata["Agent"][self.instance.name.replace(" ", "")][backup_type][
            'jobid']

        self.vsa_obj.cleanup_testdata_before_backup = False
        self.vsa_obj.generate_testdata = False
        self.vsa_obj.skip_testdata = True
        bkup_job_obj = self.vsa_obj.backup_job_obj
        self.log.info("Running vsa discovery")
        self.vsa_obj.vsa_discovery()

        # Full VM out of Place restore
        self.log.info("Running restore from backup job")
        self.vsa_obj.unconditional_overwrite = True
        self.vsa_obj.full_vm_in_place = False
        self.vsa_obj.restore_from_job = self.vsa_obj.backup_job
        self.vsa_obj.snap_restore=snap_restore
        # vsa_obj.validation=False
        self.vsa_obj.full_vm_restore()

    def run(self):
        """"Main function for testcase execution"""

        if self.preupgrade:
            try:
                self.log.info("Started executing %s testcase", self.id)
                self.start_preupgrade()
            except Exception as exp:
                self.log.error('Error in pre-upgrade: %s', str(exp))
                self.result_string = str(exp)
                self.status = constants.FAILED

        elif self.postupgrade:
            self.log.info("in postupgrade")
            decorative_log("out of Place Full VM Restore")
            try:
                self.log.info("Started executing %s testcase", self.id)
                decorative_log("Initialize browser objects")
                self.start_postupgrade()
            except Exception as exp:
                self.log.error('Error in post-upgrade: %s', str(exp))
                self.result_string = str(exp)
                self.status = constants.FAILED
                handle_testcase_exception(self,exp)
            finally:
                AdminConsole.logout_silently(self.admin_console)
                Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            if self.preupgrade:
                self.log.info("This is preuprgrade, nothing to cleanup/teardown")
                if self.status == constants.PASSED:
                    self.log.info("Preuprgrade test completed successfully")
            if self.postupgrade:
                if self.vsa_obj:
                    self.log.info("postcleanup")
                    if self.status == constants.PASSED:
                        self.log.info("Postuprgrade test completed successfully. Now cleaning up.")
                        self.vsa_obj.cleanup_testdata()
                    self.vsa_obj.post_restore_clean_up(status=True if self.status == constants.PASSED else False)
                self.log.warning("Testcase and/or Restored VM cleanup was not completed")
                pass
        except Exception as exp:
            self.log.info("Exception in teardown {0}".format(exp))
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
