# coding=utf-8
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

    is_v2_indexing()    -- check if V2 indexing is enabled

    setup_environment() -- configures all entities to run the case

    run_backup()    -- runs backup on VSA iDA client

    run_data_aging()    -- runs data aging job for storage policy and copy

    get_child_job() -- returns list of child jobs for a parent job

    clean() -- cleans up all created entities

TC Input JSON:
"58719": {
            "MediaAgentName": "<MA Name>",
            "VMtoBackup": "<VM Name or pattern>",
        }
"""

from cvpysdk.constants import VSAObjects
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "ArchiveManager - Spool copy for VSA agent basic case"
        self.tcinputs = {
            "MediaAgentName": None,
            "VMtoBackup": None
        }
        self.vmagent_name = 'virtual server'
        self.library = None
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.mmhelper = None
        self.content = None
        self.primary_copy = None
        self.secondary_copy = None
        self.subclient = None
        self.backupset = None
        self.vmclient = None
        self.vmagent = None
        self.mmhelper = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mount_path = None

    def setup(self):
        """Setup function of this test case"""
        # entity names
        self.library_name = str(self.id) + "_lib"
        self.storage_policy_name = str(self.id) + "_SP"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"

        # initialize MMHelper class
        self.mmhelper = MMHelper(self)

        # vm client objects
        self.vmclient = self.client
        self.vmagent = self.vmclient.agents.get(self.vmagent_name)

        # select storage drive
        utility = OptionsSelector(self.commcell)
        media_agent = self.commcell.clients.get(self.tcinputs['MediaAgentName'])
        media_agent_machine = Machine(media_agent, self.commcell)
        mount_path_drive = utility.get_drive(media_agent_machine, size=30720)
        if not mount_path_drive:
            raise Exception("no free space on MA to create library")
        self.log.info("selected backup content drive: %s", mount_path_drive)
        self.mount_path = media_agent_machine.join_path(mount_path_drive, f'{self.id}MP')

    def is_v2_indexing(self):
        """
        check if V2 indexing is enabled and return true or false
        """
        query = f"""select attrval from app_clientprop
                where componentNameId = {self.vmclient.client_id} 
                    and attrname like 'IndexingV2_VSA'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", result[0])
        if result[0] != '' and int(result[0]) == 1:
            return True
        return False

    def setup_environment(self):
        """configures environment by making sure VSA v2 iDA"""
        if self.vmagent.agent_name != self.vmagent_name:
            raise Exception('iDataAgent is not virtual server')
        self.log.info("agent is virtual server")

        if not self.is_v2_indexing():
            raise Exception('V2 indexing not enabled')
        self.log.info("V2 indexing is enabled")

        self.library = self.mmhelper.configure_disk_library(self.library_name,
                                                            self.tcinputs["MediaAgentName"],
                                                            self.mount_path)

        self.storage_policy = self.mmhelper.configure_storage_policy(self.storage_policy_name,
                                                                     self.library_name,
                                                                     self.tcinputs["MediaAgentName"])

        self.secondary_copy = self.mmhelper.configure_secondary_copy('sec-copy',
                                                                     self.storage_policy_name,
                                                                     self.library_name,
                                                                     self.tcinputs['MediaAgentName'])

        # update retention to 1 day, 0 cycle
        self.log.info("setting secondary copy retention: 1 day, 0 cycle")
        self.secondary_copy.copy_retention = (1, 0, 1)

        # update primary to spool copy
        self.log.info("setting primary copy retention to 0 day, 0 cycle (Spool copy)")
        self.primary_copy = self.storage_policy.get_copy('Primary')
        self.primary_copy.copy_retention = (0, 0, 0)

        # disable managed disk space
        self.primary_copy.copy_retention_managed_disk_space = False

        self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.vmagent)

        self.content = {
            'type': VSAObjects.VMName,
            'name': f"*{self.tcinputs['VMtoBackup']}*",
            'display_name': f"*{self.tcinputs['VMtoBackup']}*"
        }

        self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                           self.subclient_name,
                                                           self.storage_policy_name,
                                                           self.content,
                                                           self.vmagent)
        # remove auto-copy schedule association
        self.mmhelper.remove_autocopy_schedule(self.storage_policy_name, 'sec-copy')

    def run_backup(self, backup_type="FULL"):
        """
        Runs backup on VSA iDA client
        Args:
            backup_type (str): type of backup to run

        Returns:
        (object) -- returns job object to backup job
        """
        self.log.info("Running %s VSA backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("VSA Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} VSA backup with error: {job.delay_reason}")
        self.log.info("VSA Backup job completed.")
        return job

    def run_data_aging(self, storage_policy=None, copy=None):
        """
        runs data aging job for a given storage policy, copy. if no storage policy is provided,
        runs data aging for entire commcell.

        Args:
            storage_policy  - storage policy name for granular data aging job

            copy    - copy name for granular data aging job
        """
        if storage_policy:
            da_job = self.commcell.run_data_aging(copy_name=copy,
                                                  storage_policy_name=storage_policy,
                                                  is_granular=True,
                                                  include_all_clients=True)
        else:
            da_job = self.commcell.run_data_aging()
        self.log.info("data aging job: %s", da_job.job_id)
        if not da_job.wait_for_completion():
            raise Exception(f"Failed to run data aging with error: {da_job.delay_reason}")
        self.log.info("Data aging job completed.")

    def get_child_jobs(self, parent_job):
        """
        returns list of child jobs for a parent job

        Args:
            param parent_job    - VSA parent backup job id

        Returns (list): list of child job ids
        """
        query = f"select childJobId from JMJobDataLink where parentJobId = {parent_job}"
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info("RESULT: %s", result)
        return result

    def cleanup(self):
        """cleans up all created entities"""
        self.log.info("cleanup started")
        if self.vmagent.backupsets.has_backupset(self.backupset_name):
            self.log.info("deleting backupset...")
            self.vmagent.backupsets.delete(self.backupset_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            # re-associate subclients to Not Assigned state
            request_xml = '''<App_ReassociateStoragePolicyReq>
                                <forceNextBkpToFull>1</forceNextBkpToFull>
                                <runSyntheticFullForTurbo/>
                                <currentStoragePolicy>
                                    <storagePolicyName>{0}</storagePolicyName>
                                </currentStoragePolicy>
                                <newStoragePolicy>
                                    <storagePolicyName>CV_DEFAULT</storagePolicyName>
                                </newStoragePolicy>
                            </App_ReassociateStoragePolicyReq>
                            '''.format(self.storage_policy_name)
            self.commcell.qoperation_execute(request_xml)
            self.log.info("deleting storage policy...")
            self.commcell.storage_policies.delete(self.storage_policy_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("deleting library...")
            self.commcell.disk_libraries.delete(self.library_name)
        self.log.info("cleanup done.")

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.setup_environment()

            # Run FULL backup
            parent_backup_job = self.run_backup()
            child_backup_jobs = self.get_child_jobs(parent_backup_job.job_id)

            # Run Incr backup
            parent_incr_job = self.run_backup("incremental")
            child_incr_jobs = self.get_child_jobs(parent_incr_job.job_id)

            # run data aging
            self.run_data_aging(self.storage_policy_name, 'Primary')

            self.log.info("VALIDATION: backup job not yet aged")
            # validate backup
            self.log.info("Validating full backups...")
            for backup_job in child_backup_jobs:
                retcode = self.mmhelper.validate_job_prune(int(backup_job[0]), int(self.primary_copy.copy_id))
                if not retcode:
                    self.log.info("Validation success")
                else:
                    raise Exception(f"Backup job {backup_job} is not expected to age")

            # Run aux copy
            self.log.info("Running Auxcopy job...")
            aux_job = self.storage_policy.run_aux_copy('sec-copy',
                                                       self.tcinputs['MediaAgentName'],
                                                       False, 0)
            self.log.info("Auxcopy job: %s", aux_job.job_id)
            if not aux_job.wait_for_completion():
                raise Exception(f"Failed to run Auxcopy with error: {aux_job.delay_reason}")

            # run data aging
            self.run_data_aging(self.storage_policy_name, 'Primary')

            self.log.info("VALIDATION: backup, incr job should be aged")
            # validate backup
            self.log.info("Validating full backups...")
            for backup_job in child_backup_jobs:
                retcode = self.mmhelper.validate_job_prune(int(backup_job[0]),
                                                           int(self.primary_copy.copy_id))
                if retcode:
                    self.log.info("Validation success")
                else:
                    raise Exception(f"Backup job {backup_job} did not age")

            # validate incr
            self.log.info("Validating incr backups...")
            for incr_job in child_incr_jobs:
                retcode = self.mmhelper.validate_job_prune(int(incr_job[0]), int(self.primary_copy.copy_id))
                if retcode:
                    self.log.info("Validation success")
                else:
                    raise Exception(f"Incr job {incr_job} did not age")

            # cleanup
            self.cleanup()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
