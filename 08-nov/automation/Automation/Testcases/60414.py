# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Store Reports Security
Every Report in in Store is verified for Security and delete,install,loading errors
"""
import json
import os
import math
from random import randint
from time import sleep
from multiprocessing import Process, Queue
from concurrent.futures import ThreadPoolExecutor

from cvpysdk.exception import SDKException
from cvpysdk.commcell import Commcell
from selenium.common.exceptions import ElementNotVisibleException
from AutomationUtils import constants, logger
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.utils import TestCaseUtils
from Reports.Custom.utils import CustomReportUtils
from Web.API.customreports import CustomReportsAPI
from Web.API.webconsole import Store
from Web.Common.exceptions import CVTestCaseInitFailure, CVSecurityException, NonFatalException
from Web.Common import page_object
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVWebAutomationException,
    CVTimeOutException,
    CVWebAPIException,
    CVWebNoData,
    CVTestStepFailure,
)

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.Reports.Custom.inputs import ListBoxController

_CONFIG = get_config()


class CloudReportsValidator:
    """Performs Report validation for each report passed in each process"""
    test_step = page_object.TestStep()
    InstallFailure = 'Install Failure'
    Timeout = 'Load Time out'
    NoData = 'No Data'
    Errors = 'Errors'
    Success = 'Success'
    SecurityFailure = 'Security Failure'
    unknown = 'Unknown'

    def __init__(self, machine_name, wc_uname, wc_pwd, reports, batch_name):
        self.webconsole_name = machine_name
        self.wc_uname = wc_uname
        self.wc_pwd = wc_pwd
        self.commcell = Commcell(self.webconsole_name, self.wc_uname, self.wc_pwd)
        self.store_reports = reports
        self._cre_api = None
        self._store_api = None
        self.batch_name = batch_name + ", PID " + str(os.getpid())
        self.p_name = batch_name
        _ = logger.Logger(constants.LOG_DIR, "60414", os.getpid())  # mapping caller thread to TC
        self.log = logger.get_log()
        self.browser = None
        self.webconsole = None
        self.metrics_report = None
        self.failed_reports = {}
        self.automation_username = 'TC60414'
        self.automation_password = 'TC60414#'
        self.crutils = CustomReportUtils(self)
        self.report_def = None
        self.data = None
        self.default_mapping = {
                           'timeframe': '-P7D P0D',
                           'agentname': 'Windows File System',
                           'agent': 'Windows File System',
                           'clientname': 'All'}

    def init(self):
        """Opens browse and login to webconsole"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.webconsole_name)
        self.webconsole.login(self.automation_username, self.automation_password)
        self.metrics_report = MetricsReport(self.webconsole)

    def close(self):
        """ Closes Browser"""
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)

    @property
    def cre_api(self):
        """ Creates an Object of CustomReportsAPI"""
        # if self._cre_api is None:
        self._cre_api = CustomReportsAPI(
            self.webconsole_name,
            username=self.wc_uname,
            password=self.wc_pwd
        )
        return self._cre_api

    @property
    def store_api(self):
        """ Creates an Object of Store"""
        if self._store_api is None:
            self._store_api = Store(
                machine=self.webconsole_name,
                wc_uname=self.wc_uname,
                wc_pass=self.wc_pwd,
                store_uname=_CONFIG.email.username,
                store_pass=_CONFIG.email.password
            )
        return self._store_api

    def delete_report(self, report):
        """Delete reports"""
        _ = logger.Logger(constants.LOG_DIR, "60414", os.getpid())  # mapping caller thread to TC
        retry_delete_idx = 0
        while retry_delete_idx < 2:
            try:
                sleep(2)
                self.cre_api.delete_custom_report_by_name(report, suppress=True)
                break
            except Exception as e:
                sleep(5)
                retry_delete_idx += 1
                self.log.exception(f"Delete report {report} failed : {e}")
        return "Deletion successful"

    def install_report(self, report):
        """Install report from Store"""
        sleep(randint(4, 20))
        self.store_api.install(report, "Reports")
        return "Installed Successfully"

    def validate_security(self, report):
        """Update User security and validate record count for each dataset in a report for that user"""
        self.report_def = self.cre_api.get_report_definition_by_name(report)
        report_id = self.crutils.get_report_id(report)
        self.update_security(report_id)
        report_guid = self.crutils.get_report_guid(report_id)

        # get guid of the datasets having endpoint - "DATABASE"
        database_dataset_guid = self.get_database_dataset_guid()

        # Check what parameters are required for running datasets
        required_input_param = self.check_required_params()

        # Get values of the required parameters
        params = self.get_params_values(required_input_param, report)

        # if params has any value which is empty,i.e. if any input value is not found, skip the validation
        if '' in params.values():
            # Exception to return with status as Success and reason as below
            # Intentionally raising as Exception
            raise NonFatalException(
                "Skipping Security Validation as some required parameter's value is BLANK"
            )
        # Validate security only for "DATABASE" datasets
        records = {}
        failed_ds = []
        for dataset in database_dataset_guid:  # if DATABASE dataset, then only validate else skip
            record_count = self.validate_record_count(report_guid + ':' + dataset, params, report)
            if record_count:
                records[dataset] = record_count
        if records:
            for ds in records:
                failed_ds.append(ds)
            raise CVSecurityException(
                f"Datasets {failed_ds} of Report - {report} does not have count of records as 0")
        self.log.info(f"Security Validation of Datasets of 'DATABASE' type Datasets {database_dataset_guid}"
                          f" completed successfully")

    def get_database_dataset_guid(self):
        """ Returns a list of datasets guid which are of type "DATABASE" """
        dataset_guid = []
        if self.report_def:
            for page_no in range(0, len(self.report_def["pages"])):
                ds_dict = self.report_def["pages"][page_no]["dataSets"]["dataSet"]
                for i in range(0, len(ds_dict)):
                    if ds_dict[i]["endpoint"] == "DATABASE":
                        dataset_guid.append(ds_dict[i]["guid"])
        return dataset_guid

    def validate_record_count(self, dataset_guid, params, report):
        """ Validates that no records are shown for dataset specified for a user with no association"""
        recordcount = 0
        validation_columns = ['server', 'servers', 'clients', 'client', 'name',
                              'access node', 'hana client', 'clientgroups', 'client group', 'clientgroup',
                              'client groups', 'client group name', 'server group', 'servergroup', 'server groups',
                              'servergroups', 'company', 'serverid', 'index server', 'agents',
                              'agent', 'agenttype', 'subclient', 'subclients', 'vm groups',
                              'storage policy', 'schedule', 'schedule policy', 'schedulename', 'sp name',
                              'library', 'library name', 'drive', 'drive name', 'mount path', 'media agent',
                              'mediaagent',
                              'backup location', 'backupset', 'hyper-v', 'hypervisor', 'vm',
                              'vmname', 'vm name', 'vm host', 'virtualization client name', 'proxy name', 'virtualization client', 'virtual server',
                              'customer name', 'datasource', 'commcell', 'commcell name', 'commcellid', 'commcell id',
                              'computer', 'commservuniqueid', 'hostname', 'ip address', 'cluster node', 'physical node',
                              'job id', 'last job id', 'failure reason', 'deduplication engine name', 'ddb', 'path',
                              'share owner', 'Tunnel Port', 'Topology Name', 'Group Name']

        # CRE Login with user with no association
        new_cre_api = CustomReportsAPI(
            self.webconsole_name,
            username=self.automation_username,
            password=self.automation_password
        )

        result_json = new_cre_api.get_data(dataset_guid, params)
        key = 'totalRecordCount'

        # if records are found then raise Security Exception
        if result_json[key] != 0:
            if validation_columns:
                for i in range(len(result_json["columns"])):
                    if result_json["columns"][i]["name"]:
                        if (result_json["columns"][i]["name"]).lower() in validation_columns:
                            recordcount = result_json[key]
                            break
        return recordcount

    def check_required_params(self):
        """Checks if there are any required parameters for the report
        Returns:
            a dict of required parameters
                Ex: required = {'parameter name': 'input string of parameter'}
                'input string of parameter' - to fetch values of input using this name
                'parameter name' - this name is used to form url to fetch data
            """
        required = {}  # dict with input id as key and parameter label as value
        for page_no in range(0, len(self.report_def["pages"])):
            ds_dict = self.report_def["pages"][page_no]["dataSets"]["dataSet"]
            for i in range(0, len(ds_dict)):
                # Get a dictionary of "all" Parameters, to check required parameters at Dataset level among them
                param_dict = ds_dict[i]["GetOperation"]["parameters"]
                for j in range(0, len(param_dict)):

                    # Check if "required" tag is present in the parameter dict, if yes, check if it's true:
                    # if both of these conditions are satisfied, add that paramater input string to required dict
                    if "required" in param_dict[j].keys() and param_dict[j]["required"]:
                        required[param_dict[j]["name"]] = param_dict[j]["values"][0].split('.')[1]

            # Check required parameters/inputs at Input level
            if "inputs" in (self.report_def["pages"][page_no]).keys():
                input_dict = self.report_def["pages"][page_no]["inputs"]
                for i in range(0, len(input_dict)):

                    # Check if "required" tag is present in the input dict, check if it's true and not already added in
                    # "required" dict
                    if "required" in input_dict[i].keys():
                        if input_dict[i]["required"] and input_dict[i]["id"] not in required.values():
                            required[input_dict[i]["id"]] = input_dict[i]["id"]

                    # if Timeframe input present in report, add it as required parameter always
                    if input_dict[i]["id"] == "Timeframe" and "Timeframe" not in required.values():
                        required['timeframe'] = 'timeframe'
        return required

    def get_params_values(self, params_list, report):
        """ Gets the values of the required parameters as per input
        Args:
            params_list(dict) : {'parameter name': 'input string of parameter'}
                'input string of parameter' - to fetch values of input using this name
                'parameter name' - this name is used to form url to fetch data
        Returns:
            a dict of parameter name and its value
            """
        params_values = {}
        dataset_value = []
        all_input_value = {}
        if params_list:
            for param, input_string in params_list.items():
                default_value = self.get_default_value(input_string)  # get default value if available
                if default_value and not default_value == 'All':  # if default value is All, we get all values present for that input
                    params_values[param] = default_value
                else:
                    # if fromDataSet is true, fetch input value using rpt.inputs variable
                    if not all_input_value:
                        self.open_report_url(report)
                        all_input_value = self.webconsole.browser.driver.execute_script('return rpt.inputs')
                    if all_input_value and input_string in all_input_value and all_input_value[input_string]['options']:
                        for options in all_input_value[input_string]['options']:
                            try:
                                if options['value']:
                                    # list of all possible values for input_string
                                    dataset_value.append(options['value'])
                            except TypeError:
                                if options:
                                    dataset_value.append(options)
                        # converting list of multiple values to string
                        dataset_value = ','.join(str(i) for i in dataset_value)
                        if len(dataset_value) > 1:
                            dataset_value = self.browser.driver.execute_script(
                                'return encodeURIComponent("%s")' % dataset_value)
                            # Adding [] to parameter key and adding encoded- 1 or multiple values to it
                            params_values[param + '%5B%5D'] = dataset_value
                        else:
                            params_values[param] = dataset_value
                    else:
                        # if input is hidden or rpt.inputs doesn't return any value for the input, add it as Blank
                        params_values[param] = ""
        return params_values

    def get_default_value(self, param):
        """Check if the parameter has default value defined in report definition
        Args:
            param (str): Parameter name, to check default value for it
        Returns:
            default value of the param if exists
            """
        if param.lower() in self.default_mapping.keys():  # if paramater is from mapping, return hardcoded value
            return self.default_mapping[param.lower()]
        else:  # Check default value from <defaultValue>
            for page_no in range(0, len(self.report_def["pages"])):
                if "inputs" in (self.report_def["pages"][page_no]).keys():
                    input_dict = self.report_def["pages"][page_no]["inputs"]
                    for i in range(0, len(input_dict)):
                        if (input_dict[i]["id"]).lower() == param.lower() and "defaultValue" in input_dict[i].keys():
                            def_value = input_dict[i]["defaultValue"]

                            # if input type is date range, encode the value
                            if input_dict[i]["type"] == 'DateRange':
                                unit = input_dict[i]["relativeUnits"][0][0]  # get the unit like days or Months or Year
                                if '-P' not in def_value:  # Check if already encoded
                                    if 'P' not in def_value:  # Ex: 'P7D P0D' is for next 7 days
                                        # if timerange is next n days ex: P0D P0D, don't encode in that case
                                        if unit == 'H' or 'm':
                                            def_value = '-PT%s%s P0D' % (def_value, unit)
                                        else:
                                            def_value = '-P%s%s P0D' % (def_value, unit)

                            # If default value not present and fromDataSet is also false, take first value from
                            # PossibleValues
                            if not def_value and not input_dict[i]["fromDataSet"]:
                                if "possibleValues" in input_dict[i]:
                                    def_value = input_dict[i]["possibleValues"][0]
                            return def_value

    def update_security(self, rpt_id):
        """Shares the report with the dummy user created having no association"""
        # Update security_api.json with report id for which security has to be updated
        for i in self.data['entityAssociated']['entity']:
            i['entityId'] = rpt_id
        ADD_SECURITY_ASSOCIATION = self.commcell._services['SECURITY_ASSOCIATION']
        flag, response = self.commcell._cvpysdk_object.make_request(
            'POST', ADD_SECURITY_ASSOCIATION, self.data
        )
        if flag:
            if response.json() and 'response' in response.json():
                response_json = response.json()['response'][0]
                error_code = response_json['errorCode']
                if error_code != 0:
                    error_message = response_json['errorString']
                    raise SDKException(
                        'Security',
                        '102',
                        'Failed to add associations. \nError: {0}'.format(error_message)
                    )
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self.commcell._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    @test_step
    def install_reports(self):
        """Installing all the store reports"""
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                (report, executor.submit(self.install_report, report))
                for report in self.store_reports
            ]
            finished = {}
            failed = {}
            for report_name, future in futures:
                try:
                    finished[report_name] = future.result(timeout=120)
                except CVWebAPIException as e:
                    self.log.exception(f'Install Failure of report {report_name}: [{e}]')
                    failed[report_name] = {
                        'status': CloudReportsValidator.InstallFailure,
                        'message': str(e),
                        'url': ''
                    }
                except CVSecurityException as e:
                    self.log.exception(
                        f'Report - {report_name} does not have count of records as 0: [{e}]'
                    )
                    failed[report_name] = {
                        'status': CloudReportsValidator.SecurityFailure,
                        'message': str(e),
                        'url': ''
                    }
                except Exception as e:
                    self.log.exception(f'Unknown Install Failure of report {report_name}: [{e}]')
                    failed[report_name] = {
                        'status': CloudReportsValidator.unknown,
                        'message': str(e),
                        'url': ''
                    }
        return finished, failed

    def recheck_will_all_commcell(self):
        """Rechecks by selecting all commcell"""
        viewer = CustomReportViewer(self.webconsole)
        if "CommCell" in viewer.get_all_input_names():
            commcell_input = ListBoxController('CommCell')
            try:
                commcell_input.select_all()
            except:
                pass
            else:
                commcell_input.apply()
                self.webconsole.wait_till_load_complete()
            self.metrics_report.raise_for_no_data_error()

    @test_step
    def validate_report(self, report):
        """Validate report"""
        endpoint_list = []
        report_url = ''
        if self.report_def:
            for page_no in range(0, len(self.report_def["pages"])):
                ds_dict = self.report_def["pages"][page_no]["dataSets"]["dataSet"]
                for i in range(0, len(ds_dict)):
                    endpoint_list.append(ds_dict[i]["endpoint"])
        if "MONITORING_POLICY" not in endpoint_list:
            self.log.info(f"Starting browser validation on report [{report}]")
            self.open_report_url(report)
            self.webconsole.get_all_unread_notifications(expected_count=0)
            return {
                'status': 'Success',
                'message': 'Successfully validated',
                'url': report_url
            }
        else:
            return {
                'status': 'Success',
                'message': 'Report is having Dataset as MONITORING_POLICY, hence report loading Validation skipped',
                'url': report_url
            }

    def open_report_url(self, report):
        """ Open webconsole report url"""
        store_rpt_url = self.store_api.get_package(report, "Reports")["launchURL"]
        report_url = self.webconsole.base_url + store_rpt_url.split("webconsole/")[-1]
        self.browser.driver.get(report_url)
        self.webconsole.wait_till_load_complete()

    def log_cache_summary(self):
        """
         Log Cache Summary
        """
        self.log.info(
            ("." * 5) +
            f" Cache summary ({self.batch_name}): " +
            ("." * 5)
        )
        c_info = self.store_api.get_packages.cache_info()
        self.log.info(f"self.store_api.get_packages(): {c_info}")
        c_info = self.store_api.get_all_categories.cache_info()
        self.log.info(f"self.store_api.get_all_categories(): {c_info}")

    def handle_exception(self, report, e, message, url):
        """
        :param report: report name
        :param e: Exception string
        :param message: message
        :param url: report url
        """
        self.log.error(
            f"\nReport [{report}], " +
            page_object.formatted_error_summary(e).strip()
        )
        self.log.exception(f"Validation failure in {report}: {e}")
        self.failed_reports[report].update(
            {
                'message': message,
                'url': url
            }
        )

    def run(self):
        """Starting method for each process"""
        self.store_api.get_packages("Reports", None, details=True)  # TO build cache
        self.log.info(f'Reports to install [{self.store_reports}]')
        user_sec_api = os.path.join(AUTOMATION_DIRECTORY,
                                    "Reports", "Templates", "security_api.json")
        with open(user_sec_api, encoding='utf-8', errors='ignore') as json_data:
            self.data = json.load(json_data, strict=False)
        for reports in self.store_reports:
            self.delete_report(reports)
        installed_reports, self.failed_reports = self.install_reports()
        sleep(randint(4, 20))
        self.init()
        self.store_api.get_packages.cache_clear()
        validated_reports = {}
        for report in installed_reports:
            try:
                sleep(3)
                try:
                    self.webconsole.clear_all_notifications()
                except ElementNotVisibleException:
                    pass
                self.validate_security(report)
                ret_msg = self.validate_report(report)
                validated_reports[report] = ret_msg

            except CVTimeOutException as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.Timeout}
                message = (
                    f"Timeout occurred, operation=[{e.operation}] "
                    f"wait_time=[{e.timeout_seconds} sec]"
                )
                self.handle_exception(report, e, message, e.url)
            except CVWebNoData as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.NoData}
                self.handle_exception(report, e, e.msg, e.url)
            except CVWebAutomationException as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.Errors}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)
            except CVSecurityException as e:
                self.log.exception(f'Report - {report} does not have count of records as 0: [{e}]')
                self.failed_reports[report] = {'status': CloudReportsValidator.SecurityFailure}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)
            except NonFatalException as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.Success}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)
            except Exception as e:
                self.failed_reports[report] = {'status': CloudReportsValidator.unknown}
                self.handle_exception(report, e, str(e), self.browser.driver.current_url)

        self.log_cache_summary()
        self.close()
        self.log.info(f'{self.p_name} success - {validated_reports}')
        self.log.info(f'{self.p_name} Failure - {self.failed_reports}')
        return validated_reports, self.failed_reports


def p_wrapper(reports, webconsole, uname, pwd, name, queue):
    """Wrapper to create object for each process"""
    validator = CloudReportsValidator(webconsole, uname, pwd, reports, name)
    queue.put(validator.run())


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store reports security"
        self.max_workers = 3
        self.tcinputs = {
            "Failed_only": None
        }
        self.utils = None
        self.automation_username = 'TC60414'
        self.automation_password = 'TC60414#'

    def init(self):
        """
        Initial configuration for the testcase
         """
        self.utils = TestCaseUtils(
            self,
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"]
        )
        self.create_table()
        self.create_user()

    def create_user(self):
        """Creates user and roles"""
        if not self.commcell.users.has_user(self.automation_username):
            self.commcell.users.add(
                self.automation_username,
                self.automation_username,
                "reports@testing.com",
                None,
                self.automation_password
            )
        user_sec_api = os.path.join(AUTOMATION_DIRECTORY, "Reports", "Templates", "security_api.json")
        # with open(user_sec_api, encoding='utf-8', errors='ignore') as json_data:
        #     data = json.load(json_data, strict=False)
        #     for i in data['securityAssociations']['associations'][0]['userOrGroup']:
        #         i['userId'] = self.commcell.users.get(self.automation_username).user_id
        #         i['userName'] = self.automation_username
        #         a_file = open(user_sec_api, mode="w", encoding='utf-8', errors='ignore')
        #         json.dump(data, a_file)
        #         a_file.close()

        with open(user_sec_api, encoding='utf-8', errors='ignore') as json_data:
            data = json.load(json_data, strict=False)
            data['securityAssociations']['associations'][0]['userOrGroup'][0]['userId'] = self.commcell.users.get(
                self.automation_username).user_id
            data['securityAssociations']['associations'][0]['userOrGroup'][0]['userName'] = self.automation_username
            a_file = open(user_sec_api, mode="w", encoding='utf-8', errors='ignore')
            json.dump(data, a_file)
            a_file.close()

    def create_table(self):
        """Create table"""
        sql_string = """
        IF not EXISTS (SELECT * FROM dbo.sysobjects where id = object_id(N'dbo.[StoreReportStatus]')) 
        BEGIN 
            create table StoreReportStatus
                (
                name                nvarchar(Max),
                Status              nvarchar(50),
                Reason				nvarchar(Max),
                url					nvarchar(Max),
                reviewdate			datetime
                );
            End
        """
        self.utils.cs_db.execute(sql_string)

    def get_failed_reports(self):
        """ Get failed reports"""
        sql_string = """
        SELECT Name FROM StoreReportStatus WHERE Status != 'Success'
        """
        reports = []
        result = self.utils.cre_api.execute_sql(sql_string)
        for row in result:
            reports.append(row[0])
        return reports

    def get_reports(self):
        """ Get reports"""
        try:
            failed_only = self.tcinputs['Failed_only']
            if (failed_only == 1 or str(failed_only).lower() == 'true'
                    or str(failed_only).lower() == 'yes'):
                reports = self.get_failed_reports()
            else:
                store = Store(
                    machine=self.commcell.webconsole_hostname,
                    wc_uname=self.inputJSONnode['commcell']["commcellUsername"],
                    wc_pass=self.inputJSONnode['commcell']["commcellPassword"],
                    store_uname=_CONFIG.email.username,
                    store_pass=_CONFIG.email.password
                )
                reports = store.get_reports()
            if not reports:
                return []
            size = math.ceil(len(reports) / self.max_workers)
            return [
                reports[i * size: (i + 1) * size]
                for i in range(math.ceil(len(reports) / size))
            ]
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @staticmethod
    def form_sql(report_name, result):
        """ Forms sql"""
        return f"""
        SELECT @name = '{report_name}'
        IF EXISTS (SELECT name FROM StoreReportStatus WHERE Name = @name)
            UPDATE StoreReportStatus SET Status='{result["status"]}',
             Reason='{result["message"].replace("'", "''")}',
             url='{result["url"]}',reviewdate=GETDATE() WHERE Name=@name
        ELSE
            INSERT INTO StoreReportStatus VALUES(@name,'{result["status"]}',
            '{result['message'].replace("'", "''")}','{result["url"]}', GETDATE())
        """

    @staticmethod
    def form_sql_success(report_name, result):
        """ Forms sql for success """
        status = 'Success'
        return f"""
            SELECT @name = '{report_name}'
            IF EXISTS (SELECT name FROM StoreReportStatus WHERE name = @name)
                UPDATE StoreReportStatus SET Status='{result["status"]}', Reason='',
                url='{result["url"]}',reviewdate=GETDATE() WHERE Name=@name
            ELSE
                INSERT INTO StoreReportStatus VALUES(@name, '{status}','','{result["url"]}', GETDATE())
            """

    def update_db(self, sql_string):
        """ Update database"""
        self.utils = TestCaseUtils(
            self,
            username=self.inputJSONnode['commcell']["commcellUsername"],
            password=self.inputJSONnode['commcell']["commcellPassword"]
        )
        self.utils.cs_db.execute(sql_string)

    def remove_deleted_reports(self):
        """ remove deleted reports """
        sql_string = """
        select name from StoreReportStatus where Reason like 'Package % not found'
        """
        result = self.utils.cre_api.execute_sql(sql_string)
        if result:
            temp = '\n'
            for report in result:
                temp += report[0] + '\n'
            self.log.info(f"Following reports are not present in store: {temp}")
        del_string = """
        Delete from StoreReportStatus where Reason like 'Package % not found'
        """
        self.utils.cs_db.execute(del_string)

    def update_database(self, success_dict, failed_dict):
        """ update database"""
        sql_string = 'DECLARE @name nvarchar(max) \n'
        for rpt, msg in failed_dict.items():
            sql_string += self.form_sql(rpt, msg)
            sql_string += '\n'

        for rpt, msg in success_dict.items():
            sql_string += self.form_sql_success(rpt, msg)
            sql_string += '\n'
        self.log.info(sql_string)
        self.update_db(sql_string)

    def run(self):
        try:
            self.init()
            reports = self.get_reports()
            queues = [Queue() for _ in reports]
            success_dict = {}
            failed_dict = {}
            processes = [
                Process(
                    target=p_wrapper,
                    args=(
                        report,
                        self.commcell.webconsole_hostname,
                        self.inputJSONnode['commcell']["commcellUsername"],
                        self.inputJSONnode['commcell']["commcellPassword"],
                        f"Batch_{index}, {len(report)} reports",
                        queues[index]
                    ),
                )
                for index, report in enumerate(reports)
            ]
            for process in processes:
                self.log.info(f"Spawning new process [{id(process)}]")
                sleep(5)
                process.start()
                self.log.info(f"Spawned new process [{id(process)}], PID [{process.ident}]")
            self.log.info("Collecting results from queue")
            for queue in queues:
                success, failed = queue.get()
                success_dict.update(success)
                failed_dict.update(failed)

            results_str = "\n" + "\n".join([
                "%-65s  : %s" % (rpt, str(msg))
                for rpt, msg in failed_dict.items()
            ]).strip()
            results_str += "\n" + "\n".join([
                "%-65s  : %s" % (rpt, str(msg))
                for rpt, msg in success_dict.items()
            ]).strip()
            self.log.info(results_str)
            self.update_database(success_dict, failed_dict)
            self.remove_deleted_reports()  # remove report packages that are removed from store
            for process in processes:
                self.log.info(f"Closing [{process.ident}]")
                process.join()
                self.log.info(f"Closed [{process.ident}]")
            for rpt, msg in failed_dict.items():
                if msg['status'] == 'Errors':
                    raise CVTestStepFailure('Some reports have failed status')

        except Exception as excep:
            page_object.handle_testcase_exception(self, excep)
