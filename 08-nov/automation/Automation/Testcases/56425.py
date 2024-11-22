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
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from datetime import datetime, timezone


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Backup Validation test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware Backup validation from Command center with PIT and recovery target"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
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

    def run(self):
        """Main function for test case execution"""

        try:
            backup_validation_options = {
                'recovery_target': self.tcinputs["recovery_target"],
                'retain_vms': True
            }

            # Verify if the virtual lab option - "Configure existing network" is selected in the target
            # This would enable the live mounted VMs to boot up in network connected state and reachable
            target = self.tcinputs['recovery_target']
            target_summary = self.vsa_obj.get_target_summary(target)
            if not target_summary.get("Existing network"):
                raise Exception("[Configure existing network] option is NOT selected in the target")

            _backup_jobs = []
            self.vsa_obj.setup_backup_validation(backup_validation_options)

            # Run INCR1
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()
            _backup_jobs.append({
                'backup_job': self.vsa_obj.backup_job_obj,
                'time_stamp': self.vsa_obj.timestamp
            })

            self.vsa_obj.refresh_vmgroup_content = False
            self.vsa_obj.testdata_path = None
            self.vsa_obj.cleanup_testdata_before_backup = False

            # Run INCR2
            self.vsa_obj.backup()
            _backup_jobs.append({
                'backup_job': self.vsa_obj.backup_job_obj,
                'time_stamp': self.vsa_obj.timestamp
            })

            self.vsa_obj.timestamp = _backup_jobs[0]['time_stamp']
            self.vsa_obj.testdata_path = self.vsa_obj.controller_machine.os_sep.join(
                self.vsa_obj.testdata_path.split(self.vsa_obj.controller_machine.os_sep)[:-1] + [
                    _backup_jobs[0]['time_stamp']])

            # Run validation for point in time INCR1
            point_in_time = datetime.strptime(_backup_jobs[0]['backup_job'].start_time, "%Y-%m-%d %H:%M:%S")
            point_in_time = point_in_time.replace(tzinfo=timezone.utc).astimezone()
            point_in_time = datetime.strftime(point_in_time, "%#I:%M %p")

            backup_validation_options['recovery_point'] = point_in_time
            self.vsa_obj.validate_testdata_on_live_mount = True
            self.vsa_obj.run_validate_backup_vmgroup(backup_validation_options)

        except Exception as exp:
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
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
