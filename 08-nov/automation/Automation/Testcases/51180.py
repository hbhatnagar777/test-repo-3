# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
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

    verify_sidb_compact_output() --  Verify that sidb compact output contains all
                                    the strings we expect it to

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "sidb compact"
        self.show_to_user = False
        self.spfinalresult_dict = {}
        self.tcinputs = {
            "stroagepolicy_list": None
        }
        self.backupset = "defaultBackupSet"
        self.subclient = "default"

    def setup(self):
        """Setup function of this test case"""

    def run(self):
        """Run function of this test case"""
        try:

            dedup_obj = DedupeHelper(self)
            # STEP : Fetch storage policy list from inputs file
            stroagepolicy_list = self.tcinputs['stroagepolicy_list']
            # Now run the TC in loop for each  storage policy
            for storagepolicy in stroagepolicy_list.split(','):

                sp_id = self.commcell.storage_policies.get(storagepolicy).storage_policy_id
                copy_name = 'Primary'
                # Get SIDB Engine ID associated with the storage policy primary copy
                engine_id = dedup_obj.get_sidb_ids(sp_id, copy_name)[0]
                self.log.info("""Storage Policy {0} has following
                engine id {1}""".format(storagepolicy, engine_id))

                # STEP:Get DDB MA for the given DDB Store
                ddbma_dict = dedup_obj.get_ddb_partition_ma(engine_id)

                # Run sidb compact CLI for each partition for given SP
                for partition in ddbma_dict:
                    self.log.info(
                        "Following DDB MA has been chosen for executing sidb2 compact {0}".format(
                            ddbma_dict[partition].client_name))

                    #ddbma_obj = machine.Client(self.commcell, ddbma_dict[partition].client_name)
                    ddbma_obj = ddbma_dict[partition]
                    sp_key = storagepolicy + "_" + str(engine_id) + "_" + str(partition)
                    #TODO: Make sure that SIDB2 process with this engine_id is not running
                    self.log.info("Check if SIDB is running on %s for engine id %s partition %s",
                                  ddbma_dict[partition].client_name,
                                  engine_id, partition)
                    if not dedup_obj.wait_till_sidb_down(engine_id, ddbma_obj, partition, timeout=600):
                        self.log.error("SIDBEngine is not down even after timeout of 600 seconds")
                        raise Exception("SIDBEngine not down even after timeout. Returning Failure.")

                    sidb_compact_output = dedup_obj.execute_sidb_command('compact', engine_id,
                                                                         partition, ddbma_obj)

                    # STEP:Verify output of SIDB compact
                    if sidb_compact_output[0] == 0:
                        self.log.info("Verifying the sidb compact output")
                        verification_status = self.verifysidb_compact_output(
                            engine_id, sidb_compact_output[1])
                        if verification_status != 0:
                            self.status = constants.FAILED
                            self.result_string = self.result_string + \
                                " sidb2 compact verification failed for engine id ==> {0} \
                                partition id ==> {1}".format(engine_id, partition)
                            self.spfinalresult_dict[sp_key] = "FAIL"
                        else:
                            self.log.info("***SUCCESS***==> Successfully verified the output \
                            of sidb2 compact for engine id ==> {0} partition id ==> {1}".format(
                                engine_id, partition))
                            self.spfinalresult_dict[sp_key] = "PASS"
                    else:
                        self.log.error(
                            "sidb2 compact returned non-zero output for engine id ==>{0} \
                             partition id ==> {1}".format(engine_id, partition))
                        self.log.error("command output ==> {0}".format(sidb_compact_output[1]))
                        self.status = constants.FAILED
                        self.result_string = self.result_string + '\n' + \
                            "sidb2 compact returned non-zero output for engine id ==> {0} \
                             partition id ==> {1}".format(engine_id, partition)
                        self.spfinalresult_dict[sp_key] = "FAIL"
                        self.log.error("command output ==> {0}".format(sidb_compact_output[1]))

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def verifysidb_compact_output(self, engine_id, outputstring):
        """
        Verify that sidb compact output contains all the strings we expect it to
            Args:
                engine_id (str)   -- SIDB Engine ID

                outputstring (str)   -- Ouptut of sidb compact output

            Returns:
                0 if output has all the expected string else 1

        """
        status_flag = 0
        verify_strings = ["Getting information for engine [{0}]".format(engine_id),
                          "Compacting property file.",
                          "Compressing data file",
                          "Rebuilding index file",
                          "Writing index file",
                          "Compacting primary file",
                          "Compressing data file",
                          "Rebuilding index file",
                          "Writing index file",
                          "Rebuilding additional index",
                          "Writing index file",
                          "Compacting archive file. Recs",
                          "Compacting completed successfully"]
        validation_fail = 0
        error_string = []
        # split the incoming output on new lines and store in a list
        outputlist = outputstring.splitlines()


        for datasize_string in verify_strings:
            self.log.info("Validating: [{0}]".format(datasize_string))
            verify_index = -1
            for line in outputlist:
                if line.count(datasize_string) > 0:
                    verify_index = 1
                    self.log.info("###Matched line to be validated with ==> {0}".format(line))
                    break

            if verify_index < 0:
                self.log.error(
                    "***Failed to validate following string in output : *** ===> {0}".format(
                        datasize_string))
                error_string += [datasize_string]
                validation_fail = 1
            # Later add a case for checking the sequence
            self.log.info("Successfully validated string ==> {0}".format(datasize_string))

        if validation_fail == 1:
            status_flag = str(error_string)
            self.log.error(
                "***FAILURE : SIDB compression validation failed for engine \
                 id  {0}***".format(engine_id))
        return status_flag

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info(str(self.spfinalresult_dict))
