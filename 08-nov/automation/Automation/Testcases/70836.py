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
from VirtualServer.SNAPUtils.vsa_snap_templates import VSASNAPTemplates
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMWARE Snap backup
    and Guest file Restore test case
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA V2 VMWARE Snap Backup and Guest File Restore Case using " \
                    "windows Proxy, linux Guest, Linux Plan MA and Proxyless transport mode for : {0}"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            self.name = self.name.format(self.tcinputs["snap_engine"])
            vsa_snap_templates = VSASNAPTemplates(self)
            return_values = vsa_snap_templates.vsasnap_template_v2_guestfile(
                vsaproxy_os="windows", ma_os="linux", guest_os="linux",  transport_mode="directsan")
            auto_subclient, backup_options, self.test_individual_status, self.test_individual_failure_message = return_values

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if not self.test_individual_status:
                    self.result_string = self.test_individual_failure_message
                    self.status = constants.FAILED
                else:
                    auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass


