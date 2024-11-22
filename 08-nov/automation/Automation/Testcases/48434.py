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

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    run_backup_job() -- for running a backup job depending on argument

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

basic idea of the test case:
checks different encryption, compression settings at sub client level.
Also involves different deduplication settings.

validations used:
1. Sigwhere: whether deduplication (client side,media agent side),
                                   (source side,destination side)
2. Compression: is on or not
3. Encryption: type of encryption based on sub client level setting.


input json file arguments required:

    "48434":{
        "ClientName": "name of the client machine without as in commserve",
        "AgentName": "File System",
        "MediaAgentName": "name of the media agent as in commserve"
        }

Design steps:
1. create the required resources
2. using xml file at client level enable
clientside dedupe option so that the sub client
level properties of dedupe have an effect.
3. repeat for each backup job, run total four backup jobs:
    3.1 before backup job, use qoperation to
    put the settings at subclient level of
    encryption,compression, deduplication using xml.
    3.2 run backup job.
    3.3 seal the store.
    3.4 check for conditions.
"""

from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "subclient level different encryption,compression and deduplication " \
                    "settings check"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.library_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.backup_set = None
        self.subclient_ob = None
        self.storage_pool_ob = None
        self.plan_name = None
        self.storage_pool_name = None
        self.storage_assigned_ob = None
        self.plan_ob = None
        self.plan_type = None

    def setup(self):
        """assign values to variables for testcase"""
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.plan_name = "plan" + str(self.id)
        self.storage_pool_name = "pool" + str(self.id)
        self.plan_type = "Server"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

    def previous_run_clean_up(self):
        """deletes items from the previous run of the testcase"""
        self.log.info("********* previous run clean up started **********")
        try:
            #deleting content path
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            # deleting Backupset
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset.")
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Backupset deleted.")

            # deleting Plan
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Plan exists, deleting that")
                self.commcell.plans.delete(self.plan_name)
                self.log.info("Plan deleted.")


            # deleting storage pool
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"pool[{self.storage_pool_name}] exists, deleting that")
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info("pool primary deleted.")

            self.log.info("********* previous run clean up ended **********")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def run_backup_job(self, job_type):
        """running a backup job depending on argument
            job_type                (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job type: %s", job_type)
        job = self.subclient_ob.backup(job_type)
        self.log.info("Backup job: " + str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:
            self.previous_run_clean_up()

            # create the required resources for the testcase
            # get the drive path with required free space

            drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
            drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)

            # creating testcase directory, mount path, content path, dedup
            # store path
            self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
            self.testcase_path_media_agent = "%s%s" % (
                drive_path_media_agent, self.id)

            self.mount_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "mount_path")
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")
            self.media_agent_machine.create_directory(self.dedup_store_path)

            self.content_path = self.client_machine.join_path(
                self.testcase_path_client, "content_path")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists")
            else:
                self.client_machine.create_directory(self.content_path)
                self.log.info("content path created")


            #  create storage pool
            self.log.info(f"creating storage pool [{self.storage_pool_name}]")
            self.storage_assigned_ob = self.commcell.storage_pools.add(storage_pool_name=self.storage_pool_name,
                                                                       mountpath=self.mount_path,
                                                                       media_agent=self.tcinputs['MediaAgentName'],
                                                                       ddb_ma=self.tcinputs['MediaAgentName'],
                                                                       dedup_path=self.dedup_store_path)
            self.log.info(f"storage pool [{self.storage_pool_name}] created")

            # create plan
            self.log.info(f"creating plan [{self.plan_name}]")
            self.plan_ob = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type=self.plan_type,
                                                   storage_pool_name=self.storage_pool_name)
            self.log.info(f"plan [{self.plan_name}] created")

            # Disabling schedule policy from plan
            self.plan_ob.schedule_policies['data'].disable()

            # create backupset
            self.log.info(f"Creating Backupset [{self.backupset_name}]")
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)
            self.log.info(f"Backupset created [{self.backupset_name}]")

            # generate content for subclient
            if self.mm_helper.create_uncompressable_data(
                    self.client.client_name, self.content_path, 0.3, 1):
                self.log.info(
                    "generated content for subclient %s",
                    self.subclient_name)

            self.log.info(f"Creating subclient [{self.subclient_name}]")

            # Adding Subclient to Backupset
            self.subclient_ob = self.backup_set.subclients.add(self.subclient_name)

            self.log.info(f"Added subclient to backupset [{self.subclient_name}]")
            self.log.info("Adding plan to subclient")

            # Associating plan and content path to subclient
            self.subclient_ob.plan = [self.plan_ob, [self.content_path]]
            self.log.info("Added content and plan to subclient")

            # setting properties at client level to allow sub client level settings to work
            # set performClientDeduplication to true
            # set encryption to Blowfish, allows for the sub client
            # encryption settings to take effect.
            property_dict = self.client.properties
            property_dict['clientProps']['CipherType'] = 2
            property_dict['clientProps']['encryptionSettings'] = 1
            property_dict['clientProps']['EncryptKeyLength'] = 128
            self.client.update_properties(property_dict)

            log_file = "clbackup.log"
            error_flag = []
            config_strings_clbackup = [['encryption [3]', 'compression [0]',
                                        'signature [1]'],
                                       ['encryption [1]', 'compression [0]',
                                        'signature [1]'],
                                       ['encryption [2]', 'compression [0]',
                                        'signature [2]'],
                                       ['encryption [0]', 'compression [1]',
                                        'signature [2]']]

            encryption_check = [3, 2, 1, 0]
            compression_check = [0, 0, 0, 1]
            signature_check = [1, 1, 2, 2]

            validations = [['encryption on NW only', 'compression at source',
                            'signature at client'],
                           ['encryption on NW and Media', 'compression at source',
                            'signature at client'],
                           ['encryption on Media agent only', 'compression at source',
                            'signature at MA'],
                           ['encryption NONE', 'compression at destination',
                            'signature at MA']]


            # check all this properties over four jobs

            for iteration in range(4):
                job_no = iteration + 1

                properties = self.subclient_ob.properties
                properties['subClientEntity']['appName'] = 'File System'
                properties['commonProperties']['encryptionFlag'] = encryption_check[iteration]
                properties['commonProperties']['storageDevice']['softwareCompression'] = compression_check[iteration]
                properties['commonProperties']['storageDevice']['deDuplicationOptions']['enableDeduplication'] = True
                properties['commonProperties']['storageDevice']['deDuplicationOptions']['generateSignature'] = \
                    signature_check[iteration]
                self.subclient_ob.update_properties(properties)
                self.client.set_dedup_property("clientSideDeduplication", "OFF")

                self.log.info(
                    "subclient configuration complete: for job %d", job_no)

                job = self.run_backup_job("FULL")
                # seal ddb
                self.log.info("sealing the ddb")
                self.plan_ob.storage_policy.seal_ddb("primary")
                self.log.info("*****validations for job %d "
                              "*******", job_no)
                self.log.info("Validating %s",
                              validations[iteration][0])
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[
                        iteration][0], job.job_id,
                    single_file=True)

                query = """ SELECT          attrVal
                            FROM            APP_SubClientProp, APP_Application
                            WHERE           APP_SubClientProp.componentNameId=APP_Application.id
                            AND             attrname='Encrypt: encryption'
                            AND             APP_SubClientProp.modified=0
                            AND             APP_Application.subclientName='{0}'"""\
                    .format(self.subclient_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)

                # encryption query means:
                # none 							                    - 0
                # media agent only(media agent side) 			    - 1
                # network and media(agent side)				        - 2
                # network only(agent encypts, MediaAgent decrypts)	- 3

                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == (encryption_check[iteration]):
                    self.log.info(
                        "query returned: %s",
                        validations[iteration][0])

                if matched_line or (result == encryption_check[iteration]):
                    self.log.info("Result: Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: {0}".format(
                        config_strings_clbackup[iteration][0])
                                   + "failed validation: {0}".format(validations[iteration][0])]

                self.log.info("Validating %s", validations[iteration][1])
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[
                        iteration][1], job.job_id,
                    single_file=True)

                query = """ SELECT  compressWhere
                            FROM    archPipeConfig,APP_Application
                            WHERE   APP_Application.subclientName = '{0}'
                            AND     archPipeConfig.appNumber = APP_Application.id"""\
                    .format(self.subclient_name)
                self.log.info("EXECUTING QUERY %s", query)
                self.csdb.execute(query)
                result = int(self.csdb.fetch_one_row()[0])
                self.log.info(f"QUERY OUTPUT : {result}")
                if result == compression_check[iteration]:
                    self.log.info("query returned: %s",
                                  validations[iteration][1])
                # software compression:
                #
                # on client 0
                # on mediaagent 1
                # use storage policy settings 2
                # off 4

                if matched_line or \
                        result == compression_check[iteration]:
                    self.log.info("Result: Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: {0}".format(
                        config_strings_clbackup[iteration][1])
                                   + "failed validation: {0}".format(validations[iteration][1])]

                self.log.info("Validating %s", validations[iteration][2])
                (matched_line, matched_string) = self.dedup_helper.parse_log(
                    self.client.client_hostname, log_file, config_strings_clbackup[
                        iteration][2], job.job_id,
                    single_file=True)

                if matched_line:
                    self.log.info("Result: Pass")
                else:
                    self._log.error("Result: Failed")
                    error_flag += ["failed to find: {0}".format(
                        config_strings_clbackup[iteration][2])
                                   + "failed validation: {0}".format(validations[iteration][2])]

            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.error(error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            # set the encryption back to default
            self.log.info("setting encryption to default: Use SP settings")
            self.client.set_encryption_property("USE_SPSETTINGS")
            self.log.info(
                "setting encryption to default Use SP Settings: Done")

            # set the deduplication back to default
            self.log.info(
                "setting client deduplication to default: Use storage policy settings ")
            self.client.set_dedup_property(
                "clientSideDeduplication", "USE_SPSETTINGS")
            self.log.info(
                "setting client deduplication to default Use storage policy settings: Done")

            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            # delete mount path and dedup path
            self.media_agent_machine.remove_directory(self.dedup_store_path)
            self.client_machine.remove_directory(self.mount_path)

            # run the previous_run_cleanup again to delete the backupset,
            # plan, storage pool after running the case
            self.previous_run_clean_up()

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)
