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

    login_to_commandcenter()    --  Logins to the command center

    access_subclient()      --  Navigates to the subclient details page for the created subclient

    edit_subclient_content_and_exceptions()     -- Edits the subclient content and exceptions

    verify_logs()       --  Checks the logs if clbackup is launched on all the nodes. Clrestore is launched on the proxy client.

    run_backup()        --  Runs backup and waits for completion

    run_restore_verify()    --  Runs restore (in-place / out-of-place and verfies if data is restored correctly)

    verify_subclient_properties()   -- Verifies the subclient properties

    set_DANS_and_verify_subclient_properties()       --  sets the data access nodes and verfies the default subclient properties

"""

"""
Sample JSON for the Testcase

"63461":{
        "AgentName":"Windows File System",
        "ClientName":"",
        "PlanName":"plan-name",
        "PlanName2": "plan-name2"
        "DataAccessNodes": ["DAN-1", "DAN-2"],
        "TestPath": "CIFS share path",
        "TestPath2": "CIFS share path2"
        "ImpersonateUser":,
        "ImpersonatePassword":
    }
"""

from time import sleep
import re
import base64

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview, FsSubclientAdvanceOptions
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import Backup, RPanelInfo
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.fshelper = None
        self.subclient_name = None
        self.plan_name = None
        self.admin_console = None
        self.browser = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.fileServers = None
        self.service = None
        self.machines_dict = None
        self.panel_info = None
        self.fsSubclient = None
        self.temp_mount_path = None
        self.fsSubclientOverview = None
        self.fs_subclient_adv = None
        self.base_path = None
        self.UNC_base_path = None
        self.dashboard = None
        self.file_server_utils = None
        self.config = get_config()
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "PlanName2": None,
            "ImpersonateUser": None,
            "ImpersonatePassword": None,
            "DataAccessNodes": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.name = "CIFS Multinode/ distributed backup from Command Center"
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        
        self.subclient_name = "subclient_" + str(self.id)
        self.plan_name = self.tcinputs.get("PlanName")
        self.impersonate_user = self.tcinputs.get("ImpersonateUser")
        self.impersonate_password = str(base64.b64decode(self.tcinputs.get("ImpersonatePassword")), 'utf-8')
        self.temp_mount_path = "Z:"
        self.base_path = self.client_machine.join_path(self.temp_mount_path, f'{self.id}')
        self.UNC_base_path = self.client_machine.join_path(self.test_path, f'{self.id}')

        self.backupset = self.agent.backupsets.get("defaultBackupSet")
    
    def login_to_commandcenter(self):
        """
        Logins to commandcenter

        Args:
            None
        Returns:
            None
        """
        self.log.info("Logging into command center")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)        
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

        self.fileServers = FileServers(self.admin_console)
        self.fsSubclient = Subclient(self.admin_console)
        self.fsSubclientOverview = SubclientOverview(self.admin_console)
        self.panel_info = RPanelInfo(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.jobs = Jobs(self.admin_console)
        self.file_server_utils = FileServersUtils(self.admin_console)
        self.fs_subclient_adv = FsSubclientAdvanceOptions(self.admin_console)
    
    
    def verify_subclient_properties(self, subclient, access_nodes=None, is_cifs_agent=True):
        """
        Verifies the default subclient properties

        Args:
            subclient (Subclient object) : CVPySDK subclient object
            access_nodes (list) (str)    : List of data access nodes
            is_cifs_agent     (bool)           : True if CIFS agent
        
        Retuns:
            None
        Raises:
            Exception if any property is not correct
        """

        self.log.info("Checking the subclient properties")
        
        # Using mulitple if statements to check if any one property is incorrect

        subclient.refresh()

        # Using local var to reduce mutliple requests
        subclient_props = subclient.properties

        if access_nodes is not None:

            curr_dan = []

            backup_config = ""

            if "backupConfigurationIDA" in subclient_props["fsSubClientProp"]:
                backup_config = "backupConfigurationIDA"
            
            elif "backupConfiguration" in subclient_props["fsSubClientProp"]:
                backup_config = "backupConfiguration"

            else:
                raise Exception("Unable to find the data access nodes subclient property")
            
            for dan in subclient_props["fsSubClientProp"][backup_config]["backupDataAccessNodes"]:
                curr_dan.append(dan["displayName"])

            if self.fshelper.compare_lists(curr_dan, access_nodes, True):
                self.log.info("Data Access Nodes are set correctly")
            else:
                raise Exception("Data Access Nodes are not set correctly")

            if not is_cifs_agent:
                if subclient_props["fsSubClientProp"]["enableNetworkShareAutoMount"]:
                    self.log.info("enableNetworkShareAutoMount is set to True")
                else:
                    raise Exception("enableNetworkShareAutoMount is set to False, this should be True")
                
                if subclient_props["fsSubClientProp"]["enableFolderLevelMultiThread"]:
                    self.log.info("Folder Level Multi-Threading is enabled")
                else:
                    raise Exception("Folder Level Multi-Threading is not enabled")
        else:
            if subclient_props["fsSubClientProp"]["followMountPointsMode"] == 1:
                self.log.info("Follow mount points is enabled")
            else:
                raise Exception("Follow mount points is not enabled")
            
        if subclient_props["fsSubClientProp"]["isTrueUpOptionEnabledForFS"]:
            self.log.info("TrueUp Option is enabled")
        else:
            raise Exception("TrueUp is not enabled")

        if subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"] == 30:
            self.log.info("TrueUp days is set to 30")
        else:
            raise Exception(
                f'TrueUp days is set to {subclient_props["fsSubClientProp"]["runTrueUpJobAfterDaysForFS"]} \
                this should be 30 by default')

        if subclient_props["commonProperties"]["numberOfBackupStreams"] == 0:
            self.log.info("Optimal data readers are set")
        else:
            raise Exception("Optimal Data Readers are not set")

        if subclient_props["commonProperties"]["allowMultipleDataReaders"]:
            self.log.info("Allow multiple readers is set to True")
        else:
            raise Exception("Multiple data readers are not set")

        self.log.info("Successfully verfied the subclient properties")
    
    def access_agent(self):
        """
        Navigates to file server page and clicks on File servers tab
        """

        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        
        self.fileServers.access_server(self.client_name)

        self.file_server_utils.access_protocol("CIFS")

        self.admin_console.access_tab("Subclients")
        
    def access_subclient(self, cleanup=False):
        """
        Access the subclient details page for the created subclient

        Args:
            cleanup (bool) : if delete existing subclient and create afresh

        Returns:
            None
        """

        self.log.info("Navigating to the subclient details page")

        self.access_agent()

        if cleanup:

            self.log.info("Deleting previous subclient and creating a new one")

            if self.fsSubclient.is_subclient_exists(self.subclient_name):
                self.fsSubclient.delete_subclient(backupset_name="defaultBackupSet", 
                                                  subclient_name=self.subclient_name)

            self.log.info(f"Creating new subclient: {self.subclient_name}")

            self.fsSubclient.add_subclient(subclient_name=self.subclient_name,
                                           contentpaths=[self.UNC_base_path],
                                           plan_name=self.plan_name,
                                           impersonate_user={
                                               "username": self.impersonate_user,
                                               "password": self.impersonate_password
                                            },
                                            is_nas_subclient=True)

            self.backupset.subclients.refresh()
            self.subclient = self.backupset.subclients.get(self.subclient_name)
            
            self.log.info("Successfully created a new subclient")

        self.fsSubclient.access_subclient(backupset_name="defaultBackupSet",
                                          subclient_name=self.subclient_name)

    def edit_subclient_content_and_exceptions(self, content, exclusion='*.filter', exception='**\\file1.filter'):
        """
        Removes self.test_path and adds the specified content

        Args:
            content (str) : Content to be added
            exclusion (str) : Filter to be added
                default : *.filter
            exception (str) : Exception to be added
                default : **/1.filter

        Returns:
            None
        Raises Exception if issue removing content, adding content, specifying filters / exceptions
        """

        self.access_subclient()

        del_content = self.client_machine.join_path(self.test_path, str(self.id))

        self.log.info(f"Adding content: {content}, exclusion: {exclusion}, exception: {exception}")

        self.fsSubclientOverview.edit_content(add_content=[content],
                                              del_content=[del_content],
                                              add_exclusions=[exclusion],
                                              add_exceptions=[exception])
        
        backup_content_from_plan = 0
        self.panel_info.edit_tile(tile_label="Content") 
        self.admin_console.wait_for_completion()
        
        self.log.info("Checking if backup content from plan toggle exists")
        content_modal = RModalDialog(self.admin_console, "Add/Edit content")
        try:
            content_modal.enable_toggle("overrideBackupContent")
            self.admin_console.check_error_message()
            self.admin_console.submit_form()
            self.admin_console.check_error_message()
        except Exception:
            self.log.info("Checked Backup Content from plan does not exist")
            backup_content_from_plan = 1
        finally:
            content_modal.click_submit()
            if not backup_content_from_plan:
                raise Exception("Backup Content from Plan Exists. This is not applicable for NAS clients.")

            self.log.info("Backup content from plan does not exists and is expected")
            self.log.info("Successfully changed the subclient content")
                
            # Edit plan and check content does not change.

            self.log.info(f'Changing the subclient plan to {self.tcinputs.get("PlanName2")}')
            prev_sub_content = self.subclient.content

            self.fsSubclientOverview.assign_plan(self.tcinputs.get("PlanName2"))
            self.log.info("""Successfully changed the plan. 
                        Checking if the content is same after changing the plan""")
            
            self.subclient.refresh()

            current_sub_content = self.subclient.content

            self.log.info(f"Previous subclient content: {prev_sub_content}")
            self.log.info(f"Current subclient content: {current_sub_content}")

            # Content should still remain the same after changing the plan.
            if prev_sub_content != current_sub_content:
                self.log.info("Subclient content has changed. NAS client wont derive content from plan.")
                self.log.info(f"The current Subclient content is : {current_sub_content}")

            self.log.info("Successfully changed the plan and checked current is not derived from the plan")
            
            self.log.info("Refreshing the page and sleeping for 20 seconds")
            self.admin_console.refresh_page()
            sleep(20)

    def verify_logs(self, job):
        """
        Check the logs if master node has started CVDistributor and the other nodes have launched clBackup.

        Args:
            job (Job instance) : Backup job instance
            machine_dict (Dict) : Dictionary of machines instacnes with their name as key
        Returns:
            None
        """

        # master_node = self.fshelper.identify_master(job, machines_dict)
        master_node = None
        machines_list = list(self.machines_dict.values())

        job_type = job.job_type.lower()

        # For Restore: Check if cvdist-master and clRestore is launched on the node
        if job_type == 'restore':
            
            # Launched the restore job from the first key in machines_dict
            proxy_node = machines_list[0]

            # Check if CVdistributor is launched
            if proxy_node.get_logs_for_job_from_file(job.job_id, 'StartClientRestore.log', 'DistributedIDA::CMaster'):
                self.log.info(f"CVDistributor Master is launched on {proxy_node}")

                # sleeping for 20 seconds for launching clRestore on client
                sleep(20)
            else:
                raise Exception(f"CvDistributor is not launched on {proxy_node}")

            # Check if clRestore is launched
            if proxy_node.get_logs_for_job_from_file(job.job_id, 'clRestore.log'):
                self.log.info(f"Clrestore is launched on {proxy_node}")
            else:
                raise Exception(f"clRestore is not launched on {proxy_node}")

            return

        # For Backup: Check if cvdist-master (on master) and clbackup is launched on all the nodes
        for machine in machines_list:

            # Get the master node from machines_list
            if not master_node:
                if machine.get_logs_for_job_from_file(job.job_id, 'clBackup.log', 'DistributedIDA::CMaster'):
                    master_node = machine
                    self.log.info(f"CVDistributor Master is launched on {master_node}")

            # Check if clbackup is launched on all the nodes
            if not machine.get_logs_for_job_from_file(job.job_id, 'clBackup.log'):
                raise Exception(f"clBackup is not launched on machine {machine}")

        if not master_node:
            raise Exception("CvDistributor is not launched on the master node")

        self.log.info("Clbackup was launched on all the nodes")

    def run_backup(self, backup_type, skip_logs_verf=False):
        """
        Runs the backup for the subclient from the subclientDetails page

        Args:
            backup_type (BACKUP.BackupType.FULL/INCR/SYNTH) : Type of backup to run
            skip_logs_verf (bool) : Skips logs verfication on all nodes (use when less data is generated)
        Returns:
            None
        Raises Exception if one of the nodes did not launch clBackup / backup has failed
        """

        job_id = self.fs_subclient_adv.backup(backup_type)
        job_obj = self.commcell.job_controller.get(int(job_id))

        self.log.info(f"Backup job {job_id} has started. Waiting for completion")

        self.log.info(f"Navigating to job details for the backup job : {job_id}")
        self.jobs.access_job_by_id(job_id)

        # For Synthetic full backup, we dont need to check client logs
        if not (backup_type == Backup.BackupType.SYNTH or skip_logs_verf):
            while job_obj.phase.lower() == 'scan' or \
                    (job_obj.phase.lower() == 'backup' and job_obj.status.lower() == 'waiting'):
                sleep(20)
                continue

            # sleeping for 100 seconds for waiting for the streams to launch
            self.log.info("Sleeping for 100 seconds for the streams to launch")
            sleep(100)
            self.verify_logs(job_obj)

        if not job_obj.wait_for_completion():
            raise Exception(f"Backup Job {job_id} was {job_obj.status}")

        self.log.info(f"Backup job {job_id} is completed successfully")

    def run_restore_verify(self, path, in_place=True, only_validate_filters=False, filters='.filter', exception='file1'):
        """
        Run restore for the subclient from agentDetails page -> subclient restore action button.
        Also Verifies if the data was restored correctly or filters are validated.

        Args:
            inplace (bool) : If inplace restore has to be performed
            path (str) : Share path
            in_place (bool) : True if in-place restore
            only_validate_filters (bool) : True if validate only filters and not checksum
            filters (str) : filter to be validated after restore
            exception (str) : exception be be validated after restore

        Returns:
            None
        Raises Exception if data is not restored correctly / Filter validation failed / Restore job failed.
        """

        self.fshelper.mount_cifs_share_on_drive(self.client_machine, 
                                                path,
                                                self.impersonate_user,
                                                self.impersonate_password,
                                                self.temp_mount_path)

        source_checksum = self.client_machine.get_checksum_list(self.base_path)
        source_acl = self.client_machine.get_ace(self.impersonate_user, self.base_path)

        destination_checksum = destination_acl = None

        self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)

        self.access_agent()

        rest_job_id = None
        
        impersonate_user = {
                                "username": self.impersonate_user,
                                "password": self.impersonate_password
                           }

        if in_place:
            rest_job_id = self.fsSubclient.restore_subclient(backupset_name="defaultBackupSet",
                                                             subclient_name=self.subclient_name,
                                                             dest_client=self.data_access_nodes[0],
                                                             unconditional_overwrite=True,
                                                             selected_files=[self.UNC_base_path[2:]],
                                                             cifs=True,
                                                             impersonate_user=impersonate_user)
        else:
            rest_job_id = self.fsSubclient.restore_subclient(backupset_name="defaultBackupSet",
                                                             subclient_name=self.subclient_name,
                                                             dest_client=self.data_access_nodes[0],
                                                             destination_path=self.client_machine.join_path(path,
                                                                                                f'{self.id}_tmp_restore'),
                                                             selected_files=[self.UNC_base_path[2:]],
                                                             cifs=True,
                                                             impersonate_user=impersonate_user)

        rest_job_obj = self.commcell.job_controller.get(int(rest_job_id))

        self.log.info(f"Restore job {rest_job_id} has started. Waiting for completion")
        self.log.info("Navigating to job details")

        self.jobs.access_job_by_id(rest_job_id)

        self.log.info("Sleeping for 40 seconds for launching streams")
        sleep(40)
        self.verify_logs(rest_job_obj)

        if not rest_job_obj.wait_for_completion():
            raise Exception(f"Restore Job {rest_job_id} was {rest_job_obj.status}")
        self.log.info(f"Restore job {rest_job_id} is completed successfully.")

        self.fshelper.mount_cifs_share_on_drive(self.client_machine, 
                                                path, 
                                                self.impersonate_user,
                                                self.impersonate_password,
                                                self.temp_mount_path)
        if in_place:
            destination_checksum = self.client_machine.get_checksum_list(self.base_path)
            destination_acl = self.client_machine.get_ace(self.impersonate_user, self.base_path)
        else:
            destination_checksum = self.client_machine.get_checksum_list(
                self.client_machine.join_path(self.temp_mount_path, f'{self.id}_tmp_restore', f'{self.id}'))
            
            destination_acl = self.client_machine.get_ace(self.impersonate_user,
                self.client_machine.join_path(self.temp_mount_path, f'{self.id}_tmp_restore', f'{self.id}')
            )

        if only_validate_filters:
            self.log.info("Validating only filters")
            files = self.client_machine.get_items_list(
                self.client_machine.join_path(
                    self.temp_mount_path, f'{self.id}_tmp_restore', f'{self.id}', 'full'))

            r = re.compile(rf".*{filters}")

            res = list(filter(r.match, files))

            if len(res) == 1 and exception in res[0]:
                self.log.info("Filters & Exceptions are honoured correctly")
            else:
                raise Exception("Filters & Exceptions are not honoured correctly")

        else:
            self.log.info("Comparing checksum & acl before and after restore")
            if self.fshelper.compare_lists(source_checksum, destination_checksum):
                self.log.info("Checksum comparision successful")
            else:
                raise Exception("Checksum comparision failed")
            if self.fshelper.compare_lists(source_acl, destination_acl):
                self.log.info("ACL comparision successful")
            else:
                raise Exception("ACL comparision failed")

        if not in_place:
            self.log.info("Removing temporary directory used for out-of-place restore")
            self.client_machine.remove_directory(
                self.client_machine.join_path(self.temp_mount_path, f'{self.id}_tmp_restore'))

        self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)

    def set_DANS_and_verify_subclient_properties(self, access_nodes: list):
        """
        Sets the data access nodes from fsSubclientDetailsPage and verifies the subclient properties

        Args:
            access_nodes (list) (str) : List of data access nodes
        
        Returns:
            None
        Raises:
            Exception while setting data access nodes / verifying subclient properties
        """

        self.fsSubclientOverview.edit_access_nodes(access_node_type="windows",
                                                   access_nodes=access_nodes)

        self.verify_subclient_properties(self.subclient, access_nodes)

    def run(self):
        try:

            self.login_to_commandcenter()

            self.log.info("Generating data for the full backup on the share.")

            self.fshelper.generate_data_on_share(self.client_machine,
                                                self.test_path,
                                                self.temp_mount_path,
                                                self.impersonate_user,
                                                self.impersonate_password)

            self.log.info("Accessing the subclientDetails page and checking the properties")

            self.access_subclient(cleanup=True)

            self.set_DANS_and_verify_subclient_properties(self.data_access_nodes)

            # Creating a machine dict to identify the master node after running a backup / restore job.
            self.machines_dict = {}

            for node in self.data_access_nodes:
                client_node = self.commcell.clients.get(node)
                node_machine = Machine(client_node)
                self.log.info(f"Log dir for {client_node} : {client_node.log_directory}")
                self.machines_dict[client_node.display_name] = node_machine

            self.log.info("Starting a full backup")
            self.run_backup(Backup.BackupType.FULL)

            self.log.info("Generating data for the incremental backup on the share.")

            self.fshelper.generate_data_on_share(self.client_machine,
                                                self.test_path,
                                                self.temp_mount_path,
                                                self.impersonate_user,
                                                self.impersonate_password,
                                                for_incr=True)

            self.access_subclient()

            self.log.info("Starting an incremental backup")
            self.run_backup(Backup.BackupType.INCR)

            self.access_subclient()

            self.log.info("Starting a synthetic full backup")
            self.run_backup(Backup.BackupType.SYNTH)

            self.log.info("Starting in_place restore with unconditional overwrite")
            self.run_restore_verify(self.test_path)

            self.log.info("Starting an out-of-place restore (Data & ACLS)")
            self.run_restore_verify(self.test_path, in_place=False)

            self.log.info(f"Removing the directory on {self.test_path} created for the testcase")
            self.fshelper.mount_cifs_share_on_drive(self.client_machine,
                                                    self.test_path,
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)
            self.client_machine.remove_directory(self.base_path)
            
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)

            # Changing UNC_base
            self.UNC_base_path = self.client_machine.join_path(self.test_path2, f'{self.id}')

            self.fshelper.generate_data_on_share(self.client_machine, 
                                                self.test_path2,
                                                self.temp_mount_path,
                                                self.impersonate_user,
                                                self.impersonate_password,
                                                data_with_extension=True)

            self.log.info("Changing subclient content")
            self.edit_subclient_content_and_exceptions(self.UNC_base_path, "*.img", "**\\file1.img")

            self.log.info("Starting an incremental backup")
            self.run_backup(Backup.BackupType.INCR, skip_logs_verf=True)

            # Using file1 as reference to get files inside the parent directory
            self.run_restore_verify(self.test_path2, in_place=False, only_validate_filters=True, filters='.img',
                                    exception='file1')

            self.log.info(f"Removing the directory on {self.test_path2} created for the testcase")

            self.fshelper.mount_cifs_share_on_drive(self.client_machine, 
                                                    self.test_path2, 
                                                    self.impersonate_user,
                                                    self.impersonate_password,
                                                    self.temp_mount_path)
            
            self.client_machine.remove_directory(self.base_path)
            
            self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)

            self.log.info("Deleting the subclient")
            self.access_subclient()
            self.fs_subclient_adv.delete_subclient()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        
        finally:
            if self.fshelper.is_drive_mounted(self.client_machine, self.temp_mount_path):
                self.fshelper.unmount_network_drive(self.client_machine, self.temp_mount_path)
            self.log.info("Logging out from the command center and and closing the browser")
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
