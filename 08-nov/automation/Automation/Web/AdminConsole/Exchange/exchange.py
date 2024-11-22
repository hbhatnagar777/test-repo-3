# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module will operation exchange client related operation
"""
from time import sleep

from Web.Common.exceptions import CVWebAutomationException

from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AD.page_ops import check_element, check_dialog, page_ops,\
                                        dialog_window,\
                                        check_button_text, select_single, check_rows,\
                                        check_link_text, check_span_link,\
                                        dropdown_pick, check_span_text
from Web.AdminConsole.Exchange.outlook_owa import OutlookOWA, wc_preview_email,\
                                                email_compare,\
                                                quicklink_removeexchange
from Web.Common.page_object import PageService
from .constants import AC_EXCHANGE_CLIENT_TYPE, AC_EXCHANGE_CLIENT_DELETE_INPUT


class ExchangeClientlist():
    """ Exchange clients page"""

    def __init__(self, admin_console):
        """
            Initial exchange clients page
        """
        self._admin_console = admin_console
        self.driver = admin_console.driver
        self.log = admin_console.log

    @property
    def get_clients(self):
        """
        get all exchange clients
        """
        servers = {}
        table_ = Table(self._admin_console)
        servers = table_.get_column_data("Name")
        return servers

    @PageService()
    def add_client(self, clientinput):
        """
        create a new exchange client
        Args:
            clientinput dict exchange client information
        """
        self.log.debug(f"Here is the client information {clientinput}")
        self._admin_console.select_hyperlink("Add")
        self._admin_console.select_hyperlink("Exchange archiving")
        # page 1
        ac_exchange_create_page1 = [{"etype" : "tag", "evalue" : "input",
                                     "eargs" : {"attribute" : {"name" : "serverName"}},
                                     "input" : clientinput['ClientName']},
                                    {"etype" : "id", "evalue" : "serverPlan",
                                     "select" : clientinput['Plan']},
                                    {"button" : "Next"}]
        page_ops(self.driver, ac_exchange_create_page1)
        self._admin_console.wait_for_completion()
        # page 2
        if check_element(self.driver, "id", "indexServer"):
            # working for sp21 and early
            indexserver_op = {"etype" : "id", "evalue" : "indexServer",
                              "input" : clientinput['IndexServer']}
        else:
            # working for sp22 and newer
            indexserver_op = {"etype" : "tag", "evalue" : "label",
                              "eargs" : {"text" : "Index server"},
                              "parent" : True,
                              "selectmulti" : [{"input-model" : "addMailbox.indexServerList"},
                                               clientinput['IndexServer']]}
        ac_exchange_create_page2 = [indexserver_op,
                                    {"selectmulti" : ["accessNodes", clientinput['AccessNodes']]},
                                    {"etype" : "id", "evalue" : "jobResultDirectory",
                                     "input" : clientinput['JobResultUNC']},
                                    {"etype" : "id", "evalue" : "recallService",
                                     "input" : clientinput['RecallURL']},
                                    {"button" : "Next"}]
        page_ops(self.driver, ac_exchange_create_page2)
        self._admin_console.wait_for_completion()
        #page 3
        ac_exchange_account_define = [{"etype" : "id", "evalue" : "serviceType",
                                       "select" : clientinput['ServiceAccountType']},
                                      {"etype" : "id", "evalue" : "exchangeAdminSmtpAddress",
                                       "input" : clientinput['ServiceAccountEmail']},
                                      {"etype" : "id", "evalue" : "userName",
                                       "input" :  clientinput['ServiceAccount']},
                                      {"etype" : "id", "evalue" : "password",
                                       "input" :  clientinput['ServiceAccountPassword']},
                                      {"etype" : "id", "evalue" : "confirmPassword",
                                       "input" :  clientinput['ServiceAccountPassword']},
                                      {"etype" : "tag", "evalue" : "button",
                                       "eargs" : {"text" : "Add"},
                                       "action" : "click"}]
        if clientinput['ExchangeType'] in AC_EXCHANGE_CLIENT_TYPE:
            if clientinput['ExchangeType'] == "Exchange On-premises":
                check_element(self.driver, "id", "onPremises").click()
                eservers = check_element(self.driver, "tag", "textarea",
                                         ** {"attribute" : {"name" : "exchangeServers"}})
                eservers.clear()
                eservers.send_keys(clientinput['ExchangeServers'])
                check_link_text(self.driver, "Add").click()
                self._admin_console.wait_for_completion()
                dialog_window(self.driver, ac_exchange_account_define)
                check_button_text(self.driver, "Finish")
            elif clientinput['ExchangeType'] == "Exchange Hybrid":
                check_element(self.driver, "id", "exchangeOnlineHybrid").click()
            else:
                check_element(self.driver, "id", "exchangeOnlineWithOnPremisesAD").click()

        else:
            raise CVWebAutomationException(f"the input exchange type is not valid {clientinput}")
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_client(self):
        """
        delete client from exchange
        Args:
            clientname    string    clientname to operate
        """
        client_page = ExchangeClientdetail(self._admin_console)
        client_page.deleteclient()

    @PageService()
    def open_clients_page(self):
        """ open the clients page"""
        nav_ = self._admin_console.navigator
        nav_.navigate_to_exchange()

class ExchangeClientdetail():
    """ exchange client page information"""

    def __init__(self, admin_console):
        """
        Initial exchange client page
        Args:
            driver     obj    selenium driver
        """
        self._admin_console = admin_console
        self.driver = admin_console.driver
        self.log = admin_console.log

    def _exchange_job(self, username, apppage, type_, clientname, skipjobdetail):
        """
        run archive job
        Args:
            username    str    username to archive
            apppage    object    apppage object,
            type_     str    job type, choose from
                                [archive, cleanup]
            clientname str    clientname
            skipjobdetail    boolean    skip job detail or not
        Return:
        Excetions:
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab("Mailboxes")
        table_ = Table(self._admin_console)
        table_.select_rows([username])
        if type_ == "archive":
            self.log.info(f"start to run {type_} job")
            table_.access_action_item(username, "Archive")
            ModalDialog(self._admin_console).click_submit()
        elif type_ == "cleanup":
            self.log.info(f"start to run {type_} job")
            table_.access_action_item(username, "Run Jobs")
            self._admin_console.select_hyperlink("Clean up")
            ModalDialog(self._admin_console).click_submit()
            self._admin_console.wait_for_completion()
        jid = self._admin_console.get_jobid_from_popup()
        self.log.debug(f"{type_} job id is {jid}")
        job_detail = self._job_check(jid, apppage, skipjobdetail)
        self.log.debug(f"here is the job details: {job_detail}")
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()
        self.log.info(f"end of run {type_} job")
        self._admin_console.wait_for_completion()
        self._admin_console.navigator.navigate_to_exchange()     
        self._admin_console.select_hyperlink(clientname)

    @PageService()
    def browse_message(self, username, folder="Inbox", email=None):
        """
        browse emails
        Args:
            username    list    mailboxes need to check
            folder    string     "Inbox" (default) check email in inbox
            emails    dict    email narrow options
        Return:
            email_content    list    all the email found
            totalcount    int    total number in the browse window
        """
        # open browse page
        self._admin_console.access_tab("Mailboxes")
        table_ = Table(self._admin_console)
        table_.select_rows([username])
        self._admin_console.select_hyperlink("Restore")
        self._admin_console.select_hyperlink("Restore messages")
        self._admin_console.wait_for_completion()
        self.log.debug(f"browse window for {username} is opened")

        # open the folder in browse window
        self._browse_openfolder(folder)
        self._admin_console.wait_for_completion()
        self.log.debug(f"{folder} view is openeed")

        # check email count
        # additional individual email checking, not required now.
        email_content = check_element(self.driver, "class", "page-details-list")
        if check_element(email_content, "class", "grid-no-data-message"):
            self.log.debug(f"There are no email found in {folder}")
            totalcount = 0
        else:
            # check the total email in this folder
            totalcount_ = check_element(self.driver, "class", "ui-grid-pager-count")
            self.log.debug(f"found the totalcount string {totalcount_.text}")
            if totalcount_.text.find("of") >= 0:
                self.log.debug(f"there are multiple pages, check {totalcount_.text}")
                totalcount = totalcount_.text.split("of")[1].split('items')[0].strip()
            else:
                self.log.debug(f"all emails list in one page, but not total item in page")
                goodrows = check_rows(email_content)
                totalcount = len(goodrows)-1
            self.log.debug(f"we found  {totalcount} itmes in browse windows")
        if email:
            self.log.debug("need a function to narrow down the email")
        return email_content, totalcount

    @PageService()
    def check_mailbox(self, mail_, smtp_ins, domainname, exchangeserver,
                      clientinput, apppage):
        """
        check indivdual mailbox
        Args:
            mail_    str    mailbox name
            smtp_ins    obj    smtp instance to send email
            domainname    str    domain name use to create email
            exchangeserver    str    excahnge server to check owa
        Returns:
        Excpetions:
        """
        # check email in current mailbox in browse windows
        self.log.debug(f"start to process email {mail_}")
        clientname = clientinput['ClientName']
        username = mail_.split("@")[0]
        password = clientinput["Mailboxes"][mail_]

        if clientinput['KeepClient'] and "ClientName" in clientinput:
            self.log.debug(f"This is a existing client, check already backup emails")
            _, before_archive_totalcount = self.browse_message(username)
            check_link_text(self.driver, clientname).click()
        else:
            before_archive_totalcount = 0
        self.log.debug(f"""
before send new email
    there are total {before_archive_totalcount} emails backuped in inbox folder""")
        self.log.info('send some new emails through smtp protocol')

        # keep get error when I fech job detail in sp21
        if "SkipJobDetail" in clientinput:
            skipjobdetail = clientinput['SkipJobDetail']
        else:
            skipjobdetail = False

        owainfo = self._owa_popup_email(smtp_ins, username, mail_, password,
                                        domainname, exchangeserver,
                                        apppage, clientinput)
        self.log.info(f"here is the owa info {owainfo}")
        emails = self._owa_get_email(apppage, owainfo)
        newemails = [_ for _ in emails if _['quicklook'] is None]
        self.log.debug(f"there are {len(newemails)} without quicklook")
        # run archive job
        self._exchange_job(username, apppage, "archive", clientname, skipjobdetail)

        # check archive email in browse window and find new archived email
        _, after_archive_totalcount = self.browse_message(username)
        self.log.debug(f"""
After archive job
    there are total  {after_archive_totalcount} eamils backuped in inbox folder""")
        check_link_text(self.driver, clientname).click()

        # found new emails after archive job
        newemailcount = int(after_archive_totalcount)-int(before_archive_totalcount)
        self.log.debug(f"found {newemailcount} new emails")
        if newemailcount == len(newemails):
            self.log.debug(f"there are {newemailcount} email get backuped")
        else:
            raise CVWebAutomationException(f"""
email are not match after backup,emails without quicklook is {len(newemails)},
but backup new email is {newemailcount}""")

        # run clean up job
        self._exchange_job(username, apppage, "cleanup", clientname, skipjobdetail)

        # get eamils with quicklook link
        self.log.info("start to collect quicklook link in owa")
        cleanup_emails = apppage.owa_getemails(owainfo)
        self.log.debug(f"there are {len(emails)} in user mailbox")
        newemailsubjects = [_['subject'] for _ in newemails]
        newemailonly = [_ for _ in cleanup_emails if _['subject'] in newemailsubjects]
        self.log.debug(f"I found the following new email after clean up: {newemailonly}")

        # check the quicklink preview email
        self._web_check_quicklink_emails(newemailonly, apppage)

    @PageService()
    def add_mailbox(self, mailbox, plan):
        """
        add mailbox to the subclient
        """
        self.log.debug(f"add {mailbox} to the client")
        self._admin_console.access_tab("Mailboxes")
        if check_link_text(self.driver, "Add"):
            self.log.debug("in sp22 setup,we need to click Add from the action menu")
            self._admin_console.select_hyperlink("Add")
        check_span_link(self.driver, "Add Mailbox").click()
        self._admin_console.wait_for_completion()
        dialog_ = check_element(self.driver, "tag", "div",
                                ** {"attribute" : {
                                    "uib-modal-window" : "modal-window"}})
        sleep(20)
        if check_link_text(dialog_, "Refresh"):
            check_link_text(dialog_, "Refresh").click()
            self.log.debug("need to refresh the page to get mailbox list")
            self._admin_console.wait_for_completion()
            sleep(30)
        else:
            self.log.debug("no need to refresh, the email list should be loaded")
            self._admin_console.wait_for_completion()
        table_ = Table(self._admin_console)
        self.log.debug(f"found the following mailboxes {table_.get_table_data()}")
        check_element(dialog_, "id", "searchInput").send_keys(mailbox)
        self._admin_console.wait_for_completion()
        table_ = Table(self._admin_console)
        self.log.debug(f"found the following mailboxes {table_.get_table_data()}\
                         with search {mailbox}")
        table_.select_all_rows()
        # check mail plan with better element
        if check_element(dialog_, "id", "exchangePlan_isteven-multi-select_#2"):
            # work for sp21 and early
            select_single(check_element(dialog_, "id",
                                        "exchangePlan_isteven-multi-select_#2"), plan)
        else:
            select_single(check_element(dialog_, "id", "exchangePlan_inline"), plan)
        check_button_text(dialog_, "Save")
        self._admin_console.wait_for_completion()
        table_ = Table(self._admin_console)
        self.log.debug(f"here is the emails after we add {mailbox}")
        if mailbox in table_.get_column_data("Email address"):
            self.log.debug(f"{mailbox} already added to the client list")
        else:
            raise CVWebAutomationException(f"here is the emails in client {table_.get_table_data()}")

    @PageService()
    def _browse_openfolder(self, folder):
        """
        open folder in current user mailbox
        Args:
            mailbox    list    mailboxes need to check
            folder    string     "Inbox" (default) check email in inbox
        """
        folder_content = check_element(self.driver, "class", "browse-tree")
        # check if there are multiple mailbox or single mailbox in the clinet
        folder_root_ = check_element(folder_content, 'class', "crop",
                                     ** {"text" : "User Mailbox"})
        if folder_root_:
            self.log.debug("There are only one mailbox in the subclient or\
             multiple mailboxes are selected")
            child_ = check_element(folder_content, "class", "children")
            if child_:
                if len(child_.text.split("\n")) == 1:
                    mailbox_ = child_.text
                    self.log.debug(f"click user mailbox {mailbox_} to open all folders")
                    check_span_text(child_, mailbox_).click()
                    self._admin_console.wait_for_completion()
                    folder_content = child_
                else:
                    self.log.debug(f"There are mutliple mailboxes, here is the mailboxes {child_}")
                    raise CVWebAutomationException(child_)
                self.log.debug(f'borwse root is {folder_root_.text}')

                folders = check_element(folder_content, "class", "children").text.split("\n")
                self.log.debug(f"here is the folder list in current page {folders}")
                if folder in folders:
                    folder_ = check_element(folder_content, "tag", "span",
                                            ** {"attribute" : {"title" : folder}})
                    self.log.debug(f"found the folder {folder}")
                    folder_.click()
                else:
                    raise CVWebAutomationException(f"folder name is {folder} ")
            else:
                self.log.debug(f"There is no email found or archived on this subclient")

    @PageService()
    def _job_check(self, jid, apppage, skipjobdetail=False):
        """
        cehck job status based on the job id
        Args:
            commcell_ obj    commcell object
            jid    int    job id from web console
            skipjobdetail    boolean    skip job detail or not
        Return:
            job_details    dict    detail of job information
        Exception:
            401    int    job is not completed
        can't use the Jobs
        """
        self.log.debug(f"check the job status {jid}")

        job_ = Jobs(apppage.adminconsole)
        job_details = job_.job_completion(job_id=jid,
                                          skip_job_details=skipjobdetail)
        self.log.debug(f"here is the job detail {job_details}")
        return job_details

    @PageService()
    def deleteclient(self):
        """ delete client from client page"""
        action_item = check_element(self.driver, "class", "cv-main-bar-dropdown-menu")
        self.log.debug("start to release license for the agent")
        try:
            dropdown_pick(action_item, "Release license")
            diag_ = ModalDialog(self)
            diag_.click_submit()
            self._admin_console.wait_for_completion()
        except:
            self.log.debug(f"try to release the license but failed")
        action_item = check_element(self.driver, "class", "cv-main-bar-dropdown-menu")
        self.log.debug("start to delete the agent")
        dropdown_pick(action_item, "Delete")
        self._admin_console.wait_for_completion()
        diag_title = check_element(check_dialog(self.driver), "class", "modal-header")
        if diag_title.text == "Delete Client":
            self.log.debug("The diag window before spp22 doens't have confirm")
            ModalDialog(self).click_submit()
        else:
            self.log.debug("The diag window from sp22 need confirm information")
            dialog_window(self.driver, AC_EXCHANGE_CLIENT_DELETE_INPUT)
        self._admin_console.wait_for_completion()

    @PageService()
    def get_configuration(self, edit=False):
        """
        get clinet configuration
        Args:
            edit    boolean    False(default) just read the configuration
                                True, update the configuration if not match
        Return:
            configuration    dict    configuration of the client
        """

        self._admin_console.access_tab("Configuration")
        configuration = {}
        configuration['general'] = PanelInfo(self._admin_console, title="General").get_details()
        self.log.debug(f"general information is {configuration['general']}")
        self.log.debug("start to process connection content panel")
        table_ = Table(self._admin_console)
        configuration['connection'] = table_.get_table_data()
        self.log.debug(f"connection information is {table_.get_table_data()}")
        self.log.debug("start to process infrastructure content panel")
        configuration['infrastructure'] = PanelInfo(self._admin_console,
                                                    title="Infrastructure settings").get_details()
        self.log.debug(f"infrastructure information is {configuration['infrastructure']}")
        if edit:
            self.log.debug("will need function to edit the configuration")
        return configuration

    @PageService()
    def configure_static_profile(self, accountname, ac_exchange_account_define,
                                 staticfilename):
        """ configure static profile
        Args:
            accountname    str     system account name
            ac_exchange_account_define    dict    systme account define
            staticfilename    dict    static profiel name
        """
        table_ = Table(self._admin_console)
        if accountname in table_.get_column_data("Email address/User name"):
            table_.access_action_item(accountname, "Edit")
            accountdefine = ac_exchange_account_define
            self._admin_console.wait_for_completion()
            if check_element(self.driver, "tag", "label",
                             ** {"text" : "Profile name"}):
                profilename_ = check_element(self.driver, "id", "profileName")
                profilename_.clear()
                profilename_.send_keys(staticfilename)
                check_element(self.driver, "tag", "button",
                              ** {"text" : "Save"}).click()
            else:
                dialog_window(self.driver, accountdefine)
        else:
            raise CVWebAutomationException(table_.get_column_data("Email address/User name"))

    def _owa_popup_email(self, smtp_ins, username, email_, password,
                         domainname, exchangeserver,
                         apppage, clientinput):
        """
        populate eamils
        Args:
            smtp_ins    obj    smtp instance to send email
            owa_ins    obj    owa instance to handel exchange owa operation
            username    str    username to login owa
            domainname    str    domain name use to create email
            exchangeserver    str    excahnge server to check owa
        Returns:
        Exceptions:
        """
        owainfo = {"url" : f"https://{exchangeserver}/owa",
                   "username": f"{domainname}\\{username}",
                   "password" : password}
        self.log.debug("clean up the inbox first")
        apppage.owa_folderclean(owainfo)
        self.log.debug(f"start to send eamil to {email_}")
        smtp_ins.email_ts1k(email_)
        smtp_ins.email_folder2email(email_,
                                    clientinput['TestDataPath'],
                                    group=5, atta=True)
        return owainfo

    def _owa_get_email(self, apppage, owainfo):
        """
        get email information from owa
        Args:
            owa_ins    obj    owa instance to hadnle exchange owa operation
        Returns:
        Excpetions:
        """
        emails = apppage.owa_getemails(owainfo)
        self.log.debug(f"here are the new emails {emails}")
        return emails

    def _web_check_quicklink_emails(self, newemails, apppage):
        """
        check quicklink emails content
        Args:
        Returns:
        Excpetions:
        """
        browser = apppage.browser
        driver = apppage.driver
        for ind_, _ in enumerate(newemails):
            self.log.debug(f"start to check {ind_} email")
            if _['quicklook'] is not None:
                self._admin_console.wait_for_completion()
                browser.open_new_tab()
                adminconsole_tab = self.driver.window_handles[0]
                preview_tab = self.driver.window_handles[1]
                driver.switch_to.window(preview_tab)
                self._admin_console.wait_for_completion()
                self.log.debug(f"quick link url is {_['quicklook']}")
                url = quicklink_removeexchange(_['quicklook'])
                self.log.debug(f"the real url is {url}")
                driver.get(url)
                self._admin_console.wait_for_completion()
                self.log.debug(f"will open the quick link {_['quicklook']}")
                preview_email = wc_preview_email(self.driver)
                if preview_email is not None:
                    self.log.debug(f'here is the preview email {preview_email}')
                    compareresult, diff_fields = email_compare(_, preview_email)
                    if compareresult:
                        self.log.debug(f'email compare result is same')
                    else:
                        raise CVWebAutomationException(f"this email fields {diff_fields} are not match")
                else:
                    raise CVWebAutomationException(f"""
preview email is not return correct email, url is {_['quicklook']}""")
                driver.close()
                driver.switch_to.window(adminconsole_tab)

class ApplicationExchangeAgentPage():
    """
    Common code to handle exchange related operations
    """

    def __init__(self, adminconsole_):
        """
        initial Application Page for exchange
        Args:
            id_        int    test case id
            inputjson    json    inputjson content from input file
        """
        self.adminconsole = adminconsole_
        self.driver = self.adminconsole.driver
        self.browser = self.adminconsole.browser
        self.log = self.adminconsole.log
        self.appname = "appexchangepage"

    def owa_tab(self, owainfo, login=True):
        """
        open a new tab for outlook owa session check
        Args:
            owainfo    dict    owa login information.
            login    boolean    True (default), try to login the owa page
                                false,skip login page.
                                    if owa was opened before, no need to login
        Return:
            owa_ins    obj    owa instance
            tabs    list    selenium current tab lists
        """
        self.browser.open_new_tab()
        tabs = self.driver.window_handles
        self.driver.switch_to.window(tabs[1])
        owa_ins = OutlookOWA(self.driver, **owainfo)
        if login:
            owa_ins.login()
        else:
            owa_ins.login(skip=True)
        return owa_ins, tabs

    def owa_tab_close(self, tabs):
        """
        cloase owa tab
        Args:
            tabs    list    selenium current tabs
        """
        self.driver.close()
        self.driver.switch_to.window(tabs[0])
        self.driver.refresh()

    def owa_getemails(self, owainfo):
        """
        collect email informaiton from owa page
        Args:
            owainfo    dict    owa login information
        Return:
            emails    list    list of email information
        """
        owa_ins, tabs = self.owa_tab(owainfo, login=False)
        emails = owa_ins.getemailslist()
        self.owa_tab_close(tabs)
        return emails

    def owa_folderclean(self, owainfo):
        """
        clean up all email in current inbox
        Args:
            owainfo    dict    owa login information
        """
        owa_ins, tabs = self.owa_tab(owainfo)
        owa_ins.folderclean()
        self.owa_tab_close(tabs)
