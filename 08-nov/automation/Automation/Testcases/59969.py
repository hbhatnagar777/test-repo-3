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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    _get_mountpath_info()       --  Get mountpath info from library id

    validate_unc2ip_share()     --  To validate mountpath conversion from UNC to Read-Only Dataserver- IP
    
    validate_ip2unc_share()     --  To validate mountpath conversion from Dataserver- IP to Read-Only UNC
    
    _cleanup()                  --  Cleanup the entities created
    
    install_workflow()          --  Install the workflow if it is not installed
    
    open_workflow()             --  When clicked on Open, workflow form should open
    
    populate_inputs()           --  Populates all the required inputs for the workflow
    
    create_entities()           --  create required entities for workflow execution
    
    Input Example:
    "59969": {
        "MediaAgent1": "MediaAgent1Name",
        "MediaAgent2": "MediaAgent2Name",
        "MountPath": "C:\\MP",
        "NetworkPath": "\\\\MA1\\MP",
        "NetworkUserName": "domain\\username",
        "NetworkPassword": "Password"
    }

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.Common.cvbrowser import (Browser, BrowserFactory)
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.Common.page_object import (TestStep, handle_testcase_exception)
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import  AdminConsole
from Server.Workflow.workflowhelper import WorkflowHelper


_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow Change MountPath Sharing"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Change MountPath Sharing workflow"
        self.tcinputs = {
            'MediaAgent1': None,
            'MediaAgent2': None,
            'MountPath': None,
            'NetworkPath': None,
            'NetworkUserName': None,
            'NetworkPassword': None
        }
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = None
        self.forms = None
        self.workflow_helper = None
        self.workflow = "Change Mount Path Sharing"
        self.disk_library = None
        self.mountpath = None
        self.unc_path = None
        self.disk_lib_obj = None
        self.mp_info = None

    def _get_mountpath_info(self, library_id):
        """
        Get mountpath info from library id
        Args:
            library_id (int)  --  Library Id

        Returns:
            str - mountpath_display_name
        """
        self.log.info("Get mountpath info")
        query = f"""
                SELECT '['+ cli.displayName + '] ' +MDC.Folder + ' (' + MP.MountPathName + ')' as MountPathDisplayName
                FROM MMMountPath MP,  MMMountPathToStorageDevice MP2SD, MMDeviceController MDC, APP_Client cli,
                        (SELECT MIN(MDC.DeviceControllerID) AS DeviceControllerId 
                        FROM MMDeviceController MDC GROUP BY MDC.DeviceId) FOLDER
                WHERE MP.LibraryId = {library_id}
                AND MP.MountPathTypeId = 4
                AND MP.MountPathId = MP2SD.MountPathId
                AND MP2SD.DeviceId = MDC.DeviceId
                AND MDC.DeviceControllerId = FOLDER.DeviceControllerId
                AND (MDC.DeviceAccessType & 2 = 2 OR MDC.DeviceAccessType & 4 = 4)
                AND MDC.ClientId = cli.id
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur != ['']:
            return cur[0]
        self.log.error("No mountpath entries present")
        raise Exception("Invalid LibraryId")

    def validate_unc2ip_share(self, library_id):
        """
        To validate mountpath conversion from UNC to Read-Only Dataserver IP
        Args:
            library_id (int)  --  Library Id
        """
        self.log.info("Validating mountpath conversion from UNC to Read-Only Dataserver IP")
        query = f"""
                    SELECT 1
                    FROM MMMountPath MP,  MMMountPathToStorageDevice MP2SD, MMDeviceController MDC
                    WHERE MP.LibraryId = {library_id}
                    AND MP.MountPathTypeId = 4
                    AND MP.MountPathId = MP2SD.MountPathId
                    AND MP2SD.DeviceId = MDC.DeviceId
                    AND MDC.DeviceAccessType & 20 = 20 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("Mountpath conversion from UNC to Read-Only Dataserver IP failed")
            raise Exception("Mountpath conversion from UNC to Read-Only Dataserver IP failed")
        self.log.info("Mountpath conversion from UNC to Read-Only Dataserver IP was success")

    def validate_ip2unc_share(self, library_id):
        """
        To validate mountpath conversion from Dataserver IP to Read-Only UNC
        Args:
            library_id (int)  --  Library Id
        """
        self.log.info("Validating mountpath conversion from Dataserver IP to Read-Only UNC")
        query = f"""
                    SELECT 1
                    FROM MMMountPath MP,  MMMountPathToStorageDevice MP2SD, MMDeviceController MDC
                    WHERE MP.LibraryId = {library_id}
                    AND MP.MountPathTypeId = 4
                    AND MP.MountPathId = MP2SD.MountPathId
                    AND MP2SD.DeviceId = MDC.DeviceId
                    AND MDC.DeviceAccessType & 4 = 4
                    AND (MDC.CredentialAssocId <> 0 OR MDC.UserName<>'')   AND  MDC.Folder LIKE '\\_%' 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("Mountpath conversion from Dataserver IP to Read-Only UNC failed")
            raise Exception("Mountpath conversion from Dataserver IP to Read-Only UNC failed")
        self.log.info("Mountpath conversion from Dataserver IP to Read-Only UNC was success")

    def _cleanup(self):
        """Cleanup the entities created"""
        self.log.info("********************** CLEANUP STARTING **************************")
        try:
            self.log.info("Deleting library: %s if exists", self.disk_library)
            if self.commcell.disk_libraries.has_library(self.disk_library):
                self.commcell.disk_libraries.delete(self.disk_library)
                self.log.info("Deleted library: %s", self.disk_library)
        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))
        self.log.info("********************** CLEANUP COMPLETED *************************")

    def init_tc(self):
        """Login to store"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(username=_STORE_CONFIG.Cloud.username, password=_STORE_CONFIG.Cloud.password)
            self.forms = Forms(self.adminconsole)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def install_workflow(self):
        """Install the workflow if it is not installed"""
        pkg_status = self.store.get_package_status(self.workflow, category="Workflows")
        if pkg_status == "Install":
            self.store.install_workflow(self.workflow, refresh=True)
        else:
            self.log.info("Already workflow is installed")

    @test_step
    def open_workflow(self):
        """When clicked on Open, workflow form should open"""
        self.store.open_package(self.workflow, category="Workflows")

    @test_step
    def populate_inputs(self, conversion_type):
        """
            Populates all the required inputs for the workflow
            Args:
            conversion_type (str)  --  Conversion type that should be performed
        """
        if self.forms.is_form_open(self.workflow) is False:
            raise CVTestStepFailure(f"Forms page is not open after clicking open on [{self.workflow}]")

        # workflow first window
        if conversion_type == 'unc2ip':
            self.forms.select_radio_value("Conversion type that should be performed on the Controller(s):",
                                          "Convert Regular - Network Path To Read-Only DataServer - IP")
        else:
            self.forms.select_radio_value("Conversion type that should be performed on the Controller(s):",
                                          "Convert DataServer - IP To Read-Only Regular - Network Path")
        self.forms.click_action_button("OK")
        workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)
        workflow_helper.workflow_job_status(self.workflow, expected_state="waiting")

        # workflow second window
        self.forms.select_dropdown("Libraries: ", self.disk_library)
        self.forms.click_action_button("Next")
        workflow_helper.workflow_job_status(self.workflow, expected_state="waiting")

        # workflow third window
        if conversion_type == 'unc2ip':
            self.forms.select_searchable_dropdown_value("Mount Path(s): ", self.mp_info)
            self.forms.select_dropdown_list_value("Controller MediaAgent(s): ", [self.tcinputs['MediaAgent2']])
        else:
            self.forms.select_searchable_dropdown_value("Mount Path:", self.mp_info)
            self.forms.select_dropdown_list_value("Controller MediaAgent(s):", [self.tcinputs['MediaAgent2']])
            self.forms.set_textbox_value("Network Folder Path:", self.tcinputs['NetworkPath'])
            self.forms.set_textbox_value("User Name:", self.tcinputs['NetworkUserName'])
            self.forms.set_textbox_value("Password:", self.tcinputs['NetworkPassword'])
        self.forms.click_action_button("Next")
        workflow_helper.workflow_job_status(self.workflow, expected_state="waiting")

        # workflow fourth window
        self.forms.click_action_button("Continue")
        workflow_helper.workflow_job_status(self.workflow, expected_state="completed")

    def create_entities(self):
        """create required entities for workflow execution"""
        self.disk_lib_obj = MMHelper(self).configure_disk_library(self.disk_library, self.tcinputs['MediaAgent1'],
                                                                  self.mountpath)
        self.disk_lib_obj.share_mount_path(self.tcinputs['MediaAgent2'], self.unc_path, mount_path=self.mountpath,
                                           username=self.tcinputs['NetworkUserName'],
                                           password=self.tcinputs['NetworkPassword'])
        self.mp_info = self._get_mountpath_info(self.disk_lib_obj.library_id)

    def setup(self):
        """Setup function of this test case"""
        self.disk_library = '%s_disklib-MA(%s)' % (str(self.id), self.tcinputs['MediaAgent1'])
        self._cleanup()
        ma_machine = Machine(self.tcinputs['MediaAgent1'], self.commcell)
        self.mountpath = ma_machine.join_path(self.tcinputs['MountPath'], 'Automation', str(self.id), 'MP1')
        self.unc_path = ma_machine.join_path(self.tcinputs['NetworkPath'], 'Automation', str(self.id), 'MP1')

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_entities()
            self.init_tc()
            self.install_workflow()
            self.open_workflow()
            self.populate_inputs(conversion_type="unc2ip")
            self.validate_unc2ip_share(self.disk_lib_obj.library_id)
            self.forms.open_workflow(self.workflow)
            self.populate_inputs(conversion_type="ip2unc")
            self.validate_ip2unc_share(self.disk_lib_obj.library_id)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
