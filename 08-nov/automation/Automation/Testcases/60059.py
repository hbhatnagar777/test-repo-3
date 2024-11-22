# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer
from Server.serverhelper import ServerTestCases
from Server.RestAPI.restapihelper import RESTAPIHelper


class TestCase(CVTestCase):
    """ Class for validating Metallic Tenant Security Acceptance"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """Metallic Tenant Security Acceptance"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.show_to_user = True
        self._restapi = None
        self.server = None
        self.mailer = None
        self.tcinputs = {
            "CompaniesPrefix": None,
            "CommonUsername": None,
            "CommonPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self._restapi = RESTAPIHelper()
        self.server = ServerTestCases(self)
        self.mailer = Mailer(mailing_inputs=self.inputJSONnode.get('email'),
                             commcell_object=self.commcell)

    def run(self):
        """Main function for test case execution"""
        total_count = 0
        failure_count = 0
        try:
            result = []
            all_companies = self._commcell.organizations.all_organizations
            for company in all_companies:
                if self.tcinputs.get('CompaniesPrefix').lower() in company:
                    total_count = total_count + 1
                    self.log.info("Prefix matched with company = {0}".format(company))
                    inputs = {"webserver" : self.inputJSONnode['commcell']['webconsoleHostname'],
                              "username" : company + "\\\\" + self.tcinputs.get('CommonUsername'),
                              "password" : self.tcinputs.get('CommonPassword')}
                    collection_json = 'Metallic_Tenant_Security_Acceptance.collection.json'
                    try:
                        output = self._restapi.run_newman({'tc_id': self.id, 'c_name': collection_json}, inputs,
                                                          custom_endpoint="https://{0}/webconsole/api/".format(
                                                              self.inputJSONnode['commcell']['webconsoleHostname']),
                                                          return_newman_output=True)
                        result.append({'CompanyName': company,
                                       'Status': 'Failed' if output[0] else 'Passed',
                                       'Error': output[1].split("#  ")[1] if output[0] else ""})
                        if output[0]:
                            failure_count = failure_count + 1
                    except Exception as exp:
                        self.log.info("Failed for company = {0} with error = {1}".format(company, exp))
                        failure_count = failure_count + 1
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            table,th,td
            {
                border: 1px solid black;
                border-collapse:collapse;
            }
            th,td
            {
                padding: 15px;
                text-align:left;
            }
            </style>
            </head>
            <body>
            <h2>Metallic Tenant Security Acceptance case</h2>
            <h3 style="color:green;"> PASSED : {1} </h3>
            <h3 style="color:red;"> FAILED : {2} </h3>
            <table style="width:100%">
            <tr>
            <td><b>CompanyName</b></td>
            <td><b>Status</b></td>
            <td><b>Summary</b></td>
            </tr>
            {0}
            </table>
            </body>
            </html>"""
            html_row_template = """<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>"""

            rows = ""
            for item in result:
                rows = rows + html_row_template.format(item.get("CompanyName"),
                                                       item.get('Status'),
                                                       item.get('Error').replace("\n", '<br>'))
            html_template = html_template.replace('{1}', str(total_count-failure_count))
            html_template = html_template.replace('{2}', str(failure_count))
            html_template = html_template.replace('{0}', rows)
            self.mailer.mail(subject="Metallic Tenant Security Acceptance",
                             body=html_template)
            if failure_count > 0:
                raise Exception("Validation failed for '{0}' companies out of '{1}'."
                                "Please check follow up report for more details".format(failure_count, total_count))
            if not total_count:
                raise Exception("No Matching companies found. please check prefix input")
        except Exception as excep:
            self.server.fail(excep)
        finally:
            if total_count > 0 or failure_count > 0:
                self._restapi.clean_up()

