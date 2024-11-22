from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import hashlib
from urllib.parse import urlparse

from cvpysdk.exception import SDKException

from AutomationUtils import config
from Reports.utils import TestCaseUtils
from Web.API.customreports import CustomReportsAPI
from Web.Common.exceptions import CVTestStepFailure
from Web.WebConsole.Store.storeapp import get_store_config


class StoreUtils(TestCaseUtils):

    def __init__(self, testcase):
        super().__init__(testcase)
        self._STORE_CONFIG = self.get_store_config()
        self.__STORE_SERVER_API = None
        self.tc_config = config.get_config()

    @property
    def store_server_api(self):
        if not self.__STORE_SERVER_API:
            self.__STORE_SERVER_API = CustomReportsAPI(
                self.get_store_server(),
                protocol="https",
                port=443,
                username=self._STORE_CONFIG.ADMIN_USERNAME,
                password=self._STORE_CONFIG.ADMIN_PASSWORD
            )
        return self.__STORE_SERVER_API

    def delete_alert(self, alert_name, suppress=False):
        self._LOG.info(f"Deleting alert [{alert_name}]")
        alert_id = self.get_alert_id(alert_name, suppress)
        if alert_id != -1:
            xml = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <App_QueryOperationRequest queryOp="2">
            <queryEntity queryId="%s" queryName="%s"/>
            </App_QueryOperationRequest>""" % (
                alert_id,
                alert_name
            )
            ret = self.testcase.commcell._qoperation_execute(xml)
            if ret.get("errorCode", -1) != 0 and not suppress:
                raise CVTestStepFailure(
                    "Unable to delete alert [%s]" % alert_name
                )
            else:
                self._LOG.info(f"Alert [{alert_name}] not found to delete")

    def delete_workflow(self, workflow_name):
        """
        Args:
             workflow_name (str): Name as set in Commserv.WF_Definition.name
        """
        self._LOG.info(f"Deleting workflow [{workflow_name}] using API")
        self.testcase.commcell.workflows.delete_workflow(workflow_name)

    def delete_tool(self, tool_name, suppress=False):
        try:
            self._LOG.info(f"Delete tool [{tool_name}] using qoperation")
            id_ = self.get_tool_id(tool_name, suppress)
            if id_ == 0:
                return
            self._LOG.info(f"Deleting tool [{tool_name}]")
            payload = (
                f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>""" +
                f"""<App_ToolOperationReq opType="2"><toolInfoEx toolId="{id_}"/>""" +
                f"""</App_ToolOperationReq>"""
            )
            output = self.testcase.commcell._qoperation_execute(payload)
            if "errorMessage" in output.keys():
                raise CVTestStepFailure(
                    f"Unable to delete tool [{tool_name}]"
                )
        except SDKException as e:
            if e.exception_module != "Response" and e.exception_id != "102":  # empty response is expected
                raise e

    def verify_hash(self, file_path, hash_value):
        """
        Verify is the file pointed by file_path has hash hash_value

        Args:
            file_path (str): Path to file
            hash_value (str): MD5 hash string
        """
        data = open(file_path, "rb").read()
        _hash = hashlib.md5(data).hexdigest()
        self._LOG.info(
            "Returning [%s] as generated hash for [%s]" % (
                _hash, file_path
            )
        )
        if _hash.lower() == hash_value.lower():
            raise CVTestStepFailure(
                "File [%s] does not hash [%s]; expected hash value [%s]" % (
                    file_path, hash_value.lower(), _hash.lower()
                )
            )

    def set_report_revision(self, rpt_name, revision="$Revi" + "sion: 1.0.0.9 $"):
        """
        Set the report revision to given string

        Args:
            rpt_name (str): Name of the package
            revision (str): Revision String to set
        """
        self._LOG.info(f"Changing {rpt_name}'s revision to {revision}")
        rpt_data = self.cre_api.get_report_definition_by_name(rpt_name)
        rpt_data["revision"] = revision
        self.cre_api.update_report_definition(rpt_name, rpt_data)

    def set_workflow_revision(self, wf_name, revision="$Revi" + "sion: 1.0.0.9 $"):
        self.cs_db.execute(
            f"""
            UPDATE WF_Definition SET revision = '{revision}'
            WHERE Name like '{wf_name}'
            """
        )

    def set_alert_revision(self, alert_name, revision="$Revi" + "sion: 1.0.0.9 $"):
        """Set alert revision"""
        self._LOG.info(f"Changing [{alert_name}]'s revision to [{revision}]")
        try:
            defi =  self.cre_api.execute_sql(
                f"""
                SELECT xmlInfo
                FROM NTQueryList
                WHERE queryName LIKE '{alert_name}'
                """
            )
            defi = defi[0][0].split("""revision=""")
            pre = defi[0]
            post = defi[1].rsplit("$\"")[-1]
            revision = f"revision=\"{revision} \""
            self.cs_db.execute(
                f"""
                UPDATE NTQueryList
                SET xmlInfo = '{pre + revision + post}'
                WHERE queryName LIKE '{alert_name}'
                """
            )
        except Exception as e:
            raise CVTestStepFailure(
                f"Unable to change [{alert_name}]'s revision to [{revision}]"
            ) from e

    def get_store_server(self):
        """
        Retrieve the machine name from cloudURL
        """
        url = self.get_cloud_url()
        return urlparse(url).hostname

    def get_cloud_url(self):
        """
        Return the cloud URL used by the webconsole
        """
        return self.tc_config.Store_Server

    @staticmethod
    def get_store_config():
        return get_store_config()

    def get_alert_id(self, alert_name, suppress=False):
        try:
            sql = f"""
                    SELECT queryId 
                    FROM NTQueryList 
                    WHERE queryName LIKE '{alert_name}'"""
            return self.cre_api.execute_sql(sql)[0][0]
        except IndexError:
            if suppress:
                return -1  # To mimic null integer object
            else:
                raise CVTestStepFailure(
                    f"Unable to find alert [{alert_name}] inside "
                    f"NTQueryList"
                )

    def get_pkgs_from_server_db(self, category='%', sub_category='%', price='%', version='%'):
        """Get packages from server db"""
        sql = f"""
        SELECT 
            PackageName
        FROM 
            DCPackage 
                INNER JOIN 
            DCCategory
                ON	DCCategory.CategoryId = DCPackage.CategoryId 
                    AND DCCategory.CategoryName LIKE '{category}'
                INNER JOIN
            DCSubCategory
                ON DCSubCategory.SubCategoryId = DCPackage.SubCategoryId
                    AND DCSubCategory.SubCategoryName LIKE '{sub_category}'
                INNER JOIN
            DCProductVersion
                ON DCPackage.ProductVersionId = DCProductVersion.ProductVersionId
        WHERE 
            DCPackage.PackageStatus = 0
            AND DCPackage.PriceWeightage LIKE '{price}'
            AND DCProductVersion.Name LIKE '{version}'
        """
        ret = [
            pkg[0] for pkg in self.store_server_api.execute_sql(sql)
        ]
        self._LOG.info(
            f"Store DB Found [{len(ret)}] packages matching category [{category}],"
            f"sub_category [{sub_category}], price[{price}], version[{version}]"
        )
        return ret

    def get_subcategories_from_server_db(self, category):
        """Returns all subcategories with at least one package on it"""
        sql = f"""
        SELECT SubCategoryName
        FROM 
            DCSubCategory
                INNER JOIN 
            DCCategory
                ON DCCategory.CategoryId = DCSubCategory.CategoryId
                INNER JOIN
            DCPackage
                ON DCPackage.SubCategoryId = DCSubCategory.SubCategoryId 
                    AND DCCategory.CategoryId = DCSubCategory.CategoryId
        WHERE 
            CategoryName LIKE '{category}'
                AND DCPackage.PackageStatus = 0
        GROUP BY 
            SubCategoryName
        HAVING 
            COUNT(DCPackage.PackageName) > 1
        """
        ret = [
            catg[0] for catg in self.store_server_api.execute_sql(sql)
        ]
        self._LOG.info(
            f"Store DB has [{len(ret)}] sub-categories "
            f"inside category [{category}]"
        )
        return ret

    def get_version_filters_from_db(self, category_name, subcategory_name='%'):
        sql = f"""
        SELECT DISTINCT productversionname
        FROM DCPackages
        WHERE 
            PackageStatus = 0
            AND categoryname LIKE '{category_name}'
            And subcategoryname like '{subcategory_name}'
        """
        ret = [
            catg[0] for catg in self.store_server_api.execute_sql(sql)
        ]
        self._LOG.info(
            f"Store DB has [{ret}] quick filters for [{category_name}] - [{subcategory_name}]"
        )
        return ret

    def get_alert_revision(self, alert_name):
        try:
            sql = f"""
            SELECT xmlInfo 
            FROM NTQueryList 
            WHERE queryName LIKE '{alert_name}'"""
            output = self.cre_api.execute_sql(sql, desc=f"Get [{alert_name}]'s revision")
            defi = output[0][0]
            return defi[defi.find("\"$Rev" + "ision"): defi.find("$\"/>")] + "$"
        except IndexError:
            raise CVTestStepFailure(
                f"Unable to find alert [{alert_name}]"
            )

    def get_workflow_revision(self, wf_name):
        try:
            revision = self.cre_api.execute_sql(
                f"""
                SELECT revision
                FROM WF_Definition
                WHERE name LIKE '{wf_name}'
                """
            )
            return revision[0][0]
        except IndexError:
            raise CVTestStepFailure(
                f"Unable to get [{wf_name}]'s revision"
            )

    def validate_if_tool_exists(self, tool_name):
        """Validate if the tool exists"""
        self.get_tool_id(
            tool_name,
            suppress=False,
            desc="Check if tool exists inside APP_QuickRunTools"
        )

    def get_tool_id(
            self, tool_name, suppress,
            desc="Get tool ID from APP_QuickRunTools"):
        """Get tool ID"""
        alert_id = self.cre_api.execute_sql(
            f"""
            SELECT id
            FROM APP_QuickRunTools
            WHERE aliasName LIKE '{tool_name}'
            """,
            desc=desc
        )
        if alert_id:
            return alert_id[0][0]
        else:
            if suppress:
                return 0  # maintain return type compatibility
            else:
                raise CVTestStepFailure(
                    f"Tool [{tool_name}] not found inside APP_QuickRunTools"
                )

    def has_workflow(self, wf_name):
        wf_defi = self.cre_api.execute_sql(
            f"""
            SELECT name
            FROM WF_Definition
            WHERE name LIKE '{wf_name}'
            """,
            desc=f"Search for workflow [{wf_name}] inside WF_Definition"
        )
        if not wf_defi:
            raise CVTestStepFailure(
                f"Workflow [{wf_name}] not found inside WF_Definition"
            )

    def verify_if_alert_exists(self, alert_name):
        query_name = self.cre_api.execute_sql(
            f"""
            SELECT queryName
            FROM NTQueryList
            WHERE queryName LIKE '{alert_name}'""",
            desc=f"Check if [{alert_name}] alert exists inside NTQueryList"
        )
        if len(query_name) != 1:
            raise CVTestStepFailure(
                f"Alert [{alert_name}] not found inside CommServ.NTQueryList"
            )

    def validate_for_premium_status(self, package_name):
        """Check if package has free status"""
        result = self.store_server_api.execute_sql(
            f"""
            SELECT PackageName
            FROM DCPackage
            WHERE PackageName like '{package_name}' and PriceWeightage = '1'""",
            desc=f"Check if Package [{package_name}] is premium inside DCPackage"
        )
        if not result:
            raise CVTestStepFailure(
                "[%s] does not exist or does not belong to free status"
                % package_name
            )

    def validate_for_free_status(self, package_name):
        """
        Check if package has free status
        """
        result = self.store_server_api.execute_sql(
            f"""
            SELECT PackageName
            FROM DCPackage
            WHERE PackageName LIKE '{package_name}' 
                AND PriceWeightage = '0'
                AND PackageStatus = 0""",
            desc=f"Check if package [{package_name}] price is Free inside DCPackage"
        )
        if not result:
            raise CVTestStepFailure(
                "[%s] does not exist or does not belong to free status"
                % package_name
            )

    def validate_if_package_exists(self, package_name):
        self._LOG.info(
            f"Check if [{package_name}] exists inside DCPackage Table"
        )
        result = self.store_server_api.execute_sql(
            f"""
            SELECT PackageName
            FROM DCPackage
            WHERE PackageName LIKE '{package_name}' 
                AND PackageStatus = 0""",
            desc=f"Check if Report exists by name [{package_name}]"
        )
        if not result:
            raise CVTestStepFailure(
                f"Package [{package_name}] does not exist inside DCPackage"
            )

    def poll_till_auto_update(self):
        from Web.Common.cvbrowser import BrowserFactory
        from Web.WebConsole.webconsole import WebConsole
        with BrowserFactory().create_browser_object(name="AutoUpdate") as browser:
            with WebConsole(browser, self.testcase.commcell.webconsole_hostname) as wc:
                wc.goto_store()
                update_url = "webconsole/softwarestore/checkStoreUpdates.do"
                url = f"http://{self.testcase.commcell.webconsole_hostname}/{update_url}"
                self._LOG.info(f"Opening auto-update URL [{url}]")
                wc.browser.driver.get(url)
                resp = wc.browser.driver.find_element(By.XPATH, "//*").text
                if """<msg errorCode="0""" not in resp:
                    raise CVTestStepFailure(
                        "Unexpected response during auto-update; " +
                        resp[resp.find("<msg"): resp.find("/>") + 2]
                    )
                wc.goto_store(direct=True)

    def modify_report_and_update_revision(self, report_name):
        self.set_report_revision(
            report_name,
                revision=f"$Revi" + "sion: 1.0.0.9 M<9999999>$"
        )

    def modify_workflow_and_update_revision(self, workflow_name):
        self.set_workflow_revision(
            workflow_name,
            revision=f"$Revi" + "sion: 1.0.0.9 M<9999999>$"
        )
