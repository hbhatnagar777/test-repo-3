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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case calls SnapHelper Class to execute
                            and Validate Below Operations.
                            Snap Backup, backup Copy by disassociating and associating subclient

    Test Case Flow:
        Set up the environment:
            Add hardware Array details to array management and update the snapconfig details.
            Create Restore/Mountpath/disk liberary location and Create entites like library,
           storage policy, snap and aux copy and enable intellisnap.
           Create backupset  and two subclients and enable instellisnap on the subclients.

        Test Case 1:
            Steps:
                1. Create a storage policy with backup copy enabled
                2.  Run J1  for SC1. Run jobs J2 and J3 for SC2.
                3. Disassociate Sc2 from backup copy.
                4. Run backup copy.

             Expected result:
                1. J1 and J2 jobs are picked for backup copy at step 2.
                2. After dis-associaton of Sc2, J1 and J2 jobs are unpicked for backup copy.
                3. Backup copy runs jobs only for SC1, if any.

        Test Case 2:
            Steps:
                1. Associate SC1 and SC2 to the SP1. Make sure by default both SC1 and SC2 are associated for backup copy.
                2. In the backup cop association tab, remove SC2 for backup copy.
                3. Run snapbackup for SC1 and SC2.
                4. Run backup copy.
                5 Check Backup copy runs only for SC1 and not for SC2.

            Expected result:
                1. After snap backup is completed, backup copy runs only for SC1 and SC2 jobs are not picked for
                 backup copy.

        Test Case 3:
            Steps:
                1. Associate SC1 and SC2 to SP1 with backup copy enabled.
                2. Dis-associate SC2 for backup copy.
                3. Run jobs J1 and J2 for SC2.
                4. Associate SC2 from backup copy.
                5. Run jobs  J3, J4.
                6. Run backup copy.

            Expected result:
                1. J1 and J2 are not picked for backup copy for SC2 at step 2.
                2. After backup copy association of SC2 is done, jobs J3 and J4 are picked for backup copy. Only future
                jobs are picked after association.
                3. Backup copy is successful for J3 and J4.

        Test Case 4:
            Steps:
                1. Dis-associate a subclient for backup copy.
                2. Run Full and some incrs and verify that those jobs are not picked for backup copy.
                3. Associate the subclient and run incremental.
                4. Run Backup copy


            Expected result:
                1. verify that the corresponding Full job is picked and Full and Incremental jobs are successfully
                moved to tape

        Test Case 5:
            Steps:
                1. Dis-associate a subclient for backup copy.
                2. Run Full and some incrs and verify that those jobs are not picked for backup copy.
                3. Manually pick the Full job and then mark it as do not backup copy.
                3. Associate the subclient and run incremental\differerntial job.
                4. Run backup copy


            Expected result:
                1. Verify that the corresponding Full job is not picked and verify that the incremental job is
                   skipped for backup copy and it is marked as do not backup copy since the corresponding Full is
                   marked as do not backup copy.



"""
import json
from copy import deepcopy

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils



class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of File scan for Snap file system backups test case using recursive
     scan
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None,
            "SubclientContent2": None,
            "SnapEngineAtSubclient2": None
        }
        self.name = """Automation : Subclient Association and disassociation from Backup copy
                    """


    def run(self):
        """Main function for test case execution"""


        try:
            self.log.info(f'Started executing {self.id} testcase')
            snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, snapconstants)
            self.client_machine = Machine(self.client)
            self.os_name = self.client_machine.os_info
            self.options_selector = OptionsSelector(self.commcell)
            self.entities = CVEntities(self.commcell)
            self.commonutils = CommonUtils(self.commcell)
            snap_helper.pre_cleanup()
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            snap_helper.add_array()
            if snapconstants.snap_engine_at_array == "Dell EMC VNX / CLARiiON":
                snapconstants.config_update_level = "subclient"
            if snapconstants.source_config is not None:
                x = json.loads(snapconstants.source_config)
                for config, value in x.items():
                    snap_helper.edit_array(snapconstants.arrayname, config, value,
                                           snapconstants.config_update_level)

            if snapconstants.vplex_engine is True:
                """ Adding First Backeend arrays """
                self.log.info("*" * 20 + "Adding backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName1']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName1']
                snapconstants.password = snapconstants.tcinputs['BackendArrayPassword1']
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendArrayControlHost1', None)
                snapconstants.snap_engine_at_array = snapconstants.tcinputs['BackendSnapEngineAtArray']
                snap_helper.add_array()
                """ Adding Second Backend array """
                self.log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    snapconstants.tcinputs['BackendSnapEngineAtArray']))
                snapconstants.arrayname = snapconstants.tcinputs['BackendArrayName2']
                snapconstants.username = snapconstants.tcinputs['BackendArrayUserName2']
                snapconstants.password =  snapconstants.tcinputs.get('BackendArrayPassword2')
                snapconstants.controlhost = snapconstants.tcinputs.get('BackendControlHost2', None)
                snap_helper.add_array()
            """ Re-Set arrayname and engine Name as primary """
            snapconstants.arrayname = snapconstants.tcinputs['ArrayName']
            snapconstants.snap_engine_at_array = snapconstants.tcinputs['SnapEngineAtArray']
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.log.info("Enabling Intellisnap on client: {0}".format(self.client.client_name))
            self.client.enable_intelli_snap()
            self.log.info("Successfully Enabled Intellisnap on client: {0}".format(
                self.client.client_name))
            snap_helper.create_locations()
            self.subclient1_content = self.tcinputs.get('SubclientContent', " ").replace(" ", "")
            self.subclient2_content = self.tcinputs.get('SubclientContent2', " ").replace(" ", "")
            self.sc1_entity_properties = {
                'target':
                    {
                        'force': False,
                        'mediaagent': str(self.tcinputs['MediaAgent'])
                    },
                'disklibrary':
                    {
                        'name': snapconstants.disk_lib_name,
                        'mount_path': snapconstants.disk_lib_loc
                    },
                'storagepolicy':
                    {
                        'name': snapconstants.storage_policy_name,
                        'library': str(snapconstants.disk_lib_name),
                        'copy_name': snapconstants.aux_copy_name,
                        'ocum_server': snapconstants.ocum_server,
                        'retention_period': 10,
                        'number_of_streams': 50
                    },
                'backupset':
                    {
                        'name': snapconstants.backupset_name,
                        'agent': self.agent.agent_name,
                        'client': self.client.client_name,
                        'instance': str(self.tcinputs['InstanceName'])
                    },
                'subclient':
                    {
                        'agent': self.agent.agent_name,
                        'name': '50658_SC1',
                        'content': self.subclient1_content.split(","),
                        'instance': str(self.tcinputs['InstanceName']),
                        'storagepolicy': snapconstants.storage_policy_name,
                        'backupset': snapconstants.backupset_name,
                        'client': self.client.client_name
                    },
            }
            self.sc1_entity_properties = self.entities.create(self.sc1_entity_properties)
            snapconstants.backupset = self.sc1_entity_properties['backupset']['object']
            self.sc1 = self.sc1_entity_properties['subclient']['object']
            snapconstants.disk_lib = self.sc1_entity_properties['disklibrary']['object']
            snapconstants.storage_policy = self.sc1_entity_properties['storagepolicy']['object']

            self.sc2_entity_properties = {
                'subclient':
                    {
                        'agent': self.agent.agent_name,
                        'name': '50658_SC2',
                        'content': self.subclient2_content.split(","),
                        'instance': str(self.tcinputs['InstanceName']),
                        'storagepolicy': snapconstants.storage_policy_name,
                        'backupset': snapconstants.backupset_name,
                        'client': self.client.client_name
                    },
            }
            self.sc2_entity_properties = self.entities.create(self.sc2_entity_properties)
            self.sc2 = self.sc2_entity_properties['subclient']['object']
            self.log.info("*" * 20 + "Creating Snap copy" + "*" * 20)
            snap_helper.create_snap_copy(snapconstants.snap_copy_name, False, True,
                                  snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']),
                                         source_copy="Primary",
                                  job_based_retention=snapconstants.job_based_retention
                                  )
            self.log.info("Successfully created Snap Copy ")
            snap_helper.delete_bkpcpy_schedule()

            self.log.info("Enabling Intellisnap on subclient: {0} and setting Snap engine: {1}".format(
                self.sc1.subclient_name,
                self.tcinputs['SnapEngineAtSubclient']))
            proxy_options = {
                'snap_proxy': self.tcinputs['MediaAgent'],
                'backupcopy_proxy': self.tcinputs['MediaAgent'],
                'use_source_if_proxy_unreachable': True
            }
            self.sc1.enable_intelli_snap(
                self.tcinputs['SnapEngineAtSubclient'], proxy_options)
            self.log.info("Successfully Enabled Intellisnap on subclient: {0} and set Snap engine: {1}\
                                  ".format(self.sc1.subclient_name,
                                           self.tcinputs['SnapEngineAtSubclient'])
                          )

            self.log.info("Enabling Intellisnap on subclient: {0} and setting Snap engine: {1}".format(
                self.sc2.subclient_name,
                self.tcinputs['SnapEngineAtSubclient2']))
            proxy_options = {
                'snap_proxy': self.tcinputs['MediaAgent'],
                'backupcopy_proxy': self.tcinputs['MediaAgent'],
                'use_source_if_proxy_unreachable': True
            }
            self.sc2.enable_intelli_snap(
                self.tcinputs['SnapEngineAtSubclient2'], proxy_options)
            self.log.info("Successfully Enabled Intellisnap on subclient: {0} and set Snap engine: {1}\
                                              ".format(self.sc2.subclient_name,
                                                       self.tcinputs['SnapEngineAtSubclient2'])
                          )

            #Step 1

            self.log.info(f'\n')
            self.log.info("*" * 20 + "Performing Step 1 of the Test case" + "*" * 20)
            self.log.info("*" * 20 + f"Running FULL Snap Backup job for subclient: {self.sc1.subclient_name}" + "*" * 20)
            snapconstants.subclient = self.sc1
            snapconstants.backup_level = 'FULL'
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full11_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full11_job.job_id, snapconstants.snap_copy_name)
            self.log.info(
                "*" * 20 + f"Running FULL Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            snapconstants.subclient = self.sc2
            snap_helper.add_test_data_folder()
            snap_helper.update_test_data(mode='add')
            full21_job = snap_helper.snap_backup()
            if snapconstants.vplex_engine is True:
                snap_helper.vplex_snap_validation(full21_job.job_id, snapconstants.snap_copy_name)

            self.log.info(
                "*" * 20 + f"Running Incremental Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='edit')
            inc21_job = snap_helper.snap_backup()
            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                              disassociate_sc_from_backup_copy=True)
            self.log.info("Running backup copy and validating if the correct job is picked for the operation")
            snap_helper.backup_copy()

            self.log.info("===" * 10 + "validating the backup copy operation" + "===" * 10)
            get_backcopied_jobs = snapconstants.execute_query(
                snapconstants.get_backupcopied_jobs_for_sp, {'a': snapconstants.storage_policy.storage_policy_id})
            if len(get_backcopied_jobs) == 1 and get_backcopied_jobs[0][0] == full11_job.job_id :
                self.log.info(f"Backup copy ran for subclient {self.sc1.subclient_name} as expected. validation is successfull ")
            else:
                raise Exception(f"Backup copy ran for all the subclients. Validation for disassociating subclient failed")


            # # Steps 2

            self.log.info(f'\n')
            self.log.info("*" * 20 + "Performing Step 2 of the Test case" + "*" * 20)
            self.log.info("Running snap backup and backup copy after disassociating the subclient from backup copy "
                          "for which backup copy should not be run " )
            self.log.info(f"Subclient {self.sc2.subclient_name} is already disassociated from backup copy from previous step."
                          f"Continuing with Snap backups")
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            snapconstants.backup_level = 'FULL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            full22_job = snap_helper.snap_backup()

            snapconstants.subclient = self.sc1
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc1.subclient_name}" + "*" * 20)
            full12_job = snap_helper.snap_backup()

            self.log.info("Running backup copy and validating if the job is picked for the operation")
            snap_helper.backup_copy()
            # Need to update the job Id list picked for backup copy to remove the jobs that were part of steps 1

            self.log.info("===" * 10 + "validating the backup copy operation" + "===" * 10)
            get_backcopied_jobs2 = snapconstants.execute_query(
                snapconstants.get_backupcopied_jobs_for_sp, {'a': snapconstants.storage_policy.storage_policy_id})
            updated_backupcopied_jobs = deepcopy(get_backcopied_jobs2)
            for job in get_backcopied_jobs:
                updated_backupcopied_jobs.remove(job)
            if len(updated_backupcopied_jobs) == 1 and updated_backupcopied_jobs[0][0] == full12_job.job_id :
                self.log.info(f"Backup copy ran for subclient {self.sc1.subclient_name} as expected. validation is successfull ")
            else:
                raise Exception(f"Backup copy ran for all the subclients. Validation for disassociating subclient failed")

            # #Step 3

            self.log.info(f'\n')
            self.log.info("*" * 20 + "Performing Step 3 of the Test case" + "*" * 20)
            job_list = []
            snapconstants.backup_level = 'FULL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc1.subclient_name}" + "*" * 20)
            full13_job = snap_helper.snap_backup()
            job_list.append((full13_job.job_id))

            snapconstants.subclient = self.sc2
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            full23_job = snap_helper.snap_backup()
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running one more Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            full24_job = snap_helper.snap_backup()
            self.log.info(f'Associating the subclient  {self.sc2.subclient_name} back to storage policy ')
            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                               disassociate_sc_from_backup_copy=False)

            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name} after associating it "
                           f"for backup copy" + "*" * 20)
            snap_helper.update_test_data(mode='add')
            full25_job = snap_helper.snap_backup()
            job_list.append(full25_job.job_id)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running incremental Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            inc25_job = snap_helper.snap_backup()
            job_list.append(inc25_job.job_id)

            self.log.info(
                "*" * 20 + "Running Backup Copy now to check if correct snapshots are getting picked up or not" + "*" * 20)

            snap_helper.backup_copy()
            get_backcopied_jobs3 = snapconstants.execute_query(
                snapconstants.get_backupcopied_jobs_for_sp, {'a': snapconstants.storage_policy.storage_policy_id})
            #Need to update the job Id list to remove jobs that were part of steps 1 & 2
            updated_backupcopied_jobs = deepcopy(get_backcopied_jobs3)
            for job in get_backcopied_jobs2:
                updated_backupcopied_jobs.remove(job)

            self.log.info("===" * 10 + "Validating the backup copy operation" + "===" * 10)
            if len(updated_backupcopied_jobs) == 3:
                for i in range(len(updated_backupcopied_jobs)):
                    if updated_backupcopied_jobs[i][0] == job_list[i]:
                        pass
                    else:
                        raise Exception(f"Backup copy ran for all the subclients. Validation for "
                                        f"disassociating subclient failed")
                self.log.info(
                    f"Backup copy ran for subclient {self.sc1.subclient_name} and for those snap backups which ran after "
                    f"associating the "
                    f"subclient {self.sc2.subclient_name} for backup copy. validation is successfull ")
            else:
                raise Exception(
                    f"Backup copy did not run as expected. Validation for disassociating subclient failed")

            # Step 4
            self.log.info(f'\n')
            self.log.info("*" * 20 + "Performing Step 4 of the Test case" + "*" * 20)
            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                              disassociate_sc_from_backup_copy=True)
            job_list = []
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            snapconstants.backup_level = 'FULL'
            snap_helper.update_test_data(mode='add')
            full26_job = snap_helper.snap_backup()
            job_list.append(full26_job.job_id)

            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Incremental Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            inc26_job = snap_helper.snap_backup()

            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                              disassociate_sc_from_backup_copy=False)
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Incremental Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            inc27_job = snap_helper.snap_backup()
            job_list.append(inc27_job.job_id)

            self.log.info(
                "*" * 20 + "Running Backup Copy now to check if the Full gets picked up or not" + "*" * 20)
            snap_helper.backup_copy()

            self.log.info("===" * 10 + "validating the backup copy operation" + "===" * 10)
            get_backcopied_jobs4 = snapconstants.execute_query(
                snapconstants.get_backupcopied_jobs_for_sp, {'a': snapconstants.storage_policy.storage_policy_id})
            # Need to update the job Id list to remove jobs that were part of steps 1, 2 and 3
            updated_backupcopied_jobs = deepcopy(get_backcopied_jobs4)
            for job in get_backcopied_jobs3:
                updated_backupcopied_jobs.remove(job)

            if len(updated_backupcopied_jobs) == 2:
                for i in range(len(updated_backupcopied_jobs)):
                    if updated_backupcopied_jobs[i][0] == job_list[i]:
                        pass
                    else:
                        raise Exception(f"Backup copy did not run correctly. Validation for "
                                        f"disassociating subclient failed")
                self.log.info(
                    f"Backup copy ran correctly by picking the Full. Validation for "
                                        f"disassociating subclient successfull.")
            else:
                raise Exception(
                    f"Backup copy ran for all the subclients. Validation for disassociating subclient failed")


            #Step5
            self.log.info(f'\n')
            self.log.info("*" * 20 + "Performing Step 5 of the Test case" + "*" * 20)
            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                              disassociate_sc_from_backup_copy=True)

            #Track Jobs through job_list which qualify for backup copy. This list will be used during the validation below.
            job_list = []
            snapconstants.backup_level = 'FULL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running Full Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            full27_job = snap_helper.snap_backup()
            job_list.append(full27_job.job_id)

            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            self.log.info(
                "*" * 20 + f"Running incremental Snap Backup job for subclient: {self.sc2.subclient_name}" + "*" * 20)
            inc27_job = snap_helper.snap_backup()
            job_list.append(inc27_job.job_id)

            for job_id in job_list:
                unpick_status = snapconstants.execute_query(
                    snapconstants.get_materialization_status_job, {'a': job_id})
                if unpick_status[0][0] in [None, ' ', '']:
                    self.log.info(f"Job {job_id} is not picked for backup copy as expected as subclient is disassociated")
                else:
                    raise Exception(f"Job {job_id} is picked for backup copy, even though the subclient is "
                                     f"disassociated. Validation failed ")

            self.log.info("Manually Picking the full job")
            primary_copy = snapconstants.storage_policy.get_primary_copy()
            primary_copy.pick_jobs_for_backupcopy(full27_job.job_id)
            unpick_status = snapconstants.execute_query(
                snapconstants.get_materialization_status_job, {'a': full27_job.job_id})
            if int(unpick_status[0][0]) == 0:
                self.log.info(f'Job {full27_job.job_id} is successfully picked for backup copy')
            else:
                raise Exception(f'Job {full27_job.job_id} could not be picked for backup copy. Validation failed')

            primary_copy.do_not_copy_jobs(full27_job.job_id)

            self.log.info(f'Marked job {full27_job.job_id} as Do Not Backup copy')
            self.log.info(f'Associating the subclient  {self.sc2.subclient_name} for backup copy')
            snap_helper.update_storage_policy(enable_backup_copy=True, enable_snapshot_catalog=True,
                                              disassociate_sc_from_backup_copy=False)
            self.log.info("Running Incremental after associating the subclient for backup copy")
            snapconstants.backup_level = 'INCREMENTAL'
            snap_helper.update_test_data(mode='add')
            inc28_job = snap_helper.snap_backup()
            job_list.append(inc28_job.job_id)

            try:
                self.log.info("*" * 10 + "Running backup copy" + "*" * 10)
                snap_helper.backup_copy()
            except:
                self.log.info("===" * 10 + "validating the backup copy operation" + "===" * 10)
                unpick_status = snapconstants.execute_query(
                    snapconstants.get_materialization_status_job, {'a': inc28_job.job_id})
                if int(unpick_status[0][0]) == 5:
                    self.log.info(
                        f'Job {inc28_job.job_id} is not picked for backup copy as its corresponding Full job job '
                        f'{full27_job.job_id} is marked as Do Not copy. Backup copy Validation is successful')
                else:
                    raise Exception(
                        f'Job {inc28_job.job_id} is picked for backup copy even though  its corresponding Full job '
                        f'{full27_job.job_id} is marked as Do Not copy. Validation failed.')

            self.log.info("Test Case Completed Successfully. Cleaning up the setup")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
            self.log.warning("Testcase did not complete successfully. Cleaning up the setup")

        finally:
            try:
                # Disable Intellisnap on Subclient
                self.log.info(f"Disabling Intellisnap on subclients: {self.sc1.subclient_name} & "
                          f"{self.sc2.subclient_name}")

                self.sc1.disable_intelli_snap()
                self.sc2.disable_intelli_snap()

                self.log.info(f"Successfully Disabled Intellisnap on subclients: {self.sc1.subclient_name} & "
                            f"{self.sc2.subclient_name}")

                self.entities.delete({'subclient': self.sc1_entity_properties['subclient']})
                self.entities.delete({'subclient': self.sc2_entity_properties['subclient']})
                self.entities.delete({'backupset': self.sc1_entity_properties['backupset']})
                snap_helper.delete_array
                snap_helper.cleanup

            except Exception as e:
                self.log.info("Cleanup failed with err: " + str(e))
                self.log.info("treating it as soft failure")

