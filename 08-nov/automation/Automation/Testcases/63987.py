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

    set_tppm_settings() --  sets tppm settings on webserver client

    validate_tppm() --  Validates whether dynamic tppm worked or not

    tear_down()     --  tear down function of this test case

"""
import time

from cvpysdk.commcell import Commcell

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.tppm_helper import WebServerTPPM
from dynamicindex.utils import constants as dynamic_constants


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
        self.name = "Webserver TPPM : Validate dynamic TPPM cvd thread on windows CS client by restarting sql service"
        self.tcinputs = {
            "WebServerClient": None,
            "WebServerClientUserName": None,
            "WebServerClientPassword": None,
            "CSClientUserName": None,
            "CSClientPassword": None

        }
        self.cs_machine_obj = None
        self.tppm_helper = None
        self.client_machine_obj = None
        self.tppm_commcell = None
        self.client_machine_obj_cred = None

    def set_tppm_settings(self):
        """adds tppm settings on webserver client"""
        # Set additional settings to enable tppm
        self.client_machine_obj.remove_registry(key=dynamic_constants.COMMSERV_REG_KEY,
                                                value=dynamic_constants.WEB_SERVER_ENABLE_TPPM_KEY)
        self.log.info(f"Updating existing webserver with TPPM key - {self.tcinputs['WebServerClient']}")
        result = self.client_machine_obj.create_registry(
            key=dynamic_constants.COMMSERV_REG_KEY,
            value=dynamic_constants.WEB_SERVER_ENABLE_TPPM_KEY,
            data="True",
            reg_type="String")
        if not result:
            raise Exception(
                f"Failed to set tppm enable registry key on new webserver - {self.tcinputs['WebServerClient']}")
        self.log.info("Doing IIS Reset and waiting for 5mins for webserver to come up")
        self.client_machine_obj_cred.restart_iis()
        time.sleep(300)

    def setup(self):
        """Setup function of this test case"""
        self.tppm_helper = WebServerTPPM(commcell=self.commcell, client_name=self.tcinputs["WebServerClient"],
                                         cs_machine_user=self.tcinputs['CSClientUserName'],
                                         cs_machine_password=self.tcinputs['CSClientPassword'])
        self.client_machine_obj = Machine(machine_name=self.tcinputs["WebServerClient"], commcell_object=self.commcell)
        self.client_machine_obj_cred = Machine(
            machine_name=self.tcinputs["WebServerClient"],
            username=self.tcinputs["WebServerClientUserName"],
            password=self.tcinputs["WebServerClientPassword"])
        self.cs_machine_obj = Machine(
            machine_name=self.commcell.commserv_client.client_name,
            commcell_object=self.commcell)
        self.log.info(f"Starting Firewall on CS")
        self.tppm_helper.cs_firewall_setup()
        self.cs_machine_obj.start_firewall()
        self.set_tppm_settings()
        if not self.tppm_helper.validate_firewall_entry():
            raise Exception(f"TPPM entry is not found for this webserver in app_firewalltppm table")

    def validate_tppm(self):
        """Validates whether dynamic tppm worked or not"""
        self.client_machine_obj.set_logging_debug_level(service_name=dynamic_constants.DM2_WEB_LOG, level='10')
        time.sleep(120)
        if self.tppm_helper.is_sql_port_open():
            self.log.info(f"Webserver is able to ping CS sql port. Start firewall on CS")
            self.cs_machine_obj.start_firewall()
            time.sleep(120)
            self.log.info("Restarting IIS & Waiting for 3mins")
            self.client_machine_obj_cred.restart_iis()
            time.sleep(200)
            if self.tppm_helper.is_sql_port_open():
                raise Exception(f"Webserver is able to ping CS sql port even after CS firewall start")
        self.log.info("Webserver is not able to ping CS sql port. Try login for user")
        try:
            self.tppm_commcell = Commcell(
                self.tcinputs["WebServerClient"],
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
        except Exception:
            raise Exception("Login fails for webserver. Dynamic TPPM didn't kick in")
        self.log.info("User login worked. Try finding tppm related log lines in dm2web.log")

    def run(self):
        """Run function of this test case"""
        try:
            # get current sql port
            old_port = self.tppm_helper.get_cs_sql_port()
            self.log.info(f"Sql is running in TCP port - {old_port}")
            self.log.info("Going to block sql port by restarting sql on CS")
            self.cs_machine_obj.block_tcp_port(port=int(old_port), time_interval=1800, is_sql_port_lock=True)
            self.log.info("Successfully blocked older sql port and then restarted sql")
            time.sleep(300)
            new_port = self.tppm_helper.get_cs_sql_port()
            if old_port == new_port:
                raise Exception("Sql port is same as before. Something went wrong. Plz check logs")
            self.log.info(f"Sql is running with new dynamic port - {new_port}")
            if not self.tppm_helper.validate_firewall_entry():
                raise Exception(f"TPPM entry is not found for this webserver in app_firewalltppm table")
            self.validate_tppm()
            self.tppm_helper.validate_tppm_in_log()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Webserver login worked via new dynamic port as expected. consider as PASS")
