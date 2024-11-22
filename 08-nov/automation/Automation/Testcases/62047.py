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
        "62047": {
            "SrcAccessNode": "",
            "SrcFileServerName": "",
            "SrcPath": "",
            "SMBShareUsername": ""
            "SMBSharePwd": "",
            "AzureStorageAccount": "",
            "Region": "",
            "AzureFileShareName":"",
            "AzureSMBShareUserName": "",
            "AzureSMBSharePwd": "",
            "destAccessNode": "",
            "ShareType": "SMB"
        }
    }
"""

import time
from time import sleep

from cvpysdk.commcell import Commcell
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper

from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Migration.migration import Migration, MigrationGroup
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """ 
    Class for executing acceptance test case for Migration
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Migration as service project acceptance test"
        self.migrationgroupname = "auto_tc62047" + "_" + str(int(time.time()))
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.migration = None
        self.migrationgroup = None
        self.delimiter = None
        self.slash_format = None
        self.client_machine = None
        self.share_type = None
        self.sourcepath = None
        self.destpath = None
        self.src_mountpath = None
        self.dest_mountpath = None
        self.config = get_config()
        self.nfs_client_mount_dir = None
        self.srcdrive = None
        self.destdrive = None
        self.tcinputs = {
            "SrcAccessNode": None,
            "SrcFileServerName": None,
            "SrcPath": None,
            "SMBShareUsername": None,
            "SMBSharePwd": None,
            "AzureStorageAccount": None,
            "Region": None,
            "AzureFileShareName": None,
            "AzureSMBShareUserName": None,
            "AzureSMBSharePwd": None,
            "destAccessNode": None,
            "ShareType": None,
        }

    def refresh(self, wait_time=180):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        time.sleep(wait_time)
        self.admin_console.refresh_page()

    def init_pre_req(self):
        """ Initialize test case inputs"""
        self.commcell = Commcell(self.commcell.webconsole_hostname,
                                self.config.ADMIN_USERNAME,
                                self.config.ADMIN_PASSWORD)
        self.fs_helper = FSHelper(self)
        self.srcaccessnode = self.commcell.clients.get(self.tcinputs["SrcAccessNode"])
        self.client_machine = Machine(self.srcaccessnode, self.commcell)
        self.destaccessnode = self.commcell.clients.get(self.tcinputs["destAccessNode"])
        self.dest_machine = Machine(self.destaccessnode, self.commcell)
        if self.share_type == "SMB":
            self.srcdrive = self.client_machine.mount_network_path(self.tcinputs["SrcPath"],
                                                               self.tcinputs["SMBShareUsername"],
                                                               self.tcinputs["SMBSharePwd"])
            self.src_mountpath = self.srcdrive + ":" + self.slash_format + "Test62047"
            self.destdrive = self.dest_machine.mount_network_path(self.tcinputs["AzureFileShareName"],
                                                            self.tcinputs["AzureSMBShareUserName"],
                                                            self.tcinputs["AzureSMBSharePwd"])
            self.dest_mountpath = self.destdrive + ":" + self.slash_format + "Test62047"
        else:
            self.nfs_client_mount_dir = "/tmp/Test62047"
            self.log.info(self.nfs_client_mount_dir)
            self.log.info(self.slash_format)
            self.client_machine.unmount_path(self.nfs_client_mount_dir)
            self.dest_machine.unmount_path(self.nfs_client_mount_dir)
            self.client_machine.create_directory(self.nfs_client_mount_dir, force_create=True)
            self.dest_machine.create_directory(self.nfs_client_mount_dir, force_create=True)
            self.client_machine.mount_nfs_share(self.nfs_client_mount_dir,
                                                self.tcinputs["SrcFileServerName"],
                                                self.tcinputs["SrcPath"])
            self.src_mountpath = self.nfs_client_mount_dir + self.slash_format + "Test62047"
            self.dest_machine.mount_nfs_share(self.nfs_client_mount_dir,
                                                self.tcinputs["AzureStorageAccount"],
                                                self.tcinputs["AzureFileShareName"])
            self.dest_mountpath = self.nfs_client_mount_dir + self.slash_format + "Test62047"

        self.dest_machine.create_directory(self.dest_mountpath, force_create=True)
        self.fs_helper.generate_testdata(['.html', '.py'], self.sourcepath, 6)

    def setup(self):
        """ Pre-requisites for this testcase """
        self.share_type = self.tcinputs["ShareType"].upper()
        if self.share_type == "SMB":
            self.delimiter = "\\"
            self.slash_format = '\\'
        else:
            self.delimiter = "/"
            self.slash_format = '/' 
        self.sourcepath = self.tcinputs["SrcPath"] + self.delimiter + 'Test62047'
        self.destpath = self.tcinputs["AzureFileShareName"] + self.delimiter + 'Test62047'
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login()

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_pre_req()
            self.refresh()
            self.log.info("click advanced view on file migration dashboard")
            self.service = HubServices.file_migration
            self.hub_dashboard = Dashboard(self.admin_console, self.service)
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.go_to_admin_console()
            self.migration = Migration(self.admin_console)
            self.migrationgroup = MigrationGroup(self.admin_console)

            self.refresh()
            if self.migration.is_group_exists(self.migrationgroupname):
                self.migration.delete_migration_group(self.migrationgroupname)

            self.log.info("create new migration group")
            self.migration.add_migration_group()
            self.migrationgroup.configure_pre_requisite()
            self.migrationgroup.configure_access_node()
            self.migrationgroup.configure_source(self.tcinputs["SrcFileServerName"],
                                            self.tcinputs["ShareType"],
                                            self.tcinputs["SrcAccessNode"],
                                            self.tcinputs["SMBShareUsername"],
                                            self.tcinputs["SMBSharePwd"])
            self.migrationgroup.configure_destination(self.tcinputs["AzureStorageAccount"],
                                                self.tcinputs["Region"],
                                                self.tcinputs["destAccessNode"],
                                                self.tcinputs["AzureSMBShareUserName"],
                                                self.tcinputs["AzureSMBSharePwd"])
            self.migrationgroup.configure_contents(self.sourcepath,self.destpath)
            sleep(60)
            self.migrationgroup.configure_migration_settings(self.migrationgroupname)
            self.migrationgroup.configure_summary()
            time.sleep(120)

            self.admin_console.navigator.navigate_to_migration()
            self.refresh()
            if self.migration.is_group_exists(self.migrationgroupname):
                self.log.info("migration group %s was created successfully", self.migrationgroupname)
            else:
                raise Exception("migration group creation failed")

            self.migration.sync_now(self.migrationgroupname)
            self.log.info("Waiting for migration to complete")
            i = 1
            while (True):
                self.refresh()
                if self.migration.is_group_synced(self.migrationgroupname):
                    break;
                i = i + 1
                if i == 6:
                    raise Exception("migration group sync failed")

            self.fs_helper.validate_cross_machine_restore(content_paths=[self.src_mountpath],
                                              restore_path=self.dest_mountpath,
                                              dest_client=self.tcinputs['destAccessNode'])

            self.migration.delete_migration_group(self.migrationgroupname)
            if self.share_type == "SMB":
                self.client_machine.unmount_drive(self.srcdrive)
                self.dest_machine.unmount_drive(self.destdrive)
            else:
                self.client_machine.unmount_path(self.nfs_client_mount_dir)
                self.dest_machine.unmount_path(self.nfs_client_mount_dir)

        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
