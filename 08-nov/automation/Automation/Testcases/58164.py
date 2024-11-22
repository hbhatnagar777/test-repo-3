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

    run()           --  run function of this test case

Inputs:
    "58164": {
        "powershell_configuration_file": "D:\\Configuration.yaml",
        "go_configuration_file": "D:\\Configurationgo.yaml",
        "output_folder" : "D:\\PSSDK"
        }
"""

import os
from AutomationUtils import logger, constants
from Server.SDKGenerator import generatorhelper
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for Generating SDK"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Automatic SDK Generation Case "
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI

    def run(self):
        """Main function for test case execution"""

        log = logger.get_log()
        try:
            sdk_object = generatorhelper.SdkFactory(self.commcell, self.tcinputs.get('file_location',
                                                                                     "C:\\SDK\\OpenAPI3.yaml"))

            try:
                sdk_object.generate(language="Powershell",
                                    powershell_configuration_file=self.tcinputs.get('powershell_configuration_file',
                                                                                    "C:\\SDK\\configuration.yaml"),
                                   output_folder=self.tcinputs.get('output_folder', "C:\\SDK"))
                sdk_object.build_module()
                sdk_object.pack_module()


            except Exception as exp:
                self.result_string = str(exp)
                self.status = constants.FAILED

            """

            try:
                sdk_go_object = generatorhelper.SdkFactory(self.commcell, self.tcinputs.get('file_location',
                                                                                     "D:\\SDK\\OpenAPI3.yaml"),
                                                                                     language="go")
                sdk_go_object.generate(language="go",
                                    go_configuration_file=self.tcinputs.get('go_configuration_file',
                                                                            "C:\\configuration.yaml"),
                                    output_folder=self.tcinputs.get('output_folder', "D:\\SDK"))
            except Exception as exp:
                self.result_string = str(exp)
                self.status = constants.FAILED
            
            #"""

        except Exception as exp:
            self.log.warning('Failed with error: ' + str(exp))
