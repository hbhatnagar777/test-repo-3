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
    __init__()                   --  initialize TestCase class

    run_jobs_on_subclient()      --  Run the Backup Job on SubClient

    wait_for_jobs_completion()   --  Wait for jobs to be complete

    run()                        --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server.serverhelper import ServerTestCases
from cvpysdk.cvpysdk import SDKException


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Storage policy association/deletion to subclient - Basic acceptance"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE

        self.show_to_user = True

    def run_jobs_on_subclient(self, subclient_object_list):
        """Run the Backup Job on SubClient.

            Args:
                subclient_object_list   (list)    --  List of subclient objects

            Returns:
                job_list  (list)-   Returns list of job objects
            Raises:
                Exception:
                    if failed to trigger backup for subclient
        """
        job_list = []
        for subclient in subclient_object_list:
            # Trigger backup job again for the subclient
            self._log.info("Running full backup for subclient {0}"
                           .format(subclient.subclient_name))
            job = subclient.backup("FULL")
            job_list.append(job)
            self._log.info("Success! Backup triggered for SubClient {0} with Job id: {1}".
                           format(subclient.subclient_name, job.job_id))

        return job_list

    def wait_for_jobs_completion(self, job_object_list):
        """Wait for jobs to be complete.

            Args:
                Job_object_list   (list)    --  list of the Job Objects
            Raises:
                Exception:
                    if failed to run full backup

        """
        for job in job_object_list:
            self._log.info("Waiting for job {0} to complete".format(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup with error: {0}".
                                format(job.delay_reason))
            self._log.info("Backup job {0} completed with status [{1}]".
                           format(job.job_id, job.status))

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            disklibrary = OptionsSelector.get_custom_str('disklibrary')
            sp1_name = OptionsSelector.get_custom_str('storagepolicy', 'SP1')
            sp2_name = OptionsSelector.get_custom_str('storagepolicy', 'SP2')
            sp3_name = OptionsSelector.get_custom_str('storagepolicy', 'SP3')
            backupset_name = OptionsSelector.get_custom_str('backupset')
            subclient_name = OptionsSelector.get_custom_str('subclient', 'SC1')
            subclient2_name = OptionsSelector.get_custom_str('subclient', 'SC2')
            entities = CVEntities(self)
            server_tc = ServerTestCases(self)
            job_list = []

            # Creating entities
            entity_props = entities.create({
                'disklibrary': {'name': disklibrary},
                'storagepolicy': {'name': sp1_name},
                'backupset': {'name': backupset_name},
                'subclient': {'name': subclient_name}
            })
            subclient1_object = entity_props['subclient']['object']
            storagepolicy_props = entity_props['storagepolicy']
            subclient1_props = entity_props['subclient']

            # Creating storage policy SP2
            sp_props = entities.create({'storagepolicy': {'name': sp2_name}})
            sp2_props = sp_props['storagepolicy']

            # Creating storage policy SP3
            entity_subclient = entities.create({
                'storagepolicy': {'name': sp3_name},
                'subclient': {
                    'name': subclient2_name,
                    'backupset': backupset_name
                }
            })
            subclient2_object = entity_subclient['subclient']['object']
            subclient2_props = entity_subclient['subclient']
            sp3_props = entity_subclient['storagepolicy']

            self.log.info("""
                ====================================================
                Step1:
                Delete a storage policy (SP1) that has a SubClient
                associated with it.
                ====================================================
                """)
            try:
                self.commcell.storage_policies.delete(sp1_name)
                raise Exception("Fail! SP: {0} removed though SubClient: {1}associated to it"
                                .format(sp1_name, subclient_name))
            except SDKException as exp:
                self._log.info('Success!. As expected: Failed with error: %s', str(exp))

            self.log.info("""
                ====================================================
                Step2:
                Reassociate SubClient Association for the Storage Policy(SP1)
                ====================================================
                """)
            subclient1_object.storage_policy = sp2_name
            self._log.info("Successfully reassociated SubClient with SP: {0}"
                           .format(sp2_name))
            self.log.info("""
                ====================================================
                Step3:
                Perform some backups using existing SP2 and SP3.
                When backups are running on SP2 and SP3 , delete SP1
                -->SP1 can be deleted since there is no subClient association
                and no job is using this storage policy
                ====================================================
                """)

            # Run backup on subclient1 and subclient2, and delete SP1 now...
            # Verify it can be deleted
            job_list = self.run_jobs_on_subclient([subclient1_object, subclient2_object])
            entities.delete({'storagepolicy': storagepolicy_props})

            self.log.info("""
                ====================================================
                Step4:
                While job still running using SP2 and SP3, delete SP2.
                ====================================================
                """)

            # Delete SP2 now... Verify it cannot be deleted because jobs are running
            try:
                self.commcell.storage_policies.delete(sp2_name)
                raise Exception("Fail! SP: {0} removed though SubClient: {1} associated to it"
                                .format(sp2_name, subclient_name))
            except SDKException as exp:
                self._log.info('Success! As expected: Failed with error: %s', str(exp))

            # Wait for jobs to complete.
            self.wait_for_jobs_completion(job_list)

            self.log.info("""
                ====================================================
                Step5:
                Remove or reassociate the associated SubClient for all SPs
                and delete SPs again..
                ====================================================
                """)

            entities.delete({'subclient': subclient1_props})
            entities.delete({'subclient': subclient2_props})
            entities.delete({'storagepolicy': sp2_props})
            entities.delete({'storagepolicy': sp3_props})

        except Exception as exp:
            server_tc.fail(exp)
        finally:
            self.wait_for_jobs_completion(job_list)
            entities.cleanup()
