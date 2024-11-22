# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for CloudTestTool validation

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""

from cvpysdk.client import Client
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine


class TestCase(CVTestCase):
    """Test case class for testing CloudTestTool."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("CloudTestTool validation")
        self.tcinputs = {
            "user": None,
            "password": None,
            "bucket": None,
            "host": None
        }

    def execute_exe(self, client_machine, path, host, user, password, bucket, option_type='test'):
        '''
        This Function will execute CloudTestTool.
        Raises:
                Exception:
                    if failed to execute CloudTestTool
        '''
        try:
            log = self.log
            log.info("client installed path is %s" % path)
            cmd = (path.replace(" ", "' '") + "\\Base\\CloudTestTool.exe" + ' -t 2 -h %s ' % host +
                   " -u " + user + " -p " + password + " -b " + bucket + " -o " + option_type)

            log.info("Command used for cloustest {}".format(cmd))
            output = client_machine.execute_command(cmd)

            if str(output.output).find("fail") >= 0 or output.exit_code != 0:
                raise Exception(
                    "Error while executing exe %s" %
                    str(output.output))
            elif str(output.output).find("All tests are succssful") >= 0 and output.exit_code == 0:
                log.info("Successfuly executed exe")
            else:
                raise Exception(
                    "Exception raised with unknown reason :%s" %
                    str(output))

        except Exception as err:
            raise Exception('Failed to execute Cloud Tool with error %s' % str(err))

    def run(self):
        """ Main function for test case execution.
        This Method creates custom packages and Installs them onto clients.
        If Installation is sucessful custom packages are uploaded to cloud.

        Raises:
            SDKException:
                if it fails to execute CloudTestTool
        """
        try:
            client = Client(self.commcell, self.commcell.commserv_name)
            client_machine = WindowsMachine(client.client_name, self.commcell)
            path = self.client.install_directory
            self.execute_exe(
                client_machine,
                path,
                host=self.tcinputs["host"],
                user=self.tcinputs["user"],
                password=self.tcinputs["password"],
                bucket=self.tcinputs["bucket"],
                option_type='test')

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
