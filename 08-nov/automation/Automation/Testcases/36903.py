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
"""


import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from Application.LotusNotes.cvrest_helper import CVRestHelper
from Application.LotusNotes.lndbhelper import LNDBHelper


class TestCase(CVTestCase):
    """Class for executing Basic functionality of Lotus Notes Database agent test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name                    (str)           --  name of this test case

                show_to_user            (bool)          --  test case flag to determine if
                the test case is to be shown to user or not

                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs                (dict)          --  dict of test case inputs with
                input name as dict key and value as input type

                    Ex: {
                         "MY_INPUT_NAME": None
                    }

                common_optons_dict      (dict)          --  common options for this testcase

                lndb_restore_options    (dict)          --  options particular for LNDB restore

                domino_data_path        (str)           --  path to the domino data directory

                helper                  (CVRestHelper)  --  Object of cvrest helper

                machine                 (Machine)       --  Object of machine class

                rest_ops                (dict)          --  dictionary of rest services enabled on
                domino server

                pass_count              (int)           --  count of test scenarios passed

                lnhelp                  (LNDBHelper)    --  Object of lndbhelper

                dbs_in_default_before   (list)          --  List of databases in a subclient

                dbs_in_default_after    (list)          --  List of databases in a subclient

                new_dbs_added           (list)          --  List of databases in a subclient

                default_subclient       (Subclient)     --  Instance of 'default' subclient

                trlogsubclient          (Subclient)     --  Instance of 'transaction log' subclient
        """
        super(TestCase, self).__init__()
        self.name = "Basic functionality of agent features for the NOTESDB agent"
        self.show_to_user = True

        self.tcinputs = {
            "ClientName": None,
            "DominoServerHostName": None,
            "DominoNotesUser": None,
            "DominoNotesPassword": None,
            "AgentName": "Notes Database",
            "InstanceName": None,
            "BackupsetName": "defaultbackupset"
        }
        self.common_options_dict = {}
        self.lndb_restore_options = {}
        self.domino_data_path = None
        self.rest_ops = None
        self.helper = None
        self.lnhelp = None
        self.machine = None
        self.dbs_in_default_before = []
        self.dbs_in_default_after = []
        self.new_dbs_added = []
        self.pass_count = 0
        self.default_subclient = None
        self.trlogsubclient = None

    def setup(self):
        """Setup function of this test case"""
        self.helper = CVRestHelper(self)
        self.lnhelp = LNDBHelper(self)
        self.machine = Machine(self.client.client_name, self.commcell)
        self.helper.start_domino()
        self.helper.check_for_api()
        self.trlogsubclient = self.backupset.subclients.get('transaction logs')
        self.default_subclient = self.backupset.subclients.get('default')

    def run(self):
        """Run function of this test case"""
        try:
            self.lnhelp.defsubclient_autodiscovery()
            self.lnhelp.disaster_recovery()
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)

        if self.pass_count == 2:
            self.log.info('TestCase has passed successfully')
            self.status = constants.PASSED
        else:
            self.log.error('Only a few test sceanrios passed: {}/2'.format(self.pass_count))
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.helper.clean_up_OOP_folder()
