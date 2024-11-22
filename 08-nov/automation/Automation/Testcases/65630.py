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

    setup()       --   setup function will create setup objects related to web adminconsole
    list_snapshots_beside_Restore_History_client_details_page() --  list of Snapshots from action item beside Restore History in client details page
    list_snapshots_Backupsets_client_details_page() --  list of Snapshots from action item beside Delete Backupset in client details page
    list_snapshots_beside_backuphistory_subclient_details_page() --  list of Snapshots from action item beside Backup History in subclient details page
    list_snapshots_for_job_backuphistory_jobs_page() --  list snapshot from action item of particular job in jobs backup history in jobs page
    list_snapshots_fsagent_fsservers_page()  --  List of Snapshots of particular client action item in file server page
    list_snapshots_array_details_page()  --  List Snapshots from action item of particular array in array details page
    list_snapshots_copy_level_plans_details_page()  --  List Snapshots from Snap copy details of particluar plan in plan details page
    list_snapshots_view_jobs_fsservers_page()  --  List of Snapshots of particular client view jobs action item in file server page
    list_snapshots_Jobs_tab_client_details_page()  --  list of Snapshots from action item in Jobs tab in client details page

	run()       --   run function of this test case will have list of snapshots from different level for fs agent

    tear_down()   --  tear down function will cleanup

Inputs:

    ClientName          --      name of the client for backup

    StoragePoolName     --      backup location for disk storage

    SnapEngine          --      snap engine to set at subclient

    SubclientContent    --      Data to be backed up

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, FsAgentAdvanceOptions, Jobs as FsJobs
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import FsSubclientAdvanceOptions
from Web.AdminConsole.AdminConsolePages.ArrayDetails import ArrayDetails
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
import random
import string
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.CopyDetails import CopyDetailsAdvanceOptions

class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Command Center: List Snapshots at different levels in Command center for File System agent"
        self.browser = None
        self.admin_console = None
        self.snap_template = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None,
            "SnapEngine": None,
            "SubclientContent": None,
        }

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.snap_template = SnapTemplate(self, self.admin_console)
        self.navigator = self.admin_console.navigator
        self.arrays = Arrays(self.admin_console)
        self.rfs_servers = FileServers(self.admin_console)
        self.rfs_subclient = Subclient(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.plandetails = PlanDetails(self.admin_console)
        self.plans = Plans(self.admin_console)
        self.vsa_hypervisor = Hypervisors(self.admin_console)
        self.fs_servers = FileServers(self.admin_console)
        self.Rfs_advance_options = FsAgentAdvanceOptions(self.admin_console)
        self.rfs_subclientdetails = FsSubclientAdvanceOptions(self.admin_console)
        self.arraydetails = ArrayDetails(self.admin_console)
        self.jobs = Jobs(self.admin_console)
        self.rfsjobs = FsJobs(self.admin_console)
        self.machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.copydetailsadv = CopyDetailsAdvanceOptions(self.admin_console)

    def list_snapshots_beside_restore_history_client_details_page(self, full_jobid):
        """
        list of Snapshots from action item beside Restore History in client details page
        """
        self.log.info("*" * 20 + "list of Snapshots from action item beside Restore History in client"
                                 " details page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rfs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.Rfs_advance_options.action_list_snaps()
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()

    def list_snapshots_backupsets_client_details_page(self, full_jobid):
        """
        list of Snapshots from action item beside Delete Backupset in client details page
        """
        self.log.info("*" * 20 + "list of Snapshots from action item beside Delete Backupset in client details"
                                 " page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rfs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        self.rfs_subclient.action_list_snaps_backupset_level()
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()


    def list_snapshots_beside_backuphistory_subclient_details_page(self, full_jobid):
        """
        list of Snapshots from action item beside Backup History in subclient details page
        """
        self.log.info("*" * 20 + "list of Snapshots from action item beside Backup History in subclient details"
                                 " page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rfs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        self.rfs_subclient.access_subclient(self.snap_template.subclient_name)
        self.rfs_subclientdetails.action_list_snaps()
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()

    def list_snapshots_for_job_backuphistory_jobs_page(self, full_jobid):
        """
        list snapshot from action item of particular job in jobs backup history in jobs page
        """
        self.log.info("*" * 20 + "list snapshot from action item of particular job in jobs backup history in jobs"
                                 " page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rfs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Subclients")
        self.rfs_subclient.access_subclient(self.snap_template.subclient_name)
        self.rfs_subclientdetails.click_on_backup_history()
        self.rtable.search_for(full_jobid)
        self.jobs.action_list_snaps(job_id=full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()

    def list_snapshots_fsagent_fsservers_page(self, full_jobid):
        """
        List of Snapshots of particular client action item in file server page
        """
        self.log.info("*" * 20 + "List of Snapshots of particular client action item in file server page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rtable.search_for(self.tcinputs["ClientName"])
        self.rfs_servers.action_list_snaps(self.tcinputs["ClientName"])
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()


    def list_snapshots_copy_level_plans_details_page(self, full_jobid):
        """
         List Snapshots from Snap copy details of particluar plan in plan details page
         """
        self.log.info("*" * 20 + "List Snapshots from Snap copy details of particluar plan in plan details page" + "*" * 20)
        self.plans.select_plan(self.snap_template.plan_name)
        self.admin_console.access_tab(self.admin_console.props['label.nav.storagePolicy'])
        table = Rtable(self.admin_console, id="planBackupDestinationTable")
        table.access_link("Primary snap")
        self.copydetailsadv.action_list_snaps_copy_level()
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()


    def list_snapshots_array_details_page(self, full_jobid):
        """
        List Snapshots from action item of particular array in array details page
        """
        self.log.info("*" * 20 + "List Snapshots from action item of particular array in array details page" + "*" * 20)
        self.navigator.navigate_to_arrays()
        array_name_list = self.snap_template.execute_query(self.snap_template.get_array_name,
                                                           {'a': full_jobid,
                                                            'b': self.spcopyt.copy_id})
        self.rtable.access_link(array_name_list[0][0])
        self.arraydetails.click_list_snapshots()
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()

    def list_snapshots_view_jobs_fsservers_page(self, full_jobid):
        """
        List of Snapshots of particular client view jobs action item in file server page
        """
        self.log.info("*" * 20 + "List of Snapshots of particular client view jobs action item in file server page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rtable.search_for(self.tcinputs["ClientName"])
        self.rfs_servers.view_jobs(self.tcinputs["ClientName"])
        self.rtable.search_for(full_jobid)
        self.jobs.action_list_snaps(job_id=full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()

    def list_snapshots_jobs_tab_client_details_page(self, full_jobid):
        """
        list of Snapshots from action item in Jobs tab in client details page
        """
        self.log.info("*" * 20 + "list of Snapshots from action item in Jobs tab in client details page" + "*" * 20)
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.rfs_servers.access_server(self.tcinputs['ClientName'])
        self.admin_console.wait_for_completion()
        self.admin_console.access_tab("Jobs")
        self.rtable.search_for(full_jobid)
        self.rfsjobs.action_list_snaps_job(full_jobid)
        self.rtable.search_for(full_jobid)
        self.rtable.click_action_menu(full_jobid)
        self.admin_console.refresh_page()


    def run(self):
        """Main function for test case execution"""

        try:
            self.snap_template.cleanup()
            self.snap_template.create_entities()
            self.source_test_data = self.snap_template.add_test_data()
            full_jobid = self.snap_template.verify_backup(Backup.BackupType.FULL)
            dir_name = "Mount_" + ''.join([random.choice(string.ascii_letters) for _ in range(3)]) + \
                       self.snap_template.string
            if self.machine.os_info == 'UNIX':
                mount_path = str('/' + dir_name)
            else:
                mount_path = str("C:" + '\\' + dir_name)
            self.machine.create_directory(mount_path)
            #below mount_multiple_snaps method will also mount single snap too at subclient level
            self.snap_template.mount_multiple_snaps_subclient_level(jobid=full_jobid, mount_path=mount_path,
                                                                    copy_name=self.snap_template.snap_primary,
                                                                    clientname=self.tcinputs["ClientName"],
                                                                    backupsetname=self.snap_template.backupset_name,
                                                                    subclientname=self.snap_template.subclient_name)
            self.list_snapshots_beside_restore_history_client_details_page(full_jobid)
            self.list_snapshots_backupsets_client_details_page(full_jobid)
            self.list_snapshots_beside_backuphistory_subclient_details_page(full_jobid)
            self.list_snapshots_for_job_backuphistory_jobs_page(full_jobid)
            self.list_snapshots_fsagent_fsservers_page(full_jobid)
            self.spcopyt = self.snap_template.spcopy_obj("Primary snap")
            self.list_snapshots_array_details_page(full_jobid)
            # below unmount_snap method will also unmount unmount at array level
            self.snap_template.unmount_snap(job_id=full_jobid, copy_name=self.snap_template.snap_primary)
            self.admin_console.refresh_page()
            self.list_snapshots_view_jobs_fsservers_page(full_jobid)
            self.list_snapshots_jobs_tab_client_details_page(full_jobid)
            self.list_snapshots_copy_level_plans_details_page(full_jobid)
            # below delete_multiple_snaps method will also delete single snap too at plan copy level
            self.snap_template.delete_multiple_snaps_plan_level(job_id=full_jobid,
                                                                copy_name=self.snap_template.snap_primary,
                                                                plan_name=self.snap_template.plan_name)
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To cleanup entities created during TC"""
        try:
            self.snap_template.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
