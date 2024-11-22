# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    setup()         -- setup function of this test case
"""
from AutomationUtils import constants
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle Stream Validation Test Case"
        self.show_to_user = False
        self.oracle_helper = None
        self.storage_policy = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        machine_object = machine.Machine(self.client)
        client_ip = machine_object.ip_address
        self.oracle_helper = OracleHelper(self.commcell, client_ip, self.instance)


    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s Test Case", self.id)

            # setting log stream at instance level to 4
            initial_log_stream = self.instance.log_stream
            self.instance.log_stream = 4
            self.instance.refresh()

            # run stream validation for archive log subclient
            archive_log_subclient = self.instance.subclients.get('ArchiveLog')
            self.storage_policy = archive_log_subclient.data_sp
            archive_log_status = self.oracle_helper.stream_validation(self.client,
                                                                      archive_log_subclient)
            self.log.info("Archive Log Status : %s", archive_log_status)

            # create subclient with data and log selected
            data_log_name = "{0}_data_and_log".format(self.id)
            data_log_subclient = self.oracle_helper.create_subclient(data_log_name,
                                                                     self.storage_policy,
                                                                     data_stream=5,
                                                                     data=True,
                                                                     log=True)

            # run stream validation for data and log subclient
            data_log_status = self.oracle_helper.stream_validation(self.client,
                                                                   data_log_subclient)
            self.log.info("Data and Log Status : %s", data_log_status)

            # create subclient with data only
            data_name = "{0}_data_only".format(self.id)
            data_subclient = self.oracle_helper.create_subclient(data_name,
                                                                 self.storage_policy,
                                                                 data_stream=6)

            # run stream validation for data  only subclient
            data_only_status = self.oracle_helper.stream_validation(self.client,
                                                                    data_subclient)
            self.log.info("Data only Subclient Status : %s", data_only_status)

            # create selective online full subclient and do stream validation
            selective_name = "{0}_selective".format(self.id)
            selective_subclient = self.oracle_helper.create_subclient(selective_name,
                                                                      self.storage_policy,
                                                                      data_stream=3,
                                                                      selective_online=True)

            # run stream validation for selective online subclient
            selective_status = self.oracle_helper.stream_validation(self.client,
                                                                    selective_subclient)
            self.log.info("Selective Online Status : %s", selective_status)

            # validate all three status

            if archive_log_status and data_log_status and data_only_status and selective_status:
                self.log.info("Stream validation test case passed")
                self.status = constants.PASSED
                self.result_string = "Oracle stream validation test case completed successfully"
            else:
                self.status = constants.FAILED
                self.result_string = "Oracle stream validation test case completed successfully"
                self.log.info("Oracle stream validation test case completed successfully")
        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.log.info("Cleanup of test case subclients")
            self.instance.subclients.delete(data_name)
            self.instance.subclients.delete(data_log_name)
            self.instance.subclients.delete(selective_name)
            self.instance.log_stream = initial_log_stream
            self.instance.refresh()
