# coding=utf-8
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    setup_environment() -- configures entities based on inputs

    cleanup()   --  cleanups all created entities

    run_backup()    -- runs backup need for the case

    validate_multiple_streams()     -- Validates multiple streams for a synthfull job

Sample JSON: values under [] are optional
"63328": {
            "ClientName": "",
            "AgentName": "File System",
            "MediaAgentName": "",
            "CloudLibraryName": ""
            ["DDBPath": "",
            "ScaleFactor": "12",
            "UseScalable": true]
        }


Note:
    1. providing cloud library is must as there are various vendors for configuration. best is to have it ready
    [mmhelper.configure_cloud_library can be used if need to create library]
    2. for linux, its mandatory to provide ddb path for a lvm volume
    3. ensure that MP on cloud library is set with pruner MA


    SQL Connection :
        In order to ensure security,
        sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates
        populate the following fields in config file as required,
        "SQL": {
               "Username": "<SQL_SERVER_USERNAME>",
                "Password": "<SQL_SERVER_PASSWORD>"
            }

        At the time of execution the creds will be automatically fetched by TC.



    design:
    Cleanup previous run environment
    Create test environment
    Run backup B1 with 10GB data
    Wait for backup job to complete and notedown how many records get added from DB
    Run 10 incremental jobs : 1GB
    Wait for backup job to complete and notedown how many records get added by incremental job from  DB
    Run multi stream syntheticfull job
    Validate multiple stream get launched
    Wait SF job to complete
    Check if records are added during SF or not
    Restore Data from multi Stream SF

"""
import time
import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.mahelper import DedupeHelper
from AutomationUtils import config
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Run Multi Stream Synthetic Full job"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.ddb_path = None
        self.common_utils_obj = None
        self.scale_factor = None
        self.mmhelper = None
        self.dedupehelper = None
        self.client_machine = None
        self.library = None
        self.storage_policy = None
        self.storage_pool_name = None
        self.ma_name = None
        self.backupset = None
        self.subclient = None
        self.primary_copy = None
        self.gdsp = None
        self.sp_obj_list = []
        self.ma_machine = None
        self.sql_password = None
        self.mountpath = None
        self.is_user_defined_mp = None
        self.is_user_defined_dedup = None
        self.store_obj = None


    def setup(self):
        """ Setup function of this test case. """
        # input values
        # self.library_name = self.tcinputs.get('CloudLibraryName')

        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        # get value or set None
        self.ddb_path = self.tcinputs.get('DDBPath')
        self.scale_factor = self.tcinputs.get('ScaleFactor')

        # defining names
        self.client_machine = Machine(self.client)
        self.subclient_name = f"{self.id}_SC_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.backupset_name = f"{str(self.id)}_BS_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.storage_policy_name = f"{str(self.id)}_SP_{self.tcinputs.get('MediaAgentName')[::-1]}"
        self.storage_pool_name = f"StoragePool_TC_{self.id}_{str(self.tcinputs.get('MediaAgentName'))}"
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.ma_machine = Machine(self.ma_name, self.commcell)
        self.library_name = f"Lib_TC_{self.id}_{str(self.tcinputs.get('CloudLibraryName'))}"
        self.optionobj = OptionsSelector(self.commcell)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine, 122880)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine, 122880)
        self.dedup_helper = DedupeHelper(self)
        self.common_utils_obj = CommonUtils(self)

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mountpath = self.ma_machine.join_path(self.tcinputs.get("mount_path"), self.id)
        else:
            self.mountpath = self.ma_machine.join_path(self.ma_library_drive, self.id)

        # select drive on client & MA for content and DDB
        self.content_path = self.client_machine.join_path(self.client_system_drive, 'automation',
                                                         self.id, 'content_path')

        if not self.ddb_path:
            if "unix" in self.ma_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not provided for Unix MA!..")
            self.ddb_path = self.ma_machine.join_path(self.ma_library_drive, 'DDB')
        else:
            self.log.info("will be using user specified path [%s] for DDB path configuration", self.ddb_path)

        # helper objects
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)


    def setup_environment(self):
        """
        Configures all entities based on tcInputs. If path is provided TC will use this path instead of self selecting
        """
        self.log.info("setting up environment...")
        if not self.ma_machine.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine.create_directory(self.mountpath)

        self.log.info("Creating a storage pool")

        if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
            self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mountpath,
                                            self.ma_name,
                                            self.ma_name,
                                            self.ddb_path)
        else:
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)

        self.log.info("Done creating a storage pool")

        self.log.info("Configuring Storage Policy ==> %s", self.storage_policy_name)

        self.library_name = self.storage_pool_name

        self.commcell.disk_libraries.refresh()

        self.library = self.commcell.disk_libraries.get(self.library_name)

        if not self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                               library=self.library_name,
                                               media_agent=self.ma_name,
                                               global_policy_name=self.storage_pool_name,
                                               dedup_media_agent=self.ma_name,
                                               dedup_path=self.ddb_path)
        else:
            self.storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)

        if not self.ma_machine.check_directory_exists(self.ddb_path):
            self.ma_machine.create_directory(self.ddb_path)

        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (1, 0, 1)

        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content_path,
                                                           self.agent)
        self.subclient.data_readers = 20
        self.subclient.allow_multiple_readers = True

    def validate_multiple_streams(self, job_id):
        """
        Validates if multiple streams are launched for a synthetic full job
        Args:
            job_id (int) : Synthetic full job id
        Raises:
            Exception if Only one stream is launch
        """
        query = f"select streamReaderID from ArchChunkToSF where AdminJobId = {job_id} order by streamReaderID DESC"
        self.log.info("QUERY => %s", query)
        dbres = self.mmhelper.execute_select_query(query)
        self.log.info(f"Query output : {dbres}")
        if int(dbres[0][0]) < 2:
            raise Exception(f"Only one stream is launched for the synthetic full job {job_id}")
        self.log.info(f"More than 1 stream is launched for the synthetic full job {job_id}")

    def cleanup(self):
        """Performs cleanup of all entities"""
        try:
            self.log.info("cleanup started")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("deleting content")
                self.client_machine.remove_directory(self.content_path)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("deleting backupset: %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("deleting storage policy: %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info("deleting storage pool: %s", self.storage_pool_name)
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            if self.client_machine.check_directory_exists(self.mountpath):
                self.log.info("deleting mount path")
                self.client_machine.remove_directory(self.mountpath)

            if self.client_machine.check_directory_exists(self.ddb_path):
                self.log.info("deleting ddb path")
                self.client_machine.remove_directory(self.ddb_path)

            self.log.info("cleanup completed")


        except Exception as exe:
            self.log.warning("error in cleanup: %s. please cleanup manually", str(exe))

    def run_backup(self, path = None, backup_type="FULL", scale_factor=10):
        """Run backup by generating new content to get unique blocks for dedupe backups.
        If ScaleFactor in tcInputs, creates factor times of backup data

        Args:

            path (str): path to generate the test data

            backup_type (str): type of backup to run
                Default - FULL

            scale_factor (int): size of backup content to generate
                Default - 1 GB

        Returns:
            (Job): returns job object of the backup job
        """

        if backup_type == "Synthetic_full":
            multi_stream_sfull = self.common_utils_obj.subclient_backup(
                self.subclient,
                backup_type="Synthetic_full",
                wait=False,
                advanced_options={
                    'use_multi_stream': True,
                    'use_maximum_streams': True
                }
            )
            multi_stream_sfull.wait_for_completion()
            return multi_stream_sfull

        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
        self.client_machine.create_directory(path)

        # if scale test param is passed in input json, multiple size factor times and generate content
        size = 1.0
        if scale_factor:
            size = size * int(scale_factor)

        self.mmhelper.create_uncompressable_data(self.client, path, size, 1)
        self.log.info("Done generating data. Running backup")

        job = self.subclient.backup(backup_type)
        self.log.info(f"Backup job {job.job_id} has started. Waiting for completion.")
        return job


    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()
            backup_job_list = []

            additional_content = self.client_machine.join_path(self.content_path, 'generated_content')
            self.client_machine.create_directory(additional_content)

            full_path = self.client_machine.join_path(additional_content, "full")

            job_full = self.run_backup(full_path)
            backup_job_list.append(job_full.job_id)
            if not job_full.wait_for_completion():
                raise Exception(f"Backup job {job_full.job_id} was {job_full.status}. JPR: {job_full.delay_reason}")
            self.log.info(f"Backup job {job_full.job_id} has completed")

            for num in range(1, 12):
                self.log.info("*" * 25)
                incr_path = self.client_machine.join_path(additional_content, "incr{}".format(str(num)))
                job_incr = self.run_backup(incr_path, "Incremental")
                if not job_incr.wait_for_completion():
                    raise Exception(f"Backup job {job_incr.job_id} was {job_incr.status}. JPR: {job_incr.delay_reason}")
                self.log.info(f"Backup job {job_incr.job_id} has completed")
                self.log.info("-" * 25)

            job_synth = self.run_backup(backup_type="Synthetic_full")
            self.validate_multiple_streams(job_synth.job_id)

            if not job_synth.wait_for_completion():
                raise Exception(f"Backup job {job_synth.job_id} was {job_synth.status}. JPR: {job_synth.delay_reason}")
            self.log.info(f"Backup job {job_incr.job_id} has completed")

            self.log.info("The testcase has passed successfully!")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED')
        else:
            self.log.warning('Test Case FAILED')
        self.cleanup()
