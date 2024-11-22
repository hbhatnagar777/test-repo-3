# -*- coding: utf-8 -*-
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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    ldd_verification()          --  Method to verify the ldd output

    binary_version_verification() -- Method to verify the binary versions

    psql_validation()           --  Method to verify the psql symlink

    validate_pgsql_version()    --  Method to validate the PGSQL version on the client

    process_client()            --  Method to execute the test steps

    process_failed_list()       --  Method to process the failed validation list

    tear_down()                 --  tear down method for testcase

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "70878":
                        {
                        ClientList: "CVCloud_CLIENT_CGROUP", ##### Example for passing client group name
                        },
                "70878":
                        {
                        ClientList: "['client1, 'client2', 'client3']" ####Example for passing list of clients
                        }
            }

"""

import ast
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Class for verifying PostgreSQL CVCLOUDADDONS packages"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "PostgreSQL CVCLOUDADDONS package verification"
        self.commserv_version = None
        self.input_client_list = None
        self.support_matrix = None
        self.binary_matrix = None
        self.failed_validation_list = None
        self.ignore_failure_matrix = None
        self.tcinputs = {
            'ClientList': None
        }

    def setup(self):
        """ Method to set up test variables """
        self.log.info(f"Started executing {self.id} testcase")
        self.commserv_version = self.commcell.commserv_version
        self.input_client_list = self.tcinputs['ClientList']
        if self.commcell.client_groups.has_clientgroup(self.input_client_list):
            self.input_client_list = self.commcell.client_groups.get(self.input_client_list).associated_clients
        elif isinstance(self.input_client_list, str):
            self.input_client_list = ast.literal_eval(self.input_client_list)
        else:
            raise Exception("Invalid input for ClientList")


        # Support matrix for the clients. Specifies the versions of PGSQL supported in each SP. Starting from SP32
        self.support_matrix = {
            32: ['9.5', '9.6', '10', '11', '12', '13', '14', '15', '16'],
            34: ['9.5', '9.6', '10', '11', '12', '13', '14', '15', '16'],
            36: ['10', '11', '12', '13', '14', '15', '16'],
            3609: ['10', '11', '12', '13', '14', '15', '16'],
            38: ['10', '11', '12', '13', '14', '15', '16']
        }

        # Binary matrix for the PGSQL versions. Specifies the binaries to be validated for each version of PGSQL
        # psql is not added in this list as psql is validated seperately for each version
        self.binary_matrix = {
            "10": ["dropdb", "pg_ctl", "pg_dump", "pg_dumpall", "pg_restore"],
            "11": ["dropdb", "pg_ctl", "pg_dump", "pg_dumpall", "pg_restore"],
            "12": ["dropdb", "pg_config", "pg_ctl", "pg_dump", "pg_dumpall", "pg_controldata", "pg_restore"],
            "13": ["dropdb", "pg_config", "pg_ctl", "pg_dump", "pg_dumpall", "pg_controldata", "pg_restore"],
            "14": ["dropdb", "pg_config", "pg_ctl", "pg_dump", "pg_dumpall", "pg_controldata", "pg_restore"],
            "15": ["dropdb", "pg_config", "pg_ctl", "pg_dump", "pg_dumpall", "pg_controldata", "pg_restore"],
            "16": ["dropdb", "pg_config", "pg_ctl", "pg_dump", "pg_dumpall", "pg_controldata", "pg_restore"]
        }

        ###There are some unsupported versions specific to OS.
        ###For example PG10 and 16 are not supported in CENTOS7/RHEL7/ROCKY7
        ###We can add such exceptions to the ignore_failure_list
        self.ignore_failure_matrix = {
            "rocky linux 7": ["10", "16"],
            "centos linux 7": ["10", "16"],
            "rocky linux 9": ["10"],
            "red hat enterprise linux 7": ["10", "16"],
            "red hat enterprise linux 9": ["10"],
            "amazon linux 2023": ["10", "11", "12", "13", "14", "16"],
            "amazon linux 2": ["10", "11", "16"],
        }

        # List to store the failed validations.
        # If any client fails the validation, it will be added to this list in this format
        # ['clientname', 'os_info', 'pgsql_version']
        self.failed_validation_list = []

    def ldd_verification(self, client_machine_object, cv_cloud_addons_path, pgsql_version):
        """ Method to verify the ldd output """
        self.log.info(f"Validating ldd output for {cv_cloud_addons_path}")
        bin_path = client_machine_object.join_path(cv_cloud_addons_path, 'bin')
        lib_path = client_machine_object.join_path(cv_cloud_addons_path, 'lib')
        command = f"export LD_LIBRARY_PATH={lib_path};cd {bin_path}"
        for binary in self.binary_matrix[pgsql_version]:
            command = f"{command};ldd {binary}"
        ldd_output = client_machine_object.execute_command(command)
        if ldd_output.exception_message or ldd_output.exception:
            self.log.error(
                f"Failed ldd validation command:{command} on client: {client_machine_object.machine_name}")
            self.log.error(
                f"ldd Validation failed for client: {client_machine_object.machine_name}, PGSQL version: {pgsql_version}")
            if [client_machine_object.machine_name, client_machine_object.os_pretty_name,
                    pgsql_version] not in self.failed_validation_list:
                self.failed_validation_list.append(
                    [client_machine_object.machine_name, client_machine_object.os_pretty_name, pgsql_version])

    def binary_version_verification(self, client_machine_object, cv_cloud_addons_path, pgsql_version):
        """ Method to verify the binary versions """
        self.log.info(f"Validating binary versions for {cv_cloud_addons_path}")
        bin_path = client_machine_object.join_path(cv_cloud_addons_path, 'bin')
        lib_path = client_machine_object.join_path(cv_cloud_addons_path, 'lib')
        command = f"export LD_LIBRARY_PATH={lib_path};cd {bin_path}"
        for binary in self.binary_matrix[pgsql_version]:
            command = f"{command};./{binary} --version"
        binary_output = client_machine_object.execute_command(command)
        if binary_output.exception_message or binary_output.exception:
            if [client_machine_object.machine_name, client_machine_object.os_pretty_name,
                    pgsql_version] not in self.failed_validation_list:
                self.log.error(
                    f"Failed binary validation command:{command} on client: {client_machine_object.machine_name}")
                self.log.error(
                    f"binary Validation failed for client: {client_machine_object.machine_name}, "\
                    "PGSQL version: {pgsql_version}")
                self.failed_validation_list.append(
                    [client_machine_object.machine_name, client_machine_object.os_pretty_name, pgsql_version])

    def psql_validation(self, client_machine_object, cv_cloud_addons_path, pgsql_version):
        """ Method to verify the psql symlink """
        self.log.info(f"Validating psql symlink in {cv_cloud_addons_path}")
        bin_path = client_machine_object.join_path(cv_cloud_addons_path, 'bin')
        lib_path = client_machine_object.join_path(cv_cloud_addons_path, 'lib')
        command = f"export LD_LIBRARY_PATH={lib_path};cd {bin_path}; ldd psql; ls -l psql;./psql --version"
        ldd_output = client_machine_object.execute_command(command)
        if ldd_output.exception_message or ldd_output.exception:
            self.log.error(
                f"Failed binary validation command:{command} on client: {client_machine_object.machine_name}")
            self.log.error(
                f"psql symlink Validation failed for client: {client_machine_object.machine_name}, "\
                "PGSQL version: {pgsql_version}")
            if [client_machine_object.machine_name, client_machine_object.os_pretty_name,
                    pgsql_version] not in self.failed_validation_list:
                self.failed_validation_list.append(
                    [client_machine_object.machine_name, client_machine_object.os_pretty_name, pgsql_version])

    def validate_pgsql_version(self, client_object, client_machine_object, pgsql_version):
        """ Method to validate the PGSQL version on the client """
        self.log.info(
            f"---Validating PGSQL version *{pgsql_version}* on client: *{client_machine_object.machine_name}*---")
        install_directory = client_object.install_directory
        cv_cloud_addons_path = client_machine_object.join_path(
            install_directory, 'CVCloudAddOns', 'PostgreSQL', pgsql_version)
        self.ldd_verification(client_machine_object,
                              cv_cloud_addons_path, pgsql_version)
        self.binary_version_verification(
            client_machine_object, cv_cloud_addons_path, pgsql_version)
        self.psql_validation(client_machine_object,
                             cv_cloud_addons_path, pgsql_version)

    def process_client(self):
        """ Method to execute the test steps """
        for client in self.input_client_list:
            client_object = self.commcell.clients.get(client)
            try:
                self.log.info(f"######Validating client: {client}######")
                client_machine_object = Machine(client, self.commcell)
            except Exception as exp:
                self.failed_validation_list.append(
                    [client, 'Client not found', 'Client not found'])
                continue
            for pgsql_version in self.support_matrix[self.commserv_version]:
                self.validate_pgsql_version(
                    client_object, client_machine_object, pgsql_version)

    def process_failed_list(self):
        """ Method to process the failed validation list """
        temp_list = self.failed_validation_list.copy()
        for failed_entry in temp_list:
            client = failed_entry[0]
            os_info = failed_entry[1]
            pgsql_version = failed_entry[2]
            formatted_os_name = os_info.lower().split(".")[0]
            if formatted_os_name in self.ignore_failure_matrix:
                if pgsql_version in self.ignore_failure_matrix[formatted_os_name]:
                    self.log.info(
                        f"Ignoring validation failure for client: {client}, OS: {formatted_os_name}, "\
                        "PGSQL version: {pgsql_version}")
                    self.failed_validation_list.remove(failed_entry)

    def tear_down(self):
        """ tear down method for testcase """
        pass

    def run(self):
        """ Main function for test case execution """
        try:
            self.process_client()
            self.process_failed_list()
            if self.failed_validation_list:
                for client in self.failed_validation_list.copy():
                    self.log.error(
                        f"Validation failed for client: {client[0]}, OS: {client[1]}, PGSQL version: {client[2]}")
                raise Exception("TESTCASE FAILURE")

        except Exception as exp:
            handle_testcase_exception(self, exp)
