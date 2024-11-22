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

    simulate()      --  Simulate DDB with given parameters.

    validate()      --  Validates the DDB simulation with given parameters.

Steps :
    1. Create machine object and find the install directory and store path.
    2. Adjust zero values with the defaults
    3. Run simluations based on provided parameters.
    4. Check validation results to make sure all simulations were successful.
    5. Return exception and mark test as FAILED if any validation did not succeed.

    Sample Input:
    	"50678": {
          "ClientName": "client name",
          "AgentName": "File System",
          "MediaAgentName": "ma name",
          "connections": "5",
          "datasize": "5",
          "blocksize": "512",
          "tlimit": "100",
          "dratio": "0"
        }
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import constants

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "DDB Simulator Testcase"
        self.media_agent_name = ""
        self.client_name = ""
        self.connections = ""
        self.data_size = ""
        self.blocksize = ""
        self.tlimit = ""
        self.dratio = ""
        self.install_dir = ""
        self.machine = None
        self.dedup_store_path = ""

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup function of %s TestCase", self.name)
        self.media_agent_name = self.tcinputs['MediaAgentName']
        self.client_name = self.tcinputs['ClientName']
        self.connections = self.tcinputs['connections']
        self.data_size = self.tcinputs['datasize']
        self.blocksize = self.tcinputs['blocksize']
        self.tlimit = self.tcinputs['tlimit']
        self.dratio = self.tcinputs['dratio']

        self.log.info("Setting up machine")
        self.machine = Machine(self.client_name, self.commcell)
        self.install_dir = self.client.install_directory
        self.install_dir = self.machine.join_path(self.install_dir, "Base")
        self.install_dir = self.machine.join_path(self.install_dir, "sidb2")
        self.install_dir = '"' + self.install_dir + '"'
        optionobj = OptionsSelector(self.commcell)
        self.dedup_store_path = optionobj.get_drive(self.machine, 15)
        self.dedup_store_path = self.machine.join_path(self.dedup_store_path, "Simulate_DDBs")

        if int(self.dratio) == 0:
            self.dratio = "5"
        if int(self.blocksize) == 0:
            self.blocksize = "128"
        if int(self.connections) == 0:
            self.connections = "16"
        elif int(self.connections) < 1 or int(self.connections) > 16:
            self.log.info("Invalid value for connections")
            self.log.info("Setting to default value")
            self.connections = "16"
        if int(self.tlimit) == 0:
            self.tlimit = "1000"

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("This is tear down function of %s TestCase", self.name)

        if self.status == constants.FAILED:
            self.log.info("Skipping cleanup because test case failed. Please check logs for more information.")
        else:
            self.log.info("Removing directory: %s", self.dedup_store_path)
            self.machine.remove_directory(self.dedup_store_path)
            self.log.info("Removed directory: %s", self.dedup_store_path)

            self.log.info("Cleanup completed successfully.")

    def run(self):
        """Run function of this test case"""

        try:
            self.log.info("Running the %s TestCase", self.name)

            result1 = self.simulate(
                dratio=self.dratio, connections=self.connections, datasize=self.data_size, validate=True)

            result2 = self.simulate(dratio=self.dratio, connections=self.connections,
                                    datasize=self.data_size, blocksize=self.blocksize, validate=True)

            result3 = self.simulate(
                dratio=self.dratio, connections=self.connections, tlimit=self.tlimit, validate=True)

            if not result1[3] or not result2[3] or not result3[3]:
                raise Exception("Validation failed")

            self.log.info("Testcase completed successfully")

        except Exception as exp:
            self.status = constants.FAILED
            self.result_string = str(exp)
            self.log.error("Exception in main.run()")
            if str(exp).count("Response was not success"):
                self.log.info("Add the following D-WORD value at "
                        "Computer\\HKEY_LOCAL_MACHINE\\SOFTWARE\\CommVault Systems\\Galaxy\\Instance001\\WebConsole:")
                self.log.info("\"proxyConnectionTimeout\": XXXXXXX (in Decimal)")
                self.log.info("XXXXXXX represents the number of milliseconds before the SIDB task times out")

    def simulate(self, dratio="", tlimit="", blocksize="", connections="", datasize="", validate=False):
        """
        Simulate DDB with given parameters.

        Args:
            dratio (str)       --  Deduplication Ratio
            tlimit (str)       --  Query and insertion (Q&I) time limit (in microseconds)
            blocksize (str)    --  Size of block (in KB)
            connections (str)  --  Number of simultaneous threads accessing DDB
            datasize (str)     --  Application data size (unit in GB)
            validate (bool)    --  Specifies whether or not validation should be run following the simulation

        Returns:
            tuple of the result of the simulation, appended with the validation result is validate set to True
        """

        self.log.info("Simulating DDB")

        simulation_cmd = self.install_dir + " -simulateddb"

        simulation_cmd += " -p " + self.dedup_store_path

        if dratio != "":
            simulation_cmd += " -dratio " + str(dratio)

        if tlimit != "":
            simulation_cmd += " -tlimit " + str(tlimit)
        elif datasize != "":
            simulation_cmd += " -datasize " + str(datasize)

        if blocksize != "":
            simulation_cmd += " -blocksize " + str(blocksize)

        if connections != "":
            simulation_cmd += " -threads " + str(connections)

        simulation_cmd += " -cleanddb"

        self.log.info(simulation_cmd)
        result = self.client.execute_command(simulation_cmd)
        self.log.info(str(result))

        if validate:
            self.log.info("Validating the simulation")
            return self.validate(dratio, tlimit, blocksize, connections, datasize, result)
        else:
            return result

    def validate(self, dratio="", tlimit="", blocksize="", connections="", datasize="", result=()):
        """
        Validates the DDB simulation with given parameters.

        Args:
            dratio (str)       --  Deduplication Ratio
            tlimit (str)       --  Query and insertion (Q&I) time limit (in microseconds)
            blocksize (str)    --  Size of block (in KB)
            connections (str)  --  Number of simultaneous threads accessing DDB
            datasize (str)     --  Application data size (unit in GB)
            result (tuple)     --  Result that was received from the command execution

        Returns:
            tuple with the result of simulation, appended with the validation result

        """

        if result == ():
            self.log.info("No result provided to validate.")
            return ('', '', '', False)
        elif result[0] != 0:
            self.log.info("Simulation failed.")
            return result + (False,)

        if dratio != "":
            dedup_ratio_string = f"Dedupe Ratio\t\t\t    -> [{dratio}]"
            if dedup_ratio_string not in result[1]:
                self.log.info("Dedupe Ratio not found in the output.")
                return result + (False,)

        if tlimit != "":
            tlimit_string = f"Threshold Time Limit\t\t    -> [{float(tlimit)}] microseconds"
            if tlimit_string not in result[1]:
                self.log.info("Threshold Time Limit not found in the output.")
                return result + (False,)
        elif datasize != "":
            datasize_string = f"Application data size\t\t    -> [{datasize}] GB"
            if datasize_string not in result[1]:
                self.log.info("Data Size not found in the output.")
                return result + (False,)

        if blocksize != "":
            blocksize_string = f"Block Size\t\t\t    -> [{blocksize}] KB"
        else:
            blocksize_string = "Block Size\t\t\t    -> [128] KB"

        if blocksize_string not in result[1]:
            self.log.info("Block Size not found in the output.")
            return result + (False,)

        if connections != "":
            connections_string = f"No. of threads\t\t    -> [{connections}]"
            if connections_string not in result[1]:
                self.log.info("Connections not found in the output.")
                return result + (False,)

        self.log.info("Validation successful")
        return result + (True,)
    
