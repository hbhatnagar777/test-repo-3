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

    wait_for_job_completion()    -- wait the job completion




    cleanup()    -- remove all objects created by test cases

    ad_pick_subcilent()    -- pick up the subclient from ad agent page

    full_backup()    -- run full backup testing

    inc_backup()    -- run inc backup testing

    restore()    -- restore inc objects after desletion

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure

from Web.AdminConsole.AD.ad import ADClientsPage, ADPage, CvAd
from Application.AD.exceptions import ADException

class TestCase(CVTestCase):
    """ Class for executing AD admin console operation"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
        """
        super().__init__()
        self.name = "AD agent basic operation with command center"
        self.tcinputs = {}

        self.browser = None
        self.driver = None
        self.adminconsole = None
        self.adclientspage = None
        self.adclientpage = None
        self.ad_ins = None
        self.adformat_content = None
        self.subclientname = None
        self.cvad = None
        self.ad_browse_base = None

        self.tcinputs = {
            "MachineFQDN": None,
            "MachineUserName": None,
            "MachinePassword": None
            }

    def cleanup(self, objs):
        """
        delete all objects created in the test case
        Args:
            objs    (list):    ad objects created in test case
        """
        self.ad_ins.cv_ugo_delete(objs, entrypoint =self.adformat_content)

    @test_step
    def ad_pick_subclient(self, default=False):
        """
        check subclient, create it if subclient is not existing
        Args:
            default    (boolean):   pick default subclient first
        """
        if default:
            self.log.debug("will use default subclient")
            subclientname = "default"
        else:
            self.adclientpage = ADPage(self.adminconsole, self.commcell)
            if "SubclientName" in self.tcinputs:
                subclientname = self.tcinputs['SubclientName']
                self.log.debug(f"use input subclient name {subclientname}")
            else:
                subclientname = f"TC_{self.id}"
                self.log.debug(f"use default subclient name {subclientname}")
            self.log.debug(f"select subclient {subclientname}")

            if "KeepSubclient" in self.tcinputs:
                self.log.debug("will keep exisitng subclient")
                if subclientname in self.adclientpage.subclients():
                    self.log.debug(f"find the correct subclient {subclientname}")
                else:
                    raise ADException("testcase", self._id,
                                      f"Subcient {subclientname} is not existing")
            else:
                if subclientname in self.adclientpage.subclients():
                    self.log.debug(f"subclient {subclientname} existing, delete it")
                    self.adclientpage.ad_delete_subclient(subclientname)
                    self.adminconsole.refresh_page()
                self.adclientpage.ad_add_subclient(subclientname,
                                                   self.tcinputs['Plan'],
                                                   self.tcinputs['Content'])
                self.adminconsole.refresh_page()
                self.log.debug(f"subclient {subclientname} is created")
        return subclientname

    @test_step
    def full_backup(self):
        """
        Test ad full backup
        """
        objs = self.ad_ins.ugo_package(entrypoint=self.adformat_content,
                                        prestring =f"{self.id}_b")
        self.adclientpage.backup(self.subclientname, backuptype ="Full")
        self.cvad.ad_browse_check(self.subclientname,
                                  self.tcinputs['Content'],
                                  self.adformat_content)
        self.log.debug(f"new ad objects are {objs}")
        self.adclientpage.browse_to_subclient(self.tcinputs['ClientName'])
        return objs

    @test_step
    def inc_backup(self):
        """
        Test ad inc backup
        """
        self.log.info("create more objects before incremntal job")
        objs = self.ad_ins.ugo_package(entrypoint=self.adformat_content,
                                        prestring =f"{self.id}_i")
        self.adclientpage.backup(self.subclientname)
        self.cvad.ad_browse_check(self.subclientname,
                                  self.tcinputs['Content'],
                                  self.adformat_content)
        self.adclientpage.browse_to_subclient(self.tcinputs['ClientName'])
        return objs

    @test_step
    def restore(self, restoreobjs):
        """
        Test ad restore
        Args:
            restoreobjs    (list):    ad objects to restore
        """
        self.ad_ins.cv_ugo_delete(restoreobjs, entrypoint =self.adformat_content)
        self.log.debug(f"the following objects are deleted {restoreobjs}")
        browse_objects, objects_name = self.adclientpage.format_ad_to_browse(restoreobjs)
        compare_, status = self.cvad.ad_check_objs(objects_name, self.adformat_content)
        if not status:
            self.log.debug(f"all objects {objects_name} are deleted")
        else:
            self.log.debug(f"delete result in comparing, check result manually {compare_}")

        self.adclientpage.restore(self.subclientname,
                                  self.ad_browse_base,
                                  self.tcinputs['Content'],
                                  browse_objects)
        self.adclientpage.browse_to_subclient(self.tcinputs['ClientName'])

        compare_, status = self.cvad.ad_check_objs(objects_name, self.adformat_content)
        if status:
            self.log.debug(f"all objects {objects_name} are restored")
        else:
            self.log.debug(f"restore result in comparing, check result manually {compare_}")

    def setup(self):
        """Setup the basic class for test case"""
        # initial connection and login
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.log.info("open the browser")
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.adminconsole = AdminConsole(self.browser,
                                             self.inputJSONnode['commcell']['webconsoleHostname'])
            self.adminconsole.login(username, password)
            self.log.info("login to command center page")
            self.driver = self.browser.driver

            self.log.info("navigate to virtulization page")
            adminpage = self.adminconsole.navigator
            adminpage.navigate_to_activedirectory()
            self.log.info("select client")
            self.adclientspage = ADClientsPage(self.adminconsole)
            self.adclientspage.select_client(self.tcinputs['ClientName'])
            self.log.info("select subclient")
            self.subclientname = self.ad_pick_subclient()

            self.cvad = CvAd(self.adclientpage, self.tcinputs)
            self.ad_ins = self.cvad.ad_connect()
            self.adformat_content = self.cvad.ad_content_format_convert()
            self.log.debug(f"correct ad format entrypoint is {self.adformat_content}")
            self.ad_browse_base = "/".join(self.ad_ins.basedn.split(",")[::-1])
            self.log.debug(f"browse window will use this for domain {self.ad_browse_base}s")
        except Exception as ex:
            raise CVTestCaseInitFailure(ex) from ex

    def run(self):
        """Run the script steps"""
        try:
            base_objs = self.full_backup()
            inc_objs = self.inc_backup()
            self.restore(inc_objs)
        except Exception as exception_:
            handle_testcase_exception(self, exception_)
        finally:
            self.log.info("run phase is completed")
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
            try:
                self.cleanup(inc_objs)
                self.cleanup(base_objs)
            except:
                self.log.debug("clean up is not completed, please do manual cleanup")
    def tear_down(self):
        """tear down the test case"""
        self.log.debug("tear down process started")
