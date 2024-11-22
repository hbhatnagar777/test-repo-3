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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""



from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.AdminConsole.Hub.constants import HubServices, ADTypes

from Web.AdminConsole.AD.ad import ADClientsPage
from Web.AdminConsole.AD.azuread import AzureADPage, CvAad

class TestCase(CVTestCase):
    """ Class for executing AD basic validation on metallic"""

    test_step = TestStep()

    def __init__(self):
        """Initial the class"""
        super().__init__()
        self.name = "AD agent acceptance on metallic"
        self.tcinputs = {}

        self.browser = None
        self.driver = None
        self.config = None
        self.adminconsole = None
        self.adclientpage = None
        self.adclientspage = None
        self.cvad = None
        self.cvaad = None
        self.aad_clientname = None
        self.metallicad = None
        self.aad_ins = None
        self.aad_types  = None
        self.azureadpage = None
        self.clean_up_objs = {"ad_inc" : None,
                              "ad_base" : None,
                              "aad_objs" : None}
        self.tenantname = None
        self.tenantuser = None
        self.tenantpassword = None
        self.plan = None
        self.content = None
        self.utils = TestCaseUtils(self)
        self.custompkg_directory = None
        self.servicecatalog = None

        self.tcinputs = {
            "NewAADclient" : False,
            "NewTenant": False,
            "KeepAADclient": False,
            "Metallic": True,
            "ReactUI": False
        }


    def aad_create_client(self):
        """
        create azure ad client if necessary
        """
        aad_clientname = f"AAD_{self.id}_manual"
        self.aad_clientname = f"{self.tenantname}_{aad_clientname}"
        allclients = self.adclientspage.get_ad_clients()
        self.log.debug(f"here is the clients for ad {allclients}")
        self.log.debug(f"will check the azure ad client {self.aad_clientname}")
        if self.aad_clientname in allclients and self.tcinputs['NewAADclient']:
            self.log.debug("azure ad client is existing, delete it first")
            self.adclientspage.aad_delete(self.aad_clientname)
            allclients = self.adclientspage.get_ad_clients()
            self.log.debug(f"{self.aad_clientname} should be deleted. \
                            Here is the list of client {allclients}")

        if self.aad_clientname in allclients:
            self.log.debug("azure ad client is there, skip creation")
            self.adclientspage.select_client(self.aad_clientname)
        else:
            self.log.debug("will create azure ad client from service catalog v2")
            self.adminconsole.navigator.search_nav_by_id("Service Catalog","navigationItem_serviceCatalogV2")
            self.servicecatalog.start_azureAD_trial()
            self.adclientspage.aad_creation_metallic_react(aad_clientname, self.tcinputs)

    @test_step
    def aad_full_backup(self):
        """
        run full backup and check existing azure ad objects
        """
        return self.cvaad.aad_simple_backup(backuptype="Full", clientname=self.aad_clientname)

    @test_step
    def aad_inc_backup(self, init_objs):
        """
        create new object based on type and run inc job to check
        Args:
            init_objs    (list):    azure ad objects before incremental job
        """
        return self.cvaad.aad_simple_backup(backuptype="Incremental", objs=init_objs, clientname=self.aad_clientname)

    @test_step
    def aad_restore(self, objs):
        """
        delete new inc objects then run restore
        Args:
            objs        (dict):    objecst list in each types, example:
        """
        return self.cvaad.aad_simple_restore(objs, clientname=self.aad_clientname)

    def setup(self):
        """prepare the environment"""
        self.config = get_config()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.custompkg_directory)
        self.browser.open()
        self.log.info("open the browser")
        self.driver = self.browser.driver
        self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.tenantuser = self.tcinputs['TenantUser']
        self.tenantpassword = self.tcinputs['TenantPassword']
        self.tenantname = "".join(self.tenantuser.split("\\")[0].split("-"))

        self.adminconsole.login(self.tenantuser, self.tenantpassword)
        self.log.info("login to metalllic page")
        self.adminconsole.wait_for_completion(wait_time=60)

        self.servicecatalog = ServiceCatalogue(self.adminconsole, HubServices.ad, app_type=ADTypes.aad)
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.adminconsole.navigator.navigate_to_activedirectory()

    def run(self):
        """ Main function for test case """
        try:
            self.adminconsole.navigator.navigate_to_activedirectory()
            self.log.info("Start azure ad agent testing")
            self.azureadpage = AzureADPage(self.adminconsole)
            self.cvaad = CvAad(self.azureadpage, self.tcinputs)
            self.aad_create_client()

            aad_ini_objs = self.aad_full_backup()
            aad_inc_objs = self.aad_inc_backup(aad_ini_objs)
            self.aad_restore(aad_inc_objs)
            self.clean_up_objs['aad_objs'] = aad_ini_objs
        except Exception as exception_:
            handle_testcase_exception(self, exception_)
        finally:
            self.log.info("run phase is completed")
            self.log.debug("switch back to agentview")
            try:
                self.adminconsole.select_breadcrumb_link_using_text("Active Directory")
            except:
                self.log.debug("in sp3201 have issue to switch to agent view")
                self.adminconsole.navigator.navigate_to_activedirectory()
                self.adclientspage.switch_to_app()
                self.adminconsole.wait_for_completion()

            if self.tcinputs['KeepAADclient']:
                self.log.debug("will keep azure ad client")
            else:
                self.log.debug("delete aad client")
                self.adclientspage.aad_delete(self.aad_clientname)
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """tear down the test case"""
        self.log.debug("tear down process started")
        try:
            cleanlist = ["ad_inc", "ad_base", "aad_objs"]
            for _ in cleanlist:
                if self.clean_up_objs[_]:
                    self.cvad.ad_cleanup(self.clean_up_objs[_])
        except:
            self.log.debug("clean up is not completed, please do manual cleanup")