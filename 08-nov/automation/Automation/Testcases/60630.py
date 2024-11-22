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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case calls license_helper Class to execute
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from Server.License import license_helper,licenseconstants


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""

    def __init__(self):
        """Init testcase object"""
        super(TestCase, self).__init__()
        self.name = "Activate Licenses"

    def run(self):
        '''Initialises the license objects and TC inputs, run the testcase'''
        try:
            license_sku_perm = self.tcinputs.get('license_sku_perm', None)
            license_sku_perm_quantity = self.tcinputs.get('license_sku_perm_quantity', None)
            license_sku_eval = self.tcinputs.get('license_sku_eval', None)
            license_sku_eval_quantity = self.tcinputs.get('license_sku_eval_quantity', None)
            sku_expiration = self.tcinputs.get('sku_expiration', licenseconstants.sku_expiration)
            license_expiration_days = self.tcinputs.get(
                'license_expiration_days', licenseconstants.license_expiration_days)
            license_evaluation_days = self.tcinputs.get(
                'license_evaluation_days', licenseconstants.license_evaluation_days)
            hyperv_name = self.tcinputs.get('hyperv_name', None)
            hyperv_user = self.tcinputs.get('hyperv_user', None)
            hyperv_password = self.tcinputs.get('hyperv_password', None)
            cs_vmname = self.tcinputs.get('cs_vmname', None)
            self.csclient = self.commcell.clients.get(self.commcell.commserv_name)

            self.license = license_helper.LicenseGenerator(
                self.commcell,
                self.log,
                self.inputJSONnode,
                hyperv_name,
                hyperv_user,
                hyperv_password,
                cs_vmname)
            license_types = list(self.license.license_types.keys())
            license_type = license_types[2]
            self.license.delete_license
            '''create and apply new license with permanent type'''
            self.license.applyfrom_ac_licensepage(
                self.license.create_newlicense(
                    license_type,
                    license_sku_perm,
                    license_sku_perm_quantity,
                    license_sku_eval,
                    license_sku_eval_quantity,
                    sku_expiration,
                    license_expiration_days,
                    license_evaluation_days),
                license_sku_perm,
                license_sku_eval,
                validate_popup=False)
            self.license.validate_license_details
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.license.close
            self.license.hyperv_operation(optype="REVERT")
            self.license.hyperv_operation(optype="DELETE")
