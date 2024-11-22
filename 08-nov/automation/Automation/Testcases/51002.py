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

"""

import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from Application.LotusNotes.cvrest_helper import CVRestHelper
from Application.LotusNotes.lndochelper import LNDOCHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Notes Document"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name                    (str)       --  name of this test case

                show_to_user            (bool)      --  test case flag to determine if the
                test case is to be shown to user or not

                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs                (dict)      --  dict of test case inputs with
                input name as dict key and value as input type

                    Ex: {
                         "MY_INPUT_NAME": None
                    }

                domino_data_path        (str)       --  path to the domino data directory

                helper                  (object)    --  Object of cvrest helper

                rest_ops                (dict)      --  dictionary of rest services enabled
                on domino server

                pass_count              (int)       --  count of test scenarios passed

                lnhelp                  (object)    --  Object of lndochelper

                dbs_in_subclient        (list)      --  List of databases in a subclient

                common_options_dict     (dict)      --  common options for restore

                machine                 (object)    --  Object of machine class
        """
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test of basic options for LNDOC"
        self.show_to_user = True

        self.tcinputs = {
            "ClientName": None,
            "DominoServerHostName": None,
            "SubclientName": None,
            "DominoNotesUser": None,
            "DominoNotesPassword": None,
            "AgentName": "Notes Document",
            "InstanceName": None,
            "BackupsetName": "defaultbackupset"
        }
        self.domino_data_path = None
        self.helper = None
        self.rest_ops = None
        self.pass_count = 0
        self.dbs_in_subclient = []
        self.lnhelp = None
        self.machine = None
        self.dbhelper = None
        self.common_options_dict = {}

    def setup(self):
        """Setup function of this test case"""
        self.helper = CVRestHelper(self)
        self.lnhelp = LNDOCHelper(self)
        self.machine = Machine(self.client.client_name, self.commcell)
        self.helper.start_domino()
        self.helper.check_for_api()

    def run(self):
        """Run function of this test case"""
        try:
            self.lnhelp.verify_full_backup()
            self.lnhelp.verify_incremental_backup()
            self.lnhelp.verify_differential_backup()
            self.lnhelp.verify_synthetic_backup()
            self.lnhelp.verify_restores()
        except Exception as ex:
            self.log.error(
                f'Error {type(ex).__name__} on line {sys.exc_info()[-1].tb_lineno}. Error {ex}')
            self.result_string = str(ex)

        if self.pass_count < 5:
            self.log.error(f'Not all test scenarios passed. Passed :{self.pass_count}/5')
            self.status = constants.FAILED
        else:
            self.log.info('Test Case Passed Successfully')
