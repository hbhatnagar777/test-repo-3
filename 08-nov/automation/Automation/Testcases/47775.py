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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
import threading
import random


class TestCase(CVTestCase):
    """Class for executing VSA VMWARE Parallel File level Browse of multiple vms"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "V2: VSA VMWARE Parallel File level Browse of multiple VMs"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            if not auto_subclient.auto_vsaclient.isIndexingV2:
                self.log.exception('This testcase is for indexing v2. The client passed is indexing v1 ')
                raise Exception

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)
            browse_ma = self.tcinputs.get('browse_ma', '')
            auto_subclient.parallel_browse_multiple_vm(browse_ma)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testdata cleanup was not completed")
                pass
