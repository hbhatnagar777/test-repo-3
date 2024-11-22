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
    
    setup()         --  Initializes pre-requisites for this test case

    run()           --  run function of this test case

Input Example:

   "testCases": {
        "62828": {
            "AccessNode": "",
            "FileServerName": "",
            "SrcPath": "",
            "SMBShareUsername": ""
            "SMBSharePwd": "",
            "Region": ""
        }
    }
"""

import time
from datetime import datetime

from cvpysdk.commcell import Commcell
from cvpysdk.subclients.fssubclient import FileSystemSubclient
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Archiving.ContentGroups import ContentGroups, ArchivingNasServer, ArchivingPlans
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Archiving.Archiving import Archiving
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep

class TestCase(CVTestCase):
    """ 
    Class for executing acceptance test case for AaaS - archive and analyze
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Metallic Archiving: acceptance test for archive and analyze"
        self.contentgroupname = "auto_archive_tc62828"
        self.archiving_auto_plan = "auto_plan_tc62828"
        self.config = get_config()
        self.archiving_client = None
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.contentgroup = None
        self.contentgroups = None
        self.op_helper = None
        self.slash_format = None
        self.share_type = None
        self.sourcepath = None
        self.src_mountpath = None
        self.nfs_client_mount_dir = None
        self.srcdrive = None
        self.tcinputs = {
            "AccessNode": None,
            "FileServerName": None,
            "SrcPath": None,
            "SMBShareUsername": None,
            "SMBSharePwd": None,
            "Region": None
        }

    def refresh(self, wait_time=180):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    @test_step
    def add_content_group(self):
        """ Function to add new content group """
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        if self.contentgroups.is_content_group_exists(self.contentgroupname):
            self.contentgroups.delete_content_group(self.contentgroupname)
        self.admin_console.refresh_page()
        self.contentgroup = self.contentgroups.add_new_content_group()
        self.contentgroup.select_deploy_option(analyze=False)
        self.contentgroup.select_access_node(self.tcinputs["AccessNode"])
        self.contentgroup.configure_source(self.tcinputs["FileServerName"],
                                           self.share_type,
                                           self.tcinputs["Region"],
                                           self.tcinputs["SMBShareUsername"],
                                           self.tcinputs["SMBSharePwd"])
        self.contentgroup.configure_plan(self.archiving_auto_plan,
                                                             self.tcinputs["Storage"])
        self.contentgroup.configure_content_group(self.contentgroupname,
                                                  self.sourcepath,
                                                  self.share_type,
                                                  self.tcinputs["FileServerName"])

        self.contentgroup.view_summary()
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        i = 1
        while (True):
            time.sleep(120)
            self.admin_console.refresh_page()
            if self.contentgroups.is_content_group_exists(self.contentgroupname):
                self.log.info("new content group %s was created successfully", self.contentgroupname)
                break;
            i = i + 1
            if i == 8:
                raise Exception("could not see newly created content group from content group list")

    @test_step
    def validate_contentgroup_creation(self):
        """
        Function to validate content group creation
        Args:
            contentgroupname    (str)   --  content group name.
        """
        self.commcell.refresh()
        client = self.commcell.clients.get(self.tcinputs["FileServerName"])
        self.log.info("      NAS client with given FileServerName exists or creation Successful")
        if self.share_type == 'CIFS':
            agent = client.agents.get("Windows File System")
        else:
            agent = client.agents.get("Linux File System")
        self.log.info("      File System agent Creation Successful")
        archive_set = agent.backupsets.get("DefaultArchivingSet")
        self.log.info("      Archiveset Creation Successful")
        self.fs_subclient = FileSystemSubclient(backupset_object=archive_set, subclient_name=self.contentgroupname)

    @test_step
    def validate_contentgroup_creation(self):
        """
        Function to validate content group creation
        Args:
            contentgroupname    (str)   --  content group name.
        """
        self.commcell.refresh()
        client = self.commcell.clients.get(self.tcinputs["FileServerName"])
        self.log.info("      NAS client with given FileServerName exists or creation Successful")
        if self.share_type == 'CIFS':
            agent = client.agents.get("Windows File System")
        else:
            agent = client.agents.get("Linux File System")
        self.log.info("      File System agent Creation Successful")
        archive_set = agent.backupsets.get("DefaultArchivingSet")
        self.log.info("      Archiveset Creation Successful")
        self.fs_subclient = FileSystemSubclient(backupset_object=archive_set, subclient_name=self.contentgroupname)

    @test_step
    def enable_archive(self, contentgroupname):
        """
        Function to enable archive for newly created content group
        """
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        self.admin_console.refresh_page()
        self.contentgroups.access_content_group(contentgroupname)
        self.contentgroup.access_insights_tab()
        self.contentgroup.set_archiving_rule_and_create_plan(self.archiving_auto_plan,
                                                             self.tcinputs["Storage"])

    @test_step
    def run_archive_job(self, contentgroupname):
        """ Function to run archive job """
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        self.contentgroups.run_archive(contentgroupname)
        time.sleep(60)
        job = self.fs_subclient.find_latest_job()
        self.admin_console.log.info("Waits for archiving job %s to complete", str(job.job_id))
        if self.commcell.job_controller.get(job.job_id).wait_for_completion(timeout=300):
            self.log.info("Archive job completed Successfully.")
            time.sleep(15)
        else:
            raise CVTestStepFailure("Archive job could not be completed")

    @test_step
    def run_in_place_restore(self, contentgroupname):
        """ 
        Function to run in place restore job
        Args:
            contentgroupname    (str)   --  content group name.
        """
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        self.admin_console.refresh_page()

        if self.share_type == 'NFS':
            selectedfiles = [(self.slash_format + self.tcinputs["FileServerName"] + self.sourcepath)]
        else:
            selectedfiles = None

        job_id = self.archiving.restore_subclient(
            self.contentgroupname,
            proxy_client=self.tcinputs["AccessNode"],
            restore_path=None,
            unconditional_overwrite=True,
            restore_ACLs=True,
            selected_files=selectedfiles,
            impersonate_user=self.tcinputs["SMBShareUsername"],
            impersonate_password=self.tcinputs["SMBSharePwd"])

        self.admin_console.log.info("Waits for restore job %s to complete", str(job_id))
        if self.commcell.job_controller.get(job_id).wait_for_completion(timeout=120):
            self.log.info("Restore job completed Successfully.")
            time.sleep(15)
        else:
            raise CVTestStepFailure("Restore job could not be completed")

    @test_step
    def validate_restore_result(self):
        """ validate restore result"""
        if self.share_type == 'CIFS':
            self.restore_hashcode = self.op_helper.client_machine.get_checksum_list(self.sourcepath)
        else:
            self.restore_hashcode = self.op_helper.client_machine.get_checksum_list(self.src_mountpath)
            
        _matched, _code = self.op_helper.client_machine._compare_lists(
            self.restore_hashcode,
            self.org_hashcode
            )
        if _matched is False:
            raise Exception("      Restored file content does not match with the original")
        self.admin_console.log.info("      Restored files are matching with the original content")

    @test_step
    def cleanup_test_data(self):
        """ clean up test data
        """
        self.admin_console.navigator.navigate_to_archivingv2()
        self.admin_console.access_tab("Content groups")
        if self.contentgroups.is_content_group_exists(self.contentgroupname):
            self.contentgroups.delete_content_group(self.contentgroupname)
        self.refresh(wait_time=60)
        self.admin_console.access_tab("NAS servers")
        if self.nasclient.is_nas_server_exists(self.archiving_client):
            self.nasclient.retire_nas_server(self.archiving_client)
        self.refresh()
        if self.nasclient.is_nas_server_exists(self.archiving_client):
            self.nasclient.delete_nas_server(self.archiving_client)
        self.refresh(wait_time=60)
        self.admin_console.access_tab("Plans")
        self.admin_console.log.info(self.archiving_auto_plan)
        if self.archivingplan.is_plan_exists(self.archiving_auto_plan):
            self.archivingplan.delete_plan(self.archiving_auto_plan)

        #clean up the mount points
        if self.share_type == "CIFS":
            self.op_helper.client_machine.unmount_drive(self.srcdrive)
        else:
            self.op_helper.client_machine.unmount_path(self.nfs_client_mount_dir, delete_folder=True)

    def generate_test_data(self):
        """ Function to generate test data with required file_size and modified_time attribute """
        if self.share_type == 'CIFS':
            tpath = self.sourcepath
        else:
            tpath = self.src_mountpath

        self.testfile_list = [("test1.txt", True), ("test2.txt", False), ("test3.txt", True),
             ("test4.txt", False), ("test5.txt", True), ("test6.txt", False),
             ("test7.txt", True), ("test8.txt", False), ("test9.txt", True),
             ("test10.txt", False)]
        self.op_helper.prepare_turbo_testdata(
            tpath,
            self.testfile_list,
            size1=1536 * 1024,
            size2=20 * 1024)

        for i in range(10):
            self.op_helper.client_machine.modify_item_datetime(path=self.op_helper.client_machine.join_path(
                tpath, self.testfile_list[i][0]),
                creation_time=datetime(year=2019, month=1, day=1),
                access_time=datetime(year=2019, month=1, day=1),
                modified_time=datetime(year=2019, month=1, day=1))

        self.org_hashcode = self.op_helper.client_machine.get_checksum_list(tpath)
        self.log.info("Test data populated successfully.")

    def init_pre_req(self):
        """ Initialize test case inputs"""
        self.commcell = Commcell(self.commcell.webconsole_hostname,
                                self._inputJSONnode['commcell']['commcellUsername'],
                                self._inputJSONnode['commcell']['commcellPassword'])
        self.accessnode = self.commcell.clients.get(self.tcinputs["AccessNode"])
        self.op_helper = cvonepas_helper(self)
        self.op_helper.client_machine = Machine(self.accessnode, self.commcell)
        self.log.info("access node os version: %s", self.accessnode.os_info)
        if "Windows" in self.accessnode.os_info:
            self.share_type = "CIFS"
            self.slash_format = '\\'
            self.srcdrive = self.op_helper.client_machine.mount_network_path(self.tcinputs["SrcPath"],
                                                   self.tcinputs["SMBShareUsername"],
                                                   self.tcinputs["SMBSharePwd"])
            self.src_mountpath = self.srcdrive + ":" + self.slash_format + self.id
        else:
            self.share_type = "NFS"
            self.slash_format = '/'
            self.nfs_client_mount_dir = "/tmp/test" + self.id
            self.op_helper.client_machine.execute_command(f"umount -fl {self.nfs_client_mount_dir}")
            self.op_helper.client_machine.mount_nfs_share(self.nfs_client_mount_dir,
                                                self.tcinputs["FileServerName"],
                                                self.tcinputs["SrcPath"])
            self.src_mountpath = self.nfs_client_mount_dir + self.slash_format + self.id

        self.contentgroupname = self.contentgroupname + self.share_type
        self.archiving_auto_plan = self.archiving_auto_plan + self.share_type

        self.sourcepath = self.tcinputs["SrcPath"] + self.slash_format + self.id
        self.archiving_client = self.tcinputs["FileServerName"]

        self.generate_test_data()

        self.archiving = Archiving(self.admin_console)
        self.nasclient = ArchivingNasServer(self.admin_console)
        self.archivingplan = ArchivingPlans(self.admin_console)
        self.contentgroups = ContentGroups(self.admin_console)

    def setup(self):
        """ Pre-requisites for this testcase """
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

    def run(self):
        """Main function for test case execution"""
        _desc = """
        1)    delete existing automation content group if exists
        2)    add new automation content group
        3)    validate content group is created correctly
        4)    access newly content group, explore archiving rules
        6)    run archiving job
        7)    run in place restore job
        8)    validate the restored data
        9)    delete the test data once test is done
              delete automation content group, delete automation client, delete automation plan
        """
        try:
            try:
                self.service = HubServices.file_archiving
                self.hub_dashboard = Dashboard(self.admin_console, self.service)
                self.hub_dashboard.choose_service_from_dashboard()
                self.admin_console.click_button(value="Acknowledge")
            except:
                pass
            self.init_pre_req()
            self.add_content_group()
            self.verify_analyzed_data(self.contentgroupname)
            self.validate_contentgroup_creation()
            self.run_archive_job(self.contentgroupname)
            self.run_in_place_restore(self.contentgroupname)
            self.validate_restore_result()
            self.cleanup_test_data()

        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
