# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing IntelliSnap operations

SNAPHelper is the only class defined in this file

SNAPHelper: Helper class to perform IntelliSnap operations

SNAPHelper:
    __init__()                   --  initializes Snap helper object

    setup()                      --  Setup function which calls create_locations() and
                                     create_snap_environment()

    create_locations()           --  Create MountPath, Restore and DisKlibrary Locations
                                     if does not exists

    create_snap_copy()           --  wrapper for creating snap, snapvault, snapmirror, replica,
                                     and replica mirror copies

    create_secondary_snap_copy()       --  creates snapvault, snapmirror, replica,
                                     and replica mirror copies

    create_snap_environment()    --  includes Add Array, Enabling IntelliSnap at Subclient
                                     Create Library, Storage Policy, Snap Copy, Aux Copy, BackupSet
                                     Subclient, set content and Enable IntelliSnap on it,
                                     add test data folder to subclient content

    kill_job()                   --  Starts a SnapBackup job and kills it after Snap Phase
                                     completes and adds the job in to
                                     Job_Tracker to check while DA validation

    suspend_job()                --  Suspends a snap Backup/ backup copy/restore/ aux copy job
    resume_job()                 --  Resumes a suspended job

    delete_copy()                --  deletes storage policy copysnap

    snap_backup()                --  Runs SnapBackup based on the following inputs
                                     if only inlinebkpcpy is True, Runs Backup with Catalog and
                                     inline backup copy
                                     if only skipCatalog is True, Runs Backup with Skip Catalog
                                     if Both inlinebkpcpy, skipCatalog are True, Runs Backup with
                                     skip catalog and inline backup copy
                                     if Both inlinebkpcpy, skipCatalog are False, Runs Backup with
                                     Catalog, Also if inline is true, monitors backup copy job.

    snap_outplace()              --  OutPlace Restore from Snap copy

    snap_inplace()               --  Inplace Restore from Snap copy

    time_formattor()             --  Takes job times as input and Formats it for Browse

    snap_inplace_validation()    --  Validate inplace restored content from snap by
                                     mounting the snapshot

    snap_outplace_validation()   --  Validate outplace restored content from snap with
                                     subclient content

    compare()                    --  Compares two directories

    tape_outplace()              --  Outplace Restore from tape copy

    tape_inplace()               --  Inplace restore from tape copy

    tape_outplace_validation()   --  Validate outplace restored content with the subclient content

    tape_inplace_validation()    --  Validate inplace restored content

    mount_snap()                 --  Mounts Snap of the given job_id and Copy

    unmount_snap()               --  UnMounts Snap of the given job_id and Copy

    revert_snap()                --  Reverts Snap of the given job_id and Copy

    delete_snap()                --  Deletes Snap of the given job_id and Copy

    force_delete_snap()          --  Force Deletes Snap of the given job id and Copy

    mount_validation()           --  Validates mounted snap with subclient content

    unmount_validation()         --  Validates if snap is unmounted

    revert_validation()          --  Validates reverted snap by mounting the snap

    delete_validation()          --  Validates if the snap is deleted

    unmount_status()             --  checks if the snap is unmounted

    update_storage_policy()      --  Method for Updating Backup copy and Snapshot Catalog options

    backup_copy()                --  Runs Offline backup copy for the given storage policy

    snapshot_cataloging()        --  Runs Offline Snapshot Cataloging for the given storage policy

    aux_copy()                   --  Runs Aux copy for the given storage policy and copy

    data_aging()                 --  Runs Data aging for the given storage policy and copy

    get_volumeid_list()          --  Fetches jobid's for the snap copy

    data_aging_validation()      --  Validates Pruning of Snap jobs

    clean_snap_environment()     --  includes disable intellisnap at subclient, delete subclient,
                                     backupset, auxcopy, snapcopy, storage policy, library,
                                     disable intellisnap at client and delete array

    clear_locations()            --  Deletes MountPath, Restores and DiskLibrary locations

    cleanup()                    --  Calls clean_snap_environment() and clear_locations()

    add_array()                  --  To add array in the array management

    delete array()               --  To delete array entry from the array managament

    spcopy_obj()                 --  Creates storage policy Copy Object

    remove_subclient_content()   --  deletes data under subclient content

    vplex_snap_validation()      --  snap validation on VPLEX Metro cluster

    svm_association()            --  Add SVM association to Replica Copy for Netapp Open Replication

    update_mmconfig()            --  Updates MMConfig MM config 'MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES'
                                     with provided value

    run_pruning()                --  Runs data aging for the given storage policy and copy and
                                     waits for the snaps to prune

    edit_array()                 --  Method to Update Snap Configuration and array Controller for
                                     the given array

    update_test_data()           --  Method to edit and delete test data

    delete_bkpcpy_schedule()     --  delete backup copy schedule as it interferes with the
                                     test case flow

    disable_auxcpy_schedule()    --  disable Auxilliary copy schedule policy as it interferes
                                     with the test case flow

    snap_extent_template()       -- Template to run extent cases for intellisnap

    verify_extentbased_subclient()      -- Verify all the extents are backed up from source_list

    update_metro_config()         -- Updates the metro congig used for Active - Active replication backup

    create_mount_path()           -- Creates the mount path on a specified client

    snap_configs_validation()     -- To Validate the Snapshot Configurations

    unique_control_host()         -- fetches unique control host for a snap backup

    verify_3dc_backup()           -- Verifies backups for 3DC configuration

    get_restore_client()           -- Gets the machine classs of given client and creates the restore location

    get_subclient_details()        -- returns subclient details for the given subclient

"""

from __future__ import unicode_literals

import time
from FileSystem.SNAPUtils.snapconfigs import SNAPConfigs
from FileSystem.SNAPUtils.snapconstants import ReplicationType
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils
from cvpysdk.job import Job
from cvpysdk.policies.storage_policies import StoragePolicyCopy
from cvpysdk.exception import SDKException
from cvpysdk.schedules import Schedules



class SNAPHelper(object):
    """Helper class to perform snap operations"""

    def __init__(self, commcell, client, agent, tcinputs, snapconstants):
        """Initializes Snaphelper object and gets the commserv database object if not specified

            Args:
                commcell        (object)    --  commcell object

                client          (object)    --  client object

                agent           (object)    --  agent object

                tcinputs        (dict)      --  Test case inputs dictionary

                snapconstants   (object)    --  snapconstants object

        """
        self.snapconstants = snapconstants
        self.log = logger.get_log()
        self.commcell = commcell
        self.schedules = Schedules(self.commcell)
        self.client = client
        self.agent = agent
        self.tcinputs = tcinputs
        self.snapconfigs = SNAPConfigs(commcell, client, agent, tcinputs, snapconstants)
        self.client_machine = Machine(self.client)
        self.options_selector = OptionsSelector(self.commcell)
        self.entities = CVEntities(self.commcell)
        self.commonutils = CommonUtils(self.commcell)
        if self.commonutils.check_client_readiness(
                [self.tcinputs['MediaAgent'], self.tcinputs['ClientName']]):
            self.log.info("Check readiness for the Client and Media Agent successful")
        self.os_name = self.client_machine.os_info
        if self.os_name.upper() == 'WINDOWS':
            self.snapconstants.delimiter = "\\"
            if self.snapconstants.snap_automation_output is None:
                self.snapconstants.snap_automation_output = self.client_machine.create_directory(
                    f"C:{self.snapconstants.delimiter}CVAutomationOutput")
        else:
            self.snapconstants.delimiter = "/"
            if self.snapconstants.snap_automation_output is None:
                self.snapconstants.snap_automation_output = self.client_machine.create_directory(
                    f"/home{self.snapconstants.delimiter}CVAutomationOutput")

        if self.snapconstants.arrayname is not None:
            self.ctrlhost_array1 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName']})
        if self.snapconstants.arrayname2 is not None:
            self.ctrlhost_array2 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName2']})
        if self.snapconstants.arrayname3 is not None:
            self.ctrlhost_array3 = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.tcinputs['ArrayName3']})


    def snap_configs_validation(self, jobid, snapconfigs_to_validate, config_level, options, primary=True):
        """To Validate the Snapshot Configurations
            Args:
                jobid                   (int)       jobid of which configs to validate
                snapconfigs_to_validate (dict)      snap configs to validate
                config_level            (str)       snapconfig level
                options                 (set)       operations to validate
                                                    ex: for Remote MA : {'prepare', 'create', 'map', 'unmap',
                                                    'revert', 'delete', 'recon', 'remote-prepare', 'remote-create'}
                primary                 (bool)      in primary or secondary array
        """

        if primary:
            array_name = self.tcinputs['ArrayName']
        else:
            array_name = self.tcinputs['ArrayName2']

        if snapconfigs_to_validate is not None:
            for config, value in snapconfigs_to_validate.items():
                self.log.info("DB Validating Config: %s on Array: %s at : %s *level*" , config, array_name, config_level)
                self.snapconfigs.db_validation(
                    config,
                    value,
                    self.snapconstants.snap_engine_at_array,
                    array_name,
                    config_level)

                self.log.info("Functionality Validation of Config: %s on Array: %s using jobid : %s" ,
                    config, array_name, jobid)
                self.snapconfigs.func_validation(
                    config, value,
                    self.snapconstants.snap_engine_at_array,
                    array_name,
                    jobid,
                    self.client_machine,
                    options)

    def pre_cleanup(self):
        """Pre cleanup to clean up the failed/stale entries of snapshots, Index server,  Backupset and Storage policies """
        # Unmount the snaps which are in mounted status.
        try:
            self.log.info("Starting pre cleanup of the entities like Stale snaps, SP, Backupset and libraries.")
            sp_list = self.snapconstants.execute_query({'a': self.snapconstants.sp_name, 'b': '59'},
                                                       self.snapconstants.get_sp)
            self.log.info("Going to unmount the snaps if snaps are in mounted state. {0}".format(sp_list))
            try:
                for i in range(len(sp_list)):
                    self.unmount_snap(sp_list[i][1], sp_list[i][0])
                    self.log.info("unmounted snapshots: %s", sp_list[i][0])
            except Exception as e:
                self.log.info("Unmount of snaps failed with error" + str(e))

            # Delete the snaps which are in failed to delete status
            self.log.info("Going to delete the snaps")
            delete_status = self.snapconstants.execute_query({'a': self.snapconstants.sp_name, 'b': 79},
                                                             self.snapconstants.get_sp)
            try:
                for i in range(len(delete_status)):
                    self.delete_snap(delete_status[i][1], delete_status[i][0])
                    self.log.info("deleted snapshots: %s", sp_list[i][0])
            except Exception as e:
                self.log.info("Deletion of snapshots failed with error" + str(e))

            # Delete the Index server which exist due to previous failed test cases
            indexserver_list = self.snapconstants.execute_query(self.snapconstants.get_indexserver_list,
                                                                {'a': self.snapconstants.indexserver_name})
            if indexserver_list in [[[]], [['']], ['']]:
                self.log.info("Unable to delete any Indexserver, query returned none.")
            else:
                self.log.info("Going to delete the  Indexserver: {0}".format(indexserver_list))
            self.log.info("Going to delete the  Indexserver")
            for indexserver in range(len(indexserver_list)):
                try:
                    self.commcell.clients.delete(indexserver_list[indexserver][0])
                    self.log.info("deleted Indexserver: %s", indexserver_list[indexserver][0])
                except Exception as error:
                    self.log.info("Indexserver deletion failed with error %s %s",error, indexserver)

            # Delete the backupsets which exist due to previous failed test cases
            bkpset_list = self.snapconstants.execute_query(self.snapconstants.get_bkpset_list,
                                                           {'a': self.snapconstants.bkpset_name})
            if bkpset_list in [[[]], [['']], ['']]:
                self.log.info("Unable to delete any backupset, query returned none.")
            else:
                self.log.info("Going to delete the  backupset: {0}".format(bkpset_list))
            self.log.info("Going to delete the  backupset")
            for i in range(len(bkpset_list)):
                try:
                    self.agent.backupsets.delete(bkpset_list[i][0])
                    self.log.info("deleted bkpset: %s", bkpset_list[i][0])
                except Exception as e:
                    self.log.info("backupset deletion failed with error" + str(e))
            # Delete the storage policies which exist due to previous failed test cases.
            sp_list = self.snapconstants.execute_query(self.snapconstants.get_sp_list,
                                                       {'a': self.snapconstants.sp_name})
            if sp_list in [[[]], [['']], ['']]:
                self.log.info("Unable to delete Storage policies, query returned none")
            else:
                self.log.info("Going to delete Storage policies: {0}".format(sp_list))
            for i in range(len(sp_list)):
                try:
                    self.commcell.storage_policies.delete(sp_list[i][0])
                    self.log.info("deleted storage policy: %s", sp_list[i][0])
                except Exception as e:
                    self.log.info("storage policy deletion failed with error" + str(e))
            # Delete the libraries which exist due to previous failed test cases.
            lib_list = self.snapconstants.execute_query(self.snapconstants.get_lib_list,
                                                        {'a': self.snapconstants.lib_name})
            self.log.info("lib list: {0}".format(lib_list))
            if lib_list in [[[]], [['']], ['']]:
                self.log.info("Unable to delete libraries, query returned none.")
            else:
                self.log.info("Going to delete libraries:{0}".format(lib_list))
            for i in range(len(lib_list)):
                try:
                    self.commcell.disk_libraries.delete(lib_list[i][0])
                    self.log.info("deleted libraries: %s", lib_list[i][0])
                except Exception as e:
                    self.log.info("library deletion failed with error : {0}" + str(e))
        except Exception as e:
            self.log.info("Pre cleanup task has finished" + str(e))

    def setup(self):
        """ Setup function to create locations and snap entities """

        self.create_locations()
        if self.snapconstants.sc_name is None:
            attempt_count = 0
            while attempt_count <= 15:
                attempt_count += 1
                try:
                    self.create_snap_environment()
                    break
                except Exception as e:
                    self.log.info("Creation of Snap Environment failed with error: %s, "
                                  "will retry after 90 seconds, Retry Count: %s" % (e, attempt_count))
                    time.sleep(90)
                    if attempt_count > 15:
                        raise Exception('Failed with error: ' + str(e))
        else:
            self.log.info("***Not creating the snap entities as the test case is run on Existing "
                          "subclient***")

    def create_locations(self):
        """ Clean subclient content if exists and create new one
            Create restore location
            Create Mountpath
        """
        temp1 = self.snapconstants.snap_engine_at_array.replace("/", "").replace(" ", "").replace("(", "").replace(")",
                                                                                                                   "")
        temp2 = self.snapconstants.snap_engine_at_subclient.replace("/", "").replace(" ", "").replace("(", "").replace(
            ")", "")

        # Create Restore Location
        Restores = f"Restores_{self.snapconstants.string}"
        self.snapconstants.windows_restore_location = (
            f"{self.snapconstants.snap_automation_output}"
            f"{self.snapconstants.delimiter}{temp1}{self.snapconstants.delimiter}"
            f"{temp2}{self.snapconstants.delimiter}{Restores}")
        if self.client_machine.check_directory_exists(self.snapconstants.windows_restore_location):
            self.log.info(
                "snap restore location: %s exists, cleaning it and creating new folder",
                self.snapconstants.windows_restore_location
            )
            self.client_machine.remove_directory(self.snapconstants.windows_restore_location)
        else:
            self.log.info("snap restore location does not exists, creating one! ")
        self.client_machine.create_directory(self.snapconstants.windows_restore_location)
        self.log.info("Successfully Created restore location : %s",
                      self.snapconstants.windows_restore_location)
        #create mount path
        self.log.info("Creating the mount path in source client %s", self.client.client_name)
        self.create_mount_path()

        if self.snapconstants.proxy_client != self.client.client_name and self.snapconstants.proxy_client is not None:
            self.log.info("Creating the mount path in proxy client %s", self.snapconstants.proxy_client)
            self.create_mount_path(Machine(self.commcell.clients.get(self.snapconstants.proxy_client)))

        # Create DiskLibrary Location
        disk_library = f"DiskLibrary_{self.snapconstants.string}"
        self.snapconstants.disk_lib_loc = (
            f"{self.snapconstants.snap_automation_output}"
            f"{self.snapconstants.delimiter}{temp1}{self.snapconstants.delimiter}"
            f"{temp2}{self.snapconstants.delimiter}{disk_library}")

        if self.client_machine.check_directory_exists(self.snapconstants.disk_lib_loc):
            self.log.info(
                "Disk library location: %s exists, Not creating!!",
                self.snapconstants.disk_lib_loc
            )
        else:
            self.log.info("Disk library location does not exists, creating one! ")
            self.client_machine.create_directory(self.snapconstants.disk_lib_loc)
            self.log.info("Successfully Created Disk Library location : %s",
                          self.snapconstants.disk_lib_loc)

    # Adding array management entry
    def add_array(self, snap_configs=None):
        """Method to Add Hardware Array in to the Array Management
        """
        try:
            vendor_id = self.snapconstants.execute_query(
                self.snapconstants.get_vendor_id, {'a': self.snapconstants.snap_engine_at_array}, fetch_rows='one')
            if snap_configs is not None:
                config_data = {}
                for config, value in snap_configs.items():
                    master_config_id = self.snapconstants.execute_query(
                        self.snapconstants.get_master_config_id,
                        {'a': config, 'b': self.snapconstants.snap_engine_at_array},
                        fetch_rows='one')
                    config_data[master_config_id] = value
            else:
                config_data = None
            self.log.info("Adding array management entry for : %s", self.snapconstants.arrayname)
            error_message = self.commcell.array_management.add_array(self.snapconstants.snap_engine_at_array,
                                                                     self.snapconstants.arrayname,
                                                                     self.snapconstants.username,
                                                                     self.snapconstants.password,
                                                                     vendor_id,
                                                                     config_data,
                                                                     self.snapconstants.controlhost,
                                                                     self.snapconstants.array_access_nodes_to_add,
                                                                     self.snapconstants.is_ocum)
            self.log.info("Successfully added the Array with ControlHost id: %s", error_message)

        except SDKException as e:
            if e.exception_id == '101':
                self.log.info("{0}".format(e.exception_message))
            else:
                raise Exception(e)

    def create_snap_copy(self,
                         copy_name,
                         is_mirror_copy,
                         is_snap_copy,
                         library_name,
                         media_agent_name,
                         source_copy="",
                         provisioning_policy=None,
                         resource_pool=None,
                         is_replica_copy=None,
                         **kwargs):
        """ includes adding Snap Copy, Snapvault Copy, SnapMirror Copy, Replica/Vault Copy,
            Replica Mirror Copy etc
            Args:
                copy_name           (str)       -- Copy Name to create

                is_mirror_copy      (bool)      -- Creates Mirror Copy if true

                is_snap_copy        (bool)      -- Creates Snap Copy if true

                library_name        (str)       -- library name for creating copy

                media_agent_name    (str)       -- Media Agent name for creating copy

                source_copy         (str)       -- Source Copy for the Copy
                default: None

                provisioning_policy (str)       -- Provisioning Policy Name for the Vault/Mirror
                                                   Copy
                default: None

                resource_pool       (str)       -- Resource Pool for the Vault/Mirror Copy
                default: None

                is_replica_copy     (bool)      -- Creates Replica Copy if true
                
                kwargs:
                    
                    job_based_retention     (bool)       -- Job Based retention 
                    is_c2c_target           (bool)      -- Creates NetApp Cloud Target Copy
                    enable_selective_copy   (int)       -- Value of Selective Rule
        """
        job_based_retention = kwargs.get('job_based_retention')
        is_c2c_target = kwargs.get('is_c2c_target')
        selectiveRule = kwargs.get('enable_selective_copy', None)
        if self.snapconstants.storage_policy.has_copy(copy_name):
            self.log.info("Storage policy : {0} already has copy named : {1}".format(
                self.snapconstants.storage_policy.storage_policy_name, copy_name))
        else:
            self.log.info("Copy with name {0} does not exists, Creating one!".format(
                copy_name))
            self.snapconstants.storage_policy.create_snap_copy(copy_name,
                                                               is_mirror_copy,
                                                               is_snap_copy,
                                                               library_name,
                                                               media_agent_name,
                                                               source_copy,
                                                               provisioning_policy,
                                                               resource_pool,
                                                               is_replica_copy,
                                                               is_c2c_target=is_c2c_target,
                                                               job_based_retention=job_based_retention,
                                                               enable_selective_copy=selectiveRule)

    def create_secondary_snap_copy(self,
                                   source_copy, **kwargs):
        """ creates Snapvault, Snapmirror, Replica Vault and Replica Mirror Copies
            Agrs:
                source_copy     (str)     -- Source copy for the copy

            kwargs:

                snapvault       (bool)    -- creates snapvault copy if true

                snapmirror      (bool)    -- creates snapmirror copy if true

                replica_vault   (bool)    -- creates replica vault copy if true

                replica_mirror  (bool)    -- creates replica mirror copy if true

                is_c2c_target   (bool)    -- creates NetApp Cloud Target copy if true

                enable_selective_copy (int) -- Enable selective copy with value selectiveRule

            Returns:
                copy name       (string)  -- Newly created Copy Name
        """

        snapvault = kwargs.get('snapvault', False)
        snapmirror = kwargs.get('snapmirror', False)
        replica_vault = kwargs.get('replica_vault', False)
        replica_mirror = kwargs.get('replica_mirror', False)
        is_c2c_target = kwargs.get('is_c2c_target', False)
        selectiveRule = kwargs.get('selectiveRule', None)

        is_snap = True
        if snapmirror or replica_mirror:
            is_mirror = True
        else:
            is_mirror = False

        if snapvault:
            self.log.info("Creating SnapVault copy")
            copy_name = self.options_selector.get_custom_str(presubstr="Vault_")
            self.create_snap_copy(copy_name, is_mirror,
                                  is_snap, self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']), source_copy,
                                  self.snapconstants.prov_policy_vault,
                                  self.snapconstants.resource_pool_vault
                                  )
            self.log.info("Successfully created SnapVault Copy: {0}".format(copy_name))

        elif snapmirror:
            self.log.info("Creating SnapMirror copy")
            copy_name = self.options_selector.get_custom_str(presubstr="Mirror_")
            self.create_snap_copy(copy_name, is_mirror, is_snap,
                                  self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']), source_copy,
                                  self.snapconstants.prov_policy_mirror,
                                  self.snapconstants.resource_pool_mirror
                                  )
            self.log.info("Successfully created SnapMirror Copy : {0}".format(copy_name))
            if self.snapconstants.type == "pmm" and self.snapconstants.resource_pool_pmm is not None:
                self.snapconstants.resource_pool_mirror = self.snapconstants.resource_pool_pmm

        elif replica_vault:
            self.log.info("Creating Replica/vault copy")
            copy_name = self.options_selector.get_custom_str(presubstr="Replica_Vault_")
            self.create_snap_copy(copy_name, is_mirror, is_snap,
                                  self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']), source_copy,
                                  is_replica_copy=True,
                                  enable_selective_copy=selectiveRule
                                  )
            self.log.info("Successfully created Replica/Vault Copy : {0}".format(copy_name))

        elif replica_mirror:
            self.log.info("Creating Replica Mirror copy")
            copy_name = self.options_selector.get_custom_str(presubstr="Replica_Mirror_")
            self.create_snap_copy(copy_name, is_mirror, is_snap,
                                  self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']), source_copy,
                                  is_replica_copy=True
                                  )
            self.log.info("Successfully created Replica/Mirror Copy : {0}".format(copy_name))

        else:
            self.log.info("Creating NetApp Cloud Target copy")
            copy_name = self.options_selector.get_custom_str(presubstr="C2C_Target_")
            self.create_snap_copy(copy_name, is_mirror, is_snap,
                                  self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']), source_copy,
                                  is_replica_copy=True, is_c2c_target=True
                                  )
            self.log.info("Successfully created NetApp Cloud Target Copy : {0}".format(copy_name))

        return copy_name

    def create_snap_environment(self):
        """ includes Add Array, Enabling IntelliSnap at Client, Create Library, Storage Policy,
        Snap Copy, Aux Copy,BackupSet, Subclient and Enable IntelliSnap on it, Set Retention
        Snap Copy
        """

        # Enable Intellisnap at client
        self.log.info("Enabling Intellisnap on client: {0}".format(self.client.client_name))
        self.client.enable_intelli_snap()
        self.log.info("Successfully Enabled Intellisnap on client: {0}".format(
            self.client.client_name))

        if self.snapconstants.ocum_server is None or self.snapconstants.ocum_server == "":
            self.snapconstants.ocum_server = None

        self.snapconstants.entity_properties = self.entities.create(self.snapconstants.entity_properties)

        self.snapconstants.subclient = self.snapconstants.entity_properties['subclient']['object']
        self.snapconstants.disk_lib = self.snapconstants.entity_properties['disklibrary']['object']
        self.snapconstants.storage_policy = self.snapconstants.entity_properties['storagepolicy']['object']

        # Create Snap Copy
        if self.snapconstants.ocum_server:
            self.log.info("*" * 20 + "This is OCUM SP, Not creating Snap primary Copy" + "*" * 20)
            self.snapconstants.snap_copy_name = "Primary"
        else:
            self.log.info("*" * 20 + "Creating Snap copy" + "*" * 20)
            self.create_snap_copy(self.snapconstants.snap_copy_name, False, True,
                                  self.snapconstants.disk_lib.library_name,
                                  str(self.tcinputs['MediaAgent']),
                                  job_based_retention=self.snapconstants.job_based_retention
                                  )
            self.log.info("Successfully created Snap Copy ")
            self.delete_bkpcpy_schedule()

        if self.snapconstants.type == "pv":
            self.log.info("*" * 20 + "Creating Copies for PV Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, snapvault=True)

        elif self.snapconstants.type == "pm":
            self.log.info("*" * 20 + "Creating Copies for PM Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, snapmirror=True)

        elif self.snapconstants.type == "pvm":
            self.log.info("*" * 20 + "Creating Copies for PVM Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, snapvault=True)
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, snapmirror=True)

        elif self.snapconstants.type == "pmv":
            self.log.info("*" * 20 + "Creating Copies for PMV Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, snapmirror=True)
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, snapvault=True)

        elif self.snapconstants.type == "pmm":
            self.log.info("*" * 20 + "Creating Copies for PMM Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, snapmirror=True)
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, snapmirror=True)

        elif self.snapconstants.type == "pv_replica":
            self.log.info("*" * 20 + "Creating Copies for PV_Replica Configuration" + "*" * 20)

            if self.snapconstants.selectiveRule is None:
                self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                    self.snapconstants.snap_copy_name, replica_vault=True)
            else:
                self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                    self.snapconstants.snap_copy_name, replica_vault=True,
                    selectiveRule=self.snapconstants.selectiveRule)

            if self.snapconstants.snap_engine_at_array == "NetApp":
                self.svm_association(self.snapconstants.first_node_copy,
                                     self.snapconstants.arrayname,
                                     self.tcinputs['ArrayName2'])
            else:
                self.log.info("*" * 20 + "Since Vendor is non-Netapp, Not Updating SVM association" + "*" * 20)
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == ReplicationType.PV_Replica_c2c:
            self.log.info("*" * 20 + "Creating Copies for PV_Replica_C2C Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, is_c2c_target=True)
            self.svm_association(self.snapconstants.first_node_copy,
                                 self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "pm_replica":
            self.log.info("*" * 20 + "Creating Copies for PM_Replica Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, replica_mirror=True)
            self.svm_association(self.snapconstants.first_node_copy, self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "pvm_replica":
            self.log.info("*" * 20 + "Creating Copies for PVM_Replica Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, replica_vault=True)
            self.svm_association(self.snapconstants.first_node_copy, self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, replica_mirror=True)
            self.svm_association(self.snapconstants.second_node_copy, self.tcinputs['ArrayName2'],
                                 self.tcinputs['ArrayName3'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "pmv_replica":
            self.log.info("*" * 20 + "Creating Copies for PMV_Replica Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, replica_mirror=True)
            self.svm_association(self.snapconstants.first_node_copy, self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, replica_vault=True)
            self.svm_association(self.snapconstants.second_node_copy, self.tcinputs['ArrayName2'],
                                 self.tcinputs['ArrayName3'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "pmm_replica":
            self.log.info("*" * 20 + "Creating Copies for PMM_Replica Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, replica_mirror=True)
            self.svm_association(self.snapconstants.first_node_copy, self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, replica_mirror=True)
            self.svm_association(self.snapconstants.second_node_copy, self.tcinputs['ArrayName2'],
                                 self.tcinputs['ArrayName3'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "pvv_replica":
            self.log.info("*" * 20 + "Creating Copies for PVV_Replica Configuration" + "*" * 20)
            self.snapconstants.first_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.snap_copy_name, replica_vault=True)
            self.svm_association(self.snapconstants.first_node_copy, self.snapconstants.arrayname,
                                 self.tcinputs['ArrayName2'])
            self.snapconstants.second_node_copy = self.create_secondary_snap_copy(
                self.snapconstants.first_node_copy, replica_vault=True)
            self.svm_association(self.snapconstants.second_node_copy, self.tcinputs['ArrayName2'],
                                 self.tcinputs['ArrayName3'])
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "fanout":
            if self.snapconstants.ocum_server:
                self.log.info("*" * 20 + "Creating Copies for OCUM FanOut Configuration" + "*" * 20)
            else:
                self.log.info("*" * 20 + "Creating Copies for Open Replication FanOut Configuration" + "*" * 20)
            i = int(self.snapconstants.fanout_count_pv)
            while i != 0:
                if self.snapconstants.ocum_server:
                    copy_name = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                                snapvault=True)
                else:
                    copy_name = self.create_secondary_snap_copy(
                        self.snapconstants.snap_copy_name, replica_vault=True)
                    self.svm_association(copy_name, self.snapconstants.arrayname,
                                         self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_vault.append(copy_name)
                i = i - 1
                continue
            self.log.info("*" * 20 + "Successfully created: {0} Vault copies for FANOUT config".format(
                self.snapconstants.fanout_count_pv))
            i = int(self.snapconstants.fanout_count_pm)
            while i != 0:
                if self.snapconstants.ocum_server:
                    copy_name = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                                snapmirror=True)
                else:
                    copy_name = self.create_secondary_snap_copy(
                        self.snapconstants.snap_copy_name, replica_mirror=True)
                    self.svm_association(copy_name, self.snapconstants.arrayname,
                                         self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_mirror.append(copy_name)
                i = i - 1
                continue
            self.log.info("*" * 20 + "Successfully created: {0} Mirror copies for FANOUT config".format(
                self.snapconstants.fanout_count_pm))
            self.disable_auxcpy_schedule()

        elif self.snapconstants.type == "all":
            if self.snapconstants.ocum_server:
                self.log.info("*" * 20 + "Creating Copies for OCUM All copies Configuration" + "*" * 20)
                pv = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                     snapvault=True)
                self.snapconstants.fanout_copies_vault.append(pv)
                pm = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                     snapmirror=True)
                self.snapconstants.fanout_copies_mirror.append(pm)
                pmv = self.create_secondary_snap_copy(pm, snapvault=True)
                self.snapconstants.fanout_copies_vault.append(pmv)
                pvm = self.create_secondary_snap_copy(pv, snapmirror=True)
                self.snapconstants.fanout_copies_mirror.append(pvm)
                pm1 = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name, snapmirror=True)
                self.snapconstants.fanout_copies_mirror.append(pm1)
                pmm = self.create_secondary_snap_copy(pm1, snapmirror=True)
                self.snapconstants.fanout_copies_mirror.append(pmm)
                self.log.info("*" * 20 + "Successfully Created Copies for OCUM All copies Configuration" + "*" * 20)

            else:
                self.log.info("*" * 20 + "Creating Copies for Open Replication All copies Configuration" + "*" * 20)
                pv = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                     replica_vault=True)
                self.svm_association(pv, self.snapconstants.arrayname, self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_vault.append(pv)
                pm = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                     replica_mirror=True)
                self.svm_association(pm, self.snapconstants.arrayname, self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_mirror.append(pm)
                pmv = self.create_secondary_snap_copy(pm, replica_vault=True)
                self.svm_association(pmv, self.tcinputs['ArrayName2'],
                                     self.tcinputs['ArrayName3'])
                self.snapconstants.fanout_copies_vault.append(pmv)
                pvm = self.create_secondary_snap_copy(pv, replica_mirror=True)
                self.svm_association(pvm, self.tcinputs['ArrayName2'],
                                     self.tcinputs['ArrayName3'])
                self.snapconstants.fanout_copies_mirror.append(pvm)
                pm1 = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                      replica_mirror=True)
                self.svm_association(pm1, self.snapconstants.arrayname,
                                     self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_mirror.append(pm1)
                pmm = self.create_secondary_snap_copy(pm1, replica_mirror=True)
                self.svm_association(pmm, self.tcinputs['ArrayName2'],
                                     self.tcinputs['ArrayName3'])
                self.snapconstants.fanout_copies_mirror.append(pmm)
                pv1 = self.create_secondary_snap_copy(self.snapconstants.snap_copy_name,
                                                      replica_vault=True)
                self.svm_association(pv1, self.snapconstants.arrayname,
                                     self.tcinputs['ArrayName2'])
                self.snapconstants.fanout_copies_vault.append(pv1)
                pvv = self.create_secondary_snap_copy(pv1, replica_vault=True)
                self.svm_association(pvv, self.tcinputs['ArrayName2'],
                                     self.tcinputs['ArrayName3'])
                self.snapconstants.fanout_copies_vault.append(pvv)
                self.log.info(
                    "*" * 20 + "Successfully Created Copies for Open Replication All copies Configuration" + "*" * 20)
                self.disable_auxcpy_schedule()

        else:
            self.log.info("Not creating any replica copies")

        # Enabling Intellisnap on subclient and setting Snap engine
        self.log.info("Enabling Intellisnap on subclient: {0} and setting Snap engine: {1}".format(
            self.snapconstants.subclient.subclient_name,
            self.snapconstants.snap_engine_at_subclient))
        if 'ProxyMA' in self.tcinputs.keys() and self.tcinputs['ProxyMA'] is not None:
            backup_copy_ma = self.tcinputs['ProxyMA']
        else:
            backup_copy_ma = self.tcinputs['MediaAgent']
        proxy_options = {
            'snap_proxy': self.tcinputs['MediaAgent'],
            'backupcopy_proxy': backup_copy_ma,
            'use_source_if_proxy_unreachable': True
        }
        self.snapconstants.subclient.enable_intelli_snap(
            self.snapconstants.snap_engine_at_subclient, proxy_options)
        self.log.info("Successfully Enabled Intellisnap on subclient: {0} and set Snap engine: {1}\
                      ".format(self.snapconstants.subclient.subclient_name,
                               self.snapconstants.snap_engine_at_subclient)
                      )

    def delete_bkpcpy_schedule(self):
        """delete backup copy schedule as it interferes with the test case flow"""

        self.schedules.refresh()
        schedule_name = f"{self.snapconstants.storage_policy.storage_policy_name} snap copy"
        if self.schedules.has_schedule(schedule_name):
            self.log.info("Deleting backup copy schedule :{0}".format(schedule_name))
            self.schedules.delete(schedule_name)
            self.log.info("Successfully Deleted backup copy schedule :{0}".format(schedule_name))
        else:
            self.log.info("Schedule with name: {0} does not exists".format(schedule_name))

    def disable_auxcpy_schedule(self):
        """disable Auxilliary copy schedule policy as it interferes with the test case flow"""

        self.commcell.schedule_policies.refresh()
        schedule_policy_name = 'System Created Autocopy schedule'
        self.log.info("Disabling Auxilliary copy schedule policy :{0}".format(
            schedule_policy_name))
        schedule_policy = self.commcell.schedule_policies.get(schedule_policy_name)
        schedule_policy.disable()
        self.log.info("successfully disabled schedule policy :{0}".format(schedule_policy_name))

    def clear_subclient_data(self):
        """Clear Subclient drive data. For test purpose only."""
        self.log.info("Read Subclient Content: {0}".format(self.snapconstants.subclient.content))
        drive = self.snapconstants.subclient.content[0]
        if len(drive) < 4:
            if self.os_name.upper() == 'WINDOWS':
                path = f"{drive[:-1]}{self.snapconstants.delimiter}"
            else:
                path = f"{drive}{self.snapconstants.delimiter}"
        else:
            path = drive
            if self.os_name.upper() == 'WINDOWS':
                path = drive.split(self.snapconstants.delimiter)[0]+self.snapconstants.delimiter

        self.log.info("Subclient Content drive  is  %s", path)
        exclusion={'System Volume Information', '$RECYCLE.BIN', path+'System Volume Information', path+'$RECYCLE.BIN',''}
        inclusion=set(self.client_machine.get_files_in_path(path, recurse=False)) | set(self.client_machine.get_folders_in_path(path, recurse=False))
        delete_path = inclusion-exclusion
        if delete_path:
            self.log.info(f"Deleting paths under subclient content: {delete_path}")
            for path in delete_path:
                if self.os_name.upper() == 'WINDOWS':
                    if self.client_machine.is_file(path) and not self.client_machine.is_directory(path):
                        self.log.info(f"Deleting File: {path}")
                        self.client_machine.delete_file(path)
                    else:
                        if not self.client_machine.check_directory_exists(f"{drive[:-1]}\\empty"):
                            self.client_machine.create_directory(f"{drive[:-1]}\\empty")
                        self.client_machine.execute_command(
                            f"cmd.exe /c robocopy {drive[:-1]}\\empty {path} /purge")
                        self.client_machine.execute_command(
                            f"cmd.exe /c robocopy {drive[:-1]}\\empty {path}{self.snapconstants.delimiter}_source /purge")
                        self.client_machine.remove_directory(path)
                        self.client_machine.remove_directory(f"{drive[:-1]}\\empty")
                else:
                    self.client_machine.remove_directory(path)

    def add_test_data_folder(self):
        """Add Test data folder on the subclient content
        """
        self.log.info("Read subclient content")
        self.log.info("Subclient Content: {0}".format(self.snapconstants.subclient.content))
        for drive in self.snapconstants.subclient.content:
            if len(drive) < 4:
                if self.os_name.upper() == 'WINDOWS':
                    path = f"{drive[:-1]}{self.snapconstants.delimiter}TestData"
                else:
                    path = f"{drive}{self.snapconstants.delimiter}TestData"
            else:
                path = f"{drive}{self.snapconstants.delimiter}TestData"
            self.log.info("test data folder  is  %s", path)
            if self.client_machine.check_directory_exists(path):
                self.log.info(
                    "TestData Folder already exists under %s, deleting it and creating"
                    " new one!!", drive
                )
                if self.os_name.upper() == 'WINDOWS':
                    if not self.client_machine.check_directory_exists(f"{drive[:-1]}\\empty"):
                        self.client_machine.create_directory(f"{drive[:-1]}\\empty")
                    self.client_machine.execute_command(
                        f"cmd.exe /c robocopy {drive[:-1]}\\empty {path} /purge")
                    self.client_machine.execute_command(
                        f"cmd.exe /c robocopy {drive[:-1]}\\empty {path}{self.snapconstants.delimiter}_source /purge")
                    self.client_machine.remove_directory(path)
                    self.client_machine.remove_directory(f"{drive[:-1]}\\empty")
                else:
                    self.client_machine.remove_directory(path)
            else:
                self.log.info(
                    "TestData Folder does not exists under %s, creating one!!", drive
                )
            self.client_machine.create_directory(path)
            self.log.info("Created TestData Folder under %s", drive)
            self.snapconstants.test_data_path.append(path)

    def svm_association(self, copy_name, source_array, target_array):
        """
        Method to Update SVM association for Netapp Open Replication
        Args:
            copy_name       (str)   --  Copy name for the update

            source_array    (str)   --  Source Array Name

            target_array    (str)   --  Target Array Name

        """

        self.log.info("Adding SVM association")
        if self.snapconstants.type == ReplicationType.PV_Replica_c2c:
            target_vendor = self.snapconstants.c2c_target_vendor
            tgt_vendor_id = self.snapconstants.execute_query(self.snapconstants.get_vendor_id,
                                                             {'a': self.snapconstants.c2c_target_vendor}, fetch_rows='one')
        else:
            target_vendor = self.snapconstants.snap_engine_at_array
            tgt_vendor_id = self.snapconstants.execute_query(self.snapconstants.get_vendor_id,
                                                             {'a': self.snapconstants.snap_engine_at_array}, fetch_rows='one')

        spcopy = self.spcopy_obj(copy_name)
        src_array_id = self.snapconstants.execute_query(self.snapconstants.get_controlhost_id,
                                                        {'a': source_array}, fetch_rows='one')
        tgt_array_id = self.snapconstants.execute_query(self.snapconstants.get_controlhost_id,
                                                        {'a': target_array}, fetch_rows='one')
        kwargs = {
            'target_vendor' : target_vendor,
            'tgt_vendor_id' : tgt_vendor_id
            }
        spcopy.add_svm_association(src_array_id, source_array, tgt_array_id, target_array,
                                   **kwargs)
        self.log.info("Successfully added SVM association to copy : {0}".format(copy_name))

    def delete_copy(self, copy_name):
        """ Deletes Copy
            Args:
                string  : copy_name
        """
        self.log.info("deleting  copy: {0}".format(copy_name))
        self.snapconstants.storage_policy.delete_secondary_copy(copy_name)
        self.log.info("Successfully deleted  copy : {0}".format(copy_name))

    def suspend_job(self, job):
        """ Suspends SnapBackup/backup copy/ aux copy job
                Returns:
                        object : job Object
                """
        if job.status.lower() not in ['running', 'waiting']:
            self.log.info("job is completed before suspending it")
            return
        self.log.info("Suspending job {0}".format(job.job_id))
        job.pause(True)
        wait_count = 30
        while job.status.lower() != 'suspended' and wait_count > 0:
            if job.is_finished:
                self.log.info("Job is completed")
                return
            self.log.info("will check the suspend status after 20 seconds")
            time.sleep(20)
            wait_count -= 1

        if job.status.lower() not in ['suspended', 'completed']:
            raise Exception("Job status is {0} after suspending, we did not get the suspended job".format(job.status))
        elif job.status.lower() == 'completed':
            self.log.info("Job is completed while suspending, continuing..")
        else:
            self.log.info("Successfully suspended the job  :{0}".format(job.job_id))

    def resume_job(self, job):
        """ Resumes a job
                Returns:
                        object : job Object
                """
        if job.status.lower() not in ['suspended', 'pending']:
            self.log.info("job status {0}, Can not resume it".format(job.status))
            return
        job.resume(True)
        wait_count = 30
        while job.status.lower() not in ['running', 'waiting', 'completed'] and wait_count > 0:
            if job.status.lower() == 'pending':
                self.log.info("Job went to pending Post resume, resuming it again")
                job.resume(True)
            self.log.info("will check the resume status after 10 seconds")
            time.sleep(10)
            wait_count -= 1

        if job.status.lower() not in ['running', 'waiting', 'completed']:
            raise Exception("Job status: {0} after resuming, hence raising exception."
                            " Reason: {1}".format(job.status, job.delay_reason))
        else:
            self.log.info("Successfully resumed the job:{0}".format(job.job_id))

    def run_suspend_resume(self, job, phases):
        """
        Suspends and resumes the job in each phase
        Args:
            job: obj: Job object
            phases: list: list of phases(in str)
        """
        try:
            for phase in phases:
                attempt = 1
                skip_suspend = False
                total_wait_attempts = 180
                while not job.phase.lower() == phase:
                    self.log.info(
                        'Waiting for job [{0}] to come to [{1}] phase. Current phase [{2}]. '
                        'Attempt [{3}/{4}]'.format(
                            job.job_id, phase, job.phase, attempt, total_wait_attempts))
                    self.log.info("sleeping for 10 seconds")
                    time.sleep(10)
                    if job.is_finished:
                        self.log.info('Job already finished while waiting for phase')
                        return
                    if phases.index(job.phase.lower()) > phases.index(phase):
                        self.log.info('Phase [{0}] has already completed'.format(phase))
                        skip_suspend = True
                        break
                    attempt += 1
                    if attempt == total_wait_attempts:
                        if job.status.lower() in ['running', 'waiting']:
                            total_wait_attempts = 270
                        else:
                            raise Exception('Attempts exhausted while waiting for the job to come to the'
                                            ' required phase. Please check the Job details,'
                                            'reason :{0}'.format(job.pending_reason))

                if not skip_suspend:
                    self.log.info(f"Suspending in phase: {phase}")
                    self.suspend_job(job)
                    self.log.info("sleeping for 60 seconds before resuming job")
                    time.sleep(60)
                    self.resume_job(job)
        except AttributeError as e:
            self.log.info(f"Job has already completed.")

    def kill_job(self):
        """ Kills SnapBackup job
            Returns:
                    object : job Object
        """

        advanced_option = {
            'inline_bkp_cpy': self.snapconstants.inline_bkp_cpy,
            'skip_catalog': self.snapconstants.skip_catalog
        }
        job = self.snapconstants.subclient.backup(self.snapconstants.backup_level,
                                                  advanced_options=advanced_option)
        self.log.info("sleeping for 10 seconds for job to start")
        time.sleep(10)
        if job.status.lower() in ["failed", "failed to start"]:
            raise Exception("Job is failed or failed to start, Please rerun the test case")
        self.log.info("successfully started {0} job :{1}".format(self.snapconstants.backup_level,
                                                                 job.job_id))
        self.log.info("killing the job {0} to verify snap cleanup".format(job.job_id))

        while job.phase.upper() not in self.snapconstants.phase:
            self.log.info("will check the phase status after 10 seconds")
            time.sleep(10)
            if job.status.lower() == 'pending':
                self.log.info("""job is in pending state with reason {0}, killing it and raising
                              the exception, please check the logs!""".format(job.pending_reason))
                job.kill(True)
                raise Exception("""job is in pending state with reason {0}, killing it and raising\
                              the exception, please check the logs and rerun the test case!\
                              """.format(job.pending_reason))
            elif job.status.lower() == 'completed':
                self.log.info("""job is completed before killing it hence raising the exception,
                              please rerun the test case""")
                raise Exception("""job is completed before killing it hence raising the exception,
                              please rerun the test case""")
            continue
        self.log.info("Snap phase completed, killing the job now")
        job.kill(True)

        while job.status.lower() != 'killed':
            self.log.info("will check the killed status after 10 seconds")
            time.sleep(10)
            continue

        if job.status.lower() in ["failed", "completed"]:
            raise Exception("Job status is failed or completed, we did not get the killed job")
        else:
            self.log.info("Successfully killed the job :{0}".format(job.job_id))
        self.snapconstants.job_tracker.append(job.job_id)
        return job

    def update_test_data(self, mode, path=None, rename=False):
        """
        Method to edit or delete the test data
        Args:
            mode      --  mode values can be 'add','edit','delete' or 'copy'
            path      --  directory location to perform add/update/delete test data
        """
        if path is None and mode == "edit":
            path = self.snapconstants.test_data_folder

        elif path is None:
            path = self.snapconstants.test_data_path

        if mode == 'add':
            if self.snapconstants.backup_level != "Synthetic_full":
                for test_path in path:
                    self.snapconstants.name = self.snapconstants.folder_name(
                        self.snapconstants.backup_level)
                    test_data_folder = f"{test_path}{self.snapconstants.delimiter}{self.snapconstants.name}"
                    self.log.info("Generating test data at: %s", test_data_folder)
                    problematicData=False
                    files=5
                    size=20
                    if self.snapconstants.problematic_data:
                        self.log.info(f"Problematic data is set: {self.snapconstants.problematic_data}")
                        problematicData=True
                    if isinstance(self.snapconstants.scale_data, str):
                        self.log.info(f"Scale data is set: {self.snapconstants.scale_data}")
                        files=int(self.snapconstants.scale_data)
                        size=1
                    if self.os_name.upper() == 'WINDOWS':
                        self.client_machine.generate_test_data(test_data_folder,
                                                               acls=True,
                                                               unicode=True,
                                                               xattr=True,
                                                               problematic=problematicData,
                                                               files=files,
                                                               file_size=size)
                    else:
                        self.client_machine.generate_test_data(test_data_folder,
                                                               slinks=False,
                                                               problematic=problematicData,
                                                               files=files,
                                                               file_size=size)
                    self.log.info("Successfully Generated data at: %s", test_data_folder)
                    self.snapconstants.test_data_folder.append(test_data_folder)

        if mode == 'edit':
            for test_path in path:
                self.client_machine.modify_test_data(test_path, modify=True, rename=rename)
                self.log.info("Successfully Modified data at: {0}".format(test_path))

        if mode == 'delete':
            for test_path in path:
                self.log.info("deleting the folder for delete data verification".format(test_path))
                self.client_machine.remove_directory(test_path)

        elif mode == 'copy':
            self.snapconstants.copy_content_location = []
            for test_path in path:
                copy_content_location = (
                    f"{self.snapconstants.windows_restore_location}"
                    f"{self.snapconstants.delimiter}copied_data"
                    f"{self.snapconstants.delimiter}{self.snapconstants.folder_name('test')}")
                self.client_machine.create_directory(copy_content_location)
                self.log.info("Location to move data before delete/restore: %s", copy_content_location)
                self.client_machine.copy_folder(test_path, copy_content_location)
                self.log.info("folder move is done")
                self.snapconstants.copy_content_location.append(copy_content_location)

    def snap_backup(self):
        """
        Runs Snap Backup from Commcell for the given subclient
        Returns:
                    object : job Object

        """

        advanced_option = {
            'inline_bkp_cpy': self.snapconstants.inline_bkp_cpy,
            'skip_catalog': self.snapconstants.skip_catalog
        }

        job = self.snapconstants.subclient.backup(self.snapconstants.backup_level,
                                                  advanced_options=advanced_option)
        self.log.info("sleeping for 10 seconds for job to start")
        time.sleep(10)
        self.log.info("Started {0} Snap backup with Job ID: {1}".format(
            self.snapconstants.backup_level, str(job.job_id)))
        self.log.info("backup level :{0}, job type {1}, job status {2}".format(
            job.backup_level, job.job_type, job.status))
        if job.status.lower() in ["failed", "failed to start"]:
            raise Exception("Job status is failed or failed to start")

        if self.snapconstants.is_suspend_job:
            if self.snapconstants.skip_catalog:
                phases = ["backup", "archive index"]
            else:
                phases = ["backup", "scan", "catalog", "archive index"]

            self.run_suspend_resume(job, phases)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    self.snapconstants.backup_level, job.delay_reason)
            )
        time.sleep(10)
        if job.backup_level.upper() == self.snapconstants.backup_level or job.backup_level.upper() == "SYNTHETIC FULL":
            self.log.info("backup level is same as we started")
        else:
            raise Exception("backup level is not same as we started")

        self.log.info("Successfully finished {0} Snap backup job".format(
            self.snapconstants.backup_level))

        if self.snapconstants.inline_bkp_cpy:
            attempt_count = 1
            while attempt_count <= 10:
                time.sleep(10)
                bkp_cpy_jid = self.snapconstants.execute_query(self.snapconstants.get_backup_copy_job,
                                                               {'a': job.job_id}, fetch_rows='one')
                if bkp_cpy_jid in [None, ' ', '']:
                    self.log.info(f"backup copy job for the snap job : {job.job_id} is not started. "
                                  "Waiting for some more time")
                else:
                    self.log.info(f"This is Inline backup job and Backup copy job id is: {bkp_cpy_jid}")
                    break
                attempt_count += 1
            if bkp_cpy_jid in [None, ' ', '']:
                raise Exception(
                    f"backup copy job for the snap job : {job.job_id} is not started after 100 seconds."
                    f" Please check logs"
                )
            else:
                bkp_job = Job(self.commcell, bkp_cpy_jid)
                self.log.info("Monitoring backup copy job: {0}".format(bkp_job.job_id))
            if self.snapconstants.is_suspend_job:
                phases = ['scan', 'backup', 'archive index']
                self.run_suspend_resume(bkp_job, phases)

            if not bkp_job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        bkp_job.backup_level, bkp_job.delay_reason)
                )
            self.log.info("successfully completed backup copy job: {0}".format(bkp_job.job_id))
        self.snapconstants.job_tracker.append(job.job_id)
        return job

    def snap_restore(self,
                     copy_precedence,
                     from_time=None,
                     to_time=None,
                     fs_options=False,
                     outplace=False,
                     inplace=False):
        """ Method for Restore from Snap job
            Return :
                    Object : job object of restore job
        """

        if fs_options:
            fs_options = {'no_image': True}
        else:
            fs_options = None
        self.log.info("*" * 10 + " Running restore from Snap Backup " + "*" * 10)
        if outplace:
            self.log.info("Running outplace restore from snap using Copy Precedence:{0}".format(
                copy_precedence))
            job = self.snapconstants.subclient.restore_out_of_place(
                self.client.client_name, self.snapconstants.snap_outplace_restore_location,
                self.snapconstants.source_path,
                copy_precedence=copy_precedence,
                from_time=from_time, to_time=to_time, fs_options=fs_options)

        elif inplace:
            self.log.info("Running inplace restore from snap using Copy Precedence:{0}".format(
                copy_precedence))
            job = self.snapconstants.subclient.restore_in_place(
                self.snapconstants.source_path,
                copy_precedence=copy_precedence,
                from_time=from_time, to_time=to_time, fs_options=fs_options)

        self.log.info("Started Restore from Snap Backup with job id: " + str(job.job_id))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore from Snap Backup: " + job.delay_reason
            )
        self.log.info("Successfully finished restore from Snap Backup")

    def snap_outplace(self, copy_precedence, from_time=None, to_time=None, fs_options=False):
        """ OutPlace restore from snapbackup

            Args :
                copy_precedence : precedence of snap copy

                from_time       : from time for browse, default: None

                to_time         : to time for Browse,  default: None

                fs_options      : if true then 'no_image'(show deleted items) option will be set
        """

        dir_name = self.options_selector._get_restore_dir_name()
        self.log.info("dir name: %s", dir_name)
        self.snapconstants.snap_outplace_restore_location = (f"{self.snapconstants.windows_restore_location}"
                                                             f"{self.snapconstants.delimiter}{dir_name}")
        self.client_machine.create_directory(self.snapconstants.snap_outplace_restore_location)
        self.log.info("restore location is %s", self.snapconstants.snap_outplace_restore_location)
        return self.snap_restore(
            copy_precedence, from_time=from_time, to_time=to_time, fs_options=fs_options,
            outplace=True)

    def snap_inplace(self, copy_precedence, from_time=None, to_time=None, fs_options=False):
        """ OutPlace restore from snapbackup

            Args :
                copy_precedence : precedence of snap copy

                from_time : from time for browse, default: None

                to_time : to time for Browse,  default: None

                fs_options : if true then 'no_image'(show deleted items) option will be set
        """
        return self.snap_restore(
            copy_precedence, from_time=from_time, to_time=to_time, fs_options=fs_options,
            inplace=True)

    def inplace_validation(self, jobid, copy_name, source_path):
        """ Validation for inplace restore operation
            Args:
                jobid : Job id used for the restore

                copy_name : copy name from which the restore is done

                source_path: Source directory Path
        """
        if isinstance(source_path, list):
            i = 0
            for path in source_path:
                folder_list = self.client_machine.get_folder_or_file_names(path, False)
                if self.os_name.upper() == 'WINDOWS':
                    folder_list = ' '.join(folder_list.splitlines()).split()[2:]
                for folder in folder_list:
                    self.compare(self.client_machine, self.client_machine,
                                 f"{path}{self.snapconstants.delimiter}{folder}",
                                 (f"{self.snapconstants.copy_content_location[i]}"
                                  f"{self.snapconstants.delimiter}TestData"
                                  f"{self.snapconstants.delimiter}{folder}"))
                i = i + 1

        elif isinstance(source_path, str):
            spcopy = self.spcopy_obj(copy_name)
            self.mount_snap(jobid, copy_name)
            mount_path = self.snapconstants.execute_query(self.snapconstants.get_mount_path,
                                                          {'a': jobid, 'b': spcopy.copy_id}
                                                          )
            i = 0
            for path in mount_path:
                if self.os_name.upper() == 'WINDOWS':
                    path[0] = f"{path[0]}\\TestData"
                else:
                    path[0] = f"{path[0]}/TestData"
                i = i + 1

            for path in mount_path:
                folder_list = self.client_machine.get_folder_or_file_names(
                    f"{path[0]}", False)
                if self.os_name.upper() == 'WINDOWS':
                    folder_list = ' '.join(folder_list.splitlines()).split()[2:]
                for folder in folder_list:
                    self.compare(self.client_machine, self.client_machine,
                                 f"{path[0]}{self.snapconstants.delimiter}{folder}",
                                 (f"{source_path}{self.snapconstants.delimiter}"
                                  f"TestData{self.snapconstants.delimiter}{folder}"))
            self.unmount_snap(jobid, copy_name)
            self.unmount_validation(jobid, copy_name)

    def outplace_validation(self, restore_location, restore_client):
        """ Validation for outplace restore operation
            Args:
                restore_location    : Data restore path

                restore_client      : client where the data is restored
        """
        outplace_restore_location = f"{restore_location}{self.snapconstants.delimiter}TestData"
        self.log.info("restore location is: %s", outplace_restore_location)
        for path in self.snapconstants.source_path:
            folder_list = self.client_machine.get_folder_or_file_names(path, False)
            if self.os_name.upper() == 'WINDOWS':
                folder_list = ' '.join(folder_list.splitlines()).split()[2:]
            for folder in folder_list:
                self.compare(self.client_machine, restore_client,
                             f"{path}{self.snapconstants.delimiter}{folder}",
                             f"{outplace_restore_location}{self.snapconstants.delimiter}{folder}")

    def compare(self, client_obj, destclient_obj, source_dir, dest_dir):
        """ Compare two directories
            Args:
                client_obj      : client Object of the Source machine

                destclient_obj  : client Object of the Destination machine

                source_dir      : Source directory Path

                dest_dir        : Destination directory Path
        """

        self.log.info("comparing content")
        self.log.info("source dir: %s", source_dir)
        self.log.info("dest dir : %s", dest_dir)

        difference = client_obj.compare_folders(
            destclient_obj, source_dir, dest_dir
        )

        if difference != []:
            self.log.error(
                "Validation failed. List of different files \n{0}".format(difference)
            )
            raise Exception(
                "validation failed. Please check logs for more details."
            )
        self.log.info("Compare folder validation was successful")

    def tape_restore(self,
                     copy_precedence,
                     from_time=None,
                     to_time=None,
                     fs_options=False,
                     outplace=False,
                     inplace=False):
        """ Restore from Tape Copy
            Args:
                copy_precedence : precedence of snap copy

                from_time       : from time for browse, default: None

                to_time         : to time for Browse,  default: None

                fs_options      : if true then 'no_image'(show deleted items) option will be set

                outplace        : set to True if outplace restore

                inplace         : set to True if inplace restore
        """

        if fs_options:
            fs_options = {'no_image': True}
        else:
            fs_options = None
        self.log.info("*" * 10 + " Running restore from tape copy " + "*" * 10)

        if outplace:
            self.log.info("""Running out of place restore from Tape using Copy Precedence: {0}
                """.format(copy_precedence))
            job = self.snapconstants.subclient.restore_out_of_place(
                self.snapconstants.windows_restore_client.machine_name,
                self.snapconstants.tape_outplace_restore_location, self.snapconstants.source_path,
                copy_precedence=copy_precedence,
                from_time=from_time, to_time=to_time, fs_options=fs_options
            )

        elif inplace:
            self.log.info("Running in place restore from Tape using Copy Precedence: {0}".format(
                copy_precedence))
            job = self.snapconstants.subclient.restore_in_place(
                self.snapconstants.source_path,
                copy_precedence=copy_precedence,
                from_time=from_time, to_time=to_time, fs_options=fs_options
            )

        self.log.info("Started Restore from tape copy with job id: " + str(job.job_id))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore from Tape copy: " + job.delay_reason
            )
        self.log.info("Successfully finished restore from Tape copy")

    def tape_outplace(self,
                      jobid,
                      copy_precedence,
                      from_time=None,
                      to_time=None,
                      fs_options=False):
        """ Outplace restore from tape copy
            Args:
                jobid           : jobid to find total nackup size

                copy_precedence : precedence of snap copy

                from_time       : from time for browse, default: None

                to_time         : to time for Browse,  default: None

                fs_options      : if true then 'no_image'(show deleted items) option will be set
        """
        size = 200
        size += int(self.snapconstants.execute_query(self.snapconstants.get_total_backup_size,
                                                     {'a': jobid},
                                                     fetch_rows='one')) / (1024 * 1024)
        self.log.info("Total Backed up size: {0}".format(size))
        # Find a client to restore the data
        if self.snapconstants.restore_client and self.snapconstants.restore_client is not None:
            self.snapconstants.windows_restore_client, self.snapconstants.tape_outplace_restore_location = \
                self.get_restore_client(self.snapconstants.restore_client, size=size)
        else:

            if self.os_name.upper() == 'WINDOWS':
                self.snapconstants.windows_restore_client, self.snapconstants.tape_outplace_restore_location = \
                    self.options_selector.get_windows_restore_client(size=size)
            else:
                self.snapconstants.windows_restore_client, self.snapconstants.tape_outplace_restore_location = \
                    self.options_selector.get_linux_restore_client(size=size)

        return self.tape_restore(
            copy_precedence, from_time=from_time, to_time=to_time, fs_options=fs_options,
            outplace=True)

    def tape_inplace(self, copy_precedence, from_time=None, to_time=None, fs_options=False):
        """ Inplace restore from tape copy
            Args:
                copy_precedence : precedence of snap copy

                from_time       : from time for browse, default: None

                to_time         : to time for Browse,  default: None

                fs_options      : if true then 'no_image'(show deleted items) option will be set
        """
        return self.tape_restore(
            copy_precedence, from_time=from_time, to_time=to_time, fs_options=fs_options,
            inplace=True)

    def snap_operations(self, jobid, copy_id, mode, client_name=None, mountpath=None, do_vssprotection=True):
        """ Common Method for Snap Operations
            Args :
                jobid             : jobid for the Snap operation

                copy_id           : copy id from which the snap operations needs to be done

                client_name       : name of the destination client, default: None

                MountPath         : MountPath for Snap operation, default: None

                do_vssprotection  : enable vss protection snap during mount

                mode              : mode can be mount,unmount,force_unmount,delete,force_delete,
                                    revert,reconcile

            Return :
                object : Job object of Snap Operation job
        """

        if mode == 'reconcile':
            control_hosts = self.snapconstants.execute_query(
                self.snapconstants.get_control_host, {'a': jobid})
            self.log.info("ControlHost Id is : {0}".format(control_hosts))
            if control_hosts in [None, ' ', '', [[]], []]:
                raise Exception("ControlHost Id is Empty, Cannot proceed with Reconcile operation")
            else:
                success = 0
                fail = 0
                repeats = 0
                runs = len(control_hosts)
                repeat = []
                for control_host in control_hosts:
                    runs -= 1
                    if control_host in repeat:
                        self.log.info("Reconcile repeat skipped for %s", str(control_host))
                        repeats += 1
                        if runs:
                            continue
                        break
                    repeat.append(control_host)
                    job = self.commcell.array_management.reconcile(int(control_host[0]))
                    self.log.info("Started  job : {0} for Snap Operation".format(job.job_id))

                    if not job.wait_for_completion():
                        self.log.info(
                            "Failed to run   job {0} for Snap operation with error: {1}".format(
                                job.job_id, job.delay_reason))
                        fail += 1
                        if runs:
                            continue
                        break

                    if job.status != 'Completed':
                        self.log.info(
                            "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                                job.job_id, job.delay_reason))
                        success += 1
                        if runs:
                            continue
                        break
                    success += 1
                    self.log.info("successfully completed Snap operation of jobid :{0}".format(
                        job.job_id))

                    time.sleep(40)
                self.log.info(
                    "Snap Reconcile operation successful for {0} out of {1} arrays".format(success, success + fail))
                if fail:
                    raise Exception(
                        "Reconcile operation failed for {0} out of {1} arrays. Check logs for more info.".format(fail,
                                                                                                                 success + fail))
                return job
        else:
            self.log.info("Getting SMVolumeId using JobId: {0} and Copy id: {1}".format(
                jobid, copy_id))
            volumeid = self.snapconstants.execute_query(self.snapconstants.get_volume_id,
                                                        {'a': jobid, 'b': copy_id})
            self.log.info("SMvolumeId is : {0}".format(volumeid))
            self.log.info("destination client name is :{0}".format(client_name))
            self.log.info("mountpath is {0}".format(mountpath))
            if volumeid[0][0] in [None, ' ', '']:
                if mode in ['mount', 'unmount', 'force_unmount', 'revert']:
                    raise Exception("VolumeID is Empty, Looks like it is deleted or never been "
                                    "created, Cannot proceed with Snap operation")
                elif mode in ['delete', 'force_delete']:
                    self.log.info("VolumeID is Empty, Looks like it is already deleted, "
                                  "treating it as soft failure")
            else:
                if mode == 'mount':
                    job = self.commcell.array_management.mount(volumeid,
                                                               client_name,
                                                               mountpath,
                                                               do_vssprotection)
                elif mode == 'unmount':
                    job = self.commcell.array_management.unmount(volumeid)
                elif mode == 'force_unmount':
                    job = self.commcell.array_management.force_unmount(volumeid)
                elif mode == 'revert':
                    job = self.commcell.array_management.revert(volumeid)
                elif mode == 'delete':
                    job = self.commcell.array_management.delete(volumeid)
                elif mode == 'force_delete':
                    job = self.commcell.array_management.force_delete(volumeid)
                else:
                    raise Exception("Failed to get Snap Operation Type")

                self.log.info("Started  job: {0} for Snap Operation".format(job.job_id))
                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run job: {0} for Snap operation with error: {1}".format(
                            job.job_id, job.delay_reason)
                    )
                if job.status != 'Completed':
                    raise Exception(
                        "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                            job.job_id, job.delay_reason)
                    )
                self.log.info("successfully completed Snap operation of jobid :{0}".format(
                    job.job_id))
                time.sleep(30)
                return job

    def mount_snap(self, jobid, copy_name, do_vssprotection=True, client_name=None, mountpath=None):
        """ Mounts Snap of the given jobid
            Args:
                jobid               : jobid for mount operation

                copy_name           : copy name from which the mount operations needs to be done

                do_vssprotection    : Performs VSS protected mount

                client_name         : name of the client on which the snap should be mounted

                mountpath           : path at which snap should be mounted



            Return:
                object              : job object of Snap operation job
        """
        spcopy = self.spcopy_obj(copy_name)
        self.log.info("Mounting snapshot of jobid : {0} from Copy: {1}".format(jobid, copy_name))

        mountMA = client_name or self.client.client_name

        mount_path = mountpath or self.snapconstants.mount_path

        return self.snap_operations(jobid,
                                    spcopy.copy_id, mode='mount',
                                    do_vssprotection=do_vssprotection,
                                    client_name=mountMA, mountpath=mount_path)

    def unmount_snap(self, jobid, copy_name):
        """ UnMounts Snap of the given jobid
            Args:
                jobid       : jobid for unmount operation

                copy_name   : copy name from which the unmount operations needs to be done

            Return:
                object      : job object of Snap operation job
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapconstants.mountpath_val = self.snapconstants.execute_query(
            self.snapconstants.get_mount_path,
            {'a': jobid, 'b': spcopy.copy_id}
        )
        self.log.info("UnMounting snapshot of jobid : {0} from Copy: {1}".format(jobid, copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='unmount')

    def force_unmount_snap(self, jobid, copy_name):
        """ UnMounts Snap of the given jobid
            Args:
                jobid       : jobid for unmount operation

                copy_name   : copy name from which the force unmount operations needs to be done

            Return:
                object      : job object of Snap operation job
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapconstants.mountpath_val = self.snapconstants.execute_query(
            self.snapconstants.get_mount_path,
            {'a': jobid, 'b': spcopy.copy_id}
        )
        self.log.info("UnMounting snapshot of jobid : {0} from Copy: {1}".format(jobid, copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='force_unmount')

    def revert_snap(self, jobid, copy_name):
        """ Reverts Snap of the given jobid
            Args:
                jobid       : jobid for revert operation

                copy_name   : copy name from which the revert operations needs to be done

            Return:
                object      : job object of Snap operation job
        """
        spcopy = self.spcopy_obj(copy_name)
        self.log.info("Reverting snapshot of jobid : {0} from Copy: {1}".format(jobid, copy_name))
        self.log.info("deleting subclient content before revert operation")
        self.remove_subclient_content()
        return self.snap_operations(jobid, spcopy.copy_id, mode='revert')

    def delete_snap(self, jobid, copy_name, is_mirror=False, source_copy_for_mirror=False):
        """ Deletes Snap of the given jobid
            Args:
                jobid                   : jobid for delete operation

                copy_name               : copy name from which the delete operations needs to be
                                          done

                is_mirror               : if mirror snap needs to be deleted

                source_copy_for_mirror  : Source Copy Name of the Mirror

            Return:
                object : job object of Snap operation job
        """
        if is_mirror:
            spcopy = self.spcopy_obj(source_copy_for_mirror)
        else:
            spcopy = self.spcopy_obj(copy_name)
        self.log.info("Deleting snapshot of jobid : {0} from Copy: {1}".format(
            jobid, spcopy._copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='delete')

    def force_delete_snap(self, jobid, copy_name):
        """ Force Deletes Snap of the given jobid
            Args:
                jobid       : jobid for delete operation

                copy_name   : copy name from which the delete operations needs to be done

            Return:
                object      : job object of Snap operation job
        """

        spcopy = self.spcopy_obj(copy_name)
        self.log.info("Force Deleting snapshot of jobid : {0} from Copy: {1}".format(
            jobid, spcopy._copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='force_delete')

    def reconcile_snap(self, jobid):
        """ Runs Reconcile Operation of the array for the given jobid
            Args:
                jobid       : jobid for Reconcile operation
            Return:
                object      : job object of Snap operation job
        """
        self.log.info("Running Reconcile Operation")
        return self.snap_operations(jobid, copy_id=None, mode='reconcile')

    def snapop_validation(self,
                          jobid,
                          copy_id,
                          mount=False, revert=False, delete=False, unmount=False,
                          client_name=None):
        """ Common Method for Snap Operation Validations
            Args:
                jobid       : snap backup jobid

                copy_id     : copy id from which the snap validation needs to be done

                client_name : client name or proxy on which snap is mounted

        """
        self.log.info("validating snap operation")

        if mount:

            if client_name is not None:
                mountMA = Machine(self.commcell.clients.get(client_name))
            else:
                mountMA = self.client_machine

            self.snapconstants.mountpath_val = self.snapconstants.execute_query(
                self.snapconstants.get_mount_path,
                {'a': jobid, 'b': copy_id}
            )
            for i in range(len(self.snapconstants.mountpath_val)):
                if self.os_name.upper() == 'WINDOWS':
                    test_data_path = "\\TestData"
                else:
                    test_data_path = "/TestData"
                self.compare(
                    mountMA, self.client_machine,
                    f"{self.snapconstants.mountpath_val[i][0]}{test_data_path}",
                    self.snapconstants.test_data_path[i])
                self.log.info("comparing files/folders was successful")

        elif revert:
            self.inplace_validation(jobid,
                                    self.snapconstants.snap_copy_name,
                                    self.snapconstants.test_data_path)

        elif delete:
            wait_time = 0
            self.log.info("Checking if the snapshot of JobId: {0} exists in the DB".format(jobid))
            while True:
                volumeid = self.snapconstants.execute_query(self.snapconstants.get_volume_id,
                                                            {'a': jobid, 'b': copy_id})
                self.log.info("smvolumeid from DB is: {0}".format(volumeid))
                if volumeid[0][0] in [None, ' ', '']:
                    self.log.info("Snapshot is successfully deleted")
                    break
                else:
                    self.log.info("Sleeping for 2 minutes")
                    time.sleep(120)
                    wait_time += 2
                if wait_time > 20:
                    raise Exception(
                        "Snapshot of jobid: %s is not deleted yet, please check the CVMA logs" %jobid)
            self.log.info("Successfully verified Snapshot cleanup")

        elif unmount:
            for path in self.snapconstants.mountpath_val:
                if self.client_machine.check_directory_exists(path[0]):
                    raise Exception("MountPath folder still exists under {0}".format(path[0]))
                else:
                    self.log.info("MountPath folder path: {0} does not exists".format(path[0]))

        time.sleep(60)

    def mount_validation(self, jobid, copy_name, client_name=None):
        """ Mount Snap validation
            Args :
                jobid       : snap backup jobid

                copy_name   : copy name from which the mount validation needs to be done

                client_name : client on which snap to be mounted

        """

        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, mount=True, client_name=client_name)
        self.log.info("mount validation was successful")

    def revert_validation(self, jobid, copy_name):
        """ Revert Snap validation
            Args :
                jobid       : snap backup jobid

                copy_name   : copy name from which the revert validation needs to be done
        """
        spcopy = self.spcopy_obj(copy_name)
        time.sleep(60)
        self.snapop_validation(jobid, spcopy.copy_id, revert=True)
        self.log.info("revert validation was successful")

    def delete_validation(self, jobid, copy_name):
        """ Delete Snap validation
            Args :
                jobid       : snap backup jobid

                copy_name   : copy name from which the delete validation needs to be done
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, delete=True)
        self.log.info("delete validation was successful")

    def unmount_validation(self, jobid, copy_name):
        """ UnMount Snap validation
            Args :
                jobid       : snap backup jobid

                copy_name   : copy name from which the unmount validation needs to be done
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, unmount=True)
        self.log.info("unmount validation was successful")

    def check_mountstatus(self, jobid, unmount=False):
        """ Common function to check mount status
            Args:
                jobid : snap backup jobid
        """

        if unmount:
            while self.snapconstants.mount_status not in ['79', '']:
                self.snapconstants.mount_status = self.snapconstants.execute_query(
                    self.snapconstants.get_mount_status, {'a': jobid}, fetch_rows='one')
                self.log.info("mount status of jobid :{0} is :{1}".format(
                    jobid, self.snapconstants.mount_status))
                self.log.info("snapshot is not unmounted yet, checking after 1min")
                time.sleep(60)
                continue
            self.log.info("snapshot of jobid {0} is unmounted successfully".format(jobid))

        return self.snapconstants.mount_status

    def unmount_status(self, jobid):
        """ Check Unmount status
            Args:
                jobid : snap backup jobid
        """
        return self.check_mountstatus(jobid, unmount=True)

    def update_storage_policy(self,
                              enable_backup_copy=False,
                              source_copy_for_snap_to_tape=None,
                              enable_snapshot_catalog=False,
                              source_copy_for_snapshot_catalog=None,
                              enable_selective_copy=0,
                              disassociate_sc_from_backup_copy=None):
        """ Method for Updating Storage Policy Options like Backup Copy and Snapshot Catalog
            Args:
                enable_backup_copy               (bool) -- Enables backup copy if the value is True

                source_copy_for_snap_to_tape     (str)  -- Source Copy name for backup copy

                enable_snapshot_catalog          (bool) -- Enables Snapshot Catalog if value isTrue

                source_copy_for_snapshot_catalog (str)  -- Source Copy name for Snapshot Catalog

                enable_selective_copy                (int)  -- Enables selective copy with value provided

                disassociate_sc_from_backup_copy    (bool)  -- If True: Disassociates subclient from backup copy
                                                                False: Associates subclient from backup copy

        """

        options = {
            'enable_backup_copy': enable_backup_copy,
            'source_copy_for_snap_to_tape': source_copy_for_snap_to_tape,
            'enable_snapshot_catalog': enable_snapshot_catalog,
            'source_copy_for_snapshot_catalog': source_copy_for_snapshot_catalog,
            'is_ocum': self.snapconstants.ocum_server,
            'enable_selective_copy': enable_selective_copy,
            'disassociate_sc_from_backup_copy': disassociate_sc_from_backup_copy
        }

        if options['disassociate_sc_from_backup_copy'] is not None:
            subclient_details = self.get_subclient_details(self.snapconstants.subclient)
            options.update(subclient_details)
            if options['disassociate_sc_from_backup_copy']:
                self.log.info(f'Disassociating Subclient {self.snapconstants.subclient.subclient_name} from storage policy '
                              f'{self.snapconstants.storage_policy.storage_policy_name} ')
            else:
                self.log.info(f'Associating Subclient {self.snapconstants.subclient.subclient_name} from storage policy '
                              f'{self.snapconstants.storage_policy.storage_policy_name} ')
            self.snapconstants.storage_policy.update_snapshot_options(**options)
            self.log.info("successfully completed update operation on storage policy: {0}".format(
                self.snapconstants.storage_policy.storage_policy_name))

        else:

            if enable_backup_copy:
                self.log.info("Enabling Backup Copy Option on Storage Policy: {0}".format(
                    self.snapconstants.storage_policy.storage_policy_name)
                )
            else:
                self.log.info("Disabling Backup Copy Option on Storage Policy: {0}".format(
                    self.snapconstants.storage_policy.storage_policy_name)
                )

            if enable_snapshot_catalog:
                self.log.info("Enabling Snapshot Catalog Option on Storage Policy: {0}".format(
                    self.snapconstants.storage_policy.storage_policy_name)
                )
            else:
                self.log.info("Disabling Snapshot Catalog Option on Storage Policy: {0}".format(
                    self.snapconstants.storage_policy.storage_policy_name)
                )

            self.snapconstants.storage_policy.update_snapshot_options(**options)
            self.log.info("successfully completed update operation on storage policy: {0}".format(
                self.snapconstants.storage_policy.storage_policy_name))
            if enable_backup_copy:
                self.delete_bkpcpy_schedule()

    def backup_copy(self):
        """ Runs Offline backup copy for the given storage policy
        """

        job = self.snapconstants.storage_policy.run_backup_copy()
        self.log.info("Backup copy workflow job id is : {0}".format(job.job_id))

        if self.snapconstants.is_suspend_job:
            suspend_completed_jobs = []
            while True:
                self.log.info("Sleeping for 20 secs")
                time.sleep(20)
                backup_job_id = self.snapconstants.execute_query(self.snapconstants.get_backup_copy_jobid,
                                                                 {'a': job.job_id})
                new_job = False
                for i in backup_job_id:
                    self.log.info(f"backup copy job id: {i}")
                    if bool(i[0]) and i not in suspend_completed_jobs and i[0] != '0':
                        new_job = True
                        suspend_completed_jobs.append(i)
                        self.log.info("Sleeping for 1 minute")
                        time.sleep(60)
                        backup_job = Job(self.commcell, i[0])
                        phases = ['scan', 'backup', 'archive index']
                        self.run_suspend_resume(backup_job, phases)
                        if not backup_job.wait_for_completion(timeout=60):
                            self.log.info("Backup copy job {0} failed/killed".format(backup_job.job_id))
                            new_job = False
                            break
                if not new_job:
                    break

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run  Workflow job {0} for backup copy with error: {1}".format(
                    job.job_id, job.delay_reason)
            )
        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, Reason: {1}".format(
                    job.job_id, job.delay_reason)
            )
        self.log.info("Successfully finished backup copy workflow Job :{0}".format(job.job_id))

    def snapshot_cataloging(self):
        """ Runs Offline snapshot cataloging for the given storage policy
        """

        job = self.snapconstants.storage_policy.run_snapshot_cataloging()
        self.log.info("Deferred Catalog workflow job id is : {0}".format(job.job_id))

        if self.snapconstants.is_suspend_job:
            suspend_completed_jobs = []
            while True:
                self.log.info("Sleeping for 20 secs")
                time.sleep(20)
                catalog_job_id = self.snapconstants.execute_query(self.snapconstants.get_backup_copy_jobid,
                                                                  {'a': job.job_id})
                new_job = False
                for i in catalog_job_id:
                    self.log.info(f"catalog copy job id: {i}")
                    if bool(i[0]) and i not in suspend_completed_jobs and i[0] != '0':
                        new_job = True
                        suspend_completed_jobs.append(i)
                        catalog_job = Job(self.commcell, i[0])
                        phases = ['scan', 'catalog', 'archive index']
                        self.run_suspend_resume(catalog_job, phases)
                        if not catalog_job.wait_for_completion(timeout=60):
                            self.log.info("Backup copy job {0} failed/killed".format(catalog_job.job_id))
                            new_job = False
                            break
                if not new_job:
                    break

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run  Workflow job {0} for Deferred Catalog with error: {1}".format(
                    job.job_id, job.delay_reason)
            )
        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Snapshot catalog operation is completed with errors".format(
                    job.job_id)
            )
        self.log.info("Successfully completed deferred catalog job: {0}".format(job.job_id))

    def aux_copy(self, copy_name=None, use_scale=False):
        """ Runs Auxilliary copy for the given storage policy and copy
            Args:
                copy_name       (str)       -- Copy name for which aux copy needs to be run
                default: None

                use_scale       (bool)      -- Use scalable resource allocation
                default: None
                
            Returns:
                    object : job Object
        """

        if copy_name is not None:
            job = self.snapconstants.storage_policy.run_aux_copy(
                copy_name, str(self.tcinputs['MediaAgent']), use_scale)
        else:
            job = self.snapconstants.storage_policy.run_aux_copy(
                media_agent=str(self.tcinputs['MediaAgent']), use_scale=use_scale)
        self.log.info("Started Aux copy job with job id: " + str(job.job_id))

        if self.snapconstants.is_suspend_job:
            count = 0
            if use_scale:
                while count <= 2:
                    time.sleep(30)
                    if job.is_finished:
                        self.log.info('Job finished before suspending, continuing..')
                        break
                    self.suspend_job(job)
                    self.log.info("sleeping for one minutes")
                    time.sleep(60)
                    self.log.info("Resuming job :{0}".format(job))
                    if job.is_finished:
                        self.log.info('Job finished before resuming, continuing..')
                        break
                    self.resume_job(job)
                    count += 1
            else:
                while count <= 2:
                    time.sleep(150)
                    if job.is_finished:
                        self.log.info('Job finished before suspending, continuing..')
                        break
                    self.suspend_job(job)
                    self.log.info("sleeping for one minutes")
                    time.sleep(60)
                    self.log.info("Resuming job :{0}".format(job))
                    if job.is_finished:
                        self.log.info('Job finished before resuming, continuing..')
                        break
                    self.resume_job(job)
                    count += 1

        elif self.snapconstants.is_kill_process:
            time.sleep(150)
            self.log.info("Killing Aux copy Process to make aux opy failure")
            self.client_machine.kill_process("AuxCopy")
            count = 0
            while count <= 4:
                time.sleep(30)
                flag = self.client_machine.is_process_running("AuxCopy")
                if count == 4 and flag:
                    raise Exception("Aux Copy Process did not get killed")
                elif not flag:
                    self.log.info("Aux copy process is killed")
                    break
                count += 1
            self.log.info("sleeping for 3 minutes")
            time.sleep(180)
            self.log.info("Resuming job :{0}".format(job))
            if job.is_finished:
                self.log.info('Job finished before resuming, continuing..')
            else:
                self.resume_job(job)

        if not job.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: " + str(job.delay_reason))
        if job.status != 'Completed':
            raise Exception(
                "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                    job.job_id, job.delay_reason)
            )
        self.log.info("Successfully finished Aux copy job: {0}".format(job.job_id))
        time.sleep(30)
        return job

    def run_data_aging(self, copy_name=None):
        """Runs data aging for the given storage policy and copy
            Args:
                copy_name       (str)       -- Copy name for which Data Aging needs to be run
        """

        attempt_count = 1
        while attempt_count <= 10:
            job = self.commcell.run_data_aging(copy_name=copy_name,
                                               storage_policy_name=self.snapconstants.storage_policy.storage_policy_name,
                                               is_granular=True,
                                               include_all_clients=True,
                                               select_copies=True,
                                               prune_selected_copies=True)
            if job.status.lower() == 'failed to start':
                self.log.info("Failed to start the Data aging Job, will Retry after 60 seconds, "
                              "Retry Attempt: %s", attempt_count)
                time.sleep(60)
            else:
                self.log.info("Successfully started data aging jobid: %s, job status: %s"
                              % (job.job_id, job.status))
                break
            attempt_count += 1

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run data aging job {0} with error: {1}".format(
                    job.job_id, job.delay_reason)
            )
        if job.status != 'Completed':
            raise Exception(
                "Data Aging job: %s did not completed Successfully, Job status: %s, Reason: %s "
                "" %(job.job_id, job.status, job.delay_reason)
            )
        self.log.info("Successfully finished data aging Job :{0}".format(job.job_id))

    def get_jobid_list(self, copy_id):
        """ Fetches job id list from the snap copy
            Args:
                copy_id         (int)   -- copy id to which snap list need be queried
        """

        snapbda = self.snapconstants.execute_query(self.snapconstants.fetch_job_ids, {'a': copy_id})

        if len(snapbda) <= 0:
            self.log.error("Unable to fetch the smvolumeID from DB")

        else:
            volume_id_list = []
            for i in range(len(snapbda)):
                if snapbda[i] not in volume_id_list:
                    volume_id_list.append(snapbda[i][0])

        return volume_id_list

    def data_aging_validation(self,
                              copy_name,
                              source_copy_for_mirror=None, vault=False, mirror=False):
        """Validates if the jobs are pruned after running the data aging
            Agrs:
                copy_name               (str) -- copy name for which data aging validation needs
                                                 to be done

                source_copy_for_mirror  (str) -- if Copy type is mirror then source copy name needs
                                                 to be provided
        """

        spcopy = self.spcopy_obj(copy_name)
        job_id_list = self.get_jobid_list(spcopy.copy_id)
        self.log.info("Job IDs before running data aging %s" % (job_id_list))
        jobtracker = self.snapconstants.job_tracker

        if vault:
            self.log.info("""setting retention to 0 day 1 cycle on vault copy : {0} to verify aging
                          """.format(copy_name))
            spcopy.copy_retention = (0, 1, 0)
            self.run_data_aging(copy_name=copy_name)
            number_of_jobs = len(jobtracker) - 2

        elif mirror:
            sourcecopy = self.spcopy_obj(source_copy_for_mirror)
            if self.snapconstants.type in {"pvm", "pvm_replica", "all"}:
                self.log.info("setting retention to 0 day 1 cycle on source copy **{0}** of "
                              "mirror to verify aging".format(source_copy_for_mirror))
                sourcecopy.copy_retention = (0, 1, 0)
                number_of_jobs = len(jobtracker) - 2
            else:
                sourcecopy.copy_retention = (0, 0, 0)
                number_of_jobs = len(jobtracker)
            self.run_data_aging(copy_name=source_copy_for_mirror)

        else:
            self.log.info("setting retention to spool on snap copy : {0} to verify aging".format(
                copy_name))
            spcopy.copy_retention = (0, 0, 0, 0)
            self.run_data_aging(copy_name=copy_name)
            number_of_jobs = len(jobtracker)

        job_id_list = self.get_jobid_list(spcopy.copy_id)
        self.log.info("Job IDs after running data aging %s" % (job_id_list))

        i = 1
        wait_time = 0
        for job in jobtracker:
            if i <= number_of_jobs:
                while True:
                    volumeid_val = self.snapconstants.execute_query(self.snapconstants.get_volumeid_da,
                                                                    {'a': job, 'b': spcopy.copy_id})
                    if volumeid_val[0][0] in [None, ' ', '']:
                        break
                    else:
                        self.log.info("Sleeping for 2 minutes")
                        time.sleep(120)
                        wait_time += 2
                    if wait_time > 20:
                        raise Exception(
                            "Snapshot of jobid: {0} is not yet deleted,"
                            "please check the CVMA logs".format(job)
                        )

                self.log.info("Snapshot for job {0} deleted successfully".format(job))

            i = i + 1
        self.log.info("Successfully completed Aging verification on copy :{0}".format(copy_name))
        if mirror:
            sourcecopy.copy_retention = (0, 1, 0)
        else:
            spcopy.copy_retention = (0, 1, 0)

    def update_mmconfig(self, value):
        """ Method to Update MM config MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES
        Args:
            value       (int)       --  Config Value to Update
        """

        qscript = "-sn setConfigParam -si MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES -si {0}".format(value)
        response = self.commcell._qoperation_execscript(qscript)
        self.log.info("qscript response: [{0}]".format(response))

        self.log.info("""Successfully Updated MMConfig 'MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES'
                      to :{0}""".format(value))

    def clean_snap_environment(self):
        """ includes disable Intellisnap at subclient, delete subclient, delete backupset,
            delete aux and snap copy, delete storage policy, delete library,
        """

        # Disable Intellisnap on Subclient
        self.log.info("Disabling Intellisnap on subclient: {0}".format(
            self.snapconstants.subclient.subclient_name)
        )
        self.snapconstants.subclient.disable_intelli_snap()
        self.log.info("Successfully Disabled Intellisnap on subclient: {0}".format(
            self.snapconstants.subclient.subclient_name)
        )

        self.entities.delete({'subclient': self.snapconstants.entity_properties['subclient']})
        self.entities.delete({'backupset': self.snapconstants.entity_properties['backupset']})

        current_value = self.snapconstants.execute_query(self.snapconstants.current_mmconfig,
                                                         fetch_rows='one')
        self.log.info("""Current value of MM Config 'MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES'
                      is : {0} minutes""".format(current_value))
        self.log.info("Updating it to 1 Minutes to Prune SP and copies")

        self.update_mmconfig(1)

        if self.snapconstants.type in {"pv", "pv_replica", ReplicationType.PV_Replica_c2c}:
            self.log.info("Deleting First Node Copy {0}".format(
                self.snapconstants.first_node_copy))
            self.delete_copy(self.snapconstants.first_node_copy)
            self.log.info("Sucessfully delete First Node Copy: {0}".format(
                self.snapconstants.first_node_copy))
            self.run_data_aging()
            self.log.info("Sleeping for 8 mins")
            time.sleep(480)
            if self.snapconstants.ocum_server:
                self.log.info("Storage Policy is created with OCUM, Not deleting\
                              Primary Snap Copy")
            else:
                self.log.info("deleting Primary Snap Copy")
                self.delete_copy(self.snapconstants.snap_copy_name)

        elif self.snapconstants.type in {"pvm", "pmv_replica", "pmm_replica", "pvv_replica"}:
            self.log.info("Deleting Second Node Copy {0}".format(
                self.snapconstants.second_node_copy))
            self.delete_copy(self.snapconstants.second_node_copy)
            self.log.info("Sucessfully deleted Second Node Copy: {0}".format(
                self.snapconstants.second_node_copy))
            self.run_data_aging()
            self.log.info("Sleeping for 8 mins")
            time.sleep(480)
            self.log.info("Deleting First Node Copy {0}".format(
                self.snapconstants.first_node_copy))
            self.delete_copy(self.snapconstants.first_node_copy)
            self.log.info("Sucessfully delete First Node Copy: {0}".format(
                self.snapconstants.first_node_copy))
            self.run_data_aging()
            self.log.info("Sleeping for 8 mins")
            time.sleep(480)
            if self.snapconstants.ocum_server:
                self.log.info("Storage Policy is created with OCUM, Not deleting Primary Snap Copy")
            else:
                self.log.info("deleting Primary Snap Copy")
                self.delete_copy(self.snapconstants.snap_copy_name)

        elif self.snapconstants.type == "fanout":
            try:
                self.entities.delete(
                    {'storagepolicy': self.snapconstants.entity_properties['storagepolicy']})
            except Exception as e:
                self.log.info("deleting Storage policy failed with err: " + str(e))
                self.log.info("treating it as soft failure")
            self.run_data_aging()
            self.log.info("Sleeping for 5 mins")
            time.sleep(300)

        else:
            if self.snapconstants.ocum_server:
                self.log.info("Storage Policy is created with OCUM, Not deleting Primary Snap Copy")

        # Cleanup Entities
        try:
            self.entities.cleanup()
        except Exception as e:
            self.log.info("deleting Storage policy failed with err: " + str(e))
            self.log.info("treating it as soft failure")
        self.log.info("""Updating back to original value : {0} of config
                      'MMCONFIG_ARCHGROUP_CLEANUP_INTERVAL_MINUTES'""".format(current_value))
        self.update_mmconfig(current_value)

    def clear_locations(self):
        """
            Remove Subclient content
            Remove Restore location
            Remove Mountpath
        """

        try:
            self.remove_subclient_content()
            self.log.info("Successfully removed Subclient Content")
            self.client_machine.remove_directory(self.snapconstants.windows_restore_location)
            self.log.info("Successfully removed Restore Location")
            self.client_machine.remove_directory(self.snapconstants.mount_path)
            self.log.info("Successfully removed MountPath")
            if (self.snapconstants.proxy_client != self.client.client_name and
                    self.snapconstants.proxy_client is not None):
                Machine(self.commcell.clients.get(self.snapconstants.proxy_client)).remove_directory(
                    self.snapconstants.mount_path)
                self.log.info("Successfully removed MountPath on proxy client")


            self.client_machine.remove_directory(self.snapconstants.disk_lib_loc)
            self.log.info("Successfully removed disk library location")
            self.snapconstants.windows_restore_client.remove_directory(
                self.snapconstants.tape_outplace_restore_location)
            self.log.info("Successfully removed Tape restore location")
        except Exception as e:
            self.log.info('Removing location failed with err: ' + str(e))

    def remove_subclient_content(self):
        """
            Delete data under subclient content
        """
        for path in self.snapconstants.test_data_path:
            self.log.info("deleting the content from {0}".format(path))
            self.client_machine.remove_directory(path)

    def cleanup(self):
        """ Cleanup function to clear locations and snap entities """

        if self.snapconstants.sc_name is None:
            self.clean_snap_environment()
        else:
            self.log.info("***Not cleaning up the snap entities as the test case is run on "
                          "Existing subclient***")
        self.clear_locations()

    def delete_array(self):
        """ Method to Delete the array management entry
        """
        try:
            self.log.info("Deleting the array management entry : {0}".format(
                self.snapconstants.arrayname))
            control_host_array = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': self.snapconstants.arrayname},
                fetch_rows='one')
            if control_host_array in [None, ' ', '']:
                self.log.info("Array Management entry Not found in the database, "
                              "Treating this as Soft Failure")
            else:
                error_message = self.commcell.array_management.delete_array(control_host_array)
                self.log.info("{0}".format(error_message))

        except SDKException as e:
            if e.exception_id == '103':
                self.log.info("{0}".format(e.exception_message))
                self.log.info("Treating this as Soft failure")
            else:
                raise Exception(e)

    def spcopy_obj(self, copy_name):
        """ Create storage Policy Copy object
        Arg:
            copy_name        (str)         -- Copy name
        """
        spcopy = StoragePolicyCopy(self.commcell, self.snapconstants.storage_policy, copy_name)
        return spcopy

    def vplex_snap_validation(self, jobid, copy_name):
        """ Validate snap created on both the nodes of Vplex Array
        Args:
            jobid       (int)       -- Vplex Snapbackup job id

            copy_name   (str)       -- Copy name from where the job belongs
        """
        spcopy = self.spcopy_obj(copy_name)

        self.log.info("Getting SMVolumeId using JobId: {0}".format(jobid))
        volumeid = [self.snapconstants.execute_query(
            self.snapconstants.get_volume_id, {'a': jobid, 'b': spcopy.copy_id}, fetch_rows='one')]

        for volid in volumeid:
            cntrl_host = self.snapconstants.execute_query(
                self.snapconstants.vplex_control_host, {'a': volid})
            frontend_control_host = int(cntrl_host[0][1])
            Backend1_control_host = int(cntrl_host[0][0])
            Backend2_control_host = int(cntrl_host[1][0])
            snap_count = self.snapconstants.execute_query(self.snapconstants.get_snap_count,
                                                          {'a': frontend_control_host,
                                                           'b': jobid,
                                                           'c': Backend1_control_host,
                                                           'd': Backend2_control_host}
                                                          )
            if len(snap_count) == 2:
                self.log.info("Metrocluster Test succeed: Created snap on both Backend arrays")
            else:
                raise Exception("Metrocluster Test failed: Snap not present on both backend arrays")

    def edit_array(self,
                   array_name,
                   snap_configs=None,
                   config_update_level=None,
                   level_id=None,
                   array_access_node=None,
                   gad_arrayname=None):
        """Method to Update Snap Configurations and array access nodes for the given array
        Args:
            array_name              (str)     -- Name of the Array

            snap_configs            (dict)     -- Snap Configs in Dict format
            Ex: {"Mount Retry Interval (in seconds)" : "600", "Array Host Aliases" : {"msconfig1" : "add", "msconfig2" : "delete", "New alias Name" : "Old alias name"}}

            config_update_level     (int)     -- update level for the Snap config
            default: "array"
            other values: "subclient", "copy", "client"

            level_id                (int)     -- level Id where the config needs to be
                                                 added/updated, ex: Subclient, client, copy id's
            default: None

            array_access_node       (dict)    -- Array Access Node MA's in dict format with mode
            default: None
            Ex: {"MediaAgent1" : "add", "MediaAgent2" : "add", "MediaAgent3" : "delete"}

            gad_arrayname : array name for which snap configs to be updated in case of GAD

        """
        if gad_arrayname is not None:
            control_host_id = self.snapconstants.execute_query(
                self.snapconstants.get_gad_controlhost_id, {'a': gad_arrayname,
                                                            'b': array_name}, fetch_rows='one')
        else:
            control_host_id = self.snapconstants.execute_query(
                self.snapconstants.get_controlhost_id, {'a': array_name}, fetch_rows='one')
        if snap_configs is not None:
            config_data = {}
            for config, value in snap_configs.items():
                master_config_id = self.snapconstants.execute_query(
                    self.snapconstants.get_master_config_id,
                    {'a': config, 'b': self.snapconstants.snap_engine_at_array},
                    fetch_rows='one')
                config_data[master_config_id] = value
            self.log.info("Updating the Snap Config: '{0}' on Array: '{1}' at : *{2}* level".format(
                snap_configs, array_name, config_update_level)
            )
        else:
            config_data = None

        if array_access_node is not None:
            self.log.info("Updating Array Access Nodes :{0}".format(array_access_node))

        self.commcell.array_management.edit_array(control_host_id,
                                                  config_data,
                                                  config_update_level,
                                                  level_id=level_id,
                                                  array_access_node=array_access_node)
        if snap_configs is not None:
            self.log.info("Successfully Updated Snap Configs: '{0}' on Array: '{1}'at : *{2}* level".format(
                snap_configs, array_name, config_update_level)
            )
        if array_access_node is not None:
            self.log.info("Successfully Updated Array Access Nodes :{0}".format(array_access_node))

    def verify_extentbased_subclient(self, job):
        """

        Template to run extent level validation after snap backup

            Args:
                job     (object) --- job of the snap backup

        """
        self.job = job
        self.log.info("Getting RemoteFileCache for SubclientPropertiesFile location from MediaAgent")
        properties = self.snapconstants.subclient.subclient_guid
        self.log.info("The subclient GUID obtained is %s", properties)
        output = self.snapconstants.execute_query(self.snapconstants.get_indexcache_location,
                                                  {'a': self.client.client_name})
        self.log.info("The query output is : %s", output)
        output = output[0]
        self.log.info("The actualy ouput derived from the above query is %s", output[0])
        SPPath = output[
                     0] + '\\RemoteFileCache\\2' + '\\' + properties + '\\' + self.job.job_id + '\\File System' + '\\SubClientProperties.cvf'
        self.log.info(SPPath)
        result = self.client_machine.read_file(SPPath).find("fileAsExtentsBackupEnabled=\"1\"")
        if result != -1:
            self.log.info("File extent is enabled on the client")
            self.log.info("Snap backup validation passed")
        else:
            self.log.info("Snap backup validation failed")

    def snap_extent_template(self, set_proxy_options=False):
        """

        Template to run extent test case for intellisnap

            Args:
                set_proxy_options      (bool)   --    True, if the proxy needed otherwise False.

        """

        self.log.info("*" * 20 + "Running with Catalog Phase" + "*" * 20)

        self.create_snap_environment()
        proxy_options = {
            'snap_proxy': self.client_machine,  # assigning client name as proxy incase if set_proxy_options is false
            'backupcopy_proxy': self.client_machine,
            'use_source_if_proxy_unreachable': True
        }
        if set_proxy_options:
            proxy_options = {
                'snap_proxy': self.tcinputs['Snap_Proxy'],
                'backupcopy_proxy': self.tcinputs['Backupcopy_Proxy'],
                'use_source_if_proxy_unreachable': True
            }
            self.snapconstants.subclient.enable_intelli_snap(
                self.tcinputs['SnapEngine'], proxy_options)
        fsa = "FileSystemAgent"
        enable = "bEnableFileExtentBackup"
        slab = "mszFileExtentSlabs"
        slab_val = str(self.tcinputs.get("Slab", "10-1024=5"))
        self.log.info("01 : Enable feature by setting {} under {} on client."
                      .format(enable, fsa))
        self.client_machine.create_registry(fsa, enable, 1)
        self.log.info(
            "02 : Lowering threshold by setting {} under {} on client.".format(
                slab, fsa))
        self.client_machine.create_registry(fsa, slab, slab_val)
        self.add_test_data_folder()
        for test_path in self.snapconstants.test_data_path:
            self.snapconstants.name = self.snapconstants.folder_name(
                self.snapconstants.backup_level)
            test_data_folder = test_path + '\\' + self.snapconstants.name
            self.log.info("Generating test data at: {0}".format(test_data_folder))
            self.client_machine.generate_test_data(test_data_folder,
                                                   dirs=1,
                                                   files=5,
                                                   file_size=1097152
                                                   )
            self.log.info("Successfully Generated data at: {0}".format(test_data_folder))
        job = self.snap_backup()
        self.log.info("Snap backup completed successfully")
        self.log.info("Validation for snap backup")
        self.verify_extentbased_subclient(job)
        self.log.info("Running backupcopy job from storage policy")
        self.backup_copy()
        self.log.info("Backup copy job completed successfully")
        self.snapconstants.windows_restore_client = Machine(self.tcinputs["RestoreClient"], self.commcell)
        self.snapconstants.tape_outplace_restore_location = self.tcinputs["RestoreLocation"]
        self.snapconstants.source_path = self.tcinputs["SourcePath"]
        self.tape_outplace(job.job_id, 2, job.start_time, job.end_time)
        self.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                 self.snapconstants.windows_restore_client)
        remove_msg = "Removing registry entries {} and {} under {}".format(
            enable, slab, fsa)
        self.log.info(remove_msg)
        self.client_machine.remove_registry(fsa, enable)
        self.client_machine.remove_registry(fsa, slab)
        self.cleanup()
        self.log.info(
            "Snap Backup and restore with Extent Base Feature Test case completed Successfully")

    def update_metro_config(self,):
        """
        Method to Update metro Snap Configuration to enable\\disable the metro backup"""

        if self.tcinputs['SnapEngineAtArray'] == 'Hitachi Vantara':
            if self.snapconstants.vsm_to_vsm == 'True':
                self.edit_array(self.tcinputs['VSMArrayName1'],
                                self.snapconstants.snap_configs,
                                self.snapconstants.config_update_level,
                                int(self.snapconstants.subclient.subclient_id),
                                gad_arrayname=self.tcinputs['ArrayName'])
                self.edit_array(self.tcinputs['VSMArrayName2'],
                                self.snapconstants.snap_configs,
                                self.snapconstants.config_update_level,
                                int(self.snapconstants.subclient.subclient_id),
                                gad_arrayname=self.tcinputs['ArrayName2'])

            else:
                self.edit_array(self.tcinputs['ArrayName'],
                                self.snapconstants.snap_configs,
                                self.snapconstants.config_update_level,
                                int(self.snapconstants.subclient.subclient_id))
                self.edit_array(self.tcinputs['VSMArrayName2'],
                                self.snapconstants.snap_configs,
                                self.snapconstants.config_update_level,
                                int(self.snapconstants.subclient.subclient_id),
                                gad_arrayname=self.tcinputs['ArrayName2'])

        else:
            self.edit_array(self.tcinputs['ArrayName'],
                            self.snapconstants.snap_configs,
                            self.snapconstants.config_update_level,
                            int(self.snapconstants.subclient.subclient_id))
            self.edit_array(self.tcinputs['ArrayName2'],
                            self.snapconstants.snap_configs,
                            self.snapconstants.config_update_level,
                            int(self.snapconstants.subclient.subclient_id))

    def create_mount_path(self, client_machine=None):
        """Method to create mount path location which will be used for mount operation
        Args:

            client_machine      (object)     --- name of the client on which mount path to be created

        """
        temp1 = self.snapconstants.snap_engine_at_array.replace("/", "").replace(" ", "").replace("(", "").replace(")",
                                                                                                                   "")
        temp2 = self.snapconstants.snap_engine_at_subclient.replace("/", "").replace(" ", "").replace("(", "").replace(
            ")", "")
        mount_path = f"MountPath_{self.snapconstants.string}"
        self.snapconstants.mount_path = (
            f"{self.snapconstants.snap_automation_output}"
            f"{self.snapconstants.delimiter}{temp1}{self.snapconstants.delimiter}"
            f"{temp2}{self.snapconstants.delimiter}{mount_path}")

        client_machine = client_machine or self.client_machine
        if client_machine.check_directory_exists(self.snapconstants.mount_path):
            self.log.info(
                "Mount path location: %s exists, cleaning it and creating new folder",
                self.snapconstants.mount_path)
            client_machine.remove_directory(self.snapconstants.mount_path)
        else:
            self.log.info("Mountpath location does not exists, creating one! ")
        client_machine.create_directory(self.snapconstants.mount_path)
        self.log.info("Successfully Created Mount path location : %s", self.snapconstants.mount_path)

    def unique_control_host(self, job):
        """Method to fetch unique control host for a job
                Args:

                    job                       (object)     --- job id for which unique control hosts to be fetched

                Returns:

                    unique_controlhost_id       (list)  -- unique control host id for the jobid

                """
        controlhost_id = self.snapconstants.execute_query(
            self.snapconstants.get_control_host, {'a': job.job_id})
        unique_controlhost_id = []
        for ctlhost in controlhost_id:
            if ctlhost not in unique_controlhost_id:
                unique_controlhost_id.append(ctlhost)
        self.log.info("Control hosts are {0}".format(unique_controlhost_id))
        return list(unique_controlhost_id)

    def verify_3dc_backup(self, job):
        """Method to check if the snaps are created on the arrays involved in the metro configuration
                Args:

                    job                       (object)     --- job for which unique control hosts to be fetched


                    """
        self.log.info("Verifying if snaps are created on all the arrays of the 3DC configuration")
        unique_controlhost_id = self.unique_control_host(job)

        if len(unique_controlhost_id) == 3:
            for i in range(len(unique_controlhost_id)):
                if unique_controlhost_id[i][0] not in (self.ctrlhost_array1[0][0],
                                                       self.ctrlhost_array2[0][0],
                                                       self.ctrlhost_array3[0][0]):
                    raise Exception(
                        "Snapshots for job : {0} not created on all arrays of the 3DC configuration".format(job.job_id))
        else:
            raise Exception(
                "Snapshots for job : {0} not created on all the arrays of the 3DC configuration".format(job.job_id))
        self.log.info("Snaps are created on all the arrays of 3DC configuration")

    def metro_mount_validation(self, job_id, controlhost_id, array_name):
        """Method to check if the snaps are mounted from correct arrays involved in metro configuration

            Args:

                    job_id                       (object)     --- job id of snap being mounted

                    controlhost_id               (list)     --- control host id of the array to which snap to be mounted

                    array_name                   (string)    --- Name of the array to which snap belongs

        """
        self.log.info("Verifying if the snap is mounted from expected array")
        mnt_controlhost_id = self.snapconstants.execute_query(
            self.snapconstants.get_mount_control_host, {'a': job_id})

        if controlhost_id[0][0] == mnt_controlhost_id[0][0]:
            self.log.info("Snap is mounted from Array {0} as expected".format(array_name))
        else:
            raise Exception(
                "Snapshot is not mounted from expected Array")

    def verify_trueup(self, job):
        """ Method to check if the trueUp is run for the job

                Args:

                    job                         (object)        ---  Job class for the backup job to query

                Returns:

                      True or False:            (bool)          -- True : If trueUp is run for the job
                                                                -- False: If trueUp is not run for the job

            """
        if not self.snapconstants.skip_catalog:
            jobId = job.job_id
        else:
            jobId = self.snapconstants.execute_query(
                self.snapconstants.get_backup_copy_job, {'a', job.job_id}
            )
        trueup_check = self.snapconstants.execute_query(
            self.snapconstants.check_trueup, {'a': jobId[0][0], 'b': 38}, fetch_rows='all'
        )
        if trueup_check[0][0] == '1' and trueup_check[0][0] is not None:
            return True
        return False

    def get_restore_client(self, client_machine, size):
        """ Returns the instance of the Machine class for the given client,
                    and the directory path to restore the contents at.


            Args:
                client_machine      (object)     --- name of the client on which is used for restore
                size    (int)   --  minimum available free space required on restore machine



            Returns:
                (object, str)   -   (instance of the Machine class, the restore directory path)

                    object  -   instance of the Machine class for the Windows client

                    str     -   directory path to restore the contents at
            """
        from datetime import datetime
        restore_client = Machine(self.commcell.clients.get(client_machine))
        self.log.info(f"Restore client selected is {restore_client.machine_name} ")

        drive = self.options_selector.get_drive(restore_client, size)

        current_time = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')

        restore_path = f'{drive}CVAutomationRestore-{current_time}'

        restore_client.create_directory(restore_path)

        return restore_client, restore_path


    def get_subclient_details(self,
                              subclient):
        """ Method for returning subclient details for a given subclient name
            Args:
                subclient               (str) -- Name of the subclient
        """

        subclient_details = {
            'appName': self.agent.agent_name,
            'applicationId': self.agent.agent_id,
            'backupsetId': self.snapconstants.backupset.backupset_id,
            'backupsetName': self.snapconstants.backupset.backupset_name,
            'clientId': self.client.client_id,
            'clientName': self.client.client_name,
            'subclientId': subclient.subclient_id,
            'subclientName': subclient.subclient_name
        }
        return subclient_details



