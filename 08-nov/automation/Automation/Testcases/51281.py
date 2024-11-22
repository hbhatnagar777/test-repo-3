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

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    ServicePack     --  service pack to be downloaded
                            Example: SP12

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.Helper import adminconsoleconstants as acc
from Web.AdminConsole.adminconsole import AdminConsole
from Install.installer_constants import CURRENT_RELEASE_VERSION
from Install import installer_utils


class TestCase(CVTestCase):
    """Class for updating unix client in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Install- Admin Console- Verify download software using"
                     "third option Service packs and Hotfixes")
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.tcinputs = {
            'ServicePack': 'SP12'
        }
        self.admin_console = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)

    def run(self):
        """Main function for test case execution"""

        try:
            _version = str(CURRENT_RELEASE_VERSION.split('.')[0])
            _service_pack = str(self.tcinputs.get("ServicePack").lower().split("sp")[1])
            _sp_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
            _cu = str(installer_utils.get_latest_cu_from_xml(_sp_to_install))
            sp_version = _version + "." + _service_pack + "." + _cu

            self.deployment_helper.run_download_software(
                download_option=acc.DownloadOptions.GIVEN_SP_AND_HF.value,
                os_to_download=[acc.DownloadOSID.WINDOWS_64.value,
                                acc.DownloadOSID.UNIX_LINUX64.value],
                sp_version=sp_version)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
