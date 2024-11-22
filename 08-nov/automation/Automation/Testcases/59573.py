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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""


from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.Exchange.exchange import ExchangeClientdetail,\
                                                ExchangeClientlist,\
                                                ApplicationExchangeAgentPage
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole


from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from Web.AdminConsole.Components.table import Table
from Application.AD.smtp import SmtpOps


class TestCase(CVTestCase):
    """Class for executing and verifying Recall Link Validation"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not

                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {
                             "MY_INPUT_NAME": None

                        }

                log     (object)    --  Object of the logger module

        """
        super(TestCase, self).__init__()
        self.name = "Exchange Mailbox Agent : Recall Link Validation"
        self.show_to_user = True
        self.clientname = None
        self.tcinputs = {
            "Mailboxes" : [],
            "ExchangeServers" : None,
            "ServiceAccount" : None,
            "ServiceAccountType" : None,
            "RecallURL" : None,
            "Plan" : None,
            "IndexServer" : None,
            "AccessNodes" : []
            }
        self.apppage = None
        self.browser = None
        self.adminconsole = None

    def setup(self):
        """Setup function of this test case"""
        try:
            # initial connection and login
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']
            self.adminconsole = AdminConsole(self.browser,
                                             self.inputJSONnode['commcell']['webconsoleHostname'])
            self.adminconsole.login(username=username, password=password)
            # navigate to application page
            clientspage = ExchangeClientlist(self.adminconsole)
            clientspage.open_clients_page()
            self.apppage = ApplicationExchangeAgentPage(self.adminconsole)
        except Exception as ex:
            raise CVTestCaseInitFailure(ex)from ex

    def run(self):
        """Run function of this test case"""
        try:
            # check the client and create it if necessary
            self.tcinputs = self.check_client()
            # check mailboxes, add mailbox is required
            client_page = ExchangeClientdetail(self.adminconsole)
            # configure static profile for client
            self.configuration_static_profile(client_page)
            self.verify_configration(client_page)

            mailboxes = self.get_mailboxes(client_page)
            self.check_mailboxes(mailboxes, client_page)
        except Exception as exception_:
            handle_testcase_exception(self, exception_)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)

    @test_step
    def check_client(self):
        """
        check if the client existing or not, if not existing, create new one
        """
        clientname_ = f"ExchangeClient_{self._id}"
        clientspage = ExchangeClientlist(self.adminconsole)
        if "ExistingClientName" in self.tcinputs:
            clientname = self.tcinputs['ExistingClientName']
        else:
            self.log.info("No special client defned, will use default clientname")
            clientname = clientname_
        self.tcinputs['ClientName'] = clientname

        if "KeepClient" in self.tcinputs and clientname in clientspage.get_clients:
            if self.tcinputs["KeepClient"]:
                self.log.debug(f"client {clientname} existing, use this client")
            else:
                self.log.debug(f"cleint {clientname} already existting, will delete it")
                self.adminconsole.select_hyperlink(clientname)
                clientspage.delete_client()
                clientspage.add_client(self.tcinputs)
        else:
            self.log.debug(f"client {clientname} is NOT existing, create new one")
            clientspage.add_client(self.tcinputs)

        self.adminconsole.select_hyperlink(clientname)
        return self.tcinputs


    @test_step
    def configuration_static_profile(self, client_page):
        """
        configure app cleint with static profile
        Args:
        Returns:
        Exceptions:
        """
        if "StaticProfile" in self.tcinputs:
            self.log.debug("start to configure statsic profile for the exchagen client")
            self.adminconsole.access_tab("Configuration")
            accountname = self.tcinputs['ServiceAccount']
            ac_exchange_account_define = [
                {"etype" : "tag", "evalue" : "label",
                 "eargs" : {"text" : "Use static profile"},
                 "action" : "click"},
                {"sleep" : 5},
                {"etype" : "id", "evalue" : "profileName",
                 "input" : self.tcinputs["StaticProfile"]},
                {"etype" : "tag", "evalue" : "button",
                 "eargs" : {"text" : "Save"},
                 "action" : "click"}]
            client_page.configure_static_profile(accountname,
                                                 ac_exchange_account_define,
                                                 self.tcinputs["StaticProfile"])
        else:
            self.log.debug("skip client configuration static profile config")

    @test_step
    def verify_configration(self, client_page):
        """
        verify the client configuration
        Args:
            configuration     dict    configruation from page
        Return:
            match_state    Ture/dict    will return True if configuration is match
                                        will return configuration if not match

        """
        self.log.debug(f"input configuration is {self.tcinputs}")
        configuration = client_page.get_configuration()
        self.log.debug(f"configuration information from gui is {configuration}")
        # have issue to use panelinfo to get index server info
        current_config = {"ExchangeServers" : configuration['general']['Exchange servers'],
                          "ServiceAccount" : configuration['connection']["Email address/User name"][0],
                          "ServiceAccountType" : configuration['connection']["Account type"][0],
                          "RecallURL" : configuration['infrastructure']['Recall service'],
                          "Plan" : configuration['infrastructure']['Server plan'],
                          "AccessNodes" : configuration['infrastructure']['Access nodes']}
        self.log.debug(f"current gui config is {current_config}")

        match_state = True

        for _ in current_config:
            if len(current_config[_].split("\n")) >= 2:
                current_config[_] = current_config[_].split("\n")[0]
            if self.tcinputs[_] != current_config[_]:
                match_state = False
                self.log.debug(f'field {_} is not match, input configure is \
                {self.tcinputs[_]} while gui configure is {current_config[_]}')
            else:
                self.log.debug(f"Client configuration {_} value {self.tcinputs[_]} verified")

        if not match_state:
            self.log.debug("Some configuration are not match, please check log")
            returnvalue = configuration
        else:
            self.log.debug("all configuration are matched")
            returnvalue = match_state
        return returnvalue

    @test_step
    def get_mailboxes(self, client_page):
        """
        get mailboxes list from mailbox tab
        Args:
            mailboxes list    maiblxoes to process
            missing    boolean    True (default), will add the mailbox to client
        Return:
            mailboxes    list    selected mailboxes
        """
        mailboxes_ = self.tcinputs['Mailboxes']
        self.log.debug(f"mailboxes information from input is {mailboxes_}")
        mailboxesname = list(mailboxes_.keys())
        self.log.debug(f"mailboxes to process are {mailboxesname}")

        self.log.debug("get mailboxes from the gui")
        self.adminconsole.access_tab("Mailboxes")
        self.adminconsole.wait_for_completion()
        table_ = Table(self.adminconsole)
        pickedmailbox = table_.get_column_data("Email address")
        self.log.debug(f"There are the existing mailbox in the client {pickedmailbox} ")

        for _ in mailboxesname:
            if _ in pickedmailbox:
                self.log.debug(f"email {_} already picked")
            else:
                self.log.debug(f"email {_} is not in the client, will add it")
                client_page.add_mailbox(_, self.tcinputs['ExchangePlan'])
                self.log.debug(f"email {_} added to the client")

        table_ = Table(self.adminconsole)
        updatedmailbox = table_.get_column_data("Email address")
        self.log.debug(f"Here is updated mailbox list {updatedmailbox}")
        if set(updatedmailbox) >= set(mailboxesname):
            self.log.debug(f"all mailboxes are added to the client")
        else:
            raise CVWebAutomationException(f"""
after add mailbox, here is the result{updatedmailbox}, but the following mailboxes
shoudl be added {mailboxesname})""")
        return mailboxesname

    @test_step
    def check_mailboxes(self, mailboxes, client_page):
        """
        check all provided mailboxes
        Args:
            mailboxes    list    mailboxes
        Returns:
        Exceptions:
        """
        self.log.debug('start to check emails based on mailboxes name')
        exchangeserver = self.tcinputs['ExchangeServers']
        domainname = exchangeserver.split('.')[1]
        self.log.debug(f"setup smtp session to server {self.tcinputs['ExchangeServers']}")
        smtp_ins = SmtpOps(self.tcinputs['ExchangeServers'])
        self.log.debug("start to process indivdiaul email")
        for _ in mailboxes:
            client_page.check_mailbox(_, smtp_ins, domainname, exchangeserver,
                                      self.tcinputs, self.apppage)
