# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
 This is the basic Admin console page operation for AD agent

 ADClientsPage    ad agent clients list
     get_ad_clients    -- get all client names

     select_client    -- select client from the page

     aad_creation    -- create an azure ad client

     aad_creation_auth    -- handle MS authentication page in azure ad creation

 ADPage    ad client page to operation on subclient
     wait_for_job_completion    -- wait job to complete

    format_ad_to_browse        -- convert ad ldap content to browse format

    subclients    -- get all subclients

    browse_to_subclient    -- return to subclient page from browse page

    __click_client_backup   -- Client the client level backup

    __click_client_restore  -- Client the client level restore

    select_backup_type  -- Selects the backup type

    select_attributes_for_restore   -- Selects the attribute for restore

    backup    -- run a bakcup job and wait the job completed

    backup_submit    -- submit a backup job

    ad_add_subclinet     -- create a new subclient

    restore    -- run a resotre job and wait the job completed

    restore_submit     -- submit a restore job

    ad_open_browse    -- open a browse window

    ad_browse    -- browse content from browse window

    _ad_browse_left_panel_pick    -- pick the content from browse window left panel

    _ad_browse_right_panel_check    -- get items form browse window right panel

    ad_browse_pick    -- pick the ad entries from browse window

    entity_search   -- Search for the entity

    __expand_restore_options    -- Expands the restore advanced options

    select_gpo_link_restore_options     -- Select the GPO links restore option

    __job_details   -- Fetch the job details and wait until the job is completed

    __get_job_details   -- Fetch the job id

    ad_get_entries()    -- get the ad entries from an ldap DN

    ad_check_objs()     -- check if the ad entries objects eixsting or not

    ad_connect()    -- setup ldap connection to ad server

    ad_content_format_convert()     -- convert the ad content to ad ldap format

    ad_browse_check()    -- check browse windows to ad entries

    _get_purchased_additional_or_licensed_usage --  fetches the purchased, additional and included usages

    _get_total_licensed_users   --  Fetches the total users, total active directory users and total azure ad users

    fetch_user  --  Fetches the licensed users from the usage tab

 CvAd AD aegnt related operation

    ad_get_entries    get ad content from the ad connection

    ad_check_objs    check ad objects from  the ad connection

    ad_browse_check    check objects from browse windows

    ad_content_format_convert convert the ad content format

    ad_connect        setup ad connection
"""
from time import sleep
from random import randint
from selenium.webdriver.common.by import By
from Web.Common.page_object import PageService, WebAction
from Application.AD.exceptions import ADException
from selenium.webdriver.common.keys import Keys
from Application.AD.ms_ad import ADOps
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.core import RCalendarView
from Web.AdminConsole.Components.panel import ModalPanel, Backup, DropDown, \
                                                RPanelInfo , RDropDown
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.AD.page_ops import check_element, check_link_text, \
                                            select_content, \
                                            check_parent, select_form_submit, \
                                            select_button_text, check_dchildren
from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.AD import constants


class ADClientsPage():
    """ AD agent admin console apge"""

    def __init__(self, adminconsole):
        """ Inintial AD admin console page
        Args:
            adminconsole   (obj):    admin console page object
            driver          (obj):      selenium driver object
        """
        self._admin_console = adminconsole
        self.driver = adminconsole.driver
        self.appname = "adpage"
        self.log = adminconsole.log
        self.table_ = Rtable(self._admin_console) # from sp27, use rtable
        self.dialog_ = ModalDialog(self._admin_console)
        self.wizard = Wizard(self._admin_console)

    @PageService()
    def check_dashboard(self):
        """
        check ad dashboard
        """
        tilecontainers = self.driver.find_elements(By.CLASS_NAME, "tile-container")
        if len(tilecontainers) == 3:
            self.log.debug('find 3 tile in overwiew dashboard, check more details')
        else:
            raise Exception(" there are more than 3 tile in the page, not right, check the page")

        tile_list = ["Backup health", "Data distribution", "Applications"]
        index_ = 0
        for _ in tile_list:
            if check_element(tilecontainers[index_], 'class', 'tile-header-wrapper').text == _:
                self.log.debug(f"check {_} status")
                self.log.debug(f"{_} content is")
                content_ = check_element(tilecontainers[index_], 'class', 'tile-content').text
                for _ in content_.split("\n"):
                    self.log.debug("_")
                index_ +=1

    @PageService()
    def metallic_plan_creation(self):
        '''
        check if the metallic plan creation is required.
        '''
        try:
            if self._admin_console.dialog_get_text().startswith("'Success, you are ready to configure Active Directory apps!"):
                self.log.debug("a new ad plan is created")
                diag_ = check_element(self.driver, 'tag', 'div', **{ "role": "presentation"})
                plan_region = diag_.find_element(By.XPATH, "//div[@role='alert']//b")
                self.log.debug(f"the new plan is created for region {plan_region}")
                select_button_text(diag_, "CLOSE")
                self._admin_console.wait_for_completion()
        except:
            self.log.debug("it seem the plan already be created")

    @PageService()
    def switch_to_app(self):
        """
        switch to apps tab
        """
        tab_ = self._admin_console.get_current_tab()
        if tab_ == "Apps":
            self.log.debug("current tab is Apps")
        else:
            self.log.debug(f"current tab is {tab_}, switch to apps")
#            self.check_dashboard()
            self._admin_console.access_tab("Apps")

    @PageService()
    def get_ad_clients(self, details = False):
        """
        Solution page for Application AD page
        """
        self.switch_to_app()
        table_data = self.table_.get_table_data()
        self.log.debug(f"here is the table data: {table_data}")
        if details:
            return table_data
        else:
            return table_data['Name']

    @PageService()
    def select_client(self, clientname):
        """
        Select client in admin console page
        Args:
            clientname    (string):    client name
        """
        clients = self.get_ad_clients()
        if clientname in clients:
            check_link_text(self.driver, clientname).click() # from sp27, hyperlink is not working
        else:
            raise ADException(self.appname, 203, clientname)

    @PageService()
    def aad_pick_clientname(self, inputs, id_):
        """
        select azure ad client from the list.
        if client is not existing, will create a new one
        Args:
            inputs    (dict):    answer file input
            id_    (int):    testc ase id
        Return:
            clientname    (str):    client name
        """
        if inputs["ExistingClientName"]:
            clientname = inputs["ExistingClientName"]
        else:
            clientname = f"AAD_{id_}"
        self.log.info(f"will pick {clientname} from the list")
        self._admin_console.refresh_page()

        if clientname in self.get_ad_clients():
            if "KeepClient" in inputs:
                self.log.debug(f"{clientname} already eixsting")
            else:
                self.log.debug(f"will delete {clientname} first")
                self.aad_delete(clientname)
                self.log.debug(f"will create {clientname} again")
                self.aad_creation(clientname, inputs)
        else:
            self.log.debug(f"{clientname} is not existing, will create new one")
            self.aad_creation(clientname, inputs)
        return clientname

    @PageService()
    def aad_creation(self, clientname, tcinputs=None):
        """
        create azure ad client
        Args:
            clientname    (str):    clientname
            tcinputs    (dict)      answerfile input diction
        """
        self.log.info("start to create azure ad cleint")
        try:
            self.table_.access_toolbar_menu("Add")
            self.table_.access_menu_from_dropdown("Azure Active Directory")
        except:
            self.log.debug("sp34 have issue to use common table drowndown")
#            select_button_text(self.driver, "Add")
#            self._admin_console.wait_for_completion()
#            self.action_menu(check_element(self.driver, 'tag', 'div', **{"role": "presentation"}),"Azure AD")
            self.table_.access_menu_from_dropdown("Azure AD")

            self._admin_console.wait_for_completion()
        # create azure ad app page is opened
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()
        self.log.debug("start try to create aad client with regular way")

        self.log.debug("regular cs with sp28, sp30 and sp32")
        try:
            self._admin_console.fill_form_by_id("azureAppNameSaas", clientname)
        except:
            self.log.debug("on sp3201, id changed to azureAppName")

        self._admin_console.fill_form_by_id("azureAppName", clientname)
        #                self._admin_console.fill_form_by_id("appNameField", clientname)
        self.log.debug("input global username and password")
        self._admin_console.fill_form_by_id("globalUserName", tcinputs['AdminUser'])
        self._admin_console.fill_form_by_id("globalPassword", tcinputs['AdminPassword'])

        dropdown_ = DropDown(self._admin_console)
        dropdown_.select_drop_down_values(drop_down_id="planSummaryDropdown",
                                          values=[tcinputs['Plan']])
        self._admin_console.wait_for_completion()

        # infrastrucgtur configuration
        infra_panel = check_element(self.driver, "class", "azureADInfraAccordion-panel")
        if "Infrastructure settings will be inherited from the server plan" in infra_panel.text:
            self.log.debug("there is infra pool configured, not need to pick other")
        else:
            self.log.debug("configure access node and index server")

            dropdown_.select_drop_down_values(drop_down_id="indexServer",
                                              values=[tcinputs['IndexServer']])
            self._admin_console.wait_for_completion()

            dropdown_.select_drop_down_values(drop_down_id="memberServer",
                                              values=[tcinputs['ADagentName']])
        self._admin_console.wait_for_completion()
        if tcinputs["AzureADRegion"]:
            self.log.debug("set the region for the tenant")
            dropdown_.select_drop_down_values(drop_down_id="cloudRegions",
                                              values=[tcinputs['Region']])
        if tcinputs["AzureADManual"]:
            self.log.debug("use custom configuration")
            self._admin_console.select_radio(value="MANUALLY")
            self._admin_console.wait_for_completion()
            check_element(self.driver, "tag", "input",
                          **{
                              "data-ng-model": "azureADAddClntCtrl.azureADCrClntProp.azureDetails.azureAppId"}).send_keys(
                tcinputs["ClientId"])
            sleep(2)
            check_element(self.driver, "tag", "input",
                          **{
                              "data-ng-model": "azureADAddClntCtrl.azureADCrClntProp.azureDetails.azureAppKeyValue"}).send_keys(
                tcinputs["ClientPass"])
            sleep(2)
            check_element(self.driver, "tag", "input",
                          **{
                              "data-ng-model": "azureADAddClntCtrl.azureADCrClntProp.azureDetails.azureDirectoryId"}).send_keys(
                tcinputs["TenantName"])
            sleep(2)
            self._admin_console.checkbox_select("APP_PERMISSIONS")
            self._admin_console.click_button_using_text("Create")
            self._admin_console.wait_for_completion()
        else:
            self.log.debug("use express configuration")
            self.log.debug("check all checkboxes")
            self._admin_console.checkbox_select("SAVE_GA_CREDS")
            self._admin_console.checkbox_select("MFA_DISABLED")
            main_window = self.driver.current_window_handle
            select_button_text(self.driver, "Create Azure app")
            # wait 100 seconds to get authentication page, may create loop to check more times
            self._admin_console.wait_for_completion()
            self.aad_creation_auth(tcinputs, main_window)
            select_button_text(self.driver, "Create")
            self.log.debug("azure ad app should be created")
            # after click the create button, the page is not refresh.
            # I have to manually set the wait time not based on web response
            self._admin_console.wait_for_completion()
            self._admin_console.navigator.navigate_to_activedirectory()



        try:
            self.log.debug("input global username and password")
            self._admin_console.fill_form_by_id("globalUserName", tcinputs['AdminUser'])
            self._admin_console.fill_form_by_id("globalPassword", tcinputs['AdminPassword'])

            dropdown_ = DropDown(self._admin_console)
            dropdown_.select_drop_down_values(drop_down_id="planSummaryDropdown",
                                              values=[tcinputs['Plan']])
            self._admin_console.wait_for_completion()

            # infrastrucgtur configuration
            infra_panel = check_element(self.driver,"class","azureADInfraAccordion-panel")
            if "Infrastructure settings will be inherited from the server plan" in infra_panel.text:
                self.log.debug("there is infra pool configured, not need to pick other")
            else:
                self.log.debug("configure access node and index server")

                dropdown_.select_drop_down_values(drop_down_id="indexServer",
                                              values=[tcinputs['IndexServer']])
                self._admin_console.wait_for_completion()

                dropdown_.select_drop_down_values(drop_down_id="memberServer",
                                                  values=[tcinputs['ADagentName']])
            self._admin_console.wait_for_completion()
            if tcinputs["AzureADRegion"]:
                self.log.debug("set the region for the tenant")
                dropdown_.select_drop_down_values(drop_down_id="cloudRegions",
                                                  values=[tcinputs['Region']])
            if tcinputs["AzureADManual"]:
                self.log.debug("use custom configuration")
                self._admin_console.select_radio(value="MANUALLY")
                self._admin_console.wait_for_completion()

            else:
                self.log.debug("use express configuration")
                self.log.debug("check all checkboxes")
                self._admin_console.checkbox_select("SAVE_GA_CREDS")
                self._admin_console.checkbox_select("MFA_DISABLED")
                main_window = self.driver.current_window_handle
                select_button_text(self.driver, "Create Azure app")
                # wait 100 seconds to get authentication page, may create loop to check more times
                self._admin_console.wait_for_completion()
                self.aad_creation_auth(tcinputs, main_window)
                select_button_text(self.driver, "Create")
                self.log.debug("azure ad app should be created")
                # after click the create button, the page is not refresh.
                # I have to manually set the wait time not based on web response
                self._admin_console.wait_for_completion()
                self._admin_console.navigator.navigate_to_activedirectory()
        except:
            self.log.debug("using new way from sp32")
            self._admin_console.fill_form_by_id("appNameField", clientname)
            main_window = self.driver.current_window_handle

            if check_element(self.driver,"id", "planSummaryDropdown"):
                self.log.debug("use regular wizard to configure azure ad")
                self.wizard.click_next()
                self._admin_console.wait_for_completion()
                self.wizard.select_plan(tcinputs['Plan'])
                self.wizard.click_next()
                self._admin_console.wait_for_completion()
                wizard_body = check_element(self.driver,"class", "wizard-step-body")
                if "Infrastructure settings will be inherited from the server plan" in wizard_body.text:
                    self.log.debug("there is infra pool configured, go to next step")
                else:
                    self.log.debug("add steps to configure access node and index server")
                    assert False
                self.wizard.click_next()
                self._admin_console.fill_form_by_id("globalAdmin", tcinputs['AdminUser'])
                self._admin_console.fill_form_by_id("globalAdminPassword", tcinputs['AdminPassword'])
                self._admin_console.checkbox_select("saveGlobalAdminCredsOption")
                self._admin_console.checkbox_select("mfaConfirmation")
                select_button_text(self.driver, "CREATE AZURE APP")
                self.log.debug("creating app window will popup, need to wait and check here")
                while self.driver.find_elements(By.XPATH,"//span[text()='Azure sync completed successfully']") == []:
                    self.log.debug("azure ad creation is  not completed, will wiat and try again in next 10s")
                    sleep(10)
                self.log.debug("it seem the app creation is done, wiat for authentication")

            else:
                self.log.debug("user metallic backup app configure azure ad")
                check_element(self.driver, "id", "id-o365-sign-in-with-msft-onboarding").click()
                self.log.debug("will open microsoft authentication page,wait 20 seconds")
            sleep(20)
            self._admin_console.wait_for_completion()
            self.aad_creation_auth(tcinputs, main_window)
            self._admin_console.wait_for_completion()
            select_button_text(self.driver, "CLOSE")
            self._admin_console.wait_for_completion()
            select_button_text(self.driver, "CREATE")
            self._admin_console.wait_for_completion()

    def wizard_dropdown(self, dropdownid, value):
        """
        may not requried for wizard dropdown operation
        """
        check_element(self.driver, "id", dropdownid).click()
        self.log.debug("click the dropdown list to show values")
        self._admin_console.wait_for_completion()
        if check_element(self.driver, "id", "menu-"):
            self.log.debug(f"available select options are {check_element(self.driver, 'id', 'menu-').text}")
            select_values = check_element(self.driver, "id", "menu-").find_elements(By.TAG_NAME, "li")
            for select_ in select_values:
                if select_.text == value:
                    self.log.debug("found the correct value to select")
                    select_.click()
                    self._admin_console.wait_for_completion()
                    break
        self.log.debug(f"dropdown value {value} is selected")

    def action_menu(self, actionmenuid, value):
        """
        may not required for the wizard action
        """
        action_menu_ = check_element(actionmenuid, 'class', "MuiPaper-root")
        action_options = action_menu_.find_elements(By.TAG_NAME, "li")
        for _ in action_options:
            if _.text == value:
                self.log.debug(f"found the action menu {value}")
                _.click()
                break
            else:
                self.log.debug(f"action menu is {_.text}")

    @PageService()
    def aad_creation_react(self, clientname, tcinputs=None):
        """
        use react to create the azure ad client
        """
        if "General" in check_element(self.driver, 'class', 'active').text:
            self.log.debug('select step 1 region')
            self.log.debug("select from dropdown is not working on react, need to check")
            self.wizard_dropdown("storageRegion", tcinputs['AzureADRegion'])
            self.log.debug("region is selected, time to pick the plan")
            if check_element(self.driver, "id", "planDropdown"):
                self.wizard_dropdown("planDropdown", tcinputs['Plan'])
            else:
                self.log.debug("there is no plan dropdown menu, show the picked plan")
                alert = check_element(self.driver, 'tag', 'div', **{"role": "alert"})
                self.log.debug(f"plan show message {alert.text}")
                selected_plan = alert.find_element(By.XPATH, "//b").text
                self.log.debug(f"selected plan info is {selected_plan}")
            select_button_text(self.driver, "NEXT")
            self._admin_console.wait_for_completion()

        if "Application" in check_element(self.driver, 'class', 'active').text:
            self.log.debug("select step 2 to create azure ad app")
            self._admin_console.fill_form_by_id("appNameField", clientname)
            main_window = self.driver.current_window_handle
            signin_button = check_element(self.driver, "id", "id-o365-sign-in-with-msft-onboarding")
            check_element(signin_button, 'tag', 'svg').click()
            self._admin_console.wait_for_completion()
            try:
                diag_ = check_element(self.driver, 'tag', 'div', **{"role": "dialog"})
            except:
                self.log.debug("diag window seem not open or switch to auth page")
            self.aad_creation_auth(tcinputs, main_window)
            diag_ = check_element(self.driver, 'tag', 'div', **{"role": "dialog"})
            diag_messages = check_dchildren(check_dchildren(diag_, pc=1))
            diag_message_status = diag_messages[1].text
            diag_message_details = check_dchildren(diag_messages[2])
            self.log.debug(f"app creation status is {diag_message_status}")
            for _ in diag_message_details:
                self.log.debug(f"app creation detail is {_.text}")
            check_element(diag_, 'tag', 'button').click()
            self._admin_console.wait_for_completion()
            select_button_text(self.driver, 'CREATE')
            self._admin_console.wait_for_completion()

        if "Summary" in check_element(self.driver, 'class', 'active').text:
            self.log.debug("select step 3 to create azure ad app")
            message = check_element(self.driver, 'class', 'wizard-step-body')
            self.log.debug(f"azure ad is created with this information {message}")
            select_button_text(self.driver, "CLOSE")
            self._admin_console.wait_for_completion()

        self.log.debug(f"New azure ad app {clientname} is created")

    @PageService()
    def aad_creation_metallic_react(self, clientname, tcinputs=None,region=constants.ADconstants.EAST_US_2.value):
        """
        create azure ad client
        Args:
            clientname    (str):    clientname
            tcinputs    (dict)      answerfile input diction
        """
        self.log.info(f"create azure ad client {clientname} on metallic with react change")



        if check_element(self.driver, "id", "storageRegion"):
            self.log.debug('select step 1 region')
            self.log.debug("select from dropdown is not working on react, need to check")
            self.wizard_dropdown("storageRegion", region)
            self.log.debug("region is selected, time to pick the plan")
            if check_element(self.driver, "id", "planDropdown"):
                self.wizard_dropdown("planDropdown", tcinputs['Plan'])
            else:
                self.log.debug("there is no plan dropdown menu, show the picked plan")
                alert = check_element(self.driver, 'tag', 'div', **{"role": "alert"})
                self.log.debug(f"plan show message {alert.text}")
                selected_plan = alert.find_element(By.XPATH, "//b").text
                self.log.debug(f"selected plan info is {selected_plan}")
            select_button_text(self.driver, "NEXT")
            self._admin_console.wait_for_completion()

        if check_element(self.driver, "id", "appNameField"):
            self.log.debug("select step 2 to create azure ad app")
            if tcinputs["NewAADmanual"]:
                self._admin_console.fill_form_by_id("appNameField", clientname)
                self.log.debug("will create azure ad with manual setting")
                self.driver.find_element(By.XPATH, "//span[text()='Custom configuration (Advanced)']").click()
                self._admin_console.wait_for_completion()
                self._admin_console.fill_form_by_id("addAzureApplicationId", tcinputs['ClientId'])
                sleep(3)
                self._admin_console.fill_form_by_id("addAzureApplicationSecretKey", tcinputs['ClientPass'])
                sleep(3)
                self._admin_console.fill_form_by_id("addAzureDirectoryId", tcinputs['TenantName'])
                sleep(3)
                self._admin_console.click_by_id("permissionsConfirmation")
            else:
                self.log.debug("will use express configration")
                self._admin_console.fill_form_by_id("appNameField", clientname)
                main_window = self.driver.current_window_handle
                signin_button = check_element(self.driver, "id", "id-o365-sign-in-with-msft-onboarding")
                check_element(signin_button, 'tag', 'svg').click()
                self._admin_console.wait_for_completion()
                try:
                    diag_ = check_element(self.driver, 'tag', 'div', **{"role": "dialog"})
                except:
                    self.log.debug("diag window seem not open or switch to auth page")
                self.aad_creation_auth(tcinputs, main_window)
                diag_ = check_element(self.driver, 'tag', 'div', **{"role": "dialog"})
                diag_messages = check_dchildren(check_dchildren(diag_, pc=1))
                diag_message_status = diag_messages[1].text
                diag_message_details = check_dchildren(diag_messages[2])
                self.log.debug(f"app creation status is {diag_message_status}")
                for _ in diag_message_details:
                    self.log.debug(f"app creation detail is {_.text}")
                check_element(diag_, 'tag', 'button').click()
            self._admin_console.wait_for_completion()
            select_button_text(self.driver, 'CREATE')
            self._admin_console.wait_for_completion()

        self.log.debug("select step 3 to create azure ad app")
        message = check_element(self.driver, 'class', 'wizard-step-body')
        self.log.debug(f"azure ad is created with this information {message}")
        select_button_text(self.driver, "CLOSE")
        self._admin_console.wait_for_completion()

        self.log.debug(f"New azure ad app {clientname} is created")

    @PageService()
    def aad_creation_auth(self, tcinputs, main_window):
        """ 
        do authentication with MS page
        Args:
            tcinputs     (dict):    answer file input
            main_window    (obj):    browse tab for the admin console
        """
        # check if the new tab is opened
        tabs = self.driver.window_handles
        if len(tabs) == 2:
            self.log.debug("a new tab is opened for authentication")
            self.driver.switch_to.window(tabs[1])
            try:
                self.log.debug("check if the user name is required")
                check_element(self.driver, "tag", "input",
                              **{"type" : "email"}).send_keys(tcinputs['AdminUser'])
                sleep(3)
                check_element(self.driver, "tag", "input",
                              **{"type": "submit"}).click()
                sleep(10)
            except:
                self.log.debug("no user name page is detected, assume we passed email")
            self.log.debug("input password and continue")
            check_element(self.driver,"tag",
                          "input",
                          **{"name":"passwd"}).send_keys(tcinputs['AdminPassword'])
            select_form_submit(self.driver)
            sleep(20)
            app_name = check_element(self.driver, "class","app-name").text
            self.log.info(f" a new app is created with name {app_name}")
            perms = self.driver.find_elements(By.CLASS_NAME, "scope")
            perms_info = [_.text for _ in perms]
            self.log.info(f" Total {len(perms)} permisssions are associated to \
                            this app: {perms_info}")
            sleep(5)
            select_form_submit(self.driver)
            self.log.debug("switch back to cv main window")
            self.driver.switch_to.window(main_window)
            self.log.debug("authentication process done, the tab will closed")
        else:
            self.log.debug("didn't found the new authentication window")
            raise ADException(self.appname, 204, "there are no ms windows opened")

    @PageService()
    def aad_delete(self, clientname):
        """
        delete auzre ad client
        Args:
            clientname    (str):    clientname
        """
        self.log.debug(f"release license for cilent {clientname}")
        try:
            self.table_.access_action_item(clientname,"Release license")
            self._admin_console.wait_for_completion()
        except:
            if check_element(self.driver, "id", "row-action-menu"):
                self.log.debug("The table action is not working with latest react")
                self.action_menu(check_element(self.driver, 'id', "row-action-menu"), "Release license")
                self._admin_console.wait_for_completion()
            else:
                raise ADException("adpage", 203, "table access action item  is not working with Ad react")

        try:
            self.dialog_.click_submit()
        except:
            self.log.debug("on sp3201, need different way to handle click button")
            select_button_text(self.driver, "YES")
        self._admin_console.wait_for_completion()
        self.log.debug("wait 20 seconds to start delete azure ad client")
        sleep(20)
        self.log.debug(f"delete client {clientname}")
        try:
            self.table_.access_action_item(clientname,"Delete")
            self.log.debug("start to delete the client, dialog window is up.")
        except:
            if check_element(self.driver, "id", "row-action-menu"):
                self.log.debug("The table action is not working with latest react")
                self.action_menu(check_element(self.driver, 'id', "row-action-menu"), "Delete")
                self._admin_console.wait_for_completion()
            else:
                raise ADException("adpage", 203, "table access action item  is not working with Ad react")
        self._admin_console.wait_for_completion()

        if "erase and reuse media" in self.dialog_.get_text():
            self.log.debug("will try eras and reuse media")
            self.dialog_.type_text_and_delete("erase and reuse media",checkbox_id="deleteClientConfirmationChx")
        else:
            self.log.debug("delete window is changed. use delete")
            self._admin_console.wait_for_completion()
            self._admin_console.fill_form_by_id("confirmText", "Delete")
            select_button_text(self.driver,"DELETE")
        self._admin_console.wait_for_completion()
        if clientname in self.get_ad_clients():
            self.log.debug("for some reason, delete client failed, fail the case")
        else:
            self.log.debug(f"{clientname} is deleted")

class ADPage():
    """
    AD agent related page
    """
    def __init__(self, adminconsole, commcell):
        """ Inintial AD admin console page
        Args:
            adminconsole       (obj):    adminconsole object
            driver              (obj):      selenium driver
        """
        self._admin_console = adminconsole
        self.driver = adminconsole.driver
        self.appname = "aapage"
        self.log = adminconsole.log
        self.commcell = commcell
        self.table_ = Rtable(self._admin_console)
        self._alert = Alert(self._admin_console)
        self.__jobs = Jobs(self._admin_console)
        self.modal_ = ModalPanel(self._admin_console)
        self.dialog_ = ModalDialog(self._admin_console)
        self.browse_ = Browse(self._admin_console, is_new_o365_browse=True)
        self.wizard = Wizard(self._admin_console)
        self.__rmodal_dialog = RModalDialog(self._admin_console)
        self.rpanelinfo = RPanelInfo(self._admin_console)
        self.rcalendar = RCalendarView(self._admin_console)
        self._table = Table(self._admin_console)
        self.browse = Browse(self._admin_console)
        self.__ad_dialog = None
        self.__rmodal_dialog = RModalDialog(self._admin_console)
        self.__dropdown = RDropDown(self._admin_console)
        self.__props = self._admin_console.props


    def format_ad_to_browse(self, objs):
        """
        convert ad object type to browse type
        Args:
            objs    (list):    list of ad objects in UGO creation, like
                        [('OU', '53662_base_OU_2022-03-10T08:36:37'),
                        ('Group', '53662_base_Group_2022-03-10T08:36:37'),
                        ('User', '53662_base_User_197')]
        Return:
            objects_name    (list):    name only, used for compare ad result
            browse_objects    (list):    with CN/OU append to name, used for CV browse
        """
        browse_objects = []
        objects_name = []
        for _ in objs:
            if _[0] in ["Group" , "User"]:
                browse_format = f"CN={_[1]}"
            else:
                browse_format = f"OU={_[1]}"
            browse_objects.append(browse_format)
            objects_name.append(_[1])
            self.log.debug(f"convert {_} to browse format {browse_format}")
        self.log.debug(f"object name only is {objects_name}")
        return browse_objects, objects_name

    def switch_to_frame(self):
        """
        maybe not nesssary
        """
        if check_element(self.driver, 'id', 'cc-iframe'):
            self.log.debug("will switch to iframe")
            self.driver.switch_to.frame(check_element(self.driver, 'id', 'cc-iframe'))
        else:
            self.log.debug("no iframe detected")

    @PageService()
    def subclients(self):
        """
        get subclients name
        """
        self._admin_console.refresh_page()
        subclients = self.table_.get_table_data()
        self.log.debug(f"here are the subclient information {subclients}")
        subclients_name = subclients['Name']
        return subclients_name

    @PageService()
    def browse_to_subclient(self, clientname):
        """
        return to subclient page from browse window
        Args:
            clientname    (str):    client name
        """
        self.log.debug(f"will go back to  {clientname} page from browse window")
        try:
            check_link_text(self.driver, clientname).click()
        except:
            self.log.debug(f"{clientname} is not found, mabye use different name")
            self._admin_console.select_breadcrumb_link_using_text(clientname)

    @WebAction(delay=2)
    def __click_client_backup(self):
        """Clicks the client level backup"""
        self.driver.find_element(By.XPATH, '//div[@class="popup"]').click()
        self.driver.find_element(By.XPATH, '//button[contains(@id,"APP_LEVEL_BACKUP")]').click()

    @WebAction(delay=2)
    def __click_client_restore(self):
        """Clicks the client level restore"""
        self.driver.find_element(By.XPATH, '//button[@id="APP_LEVEL_RESTORE"]').click()

    @WebAction(delay=2)
    def select_backup_type(self, backuptype='Incremental'):
        """Selects the backup type
        Args:
            backuptype(str): AD Backup Type
        """
        self.driver.find_element(By.XPATH, f'//span[text()="{backuptype}"]').click()

    @WebAction()
    def select_attributes_for_restore(self, attributes):
        """
        Method to select attributes for restore
        Args:
            attributes (list) : List of attributes
        """

        self.driver.find_element(By.XPATH, "//input[contains(@id,'AttributeList')]").click()
        for attribute in attributes:
            search_box = self.driver.find_element(By.XPATH, "//input[contains(@name,'attributeNameFilterInput')]")
            search_box.click()
            search_box.clear()
            search_box.send_keys(attribute)
            search_box.send_keys(Keys.ENTER)

    @PageService()
    def backup(self, backuptype: str, subclient=None):
        """
        run ad backup on subclient
        Args:
            subclientname    (str):    subclientname
            backuptype    (str):    backup type , choise from "Inc" and "Full"
        """

        job_details = self.backup_submit(subclient, backuptype=backuptype)
        self.log.info('job details: %s', job_details)
        return job_details

    @WebAction()
    def _get_purchased_additional_or_licensed_usage(self):
        """fetches the purchased, additional and included usages"""
        label_xpath = "//span[@class='kpi-category-label']"
        value_xpath = "//span[@class='kpi-category-label' and contains(text(), '{}')]/preceding-sibling::span"
        purchased_and_additional_usage = dict()
        elements = self.driver.find_elements(By.XPATH, label_xpath)
        for element in elements:
            key = element.text
            value = self.driver.find_element(By.XPATH, value_xpath.format(key)).text
            purchased_and_additional_usage.update({key: value})
        return purchased_and_additional_usage


    @WebAction()
    def _get_total_licensed_users(self):
        """Fetches the total users, total active directory users and total azure ad users"""
        total_licensed_users = {}
        label_xpath = "//div[contains(@class,'MuiGrid-root')]/*/div[contains(text(),'{}')]/following-sibling::div"
        total_licensed_users["Total Licensed Users"] = self.driver.find_element(By.XPATH, label_xpath.format(
            "Total Users")).text
        total_licensed_users["Total Active Directory Users"] = self.driver.find_element(By.XPATH, label_xpath.format(
            "Total Active Directory Users")).text
        total_licensed_users["Total Azure AD Users"] = self.driver.find_element(By.XPATH, label_xpath.format(
            "Total Azure AD Users")).text
        return total_licensed_users

    def fetch_user(self):
        """Fetches the licensed users from the usage tab"""
        license_usage_report = dict()
        self._admin_console.select_hyperlink(link_text="Active Directory - Standard")
        license_usage_report.update(self._get_purchased_additional_or_licensed_usage())
        license_usage_report.update(self._get_total_licensed_users())
        return license_usage_report

    @PageService()
    def backup_submit(self, subclient, backuptype="Incremental"):
        """
        backup job submit
        Args:
            subclientname    (str):    subclientname
            backuptype    (str):    backup type , choise from "Inc" and "Full"
        Return:
            jobid    (str):    job id
        """
        self.log.debug("start a backup job")
        if subclient:
            self.log.debug(f"pick special subclient {subclient}")
            self.table_.access_action_item(subclient, "Back up")
            self._admin_console.wait_for_completion()
            self.table_.access_action_item(subclient,"Back up")
        else:
            self.log.debug("will run backup on default subclient")
            self.__click_client_backup()
            self.select_backup_type(backuptype)
            self.__rmodal_dialog.click_submit()

        job_details = self.__job_details()
        return job_details

    @PageService()
    def ad_add_subclient(self, name, plan, content):
        """
        create a new subclient
        Args:
            name    (str):    subclient name
            plan    (str):    plan used for the subclient
            content    (str):    ad content in the subclient
        """
        try:
            self._admin_console.select_hyperlink("Add subclient")
        except:
            self.log.debug("sp32 change the add subclient link to a button")
            self._admin_console.click_button( "Add")
        self._admin_console.wait_for_completion()
        self.log.debug(f"input the subclinet name {name}")
        try:
            self.driver.find_element_by_xpath("//input[@name='subclientName']").send_keys(name)
        except:
            self.log.debug("sp3001 and sp32 change the id name")
            self._admin_console.fill_form_by_id("subClientName", name)
        self.log.debug(f"add the content {content}")
        try:
            self._admin_console.select_hyperlink("Add content")
        except:
            self.log.debug("sp23 change the link to button")
            self._admin_console.click_button("Add content")
        self._admin_console.wait_for_completion()
        self.log.debug(f"will process {content}")
        select_content(self.driver, content)
        self.log.debug(f"pick the plan {plan}")
        dropdown_ = DropDown(self._admin_console)
        dropdown_.select_drop_down_values(index=0,values=[plan])
        self.modal_.submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def ad_delete_subclient(self, subclientname):
        """
        delete eixsitng subclient
        Args:
            subclientname   (str):    subclientname
        """
        self.table_.access_action_item(subclientname, "Delete")
        self._admin_console.wait_for_completion()
        self.dialog_.type_text_and_delete("DELETE")
        self._admin_console.wait_for_completion()
        self.modal_.submit(wait_for_load=True)
        self.log.debug(f"subclient {subclientname} is deleted")
        self._admin_console.wait_for_completion()

    @WebAction()
    def search_for(self, entity_names):
        """it searches for the client"""
        search = self.driver.find_element(By.XPATH, "//input[contains(@id,'ATSearchInput')]")
        search.clear()
        search.send_keys(entity_names)
        search.send_keys(Keys.ENTER)

    @PageService()
    def restore(self, subclientname=None, restore_base=None, content=None, restorecontent=None,
                entity_names=None, entity_type=None, link_restore_option="Do not restore any links from backup",
                attributes=None):
        """
        restore job
        Args:
            subclientname    (str):    subclient name
            content    (str):    ad content from input file
            restorecontent    (list):    objecst to restore, each object have format
                                    ["cn=test","ou=test2"]
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab("Overview")

        if content:
            content = content.replace(",","/")
            content = f"{restore_base}/{content}"
            self.log.info(f"star a restore job on subclient {subclientname} \
                            {restorecontent} in {content} will be restored ")
        self.restore_submit(subclientname, content, restorecontent,
                       entity_names, entity_type, link_restore_option, attributes)
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def restore_submit(self, subclientname, content, restorecontent,
                       entity_names, entity_type, link_restore_option, attributes):
        """
        restore job submit
        Args:
            subclientname    (str):    subclient name
            content    (str):    ad content from input file
            restorecontent    (list):    objects to restore, each object have format
                                    ["cn=test","ou=test2"]
        Return:
            jobid    (str):    job id
        """
        if subclientname:
            try:
                self.table_.access_action_item(subclientname, "Restore")
            except:
                self.log.debug("on sp3001 and sp32, need to use rtable")
                self.table_.access_action_item(subclientname, "Restore")
        else:
            self.log.debug("will run restore on default subclient")
            self.__click_client_restore()
        sleep(10)
        self._admin_console.refresh_page()

        if entity_names:
            self.log.debug("browse GPO objects from Ad page")
            self.search_for(entity_names)
            self._table.select_all_rows()
        else:
            self.log.debug("browse regular Ad objects from AD page")
            self.ad_browse(content)
            self._admin_console.wait_for_completion()
            self.ad_browse_pick(content, restorecontent)

        self.driver.find_element(By.XPATH, "//button[contains(@id,'RESTORE')]").click()
        self._admin_console.wait_for_completion()
        if entity_names:

            sleep(3)
            if entity_type == "GPO":
                self.select_gpo_link_restore_options(link_restore_option)
            else:
                self.select_attributes_for_restore(attributes)
        self.__rmodal_dialog.click_submit()

    @PageService()
    def ad_browse(self, content=None):
        """
        open browse window for the subclinet
        Args:
            content    (str):    Domino dn path to browse
        Return:
            childcontent    (list):    children itesm in the right panel
        """
        self.log.debug(f'Browse to {content}')
        self.browse_.select_path_for_restore(content)
        childcontent = self._table.get_table_data()
        self.log.debug(f"here is the content in this DN: {childcontent}")
        return childcontent

    @PageService()
    def ad_browse_pick(self, content, restorecontent):
        """
        pick the restore content from the ad browse right window
        Args:
            restorecontent  (list/str):    restore objects list
        """
        self.log.debug(f'Browse to {content}')
#        self.browse_.select_path_for_restore(content, file_folders=restorecontent)
        pager = check_element(self.driver,"class","k-pager-sizes")
        self.log.debug(f"here is the pager info {pager.text}")
        if pager and pager.text != "":
            self.log.debug("There are more than 1 page to display for the contnet")
            select_ = check_parent(check_element(pager,"tag","select"))
            select_.click()
            self._admin_console.wait_for_completion()
            self.log.debug("pick 500 item from popu windows")
            klist = check_element(self.driver, "class", "k-list-scroller")
            check_element(klist,"tag", "li", **{"text" : "500"}).click()
            self._admin_console.wait_for_completion()
            self.log.debug("all content shoudl displayed in one page")
        else:
            self.log.debug("content is less than 20 in this container")
        restoreentry = restorecontent[randint(0,len(restorecontent)-1)]
        self.log.debug(f"the following entries are selected {restoreentry}")
        self.log.debug("old browse page still using regular table")
        self._table.select_rows([restoreentry])
        self.log.debug(f"the following content are selected {restoreentry}")

    @PageService()
    def entity_search(self, value):
        """
        Search for the given value on Restore page
        Args:
            value (str) : Value to be searched
        """
        self.log.info(f"Selecting the ad client {value}")
        self.table_.search_for(value)
        self.driver.find_element(By.XPATH, f"//a[contains(text(),'{value}')]").click()

    @WebAction()
    def expanding_domain(self, domain):
        """"
        Splitting the domain
        Args:
            domain (str) : Domain of the controller
        Returns:
            domain (str) : Domain of the controller
        """
        domain = "DC=" + domain.replace(".", ",DC=")

        return domain

    @WebAction()
    def __expand_restore_options(self):
        """
        Expand the restore options for all entities
        """
        self.driver.find_element(By.XPATH, '//span[text()="Advanced options"]').click()

    @WebAction()
    def select_gpo_link_restore_options(self, link_restore_option):
        """
        Selects the gpo link restore options
        Args:
            link_restore_option (str) : The option for restore of GPO links
        """
        sleep(5)
        self.driver.find_element(By.XPATH, f'//span[text()="{link_restore_option}"]').click()

    @WebAction()
    def ou_path(self, ou, domain):
        """
        Create the path for OU according to the domain
        Args:
            ou(str) : Organisational Unit
            domain(str) : Domain of the AD (format: east.ad.aladdin.xyz)
        """
        domain = self.expanding_domain(domain)
        ou_path = f"OU={ou}," + f"{domain}"
        return ou_path

    @WebAction()
    def ou_path(self, ou, domain):
        """
        Create the path for OU according to the domain
        Args:
            ou(str) : Organisational Unit
            domain(str) : Domain of the AD (format: east.ad.aladdin.xyz)
        """
        domain = self.expanding_domain(domain)
        ou_path = f"OU={ou}," + f"{domain}"
        return ou_path

    @WebAction(delay=2)
    def __job_details(self, tenant_user_view=False):
        """Waits for job completion and gets the job details"""
        try:
            job_id = self._alert.get_jobid_from_popup(wait_time=1)
        except CVWebAutomationException:
            self.driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            self._admin_console.click_button("View jobs")
            self.__jobs.access_active_jobs()
            job_id = self.__jobs.get_job_ids()[0]
        job_details = self.__jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('job details: %s', job_details)
        # job_details[self.__admin_console.props['Status']]
        if (job_details[self._admin_console.props['Status']] not in [
            "Committed", "Completed", "Completed w/ one or more errors"]):
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @PageService()
    def __get_job_details(self, job_id):
        """Returns the job details
            Args:
                job_id (str)                     : Job Id of the ob
        """
        self.__jobs.access_job_by_id(job_id)
        jd = JobDetails(self._admin_console)
        details = jd.get_all_details()
        return details

    @WebAction()
    def select_date_and_time_for_compare(self, date_and_time, source_time=True):
        """
        Method to select date and time for compare
        Args:
            date_and_time(dict) : Dictionary for date and time
            source_time(bool) : If the time is source time or not
        """
        if source_time:
            element = self.driver.find_element(By.XPATH, "//button[@aria-label='Browse']")
        else:
            element = self.driver.find_element(By.XPATH, "//button[@aria-label='Browse'][1]")
        element.click()
        self.rcalendar.set_date_and_time(date_and_time)
        self.driver.find_element(By.XPATH, "// div[text() = 'Select date for compare']").click()

    @WebAction()
    def advanced_options_for_compare(self, include_unchanged_items, include_frequently_used):
        """
        Method to select the advanced options for compare job
        Args:
            include_unchanged_items(bool) : Option to include unchanged options
            include_frequently_used(bool) : Option to  include frequently used items
        """
        self.driver.find_element(By.XPATH, "//div[@aria-label='Advanced options']").click()
        if include_unchanged_items:
            self.driver.find_element(By.XPATH, "//span[text()='Include unchanged items in comparison']").click()
        if not include_frequently_used:
            self.driver.find_element(By.XPATH, "//span[text()='Exclude frequently changed system attributes']").click()

    @WebAction()
    def select_compare_type(self, compare_type):
        """
        Method to select whether the compare is between two previous backups or with live data
        Args:
            compare_type(str) : Type of the compare
        """
        if compare_type == "WithLiveBackup":
            self.driver.find_element(By.XPATH, f"//span[text()='Compare point-in-time backup with live data']").click()
        else:
            self.driver.find_element(By.XPATH, f"//span[text()='Compare two point-in-time backups']").click()

    @PageService()
    def run_ad_compare_entire_domain(self, compare_name, source_time, to_time=None,
                                     compare_type="WithLiveBackup", include_unchanged_items=False,
                                     include_frequently_used=True):
        """
        Method to launch AD compare job
        client (str) : AD client on which you want to launch compare
        compare_name (str) : Name of the AD Compare
        compare_type (str) : Type of the compare
                             ("Select two point-in-time backups to compare" or "Compare point-in-time backup with live data")
        include_unchanged_items (boolean) : Option to include unchanged items in the compare
        include_frequently_used (boolean) : Option to include frequently used items in the compare
        """
        self._admin_console.access_tab("Comparisons")
        self.rpanelinfo.click_button('Add comparison')
        self.wizard.select_card("Compare entire domain")
        self.wizard.fill_text_in_field(id='comparisonNameId', text=compare_name)
        self.wizard.click_next()
        self.select_compare_type(compare_type)
        self.select_date_and_time_for_compare(source_time)
        self.select_date_and_time_for_compare(to_time, source_time=False)
        self.advanced_options_for_compare(include_unchanged_items, include_frequently_used)
        self.wizard.click_next()
        self.wizard.click_submit()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def validate_compare_report(self, compare_name, entities=None, attribute=None):
        """
        Verify the compare results
        Args:
            compare_name(str) : Name of the compare to validate
            entities(list) : List of the entities which are changed in the compare
                                example: ["user","gpo"]
            attribute(str) : Any attribute which is modified in the compare to restore

        Returns:
            Job details of restore job
        """
        self._admin_console.access_tab("Comparisons")
        self.table_.access_action_item(compare_name, "View result")
        changed_data = ["Modified", "Added", "Deleted"]
        for change in changed_data:
            element = f"//span[contains(text(),{change})]"
            if self._admin_console.check_if_entity_exists("xpath", element):
                element.click()
        if entities is not None:
            for entity in entities:
                self.table_.search_for(entity)
                self.driver.find_element(By.XPATH, f"//button[@title='Expand all']").click()
                failed_element = "//div[text()='Something went wrong']"
                if self._admin_console.check_if_entity_exists("xpath", failed_element):
                    raise Exception(f"Compare report is not correctly generated, failed for entity : {entity}")
                self.log.info(f"Entity {entity} is generated correctly in the report")
        self.log.info(f"Performing restore from the Compare report")
        if attribute is not None:
            self._admin_console.access_tab("Attributes")
            self.driver.find_element(By.XPATH, "//span[contains(text(),'Modified')]").click()
            self.table_.select_rows(attribute)
            self.driver.find_element(By.XPATH, "//div[text()='Restore']").click()
            self.modal_.submit()
            job_details = self.__job_details()
            self.log.info('job details: %s', job_details)
            return job_details

    @PageService()
    def delete_compare(self, compare_name):
        """Deletes the compare report
        Args:
            compare_name(str) : Name of the compare
        """
        self._admin_console.access_tab("Comparisons")
        self.table_.access_action_item(compare_name, "Delete")
        self.log.info(f"Successfully deleted the compare {compare_name}")

    def __click_download(self):
        """
        Click on download button to download the package
        """
        xpath1 = "//div[contains(text(),'Windows (64-bit)')]"
        sleep(5)
        xpath2 = "//span[contains(@class,'endIcon')]"
        if self._admin_console.check_if_entity_exists('xpath', xpath1):
            self.driver.find_element(By.XPATH, xpath1).click()
        elif self._admin_console.check_if_entity_exists('xpath', xpath2):
            self.driver.find_element(By.XPATH, xpath2).click()
        else:
            self._admin_console.log.info("Download option does not show up")

    @PageService()
    def navigate_to_ad_app_on_prem(self):
        """
        Navigate to create an active directory app from service catalog page
        """
        self.driver.find_element(By.XPATH,
                                 f"//span[text()='Backup via backup gateway (for on-premise servers)']").click()
        self.wizard.click_next()

    @PageService()
    def extract_authcode(self):
        """
        Extract the authcode from the page and download the package
        Returns:
            authcode (str) : Authcode to be used for installation
        """
        self.wizard.click_add_icon()
        sleep(5)
        xpath = ("//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'copy') "
                 "and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                 "'to clipboard')]")
        text = None
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            text = self.driver.find_element(By.XPATH, xpath).get_attribute("aria-label")
        else:
            self._admin_console.log.info("Failed to get Authcode")
            return
        authcode = text.split("'")[1]
        self.__click_download()
        sleep(300)  # WAIT FOR DOWNLOAD TO COMPLETE
        self.__rmodal_dialog.click_close()
        sleep(10)
        xpath = "//button[@aria-label='close' and @title='Close']"
        if self._admin_console.check_if_entity_exists('xpath', xpath):
            self.driver.find_element(By.XPATH, xpath).click()
        else:
            self._admin_console.log.info("Failed to click close")
        return authcode

    def interactive_install_machine(self, installinputs):
        """interactive install and register new machines
            Args:
                installinputs {}:          install inputs dict
        """
        install_helper = InstallCustomPackage(
            installinputs.get('commcell'),
            installinputs,
            installinputs.get('os_type'))
        install_helper.install_custom_package(
            full_package_path=installinputs.get('full_package_path'),
            authcode=installinputs.get('authCode')
        )

    @PageService()
    def select_backup_gateway(self):
        """
        Select backup gateway
        """
        self.wizard.click_refresh_icon()
        sleep(60)
        drop_down_val = self.__dropdown.get_values_of_drop_down(drop_down_id="accessNodeDropdown")
        self.__dropdown.select_drop_down_values(drop_down_id="accessNodeDropdown", values=drop_down_val)
        self.wizard.click_next()

    @PageService()
    def perform_install_package(self, hostname, installinputs):
        """
        Perform installation of the package
        """
        self.__click_download()
        sleep(120) # sleep till package gets downloaded
        self.interactive_install_machine(installinputs)

        self.wizard.fill_text_in_field(id="activeDirectoryServerHost", text=hostname)
        # click on verify
        self.driver.find_element(By.XPATH, "//button[@aria-label='Verify']").click()
        self._admin_console.wait_for_completion()
        self.wizard.click_next()


    @PageService()
    def create_backup_target(self, disk_storage_name, storage_loc):
        """
        Create backup target
        Args:
            disk_storage_name (str) : Name of the disk storage
            storage_loc (str) : Storage location
        """

        self.driver.find_element(By.XPATH, "//button[@title='Add']").click()
        self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id("name", disk_storage_name)
        # click on add button
        self._admin_console.select_hyperlink('Add')

        self._admin_console.select_radio(value=self.__props['viewname.userGroups.local'])
        self._admin_console.fill_form_by_id("path", storage_loc)
        self._admin_console.wait_for_completion()
        self.__ad_dialog = RModalDialog(self._admin_console, title='Add backup location')
        sleep(5)
        self.__ad_dialog.click_button_on_dialog(text="Add")
        self._admin_console.wait_for_completion()
        sleep(5)
        self.__rmodal_dialog.click_button_on_dialog(text="Save")
        self._admin_console.wait_for_completion()
        self.wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def conf_cloud_storage(self):
        """
        Configure cloud storage
        """
        self.wizard.toggle.enable(id="onlLocalBackupEnabledToggle")
        self._admin_console.wait_for_completion()
        self.wizard.click_next()

    @PageService()
    def conf_service_account(self, username, password):
        """
        Configure service account
         Args:
            username (str) : username
            password (str) : password

        """
        self._admin_console.fill_form_by_id("adUserAccountName", username)
        self._admin_console.fill_form_by_id("adUserAccountPassword", password)
        self._admin_console.wait_for_completion()
        self.wizard.click_next()

    @PageService()
    def handle_summery_page(self):
        """
        Handle summary page
        """
        self._admin_console.wait_for_completion()
        sleep(35)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        sleep(35)
        self.wizard.click_next()
        self._admin_console.wait_for_completion()
        sleep(30)
        self.wizard.click_finish()

    @PageService()
    def create_plan(self, plan_name):
        """
        Create plan
        Args:
            plan_name (str) : Name of the plan
        """
        # click on add button
        self.driver.find_element(By.XPATH, "//button[@title='Add']").click()
        self._admin_console.fill_form_by_id("planNameInputFld", plan_name)
        self._admin_console.wait_for_completion()
        sleep(20)
        self.__rmodal_dialog.click_button_on_dialog(text="Done")
        self._admin_console.wait_for_completion()
        sleep(20)
        self.wizard.click_next()


class CvAd():
    """
    AD operation with AD command center operation
    """

    def __init__(self, adpage, inputs, ADconnect=True, adclientspage=None):
        """
        initial class
        Args:
            adpage    (obj):    ADPage object
            inputs    (dict):    answer file inputs
        """
        self.adclientpage = adpage
        self.adclientspage = adclientspage
        self.log = adpage.log
        self.tcinputs = inputs
        self.adminconsole = adpage._admin_console
        self.driver = adpage.driver
        if ADconnect:
            self.ad_ins = self.ad_connect()
            self.ad_browse_base = "/".join(self.ad_ins.basedn.split(",")[::-1])
            self.adformat_content = self.ad_content_format_convert()
        else:
            self.log.debug("just load clients  page, no ad instnace")

    def ad_get_entries(self, adformat_content):
        """
        get all entries in ad DN path
        Args:
            adformat_content    (str):    ad format to check the entry
                                        exmaple: cn=users,ou=test,ou=abc,ou=com
        """
        ad_contents,ad_contents_count  = self.ad_ins.ugo_list(adformat_content)
        self.log.debug(f"here are {ad_contents_count} entries in \
                         {adformat_content}\n{ad_contents}")
        return ad_contents, ad_contents_count

    def ad_check_objs(self, objs, adformat_content):
        """
        check objects in ad DN path
        Args:
            objs    (list):     name only, used for compare ad result
            adformat_content    (str):    ad format to check the entry
                                        exmaple:  cn=users,ou=test,ou=abc,ou=com
        Return:
            compare_result    (dict):    check each obj existing in the ad or not
            status    (boolean):    if all entry exist or not
        """
        compare_result = {}
        ad_contents,_  = self.ad_ins.ugo_list(adformat_content)

        status = True
        for _ in objs:
            if _ in ad_contents:
                self.log.debug(f"{_} still existing in the ad side")
                compare_result[_] = True
            else:
                self.log.debug(f"{_} is not existeing")
                compare_result[_] = False
            status = status&compare_result[_]
        return compare_result, status

    def ad_browse_check(self, subclientname, content, adformat_content):
        """
        check AD browse content in Active directory
        Args:
            subclientname      (str):    subclient name
            content            (str):    domain dn path to browse
            adformat_content    (str):    ad format to check the entry
                                        exmaple: cn=users,ou=test,ou=abc,ou=com
        """
        self.log.debug("start to check objects in browse window")
        self.adclientpage.driver.find_element(By.XPATH, '//button[@id="APP_LEVEL_RESTORE"]').click()
        self.adminconsole.wait_for_completion()
        content = content.replace(",","/")
        content = f"{self.ad_browse_base}/{content}"
        self.log.debug(f"start to check content in {content}")
        browse_contents = self.adclientpage.ad_browse(content)
        self.log.debug(f"here is the browse content: {browse_contents}")
        ad_contents,ad_contents_count =self.ad_get_entries(adformat_content)

        if ad_contents_count == len(browse_contents['Name']):
            self.log.debug(f"browse return correct {ad_contents_count} objects")
            for _ in browse_contents['Name']:
                self.log.debug(f"check {_} in active directory")
                objectname = _.split("=")[1]
                if objectname in ad_contents:
                    adobject_dn = ad_contents[objectname]['distinguishedName']
                    adobject_dn_child = adobject_dn.split(",")[0]
                    if _ == adobject_dn_child:
                        self.log.debug(f"browse object {_} is match ad object {adobject_dn}")
                    else:
                        self.log.debug(f"browse object {_} is not match ad object {adobject_dn}")
        else:
            self.log.debug(f"browse return {len(browse_contents)} objects while \
                            ad return {ad_contents_count} objects")

    def ad_content_format_convert(self):
        """
        convert input ad content to ldap format
        Return
            content    (str):    ad content in ldap format
                            "OU=mtest,OU=Test,OU=Automation"
        """
        content = self.tcinputs['Content']
        self.log.debug(f"will convert {content} to correct ldap format")
        return ",".join(content.split(",")[::-1])

    def ad_connect(self):
        """
        ad instance for ad ldap operation
        Return:
            ins_     (obj):    ADOps instance
        """
        ins_ = ADOps(server=self.tcinputs["MachineFQDN"],
                     user = self.tcinputs["MachineUserName"],
                     password = self.tcinputs["MachinePassword"],
                     log=self.log)
        return ins_

    def ad_simple_backup(self, backuptype="Inc", subclientname="default", tcinputs=None, prestring="TC"):
        """
        Run a simple ad backup, browse and restore testing

        Args:
            backuptype (str): The type of backup to perform. Valid options are "Inc" for incremental backup and "Full" for full backup.
            subclientname (str): The name of the subclient to perform the backup on. Default is "default".
            tcinputs (dict): A dictionary containing the necessary inputs for the backup job.
            prestring (str): A prefix string to be added to the names of the created objects.

        Returns:
            list: A list of objects that were created for the backup jobs.
        """
        if backuptype == "Inc":
            self.log.info("create more objects before incremental job")
            objs_ = self.ad_ins.ugo_package(entrypoint=self.adformat_content,
                                            prestring=f"{prestring}_i")
            self.adclientpage.backup(backuptype="Incremental")
        elif backuptype == "Full":
            self.log.info("create objects before full job")
            objs_ = self.ad_ins.ugo_package(entrypoint=self.adformat_content,
                                            prestring=f"{prestring}_f")
            self.adclientpage.backup(backuptype="Full")
        self.adminconsole.select_hyperlink(tcinputs['ExistingClientName'])
        self.log.debug("switch back to ad client page")
        self.adminconsole.refresh_page()
        self.ad_browse_check(subclientname,
                             tcinputs['Content'],
                             self.adformat_content)
        self.log.debug(f"new ad objects are {objs_}")
        self.adclientpage.browse_to_subclient(tcinputs['ExistingClientName'])
        return objs_

    def ad_simple_restore(self, restoreobjs):
        """
        Perform a simple restore operation for Active Directory.

        Args:
            restoreobjs (list): A list of objects to be restored.

        Returns:
            None

        Raises:
            None
        """
        self.ad_ins.cv_ugo_delete(restoreobjs, entrypoint=self.adformat_content)
        self.log.debug(f"the following objects are deleted {restoreobjs}")
        browse_objects, objects_name = self.adclientpage.format_ad_to_browse(restoreobjs)
        compare_, status = self.ad_check_objs(objects_name, self.adformat_content)
        if not status:
            self.log.debug(f"all objects {objects_name} are deleted")
        else:
            self.log.debug(f"delete result in comparing, check result manually {compare_}")


        self.adclientpage.restore(restore_base=self.ad_browse_base,
                                  content=self.tcinputs['Content'],
                                  restorecontent=browse_objects)
        self.adclientpage.browse_to_subclient(self.tcinputs['ExistingClientName'])

        compare_, status = self.ad_check_objs(objects_name, self.adformat_content)
        if status:
            self.log.debug(f"all objects {objects_name} are restored")
        else:
            self.log.debug(f"restore result in comparing, check result manually {compare_}")

    def ad_cleanup(self, objs):
        """
        delete all objects created in the test case
        Args:
            objs    (list) :     ad objects created in test case
        """
        self.ad_ins.cv_ugo_delete(objs, entrypoint =self.adformat_content)

    def ad_health_report(self, ):
        """
        check ad health report
        """
        self.ad_ins.cv_health_report()
  
    def health_content(self):
        """
        collect health page content
        """
        health_info = self.adclientspage.table_.get_table_data()
        self.log.debug(f"Health Info: {health_info}")
        health_info = self.health_info_process(health_info)
        panels = self.driver.find_elements(By.CLASS_NAME, "panel-content")
        health_status = {}
        for _ in panels:
            panel_info = check_dchildren(_, pc=1)
            self.log.debug(f"Panel Info: {panel_info.text}")
            if panel_info.text != "":
                panel_info_set = check_dchildren(check_dchildren(_, pc=1))
                health_status[panel_info_set[0].text] = panel_info_set[1].text
            else:
                self.log.debug(f"panel_info.text is empty, skip it")
        self.log.debug(f"Health Status: {health_status}")
        self.log.debug(f"Health Info: {health_info}")
        return health_status, health_info

    def _size_process(self, size):
        """
        process size string to int
        Args:
            size    (str):    size string
        Return:
            size    (int):    size in int
        """
        sizestringset = size.split(" ")
        return ((sizestringset[0],sizestringset[1]))

    def _time_process(self, date_):
        """ process the date string to correct format"""
        datestringset = date_.split(", ")
        if len(datestringset) == 3:
            self.log.debug(f"date string is {datestringset}, include year nd seconds, remove to simple the compare") 
            
            # remove the seconds from the string 
            date_time = ":".join(datestringset[-1].split(" ")[0].split(":")[0:2])
            date_timestring = f"{date_time} {datestringset[-1].split(' ')[1]}"
            if len(date_timestring.split(":")[0]) == 1:
                date_timestring = f"0{date_timestring}"
                # azure ad time hour is in short format if SLA not match
                self.log.debug(f"patch the date time string to {date_timestring}")
            self.log.debug(f"simplified date time is {date_timestring}")
            dateset = (datestringset[0], date_timestring)
        else:
            self.log.debug(f"date string is {datestringset}, only include date and time")
            if len(datestringset[1].split(":")[0]) == 1:
                datestringset[1] = f"0{datestringset[1]}"
                self.log.debug(f"patch the date time string to {datestringset[1]}")
            dateset= (datestringset[0], datestringset[1])
        return (dateset)

    def adinfo_process(self, adinfo, type=None, SLAExclude=True):
        """ process Ad/Aad information from app table"""
        self.log.debug(f"Here is the adinfo: {adinfo}")
        index_ = 0
        adclientinfo = {}
        aadclientinfo = {}
        for _ in adinfo['Type']:
            if "Active Directory" in _ or type=="AD":
                if SLAExclude:
                    if adinfo['SLA status'][index_] == "Excluded":
                        self.log.debug(f"{adinfo['Name'][index_]} SLA status is Excluded, skip it")
                    else:
                        adclientinfo[adinfo['Name'][index_]] = {"Last backup": self._time_process(adinfo['Last backup'][index_]),
                                                            "Application size": self._size_process(adinfo['Application size'][index_]),
                                                            "SLA status": adinfo['SLA status'][index_]}
            elif "Azure AD" in _ or type=="AAD":
                if SLAExclude:
                    if adinfo['SLA status'][index_] == "Excluded":
                        self.log.debug(f"{adinfo['Name'][index_]} SLA status is Excluded, skip it")
                    else:
                        aadclientinfo[adinfo['Name'][index_]] = {"Last backup": self._time_process(adinfo['Last backup'][index_]),
                                                            "Application size": self._size_process(adinfo['Application size'][index_]),
                                                            "SLA status": adinfo['SLA status'][index_]}
            else:
                raise Exception(f"Unknown AD type: {_['Type']}")
            index_ += 1
        self.log.debug(f"AD Client Info: {adclientinfo}")
        self.log.debug(f"AAD Client Info: {aadclientinfo}")
        return adclientinfo, aadclientinfo        

    def health_info_process(self, healthinfo):
        """ process health information from health report"""
        info = {}
        index_ = 0 
        for _ in healthinfo["Client"]:
            info[_] = {"Last backup": self._time_process(healthinfo["Last Successful Backup"][index_]),
                       "Application size": self._size_process(healthinfo["Application Size"][index_]),
                       "SLA status": healthinfo["SLA Status"][index_]}
            index_ += 1
        return info       

    def health_info_comparre(self, clientinfo, healthinfo, excludefields=None, mutliplesubclients=False):
        """compare the health info from app table and health page"""
        self.log.debug(f"clients info: {clientinfo}")
        self.log.debug(f"health info: {healthinfo['health_info']}")
        match_client = False
        match_state = False
        # check if all clients are listed in health report
        if mutliplesubclients:
            self.log.debug("Multiple subclients is enabled for AD client")
            clients = clientinfo.keys()
            for _ in clients:
                self.log.debug(f"start to check client {_} in health report")
                for clientname in healthinfo['health_info'].keys():
                    if _ in clientname:
                        self.log.debug(f"found client {_} in health report with name {clientname}")
                        match_client = True
                        healthinfo['health_info'][_] = healthinfo['health_info'][clientname]
                        del healthinfo['health_info'][clientname]
                        break
                if match_client:
                    self.log.debug(f"found matched client {_} and udpate healthy report key to client")
                    self.log.debug(f"updated health info is {healthinfo['health_info']}")
                    mathc_client = False
                else:
                    self.log.debug(f"client name {_} is not found in health report")
                    break
        else:
            if set(clientinfo.keys()) == set(healthinfo['health_info'].keys()):
                self.log.debug("Client names are matching")
                match_client = True
            else:
                self.log.debug("Client info are not matching health report client")
                self.log.debug(f"Client info: {clientinfo.keys()}")
                self.log.debug(f"Health info: {healthinfo.keys()}")
                match_client = False
        # check individual client info:

        for _ in clientinfo:
            self.log.debug(f"start to comparing client {_} info: {clientinfo[_]}\n\
                            with health report info: {healthinfo['health_info'][_]}")
            for item_ in healthinfo['health_info'][_]:
                if excludefields:
                    if item_ in excludefields:
                        self.log.debug(f"skip {_} {item_} for health report")
                else:
                    if clientinfo[_][item_] == healthinfo['health_info'][_][item_]:
                        self.log.debug(f"client {_} {item_} is match health report")
                        match_state = True
                    else:
                        self.log.debug(f"client {_} {item_} is NOT match health report \n\
                                        Client: {clientinfo[_][item_]} \n\
                                        Health Report: {healthinfo['health_info'][_][item_]}")
                        match_state = False
                        break

        if match_client and match_state:
            self.log.debug("Health Report is match Client information")
        else:
            raise Exception("Health Report is NOT match Client information")