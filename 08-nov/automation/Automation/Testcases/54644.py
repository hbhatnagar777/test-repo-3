# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    tear_down()     --  Tear down function to delete automation generated data

    run()           --  Main function for test case executions

"""
from time import time, sleep

from AutomationUtils.cvtestcase import CVTestCase
from Application.AD.ms_azuread import AzureAd

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.AD.ad import ADClientsPage
from Web.AdminConsole.AD.azuread import AzureADPage

class TestCase(CVTestCase):
    """ class to run admin console testing for Azure ad agent"""

    test_step = TestStep()

    def __init__(self):
        """ initial class
        Properties to be initialized:
        name            (str)        -- name of this test case
        applicable_os   (str)    -- applicable os for this test case
        product         (str)    -- applicable product for AD
        """
        super().__init__()
        self.name = "Admin console basic operation for Azure AD"
        self.tcinputs = {
            "AgentName" : "Azure AD",
            }

        self.browser = None
        self.driver = None
        self.adminconsole = None
        self.aad_ins = None
        self.adclientspage = None
        self.azureadpage = None
        self.aad_types = None
        self.clientname = None

    @test_step
    def full_backup(self):
        """
        run full backup and check existing azure ad objects
        """
        self.adminconsole.refresh_page()
        aad_credential = [self.tcinputs['TenantName'],
                          self.tcinputs['AdminUser'],
                          self.tcinputs['AdminPassword'],
                          self.tcinputs['ClientId'],
                          self.tcinputs['ClientPass']]
        self.log.debug(f"here is the azure ad connection credential: {aad_credential}")
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.aad_types = self.tcinputs['types']
        self.azureadpage = AzureADPage(self.adminconsole, self.commcell)
        aad_objs_ini = self.aad_ins.group_objs_check(types=self.aad_types)
        for type_ in self.aad_types:
            self.log.debug(f"There are total {len(aad_objs_ini[type_])} azure\
                             ad {type_} objects from azure directory.")
        self.azureadpage.backup(backuptype="Full")
        for type_ in self.aad_types:
            self.log.debug(f"check {type_} from browse window")
            totalitem = self.azureadpage.browse(type_, self.clientname)
            self.log.debug(f"here are {totalitem} objects in type {type_}")
            if len(aad_objs_ini[type_]) == totalitem:
                self.log.info(f"{type_} objects find match number. \
                                total number is {totalitem}")
            else:
                self.log.info(f"browse return {totalitem} objects while azure ad\
                                return {len(aad_objs_ini[type_])} objects")
        return aad_objs_ini

    @test_step
    def inc_backup(self, init_objs):
        """
        create new object based on type and run inc job to check
        Args:
            init_objs    list    azure ad objects before incremental job
        """
        self.log.info("start to test inc job for azure ad")
        timestamp = int(time())
        inc_objs = self.aad_ins.group_objs_create(types=self.aad_types,
                                                  prestring=f"inc_{timestamp}")
        self.log.debug(f"addtional objects are created:{inc_objs}")
        sleep(20)
        self.azureadpage.backup()
        for type_ in self.aad_types:
            totalitem = self.azureadpage.browse(type_, self.clientname)
            self.log.debug(f"here are {totalitem} objects in type {type_}")
            if len(init_objs[type_]) != totalitem:
                self.log.debug(f"after create new object, there are {totalitem}\
                                 in browse windows")
                newobjs_count = totalitem - len(init_objs[type_])
                self.log.debug(f"new {newobjs_count} is backup")
            else:
                self.log.debug(f"seem the result is match {totalitem}")
        return inc_objs

    @test_step
    def restore(self, objs):
        """
        delete new inc objects then run restore
        Args:
            objs        dict    objecst list in each types
        """
        self.log.info("will delete new objects and run restore job")
        self.log.debug(f"will delete the following {objs}")
        before_delete = self.aad_ins.group_objs_check(types=self.aad_types)
        for type_ in self.aad_types:
            self.aad_ins.type_operation(type_, "delete", objs=objs[type_])
            sleep(30)
            deleted_objs = self.aad_ins.deleted_obj_list(type_)
            self.log.debug(f"here is the deleted objects {deleted_objs}")
        after_delete = self.aad_ins.group_objs_check(types=self.aad_types)

        for type_ in self.aad_types:
            self.log.debug(f"There areb {len(before_delete[type_])} objs\
                             in {type_} before delete")
            self.log.debug(f"There are {len(after_delete[type_])} objs\
                             in {type_} after delete")
            objs_name = []
            if isinstance(objs[type_], list):
                for item in objs[type_]:
                    objs_name.append(item.display_name)
            else:
                objs_name.append(objs[type_].display_name)
            self.log.debug(f" conver the objs to name for cv restore {objs_name}")
            self.azureadpage.restore(self.clientname, type_, objs_name)
        after_restore = self.aad_ins.group_objs_check(types=self.aad_types)
        for type_ in self.aad_types:
            self.log.debug(f"There are {len(after_restore[type_])} objs in {type_} after restore")

    def cleanup(self, objs):
        """
        clean up objs created in the test
        Args:
            objs        dict    objecst list in each types
        """
        self.log.info(f"remove the {objs} from azure ad")
        for type_ in self.aad_types:
            try:
                self.aad_ins.type_operation(type_, "delete", objs=objs[type_])
            except:
                self.log.info(f"clean up objects failed, please manually check {objs}")
        self.log.debug("clean up job is done")

    def setup(self):
        """ prepare the setup environment"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.adminconsole = AdminConsole(self.browser,
                                             self.inputJSONnode['commcell']['webconsoleHostname'])
            self.adminconsole.login(username=username, password=password)
            self.log.info("login to command center page")
            self.driver = self.browser.driver

            self.adclientspage = ADClientsPage(self.adminconsole)
            self.adminconsole.navigator.navigate_to_activedirectory()
            self.log.info("select cilent name")
            self.clientname = self.adclientspage.aad_pick_clientname(self.tcinputs, self.id)



            self.adclientspage.select_client(self.clientname)

            self.aad_types = self.tcinputs['types']
        except Exception as ex:
            raise CVTestCaseInitFailure(ex) from ex

    def run(self):
        """ run test case steps"""
        try:
            ini_objs = self.full_backup()
            inc_objs = self.inc_backup(ini_objs)
            self.restore(inc_objs)
        except Exception as exception_:
            handle_testcase_exception(self, exception_)
        finally:
            self.log.info("run phase is completed")
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
            self.cleanup(inc_objs)

    def tear_down(self):
        """tear down when the case is completed, include error handle"""
        # check existing aad objects
        self.log.info("start tear down phase")
