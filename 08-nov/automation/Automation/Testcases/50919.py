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
    """Class for executing Basic acceptance test of Lotus Notes Transactional Logs subclient"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name                    (str)           --  name of this test case

                show_to_user            (bool)          --  test case flag to determine
                if the test case is to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user
                    default: False

                tcinputs                (dict)          --  dict of test case inputs with input
                name as dict key and value as input type
                        Ex: {
                             "MY_INPUT_NAME": None
                        }

                common_optons_dict      (dict)          --  common options for this testcase

                lndb_restore_options    (dict)          --  options specific to LNDB restore

                domino_data_path        (str)           --  path to the domino data directory

                helper                  (object)  		--  Object of cvrest helper

                machine                 (object)       	--  Object of machine class

                rest_ops                (dict)          --  dictionary of rest services enabled
                on domino server

                pass_count              (int)           --  count of test scenarios passed

                lnhelp                  (object)		--  Object of lndbhelper

                default_subclient       (object)     	--  Instance of 'default' subclient

                trlogsubclient          (object)     	--  Instance of 'transaction log' subclient
        """
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Lotus Notes transactional log backup"
        self.show_to_user = True

        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
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
        self.helper = None
        self.rest_ops = None
        self.pass_count = 0
        self.lnhelp = None
        self.machine = None
        self.trlogsubclient = None
        self.default_subclient = None

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
            self.lnhelp.tr_log_backup_with_indexing()
            self.lnhelp.backup_many_tr_logs()
            self.lnhelp.backup_many_databases()
            self.lnhelp.osc_schedule_backup()
        except Exception as ex:
            self.log.error(
                f'Error {type(ex).__name__} on '
                f'line {sys.exc_info()[-1].tb_lineno}. '
                f'Error {ex}. trace:{sys.exc_info()[0]}'
            )
            self.result_string = str(ex)
        if self.pass_count < 4:
            self.log.error('Not all test scenarios passed. Passed :{}/4'.format(self.pass_count))
            self.status = constants.FAILED
        else:
            self.log.info('Test Case Passed Successfully')
            self.status = constants.PASSED

    def tear_down(self):
        """Teardown function of this test case"""
        self.helper.clean_up_OOP_folder()
