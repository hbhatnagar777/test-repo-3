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

Testcase qoperation browse verification with automation

Inputs are :

remoteclient : name of the remote client on which qcommands are executed remotely

Backupclient : Name of the client which has data backed up

BackupSet : Backupset of the "Backupclient"

Subclient : Subclient of the "BackupSet" of the "Backupclient"


"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestStepFailure
import os
import xml.etree.ElementTree as ET


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
        self.name = "qoperation browse verification with automation"
        self.tcinputs = {
            "remoteclient": None,
            "Subclient": None,
            "Backupset": None,
            "Backupclient": None
        }
        self.client_name = None
        self.input = None
        self.client_object = None

    def setup(self):
        """Setup function of this test case"""
        self.client_name = self.tcinputs["remoteclient"]
        self.input = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<databrowse_BrowseRequest>

  <opType>Browse</opType>

  <entity>
    <subclientName>{self.tcinputs.get("Subclient", "default")}</subclientName>
    <backupsetName>{self.tcinputs.get("Backupset", "defaultBackupSet")}</backupsetName>
    <instanceName>DefaultInstanceName</instanceName>
    <appName>File System</appName>
    <clientName>{self.tcinputs["Backupclient"]}</clientName>
  </entity>

  <paths>
    <path>\\</path>
  </paths>

  <options>
    <skipIndexRestore>false</skipIndexRestore>
    <instantSend>false</instantSend>
  </options>

  <mode>
    <mode>3</mode>
  </mode>

  <queries>
    <type>DATA</type>
    <queryId>0</queryId>
    <dataParam>
      <paging>
        <firstNode>0</firstNode>
        <skipNode>0</skipNode>
        <pageSize>10000</pageSize>
      </paging>
      <sortParam>
        <sortBy>38</sortBy>
        <sortBy>0</sortBy>
        <ascending>true</ascending>
      </sortParam>
    </dataParam>
  </queries>

  <queries>
    <type>TOPBOTTOM</type>
    <queryId>TOPBOTTOM</queryId>
    <topBottomParam>
      <field>FileSize</field>
      <count>10</count>
      <ascending>false</ascending>
    </topBottomParam>
  </queries>

  <queries>
    <type>AGGREGATE</type>
    <queryId>2</queryId>
    <aggrParam>
      <aggrType>SUM</aggrType>
      <field>FolderSize</field>
    </aggrParam>
  </queries>

</databrowse_BrowseRequest>"""

    def qcommand_api(self, command):
        response = self.commcell.execute_qcommand(command)
        if response.status_code == 200:
            self.log.info("{} output : \n{}".format(command, response.text))
            return response.text
        else:
            raise CVTestStepFailure(f"API execution failed for {command} with {response.text}")

    def remote_command_execution(self, command):
        output = self.client_object.execute_command(command)
        if output[0]:
            raise CVTestStepFailure("The remote command execution failed for {} : \n{}".format(command, output[1]))
        else:
            self.log.info(f"Output for {command} is \n{output[1]}")
            return output[1]

    def run(self):
        """Run function of this test case"""
        try:
            # Qcommand execution via the helpers
            self.qcommand_api("qlist client")

            self.qcommand_api("qlist job")

            self.qcommand_api("qlist mediaagent")

            self.log.info("Executing browse request on commserve via the POST request")
            flag, response = self.commcell._cvpysdk_object.make_request("POST", self.commcell._services['EXECUTE_QCOMMAND'] + " -file browseresultfile.txt", self.input)

            self.log.info(response.text)  # API execution output

            if response.ok:
                commserv = Machine(self.commcell.commserv_client)
                webserverdir = commserv.join_path(self.commcell.commserv_client.install_directory, "WebServerCore")
                browseoutput = commserv.read_file(commserv.join_path(webserverdir, "browseresultfile.txt"))
                self.log.info(browseoutput)

                if self.validate_xml(browseoutput):
                    self.log.info("Databrowse is successful on the commserve")
                else:
                    self.log.info("Databrowse is unsuccessful")
                    raise CVTestStepFailure("Browse request via the REST API failed ")

                commserv.delete_file(commserv.join_path(webserverdir, "browseresultfile.txt"))
            else:
                raise CVTestStepFailure("Browse request via the REST API failed ")

            # Executing the databrowse on the remote client via the command line
            self.client_object = self.commcell.clients.get(self.client_name)
            client_machine_object = Machine(self.client_object)

            base_folder = client_machine_object.join_path(self.client_object.install_directory, "Base")
            self.log.info(" BASE DIR : {}".format(base_folder))

            # Set the basic path
            if client_machine_object.os_info == "WINDOWS":
                self.remote_command_execution(f"if not defined GALAXY_BASE set GALAXY_BASE={base_folder}")
                self.remote_command_execution("set PATH=%PATH%;%GALAXY_BASE%")
            else:
                self.remote_command_execution(f"export PATH=$PATH:{base_folder}")

            self.log.info("EXECUTING QLOGIN COMMAND IN THE CLIENT")
            self.remote_command_execution(
                f"""qlogin -u "{self.inputJSONnode['commcell']['commcellUsername']}" -clp "{self.inputJSONnode['commcell']['commcellPassword']}" """)

            inputfilepath = client_machine_object.join_path(self.client_object.install_directory, "inputXMLRequest.xml")
            outputfile = client_machine_object.join_path(self.client_object.install_directory, "outputResponse.txt")

            # Create the input XML File for qoperation
            if client_machine_object.os_info == "WINDOWS":
                client_machine_object.create_file(inputfilepath, self.input)
            else:
                with open("inputXMLRequest.xml", "w") as f:
                    f.write(self.input)
                client_machine_object.copy_from_local(os.path.join(os.getcwd(), "inputXMLRequest.xml"),
                                                      self.client_object.install_directory)

            output = self.remote_command_execution(
                'qoperation execute -af "{}" -file "{}"'.format(inputfilepath, outputfile))

            self.log.info("QOPERATION OUTPUT : {}".format(output))

            browseoutput = client_machine_object.read_file(outputfile)
            self.log.info(browseoutput)
            client_machine_object.delete_file(outputfile)
            client_machine_object.delete_file(inputfilepath)

            # Validate the XML for databrowse tags
            if self.validate_xml(browseoutput):
                self.log.info("BROWSE REQUEST IS SUCCESSFUL WITHOUT -CS PARAMETER FROM CLIENT")
            else:
                raise CVTestStepFailure(" Browse request is not successful")

            # Qlist operations on the client
            self.remote_command_execution("qlist client")

            self.remote_command_execution("qlist job")

            self.remote_command_execution("qlist mediaagent")

            self.remote_command_execution("qlogout")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def validate_xml(self, xml):
        """Tear down function of this test case"""
        root = ET.fromstring(xml)
        if root.tag == "OUTPUT":
            browsecount = 0
            for child in root:
                if child.tag == "databrowse_BrowseResponse":
                    browsecount += 1
            if browsecount > 0:
                self.log.info("BROWSE RESPONSE HAS THE APPROPRIATE RESPONSE")
                return True
            else:
                raise CVTestStepFailure(" BROWSE RESPONSE XML HAS NO BROWSE TAGS")
        else:
            raise CVTestStepFailure("XML has error")
