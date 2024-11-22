# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=broad-except
# pylint: disable=C0103

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

    init_tc()       --  Initializes browser and objects required for this testcase

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import DistributedClusterPkgName
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Helper.distributed_fs_helper import DistributedHelper
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Components.panel import Backup

class TestCase(CVTestCase):
    """Class for executing
        Distributed Apps Command Center Acceptance
        This test case does the following
        Step1,  Create Server for the App.
        Step2,  Add full data for the current run.
        Step3,  Create Subclient.
        Step4,  Run a full backup for the subclient and verify it completes without failures.
        Step5,  Add new data for the incremental
        Step8,  Run an incremental backup for the subclient and verify it completes without failures.
        Step9,  Run a synthfull job
        Step10, Run a restore of the complete subclient data and verify correct data is restored.
        Step11, Delete the subclient, the server and clean up the data
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Distributed Apps Command Center Acceptance"
        self.server_name = None
        self.distributed_fs_helper = None
        self.tcinputs = {
            "DistributedClusterPkgName": None,
            "DataAccessNodes": None,
            "Plan": None,
            "TestPath": None
        }
        self.test_path = None
        self.slash_format = ''
        self.helper = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.file_size = None
        self.runid = 0
        self.cleanup_run = None
        self.pkg = None

    def setup(self):
        """Setup function of this test case"""
        self.pkg = DistributedClusterPkgName[self.tcinputs.get('DistributedClusterPkgName').upper()]
        self.server_name = "{0}_cc_{1}".format(self.pkg.value.lower(), self.id)
        self.init_tc()

    def init_tc(self):
        """Initializes browser and objects required for this testcase"""
        try:
            self.distributed_fs_helper = DistributedHelper(self, self.pkg)
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("""Distributed Apps Command Center Acceptance
                             This test case does the following
                             Step1,  Create Server for the App.
                             Step2,  Add full data for the current run.
                             Step3,  Create Subclient.
                             Step4,  Run a full backup for the subclient and verify it completes without failures.
                             Step5,  Add new data for the incremental
                             Step8,  Run an incremental backup for the subclient and verify it completes without failures.
                             Step9,  Run a synthfull job
                             Step10, Run a restore of the complete subclient data and verify correct data is restored.
                             Step11, Delete the subclient, the server and clean up the data
                             """)
            node_count = len(self.tcinputs.get('DataAccessNodes'))
            backup_stream_count = node_count * self.tcinputs.get('StreamsPerNode', 4)
            restore_stream_count = node_count * 2

            self.log.info("Step1,  Create Server for the App.")
            self.distributed_fs_helper.add_server(
                self.server_name,
                self.tcinputs.get('DataAccessNodes'),
                self.tcinputs.get('Plan'),
                self.tcinputs.get('HadoopUser', 'hdfs'))
            self.client = self.commcell.clients.get(self.server_name)
            self.agent = self.client.agents.get('Big Data Apps')
            self.instance = self.agent.instances.get(self.server_name)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            machine = self.client_machine
            plan_name = self.tcinputs.get('Plan')
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            subclient_name = "subclient_{0}".format(self.id)
            subclient_content = []
            subclient_content.append("{0}{1}{2}".format(test_path, slash_format, subclient_name))
            tmp_path = "".join(
                [test_path, slash_format, 'cvauto_tmp', slash_format, subclient_name, slash_format, str(self.runid)])
            run_path = "".join([subclient_content[0], slash_format, str(self.runid)])
            full_data_path = "{0}{1}full".format(run_path, slash_format)

            if self.distributed_fs_helper.is_hadoop:
                self.file_size = self.tcinputs.get('FileSize', 512)
            else:
                self.file_size = self.tcinputs.get('FileSize', 20480)

            self.log.info("Add full data for the current run.")
            machine.generate_test_data(
                full_data_path,
                acls=self.acls,
                unicode=self.unicode,
                xattr=self.xattr,
                long_path=self.long_path,
                file_size=self.file_size
                )

            self.log.info("Step3,  Create Subclient.")
            self.distributed_fs_helper.add_subclient(
                self.server_name,
                subclient_name,
                plan_name,
                subclient_content=subclient_content)

            self.log.info("Step4,  Run a full backup for the subclient and verify it completes without failures.")
            job_full = self.distributed_fs_helper.backup_subclient(
                self.server_name,
                subclient_name,
                Backup.BackupType.FULL)
            helper.verify_node_and_stream_count(
                job_full,
                self.pkg,
                node_count,
                backup_stream_count)

            self.log.info("Step5,  Add new data for the incremental")
            incr_data_path = "{0}{1}incr".format(run_path, slash_format)
            machine.generate_test_data(
                incr_data_path,
                acls=self.acls,
                unicode=self.unicode,
                xattr=self.xattr,
                long_path=self.long_path,
                file_size=self.file_size
                )

            self.log.info(
                "Step8,  Run an incremental backup for the subclient and verify it completes without failures.")
            job_incr = self.distributed_fs_helper.backup_subclient(
                self.server_name,
                subclient_name,
                Backup.BackupType.INCR)
            helper.verify_node_and_stream_count(
                job_incr,
                self.pkg,
                node_count,
                backup_stream_count)

            self.log.info("Step9,  Run a synthfull job")
            self.distributed_fs_helper.backup_subclient(self.server_name, subclient_name, Backup.BackupType.SYNTH)

            self.log.info("Step10, Run a restore of the complete subclient data and verify correct data is restored.")
            job_restore = self.distributed_fs_helper.restore_server(
                self.server_name,
                source_paths=subclient_content[0],
                restore_path=tmp_path)
            helper.verify_node_and_stream_count(
                job_restore,
                self.pkg,
                node_count,
                restore_stream_count)
            helper.compare_and_verify(
                subclient_content[0], "{0}{1}{2}".format(tmp_path, slash_format, subclient_name))

            self.log.info("Step11, Delete the subclient, the server and clean up the data")
            self.distributed_fs_helper.delete_subclient(self.server_name, subclient_name)
            self.distributed_fs_helper.delete_server(self.server_name)
            machine.remove_directory(subclient_content[0])
            machine.remove_directory(tmp_path)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as error:
            handle_testcase_exception(self, error)
        finally:
            Browser.close_silently(self.distributed_fs_helper.browser)
