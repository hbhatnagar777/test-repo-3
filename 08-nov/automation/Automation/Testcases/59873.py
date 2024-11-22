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

    get_subclients() -- To get valid subclients if null is given.

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import sys

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Server.serverhelper import ServerTestCases
from Server.JobManager.rpo_helper import RpoHelper
from Server.JobManager.rpo_helper import RPOBasedSubclient as RpoSubClientHelper
from Server.JobManager.rpo_constants import RPO_ADDITIONAL_SETTING_KEY

from Server.JobManager.rpo_constants import ESTIMATED_TIME_THRESHOLD
from Server.JobManager.jobmanagement_helper import JobManagementHelper



class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "verify strike count takes priority in resource allocation when existing valid subclients are used"
        self.retval = 0
        self.tcinputs = {
            'ClientName': None,  # client name where subclient will be created
            'MediaAgent': None,  # media agent where disk library is created
            'Subclients': None  # list of subclients with history of more than 100 backup jobs  -- optional can be null
        }
        self.sc_instances = []
        self.rpo_helper_obj = None
        self.server = None
        self._utility = None
        

    def get_subclients(self,rpo_enabled_trough_regkey):
        """If subclients are not provided in TC input then this function will extract 2 subclients from the client"""
        self.log.info("Getting 2 subclients from client {0}".format(self.tcinputs['ClientName']))
        subclient_lst = []
        client_obj = self.commcell.clients.get(self.tcinputs['ClientName'])
        idata_agent = client_obj.agents.get("File System")
        self.log.debug("using File System as default idata agent")
        instance = idata_agent.instances.get("defaultinstancename")
        backup_set = instance.backupsets.get('defaultBackupSet')
        self.log.debug("using defaultBackupSet as instance")
        subclient_dict = backup_set.subclients.all_subclients
        
        for subclient in subclient_dict:
            self._utility.exec_commserv_query("select count(*) from JMBkpStats where "
                                              "appId = {0}".format(subclient_dict[subclient]['id']))
            if int(self.csdb.rows[0][0]) > ESTIMATED_TIME_THRESHOLD:
                if not rpo_enabled_trough_regkey:
                    subclient_obj = backup_set.subclients.get(subclient)
                    if subclient_obj.plan:
                        subclient_lst.append(subclient)
                else:
                    subclient_lst.append(subclient)
                if len(subclient_lst) == 2:
                    break
        if len(subclient_lst) < 2:
            raise Exception("No subclients with backup more than {0} are present ".format(
                ESTIMATED_TIME_THRESHOLD))
        return subclient_lst
        
    def setup(self):
        """Setup function of this test case"""
        self.log.info("executing testcase")
        self._utility = OptionsSelector(self.commcell)
        self.server = ServerTestCases(self)

        self.log.info("creating RPO helper instance")
        self.rpo_helper_obj = RpoHelper(self.commcell,
                                        self.tcinputs['ClientName'],
                                        self.tcinputs['MediaAgent'])
        rpo_enabled_trough_regkey = False
        try:
            self.rpo_helper_obj.verify_rpo_is_enabled()
            rpo_enabled_trough_regkey = True
        except:
            pass
        if not self.tcinputs['Subclients']:
            self.tcinputs['Subclients'] = self.get_subclients(rpo_enabled_trough_regkey)

        for subclient in self.tcinputs['Subclients']:
            self.log.info(
                "using Subclient {0} as RPO subclient".format(subclient))
            rpo_subclient = RpoSubClientHelper(self.rpo_helper_obj,
                                               subclient, True)
            self.sc_instances.append(rpo_subclient)

        strike_count = 3
        for count in range(len(self.tcinputs['Subclients'])):
            self.log.info(
                "setting strike count %s for subclient%s", strike_count, count)
            self.sc_instances[count].force_strike_count(strike_count)
            strike_count += 1

    def run(self):
        """Run function of this test case"""
        try:
            self.rpo_helper_obj.validate_rsc_alloc_order(self.sc_instances)
        except Exception as exp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.server.fail(exp, "test case failed in run function")

    def tear_down(self):
        """Tear down function of this test case"""
        pass
