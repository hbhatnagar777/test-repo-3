# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    init_tc()                   --  Testcase step to initiate testcase properties

    create_export_set()         --  Testcase step to create an ExportSet using user1

    share_export_set()          --  Testcase step to share the ExportSet to user2 with all permissions

    search_and_export_items()   --  Testcase step to search and export random items to ExportSet using user2

    validate_download_items()   --  Testcase step to validate the downloaded files from export

    cleanup()                   --  Testcase step to delete the export using user2 and ExportSet using user1

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

"""
import shutil

from cvpysdk.activateapps.constants import ComplianceConstants
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from cvpysdk.exception import SDKException
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.utils.constants import DOWNLOAD_FOLDER_PATH


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "ExportSet Share - CVPysdk - Delete Permission - Compliance Search"
        self.tcinputs = {
            "IndexServer": None,
            "Search": None,
            "ExportCount": None,
            "SharedUser": None,
            "SharedUserPassword": None
        }
        self.export_sets = None
        self.export_set = None
        self.user_2_export_sets = None
        self.user_2_export_set = None
        self.export = None
        self.user_2_export = None
        self.user_2_compliance_search = None
        self.search_items = None
        self.download_path = None
        self.index_server_name = None
        self.export_count = None
        self.query = None
        self.export_name = None
        self.export_set_name = None
        self.user_2_name = None
        self.user_2_password = None
        self.user_2_commcell = None
        self.user_2_activate_helper = None

    @TestStep()
    def init_tc(self):
        """Testcase step to initiate testcase properties"""
        self.index_server_name = self.tcinputs["IndexServer"]
        self.export_count = int(self.tcinputs["ExportCount"])
        self.query = self.tcinputs["Search"]
        self.user_2_name = self.tcinputs["SharedUser"]
        self.user_2_password = self.tcinputs["SharedUserPassword"]
        self.user_2_commcell = Commcell(self.commcell.webconsole_hostname,
                                        self.user_2_name, self.user_2_password)
        self.export_name = "Export_%s" % self.id
        self.export_set_name = "ExportSet_%s" % self.id
        self.export_sets = self.commcell.export_sets
        self.user_2_compliance_search = self.user_2_commcell.activate.compliance_search()
        self.user_2_activate_helper = ActivateSDKHelper(self.user_2_commcell)

    @TestStep()
    def create_export_set(self):
        """Testcase step to create an ExportSet using user1"""
        self.log.info(f"User 1 : Trying to create a new ExportSet {self.export_set_name}")
        if self.export_sets.has(self.export_set_name):
            self.log.info(f"User 1 : ExportSet {self.export_set_name} exists already, deleting and retrying")
            self.export_sets.delete(self.export_set_name)
            self.log.info(f"User 1 : ExportSet {self.export_set_name} deleted")
        self.log.info(f"User 1 : Now creating a new ExportSet {self.export_set_name}")
        self.export_set = self.export_sets.add(self.export_set_name)
        self.log.info(f"User 1 : ExportSet {self.export_set_name} created successfully")

    @TestStep()
    def share_export_set(self):
        """Testcase step to share the ExportSet to user2 with default permissions"""
        self.log.info(f"User 1 : Now sharing the ExportSet to user {self.user_2_name} with default permissions")
        self.export_set.share(self.user_2_name)
        self.log.info(f"User 1 : ExportSet shared with {self.user_2_name} with default permission")

    @TestStep()
    def search_and_export_items(self):
        """Testcase step to search and export random items to ExportSet using user2"""
        self.log.info("User 2 : Running Compliance search with the query now")
        self.search_items = self.user_2_compliance_search.do_compliance_search(
            search_text=self.query, index_server_name=self.index_server_name,
            app_type=ComplianceConstants.AppTypes.FILE_SYSTEM)
        self.log.info(f"User 2 : Total of {len(self.search_items)} items were found for the query")
        self.user_2_export_sets = self.user_2_commcell.export_sets
        self.user_2_export_set = self.user_2_export_sets.get(self.export_set_name)
        self.search_items = self.user_2_export_set.select(
            result_items=self.search_items, no_of_files=self.export_count)
        self.log.info(f"User 2 : Randomly selected {self.export_count} items from the total search result")
        try:
            self.log.info(f"User 2 : Now exporting the search result items to export {self.export_name}")
            restore_job_id = self.user_2_export_set.export_items_to_set(
                export_name=self.export_name, export_items=self.search_items)
            if restore_job_id is not None:
                raise Exception("User 2 : Restore Job started successfully without permissions")
        except SDKException:
            self.log.info("User 2 : Export operation failed as expected, now trying with user1")
        self.log.info(f"User 1 : Now exporting the search result items to export {self.export_name}")
        restore_job_id = self.export_set.export_items_to_set(
            export_name=self.export_name, export_items=self.search_items)
        self.log.info(f"User 1 : Search result items exported to export {self.export_name} successfully")
        if restore_job_id != 0:
            self.log.info(f"User 1 : Waiting for job {restore_job_id} to get complete")
            if not CrawlJobHelper.monitor_job(
                    commcell_object=self.commcell,
                    job=int(restore_job_id)):
                self.log.error("User 1 : Restore job failed to complete")
                raise Exception(f"User 1 : Restore job {restore_job_id} failed to complete")
            self.log.info(f"User 1 : Restore job {restore_job_id} completed successfully")

    @TestStep()
    def validate_download_items(self):
        """Testcase step to validate the downloaded files from export using user2"""
        self.user_2_activate_helper.download_validate_compliance_export(
            export_name=self.export_name,
            export_set_name=self.export_set_name,
            exported_files=self.search_items)

    @TestStep()
    def cleanup(self):
        """Testcase step to delete the export using user2 and ExportSet using user1"""
        try:
            self.log.info("User 2 : Now trying to delete the Export")
            self.user_2_export_set.delete(self.export_name)
            raise Exception(f"User 2 : {self.export_name} deleted successfully")
        except Exception as exp:
            if 'User does not have delete access' not in exp.exception_message:
                self.log.info(f"User 2 : {self.export_name} deletion failed as expected now trying with user1")
        self.log.info("User 1 : Now trying to delete the Export")
        self.export_set.delete(self.export_name)
        self.log.info(f"User 1 : {self.export_name} deleted successfully")
        try:
            self.log.info(f"User 2 : Deleting the ExportSet {self.export_set_name}")
            self.user_2_export_sets.delete(self.export_set_name)
            raise Exception(f"User 2 : ExportSet {self.export_set_name} deleted")
        except Exception as exp:
            if 'User does not have delete access' not in exp.exception_message:
                self.log.info(f"User 2 : {self.export_set_name} deletion failed as expected now trying with user1")
        self.log.info(f"User 1 : Deleting the ExportSet {self.export_set_name}")
        self.export_sets.delete(self.export_set_name)
        self.log.info(f"User 1 : ExportSet {self.export_set_name} deleted")
        self.log.info("Machine User : Deleting the export download files")
        shutil.rmtree(DOWNLOAD_FOLDER_PATH % self.export_name)
        self.log.info("Machine User : Export download folder deleted successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.create_export_set()
            self.share_export_set()
            self.search_and_export_items()
            self.validate_download_items()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == PASSED:
            try:
                self.cleanup()
            except Exception as _exception:
                raise CVTestCaseInitFailure(_exception) from _exception
