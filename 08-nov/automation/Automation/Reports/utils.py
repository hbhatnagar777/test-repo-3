# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Utilities for the TestCase"""

import csv
import hashlib
import ntpath
import os
import shutil
import time

from AutomationUtils.database_helper import MSSQL
from cvpysdk.license import LicenseDetails
from cvpysdk.metricsreport import PrivateMetrics

from AutomationUtils import (
    logger,
    constants,
    mail_box
)
from AutomationUtils.windows_machine import WindowsMachine
from Reports.metricsutils import MetricsServer
from Web.API.customreports import CustomReportsAPI
from Web.API.webconsole import Reports
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import (
    CVTimeOutException,
    CVTestStepFailure,
    CVException
)
from AutomationUtils.config import get_config

_CONFIG = get_config()


class TestCaseUtils:

    """Utilities for the TestCase"""

    def __init__(self, testcase, username=_CONFIG.ADMIN_USERNAME, password=_CONFIG.ADMIN_PASSWORD):
        self.testcase = testcase
        self._username = username
        self._password = password
        self._LOG = logger.get_log()
        self.__cre_api = None
        self.__machine = None
        self.__wc_api = None
        self.__cs_db = None

    @property
    def machine(self):
        if self.__machine is None:
            self.__machine = WindowsMachine()
        return self.__machine

    @property
    def cre_api(self):
        """To access CRE API"""
        if not self.__cre_api:
            self.__cre_api = CustomReportsAPI(
                self.testcase.commcell.webconsole_hostname,
                username=self._username,
                password=self._password
            )
        return self.__cre_api

    @property
    def cs_db(self):
        """To access CRE API"""
        if not self.__cs_db:
            ss_name_suffix = ""
            if 'Windows' in self.testcase.commcell.commserv_client.os_info:
                ss_name_suffix = r'\commvault'
            self.__cs_db = MSSQL(self.testcase.commcell.commserv_hostname + ss_name_suffix,
                                 _CONFIG.SQL.Username,
                                 _CONFIG.SQL.Password,
                                 "commserv")
        return self.__cs_db

    @property
    def wc_api(self):
        if not self.__wc_api:
            self.__wc_api = Reports(
                self.testcase.commcell.webconsole_hostname
            )
        return self.__wc_api

    def handle_testcase_exception(self, excp):
        """Set the result string and status from the exception"""
        handle_testcase_exception(self.testcase, excp)

    def reset_cre(self):
        """resets cre so that next execution will reinitialize the object"""
        self.__cre_api = None

    def reset_temp_dir(self):
        """Truncate the temp dir"""
        temp_dir = self.get_temp_dir()
        self._LOG.info("Recreating directory [%s]", temp_dir)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        time.sleep(4)

    def get_temp_dir(self):
        """Get the temp dir used"""
        return os.path.join(
            constants.TEMP_DIR,
            str(self.testcase.id)
        )

    def get_temp_files(self, ends_with=""):
        """Return the list containing all the temp files"""
        return [
            os.path.join(self.get_temp_dir(), file)
            for file in os.listdir(self.get_temp_dir())
            if file.endswith(ends_with)
        ]

    def poll_for_tmp_files(self, ends_with, timeout=3 * 60, count=1, min_size=100):
        """Wait till temp files are populated

        Set the minimum size in bytes
        """
        end_time = time.time() + timeout
        files = []
        while time.time() < end_time:
            try:
                files = [
                    file
                    for file in self.get_temp_files(ends_with)
                    if os.path.getsize(file) >= min_size
                ]
                if len(files) == count:
                    self._LOG.info(
                        f"Found [{files}] inside [{self.get_temp_dir()}]"
                    )
                    return files
            except OSError:
                pass
        err_str = (
            f"Not enough file with ending with [{ends_with}]; " +
            f"found [{len(files)}]; expecting [{count}]"
        )
        raise CVTimeOutException(
            operation=err_str,
            timeout_seconds=timeout
        )

    def hash(self, file_path):
        """Return the MD5 hash of the specified file"""
        data = open(file_path, "rb").read()
        hash_ = hashlib.md5(data).hexdigest().lower()
        self._LOG.info("Returning [%s] as hash for [%s]", hash_, data)
        return hash_

    def validate_tmp_files(self, ends_with="", count=None, hashes=None, min_size=None):
        """Validate temp files with the criteria args passed

        Args:
            ends_with (str): File extension to look for
            count (int): Number of files to check for
            hashes (list): List of hashes to look for
            min_size (int): Minimum file size
        """
        files = self.get_temp_files(ends_with)
        if count or count == 0:
            if len(files) != count:
                raise CVTestStepFailure(
                    "Not enough files; expected [%s], found [%s]" % (
                        count, len(files)
                    )
                )
        if hashes:
            file_hashes = [self.hash(file) for file in files]
            unknown_hashes = set(hashes) - set(file_hashes)
            if unknown_hashes:
                raise CVTestStepFailure(
                    "No file matching hash [%s]; found files with hash [%s]" % (
                        str(unknown_hashes), str(file_hashes)
                    )
                )
        if min_size:
            file_sizes = [os.path.getsize(file) for file in files]
            if not [file_size for file_size in file_sizes if file_size > min_size]:
                raise CVTestStepFailure(
                    "Files have size less than [%s]; file sizes [%s]" % (
                        str(min_size), str(file_sizes)
                    )
                )

    def wait_for_file_to_download(self, ends_with="", timeout_period=200, sleep_time=1):
        """
        wait for file to be downloaded

        Args:
            ends_with           (str):   Specify the file extension

            timeout_period      (int):          Max time to wait for file to be downloaded

            sleep_time          (int):          Time to sleep in between wait

        """
        i = 0
        self._LOG.info("Waiting for file to be downloaded with extension %s", ends_with)
        while i < timeout_period:
            files = self.get_temp_files(ends_with)
            if not files:
                time.sleep(sleep_time)
            elif files:
                time.sleep(5)
                self._LOG.info("Found files [%s] ", str(files))
                return
            i += sleep_time
        self._LOG.error("Files couldn't be downloaded with extension %s", ends_with)
        raise CVTestStepFailure(f"Time out occurred during {ends_with} file download")

    def wait_for_file_with_path_to_download(self, machine, path, timeout_period=200, sleep_time=1):
        """
            wait for file at given path in the given machine to be downloaded
            Args:
                machine             (obj):            Machine object
                path                (str):         Path of the file
                timeout_period      (int):          Max time to wait for file to be downloaded
                sleep_time          (int):          Time to sleep in between wait
        """
        i = 0
        self._LOG.info(f"Waiting for file with path: {path} to be downloaded")
        while i < timeout_period:
            exists = machine.check_file_exists(file_path=path)
            if exists:
                time.sleep(5)
                self._LOG.info(f"Found file {path}")
                return
            else:
                time.sleep(sleep_time)
            i += sleep_time
        self._LOG.error("File couldn't be downloaded in time")
        raise Exception("Time out occurred during file download")

    def get_csv_content(self, file_name):
        """
        Get csv data from file
        Args:
            file_name: csv file name with path
        Returns(list):csv content in terms of list of rows
        """
        self._LOG.info("Reading csv content of the file [%s]", file_name)
        csv_table_content = []
        with open(file_name, 'r', encoding='utf-8-sig') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csv_reader:
                if not row:
                    continue
                csv_table_content.append(row)
        return csv_table_content

    def get_browser_logs(self, log_level="SEVERE"):
        """ Get browser logs filtered by log level as SEVERE/WARNING/INFO"""
        logs = self.testcase.browser.driver.get_log('browser')
        return [log for log in logs if log["level"] == log_level]

    def private_metrics_upload(self, enable_all_services=False):
        """Performs metrics upload and waits for xml parsing
        Args:
            enable_all_services(bool): Enables all the services
        Returns:
            PrivateMetrics object and MetricsServer object for further use
        """
        try:
            self._LOG.info("Initiating Private metrics upload now and waiting for completion")
            private_metrics = PrivateMetrics(self.testcase.commcell)
            if enable_all_services:
                private_metrics.enable_all_services()
                private_metrics.enable_chargeback(daily=True, weekly=True, monthly=True)
            private_metrics.upload_now()
            private_metrics.wait_for_uploadnow_completion()
            self._LOG.info("Upload completed")
            private_metrics_name = private_metrics.private_metrics_server_name
            metrics_server = MetricsServer(private_metrics_name, self._username, self._password)
            metrics_server.wait_for_parsing(private_metrics.get_uploaded_filename())
            return private_metrics, metrics_server
        except Exception as excep:
            raise CVTestStepFailure(excep)

    def get_direct_dip_filename(self):
        """Gets the last uploaded metrics dip file name
        Returns:
            str: Last uploaded file name
        """
        query = "SELECT value FROM GxGlobalParam  " \
                "WHERE name ='CommservMetricsDirectDipLastCollectionTime'"
        response = self.cre_api.execute_sql(query)
        if not response:
            raise Exception("Metrics direct dip last collection time value "
                            "is not set in the database")
        commcell_id = LicenseDetails(self.testcase.commcell).commcell_id_hex
        if not int(response[0][0]):
            raise Exception("last collection time is 0, Upload didn't complete or failed")
        return "CSS" + "" + str(response[0][0]) + "_" + str(commcell_id) + ".xml"

    def download_mail(self, mail, subject, time_out=180):
        """
        Download the mail into temp/test-case-id directory

        Args:
            mail (mail_box.MailBox): MailBox object to download the mails

            subject        (String): subject of mail to be searched

            time_out          (int): time out period (max 3 minutes)
                                     default:    180
        """
        mails_download_directory = self.get_temp_dir()
        search_object = mail_box.EmailSearchFilter(subject=subject)
        self._LOG.info("looking for the email with subject [%s]", subject)
        end_time = time.time() + time_out
        while time.time() < end_time:
            try:
                mail.download_mails(search_object, mails_download_directory)
                return
            except Exception as e:
                self._LOG.exception(f"Exception while downloading the emails:[{e}]")
                time.sleep(10)
        err_str = "email is not found with the subject [%s]" % subject
        raise CVTimeOutException(time_out, err_str)

    def get_attachment_files(self, ends_with):
        """
        Return list of attachment files present

        Args:
            ends_with  (String) : extension of file

        Returns (list): list of files
        """
        head, tail = ntpath.split(self.poll_for_tmp_files(ends_with="html")[0])
        path = self.machine.join_path(self.get_temp_dir(), "Attachment-" + tail.split(".")[0])
        files = [
            self.machine.join_path(path, file)
            for file in os.listdir(path) if file.endswith(ends_with.lower())
            ]
        if files:
            return files
        else:
            raise CVException("Attachment ending with [%s] is not found in path [%s]" %
                              (ends_with, path))

    def delete_custom_report(self, report_name):
        """
        Delete custom report
        """
        defi = self.cre_api.get_report_definition_by_name(
            report_name, suppress=True
        )
        if defi:
            self.wc_api.delete_custom_report(
                report_name,
                defi["report"]["customReportId"]
            )
        else:
            self._LOG.warning(
                f"API - Report [{report_name}] not found to delete"
            )

    def get_account_global_id(self, company_name):
        """
        Get Account Global ID from commserv DB
        Args:
            company_name: Name of the company_name
        Returns: Account Global ID(list)
        """
        query = f"""
                SELECT UP.attrVal 
                    FROM UMGroups UG Inner Join UMGroupsProp UP
                        ON UG.id = UP.componentNameId 
                            WHERE UG.name = '{company_name}' 
                            AND UP.attrName in ( 'Customer User Group','CASP Partner subuser group')
              
                """
        result = self.cre_api.execute_sql(query)
        return result[0][0]

    def get_company_commcells(self, account_global_id, linked_server):
        """
        Get the commcell id from the table
        Args:
            account_global_id: Global id for a company_name
            linked_server: linked server name in string
        Returns: CommCell ID in hexadecimal
        """
        query = f"""
            SELECT LG.CommCellId 
                FROM [{linked_server}]
                    .[CvLicGen].[dbo].[LACCMCommcellInfo] LG 
                        LEFT OUTER JOIN APP_CommCell C WITH(NOLOCK)
                            ON 
                                REPLACE
                                (
                                    LG.SerialCode + LG.RegistrationCode, '-', ''
                                ) = replace(C.csGUID , '-', '')
                        LEFT OUTER JOIN App_Client CL WITH(NOLOCK)
                            ON C.clientId = CL.id where LG.[AccountGlobalId] 
                                = %s and (LG.SerialCode + LG.RegistrationCode) 
                                    IS NOT NULL and C.aliasName is not null
                """ % account_global_id
        result = self.cre_api.execute_sql(query)
        temp = []
        for commcell in range(len(result)):
            temp.append(result[commcell][0])
        return temp

    def get_migrated_clients(self, client_name):
        """
        verify the given client is migrated or not

        Args:
            client_name: name of the client in string

        Returns: True or False

        """
        query = f""" SELECT NAME FROM APP_Client WITH(NOLOCK) WHERE Name ='{client_name}'AND  origCCId > 2 """
        result = self.cre_api.execute_sql(query)
        return result[0][0]

    @staticmethod
    def assert_comparison(value, expected):
        """Performs a comparison of the value with the expected value"""
        if value != expected:
            raise CVTestStepFailure(
                f"The value: {value} does not match the expected value {expected}")

    @staticmethod
    def assert_includes(value, expected):
        """Performs an assertion for if the value exists in the expected value"""
        if value not in expected:
            raise CVTestStepFailure(
                f"The value: {value} does not match the expected value {expected}")

    def copy_config_options(self, destination_obj, input_type):
        """
        Copies all the parameters specified in testcase input under the given tag to the given object.

        Args:
             destination_obj    (Object): The object where the parameters are copied to.

             input_type         (str)   : The category of inputs which are to be copied.

        Raises:
            Exception:
                if the inputs given don't match up with any attributes of the object provided.
        """
        for testcase_input, value in self.testcase.tcinputs[input_type].items():
            if not hasattr(destination_obj, testcase_input):
                self._LOG.exception("The testcase input \"{0}\" didn't match any properties".format(testcase_input))
                raise Exception("Wrong Testcase input given.")
            setattr(destination_obj, testcase_input, value)