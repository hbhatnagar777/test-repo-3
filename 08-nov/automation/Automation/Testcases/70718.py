# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from typing import Dict

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

"""Testcase for validating platform upgrade post OS upgrade for HSX 2.x

    Sample Input json

    "70718": 
            {
                "VMDict": {
                    "VMName":"Hostname"
                },
                "NodeUsername": "",
                "NodePassword": "",
                "SqlLogin": "",
                "SqlPassword": ""
            }
"""

class TestCase(CVTestCase):
    """Testcase for validating platform upgrade post OS upgrade for HSX 2.x
    """

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Testcase for validating platform upgrade post OS upgrade for HSX 2.x"
        self.mas = []
        self.ma_machines = {}
        self.result_string = ""
        self.tcinputs = {
            "VMDict" : {},
            "NodeUsername": None,
            "NodePassword": None,
            "SqlLogin": None,
            "SqlPassword": None
        }
        self.successful = False

    def setup(self):
        """Setup method for this testcase"""

        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # MA setup
        self.node_username = self.tcinputs["NodeUsername"]
        self.node_password = self.tcinputs["NodePassword"]
        self.vm_dict = self.tcinputs["VMDict"]
        self.mas = self.vm_dict.values()
        self.vmnames = self.vm_dict.keys()
        self.ma_machines: Dict[str, UnixMachine] = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = UnixMachine(ma_name, username=self.node_username, password=self.node_password)
            self.ma_machines[ma_name] = machine

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')
        if tcinputs_sql_login is None:
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(
                    f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(
                    f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.error("Test case failed.")
            self.status = constants.FAILED
    
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def run(self):
        """Run method for this testcase"""

        try:
            
            # 1. Get platform version of all nodes from payload release date
            identical_payload, platform_version_list_from_payload = self.hyperscale_helper.fetch_cluster_platform_version_from_payload(self.ma_machines)
            if not identical_payload:
                reason = f"Platform version from payload release date is different across nodes in cluster"
                return self.fail_test_case(reason)
            self.log.info(f"Platform version as reported by payload release date is same across all node in the cluster")

            # 2. Get platform version of all nodes from CSDB
            identical_csdb, platform_version_list_from_CSDB = self.hyperscale_helper.fetch_cluster_platform_version_from_csdb(self.mas)
            if not identical_csdb:
                reason = f"Platform version from CSDB is different across nodes in cluster"
                return self.fail_test_case(reason)
            self.log.info(f"Platform version as reported by CSDB is same across all nodes in the cluster")

            # 3. Validating platform versions from payload release date and CSDB on each node
            validation_status = {}
            for ma_name in self.mas:
                if platform_version_list_from_CSDB[ma_name] != platform_version_list_from_payload[ma_name]:
                    self.log.error(f"Platform versions reported by CSDB and payload release date differ on {ma_name}")
                    validation_status[ma_name] = False
                else:
                    validation_status[ma_name] = True

            if all(validation_status.values()):
                self.log.info(f"Platform versions match on all nodes")
            else:
                failed_nodes = [ma_name for ma_name, status in validation_status.items() if not status]
                reason = f"Platform version validation failed on following nodes -> {failed_nodes}"
                self.fail_test_case(reason)

            self.successful = True
            self.log.info(f"Platform version post OS upgrade has been validated successfully on all nodes")


        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                            self.result_string)

