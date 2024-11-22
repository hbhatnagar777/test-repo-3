# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function for this testcase

    run()                   --  Main function for this testcase

TestCase Inputs (Optional):
    {
        ---------- Test Parameters ------------------
        cloud_hostname  (str)       -   hostname of cloud commcell
        cloud_admin_user    (str)   -   admin username for cloud cs, else CONFIG.ADMIN_USERNAME
        cloud_password  (str)       -   admin password for cloud cs, else CONFIG.ADMIN_PASSWORD
        existing_company    (str)   -   name of existing company to use else new company setup
        redirect_calls  (int)       -   number of redirect API calls to collect timing data, default 10
        default_password    (str)   -   password for company/commcell local users
                                        if not given, CONFIG.MultiCommcells.Local_users_password
                                        if that also not there, random password generated

        ----------- For cloud company setup -------------------
        new_company_name    (str)   -   name of company to create with
        new_company_alias   (str)   -   domain name of company to create
        new_ta_password     (str)   -   password to set for company users

        ----------- for new on prem user creation--------------------------
        new_onprem_username (str)   -   username to create for commcell user test
        new_onprem_email    (str)   -   email to create with for commcell user test

        ----------- for on prem ad user setup ------------------------------
        ADCreds (dict)              -   dict with AD details for AD user test
                                        default: will take from config.Security.LDAPs.Active_Directory
                    example:
                        {
                            "NETBIOSName": "...", "DomainName": "...", "UserName": "...", "Password": "...",
                            "UserGroupsToImport": [{"externalgroup": "..."}],
                            "UsersToImport": [{"UserName": "...", "Password": "...", "email": "..."}]
                        }

        ----------- for on prem saml user setup ----------------------------------
        SAMLCreds (dict)        -   dict with SAML (ADFS) details
                                    if not given will take from config.MultiCommcells.SAMLCreds
                    example:
                        {
                            "appname": "...",
                            "idpmetadata_xml_path": "...",
                            "email_suffixes": "...",
                            "UsersToImport": [{"UserName": "...", "Password": "...", "email": "..."}],
                            "ad_host_ip": "...",
                            "ad_machine_user": "...",
                            "ad_machine_password": "..."
                        }
                        
        ----------- config must have cloud DB SQL creds for user with EXEC permission -----------
                        CONFIG.MultiCommcell.RouterSQLCreds.username
                        CONFIG.MultiCommcell.RouterSQLCreds.password
    }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.loopy_helper import LoopyHelper


class TestCase(CVTestCase):
    """Class for executing Loopy Redirections"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Loopy Redirections"
        self.loopy_helper = None
        self.tcinputs = {
            'cloud_hostname': ''
        }

    def setup(self):
        """setup function for this testcase"""
        self.loopy_helper = LoopyHelper(self.commcell, self.tcinputs.get('default_password') or None)
        self.loopy_helper.setup_cloud(
            cloud_hostname=self.tcinputs['cloud_hostname'],
            cloud_admin_username=self.tcinputs.get('cloud_admin_user') or None,
            cloud_admin_password=self.tcinputs.get('cloud_password') or None,
            company=self.tcinputs.get('existing_company') or None,
            company_name=self.tcinputs.get('new_company_name') or None,
            company_alias=self.tcinputs.get('new_company_alias') or None,
            ta_password=self.tcinputs.get('new_ta_password') or None
        )
        self.loopy_helper.redirect_checks = int(self.tcinputs.get('redirect_calls', '0')) or 10

    def run(self):
        """Main function for test case execution"""
        errors = []
        timing_data = {}
        try:
            timing_data['commcell user'] = self.loopy_helper.commcell_user_sync_test(
                username=self.tcinputs.get('new_onprem_username'),
                email=self.tcinputs.get('new_onprem_email')
            )
        except Exception as exp:
            errors.append(f">>>>> Commcell User Sync Test Failed! with error: {str(exp)}")
        try:
            timing_data['ad user'] = self.loopy_helper.ad_user_sync_test(
                ADCreds=self.tcinputs.get('ADCreds')
            )
        except Exception as exp:
            errors.append(f">>>>> AD User Sync Test Failed! with error: {str(exp)}")
        try:
            timing_data['saml user'] = self.loopy_helper.saml_user_sync_test(
                admin_password=self.inputJSONnode['commcell']['commcellPassword'],
                SAMLCreds=self.tcinputs.get('SAMLCreds')
            )
        except Exception as exp:
            errors.append(f">>>>> SAML User Sync Test Failed! with error: {str(exp)}")
        try:
            timing_data['onprem + cloud saml user'] = self.loopy_helper.commcell_saml_user_test(
                idpmetadata_xml_path=self.tcinputs.get('SAMLCreds', {}).get('idpmetadata_xml_path')
            )
        except Exception as exp:
            errors.append(f">>>>> Onprem + cloud SAML User Sync Test Failed! with error: {str(exp)}")

        self.log.info(">>>>>>>>> LOOPY USERS FLOW TEST SUMMARY <<<<<<<<<<")
        self.log.info(">>>>>> ERRORS <<<<<<<<")
        for error in errors:
            self.log.error(">>>>>" + error)
        self.log.info(">>>>>> SUCCESSFUL CASES / RESPONSE TIMES <<<<<<<")
        for case_name in timing_data:
            self.log.info(">>>>>" + case_name)
            self.log.info(f">>>>> INPUT USERNAME: {timing_data[case_name][0]}")
            self.log.info(f">>>>> INPUT EMAIL: {timing_data[case_name][1]}")
        self.log.info(">>>>>>> IN CONCLUSION <<<<<<<<")
        if errors:
            raise Exception(f"TESTCASE FAILED! {errors}")
        else:
            self.log.info(">>>>>>> TESTCASE PASSED! <<<<<<<<<")
