# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
 This is the basic Admin console page operation for AD agent
 AzureADPage
     wait_for_job_completion        waiting job complete

     backup        run a azure ad back up job

     backup_submit    submit a backup job

     restore     run a azure ad restore job

     restore_submit     submit a restore job

     browse    browse azrue ad client

     browse_pick    pick azure ad object from browse page

     browse_to_client    return from browse window to client page

     _ad_browse_left_penal    pick azure ad type from left panel

     _ad_browse_right_panel_search    get objects from right panel

     _ad_browse_right_panel_pick    pick objects from right panel

      compare_properties    compare at two time stamps

      view_properties    view properties of a user

      download_properties    download properties of a user

      search_for_user    search for user

      __click_client_restore    click client restore button

      __click_cancel_properties    click cancel button


Know issue:
1. when azure ad client is created, cs start a backup job automatically. backup job may failed to start in thi case,
 need to check existing backup job in the future.

"""

import datetime
from time import sleep
from selenium.webdriver.common.by import By
from Web.AdminConsole.AD.page_ops import check_element, check_link_text
from Web.AdminConsole.Components.panel import  RPanelInfo
from Web.AdminConsole.Components.table import Table
from Web.Common.exceptions import CVWebAutomationException
from Application.AD.ms_azuread import AzureAd
from Web.AdminConsole.Components.panel import ModalPanel
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.Components.dialog import RModalDialog
from Application.AD.exceptions import ADException

class AzureADPage:
    """class for auzre ad page"""

    def __init__(self, adminconsole):
        """
        initial auzre ad page
        Args:
            admin_console    object admin console page object
        """
        self._admin_console = adminconsole
        self.driver = adminconsole.driver
        self.appname = "cvaad"
        self.log = adminconsole.log
        self.table_ = Table(adminconsole)
        self.panelinfo = RPanelInfo(self._admin_console)
        self.__rmodal_dialog = RModalDialog(self._admin_console)
        self.__jobs = Jobs(self._admin_console)

    @PageService()
    def backup(self, backuptype="Incremental"):
        """
        submit a backup job and wait the job compelted
        Args:
            backuptype  str     backup type, choose from: Inc, Full
        """
        self.backup_submit(backuptype=backuptype)
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)

    @PageService()
    def backup_submit(self, backuptype="Inc"):
        """
        Args:
            backuptype  str     backup type, choose from: Inc, Full
        """
        self.log.debug("start a backup job")
        self.__click_client_backup()
        self.select_backup_type(backuptype)
        self.__rmodal_dialog.click_submit()

    @PageService()
    def restore(self, clientname, type_, name):
        """
        Args:
            clientname    str    client name
            type_    str    object type, select from the following type
                                    user, group, reg_app, ent_app
            name    str    object name
        """
        self.restore_submit(type_, name)
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        self.browse_to_client(clientname)

    @PageService()
    def restore_submit(self, type_, name):
        """
        submit a restore job
            type_    str    object type, select from the following type
                                    user, group, reg_app, ent_app
            name    str    object name
        """
        self.browse_pick(type_, name)
        self._admin_console.wait_for_completion()
#        self.driver.find_element(By.XPATH, "//span[text()='Restore']").click()
        self._admin_console.wait_for_completion()
        check_element(self.driver,"id","restoreDropdown").click()
        self._admin_console.wait_for_completion()
        self._admin_console.select_hyperlink("Restore items across pages")
        modal_ = ModalPanel(self._admin_console)
        modal_.submit(wait_for_load=False)

    @PageService()
    def browse(self, type_, clientname):
        """
        Args:
            type_    (str)    object type, select from the following type
                                user, group, reg_app, ent_app
            clientname    str    clientname
        """
        self.log.debug("open a browse window")
        self._admin_console.refresh_page()
        try:
            check_link_text(self.driver, "Restore").click()
        except:
            self.log.debug("in sp32 using button")
            self._admin_console.click_button_using_text("Restore")
        self._admin_console.wait_for_completion()
        self._ad_browse_left_panel(type_)
        self._admin_console.wait_for_completion()
        objsinfo = self._ad_browse_right_panel()
        self.browse_to_client(clientname)
        return objsinfo

    @PageService()
    def browse_pick(self, type_, name, date_=None):
        """
        select the azure ad object based on type_ and name
        Args:
            type_    str    object type, select from the following type
                                    user, group, reg_app, ent_app
            name    str    object name
        """
        self.log.debug("open a browse pick window")
        self._admin_console.refresh_page()
        self._admin_console.wait_for_completion()
        if date_:
            self.log.debug(f'will pick the particular time to restore {date_}')
 #           self.calendar_pick(date_)
        else:
            self.log.debug("will browse from latest data")
            try:
                check_link_text(self.driver, "Restore").click()
            except:
                self.log.debug("on latest sp3201, may need differnet call")
                self._admin_console.click_button_using_text("Restore")
        self._admin_console.wait_for_completion()
        self._ad_browse_left_panel(type_)
        self._ad_browse_right_panel_pick(name)

    @PageService()
    def browse_to_client(self, clientname):
        """
        return to client page from browse window
        Args:
            clientname    str     client name
        """
        self.log.debug(f"from browse page to {clientname} page")
        # the clietn name will be trucate if it is too long
        try:
            check_link_text(self.driver, clientname).click()
        except:
            self.log.debug("it seem the nav-link is too long ,check antoher way")
            navlinks = self.driver.find_elements(By.CLASS_NAME,"nav-link")
            for _ in navlinks:
                self.log.debug(f"the nav link is {_.text}")
                if _.text != "Active Directory":
                    _.click()
                    self._admin_console.wait_for_completion()

    @PageService()
    def _ad_browse_left_panel(self, type_):
        """
        pick the object type from left panel
        Args:
            type_    str    object type, select from the following type
                                    user, group, reg_app, ent_app
        """

        leftpanel = check_element(self.driver, "class", "treeview")
        if not leftpanel:
            self.log.debug("from sp3001 to sp32, use different name")
            self._admin_console.wait_for_completion()
            sleep(60)
            self.log.debug("wait 60 seconds to replay the index")
            leftpanel = self.driver.find_element(By.ID, "azureADBrowseTree")
            self.log.debug(f"found the new leftpanel {leftpanel.text}")
        try:
            childnodes = leftpanel.find_elements(By.CLASS_NAME,"childNode")
        except:
            self.log.debug("sp3001 and sp32")
            childnodes = leftpanel.find_elements(By.CLASS_NAME, "k-item")
            self.log.debug(f"found total {len(childnodes)} children nodes")
        type_mapper = {"user" : "Users",
                       "group" : "Groups",
                       "reg_app" : "App registrations",
                       "ent_app" : "Enterprise applications"}
        for _ in childnodes:
            if _.text == type_mapper[type_]:
                self.log.debug(f"find {type_}, will open the object tree")
                _.click()
                break


    @PageService()
    def _ad_browse_right_panel(self):
        """
        get azure ad objects list
        """
        pageinfo = check_element(self.driver, "class", 'k-pager-info')
        self.log.debug(f"page info is {pageinfo.text}")
        totalitems = pageinfo.text.split("of")[1].split("items")[0].strip()
        totalitems = int(totalitems)
        self.log.debug(f"found total {totalitems} objects")
        if pageinfo:
            pagesize = check_element(self.driver, "class", 'k-pager-sizes')
            self.log.debug(f"page size information {pagesize.text}")
        return totalitems

    @PageService()
    def _ad_browse_right_panel_search(self, name):
        """
        search azure ad objects base don name
        Args:
            name    str    azure ad object name
        """
        self.log.debug(f"search {name} form right panel")
        searchbox = check_element(self.driver, "class", "azureSearchBox")
        if len(searchbox.text.split("\n")) == 1:
            self.log.debug("open search box")
            searchbox.click()
        self._admin_console.wait_for_completion()
        check_element(self.driver,"id","searchAllInp").send_keys(name)
        self._admin_console.wait_for_completion()
        check_element(self.driver, "class","azureSearchBox-buttons").click()
        self._admin_console.wait_for_completion()
        if check_element(self.driver, "class", 'k-pager-info').text == "":
            self.log.debug("all result in one page")
        else:
            self.log.debug("return more than 1 page result, \
                            please narrow down the search")

    @PageService()
    def _ad_browse_right_panel_pick(self, name):
        """
        select particular objects from right panle for restore
        Args:
            name    str    azure ad object name
        """
        self._ad_browse_right_panel_search(name)
        table_ = Table(self._admin_console)
        self.log.debug(f"found the following entry: {table_.get_table_data()}")
        table_.select_all_rows()

    @WebAction(delay=2)
    def __click_client_backup(self):
        """Clicks the client level backup"""
        self.driver.find_element(By.XPATH, '//button[@id="APP_LEVEL_BACKUP"]').click()

    @WebAction(delay=2)
    def select_backup_type(self, backuptype='Incremental'):
        """Selects the backup type
        Args:
            backuptype(str): AD Backup Type
        """
        self.driver.find_element(By.XPATH, f'//span[text()="{backuptype}"]').click()

    @WebAction(delay=2)
    def __job_details(self, tenant_user_view=False):
        """Waits for job completion and gets the job details"""
        try:
            job_id = self._admin_console.get_jobid_from_popup(wait_time=1)
        except CVWebAutomationException:
            try:
                job_id = self._admin_console.get_jobid_from_popup(wait_time=1)
            except CVWebAutomationException:
                if not tenant_user_view:
                    self.driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
                self._admin_console.click_button("View jobs")
                self.__jobs.access_active_jobs()
                job_id = self.__jobs.get_job_ids()[0]

            # Waiting for all job details to get updated on job page
            sleep(60)
            job_details = self.__get_job_details(job_id)
        else:
            job_details = self.__jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('job details: %s', job_details)
        # job_details[self.__admin_console.props['Status']]
        if (job_details['Status'] not in ["Committed", "Completed", "Completed w/ one or more errors"]):
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

    def job_check_bakcup(self, clientname, wait=True):
        """
        check if another backup job is running on the client
        """
#        self._admin_console.navigator.navigate_to_jobs()
        self._admin_console.navigator.search_nav_by_id("Jobs",'navigationItem_activeJobs')

        self.log.debug("will wait 20 seconds to check the active jobs")
        sleep(20)
        self.__jobs.access_active_jobs()
        active_jobs = self.table_.get_table_data()
        self.log.debug(f"here is the active jobs {active_jobs}")
        if active_jobs != {} and clientname in  active_jobs['Destination client']:
            self.log.debug(f"found the backup job for {clientname}")
            job_id = active_jobs['Job ID'][active_jobs['Destination client'].index(clientname)]
            if wait:
                self.log.debug(f"will wait {job_id} to complete")
                self.__jobs.job_completion(job_id=job_id)
                self.log.debug("job is completed")
                running_job = False
            else:
                running_job = True
        else:
            running_job = False
        return running_job

    @PageService()
    def compare_properties(self, user_name, from_time, to_time):
        """
        this function perform compare for two timestamps
        Args:
            user_name str user name to compare
            from_time str from time to compare
            to_time str to time to compare
        Return: table data for compare result
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab("Overview")
        self.__click_client_restore()
        self._admin_console.refresh_page()
        self.search_for_user(user_name)
        table_ = Table(self._admin_console)
        table_.access_action_item(entity_name=user_name, action_item="Compare")
        table_.access_action_item(entity_name=from_time, action_item="Add to compare")
        table_.access_action_item(entity_name=to_time, action_item="Compare with selected version")
        self._admin_console.wait_for_completion()
        table_data = table_.get_table_data()
        self.__click_cancel_properties()  # first time for compare result
        self.__click_cancel_properties()  # second time for compare panel
        return table_data

    @PageService()
    def view_properties(self, user_name):
        """
        this function opens a view property panel
        Args:
            user_name    str    user name for which view properties is required
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab("Overview")
        self.__click_client_restore()
        self._admin_console.refresh_page()
        self.search_for_user(user_name)
        table_ = Table(self._admin_console)
        table_.access_action_item(entity_name=user_name, action_item="Properties")
        table_data = table_.get_table_data()
        self.__click_cancel_properties()
        return table_data

    @PageService()
    def download_properties(self, user_name):
        """
        Performs download properties for a user
        Args:
            user_name    str    user name for which download is performed
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab("Overview")
        self.__click_client_restore()
        self._admin_console.refresh_page()
        self.search_for_user(user_name)
        table_ = Table(self._admin_console)
        table_.access_action_item(entity_name=user_name, action_item="Download")

    @PageService()
    def search_for_user(self, user_name):
        """
        search for user using search box in a browse window
        Args:
            user_name    str    user name to search
        """
        self.driver.find_element(By.XPATH, "//input[contains(@class,'azureSearch')]").click()
        self._admin_console.fill_form_by_id(element_id='searchAllInp', value=user_name)
        self._admin_console.click_button_using_id("submit")

    @WebAction(delay=2)
    def __click_client_restore(self):
        """Clicks the client level restore"""
        self.driver.find_element(By.XPATH, '//button[@id="APP_LEVEL_RESTORE"]').click()

    @WebAction(delay=2)
    def __click_cancel_properties(self):
        """Click on cancel button"""
        self.driver.find_element(By.XPATH, '//button[contains(., "Cancel")]').click()

class CvAad():
    """ class for combinated operation"""
    def __init__(self, azureadpage, tcinputs):

        self.azureadpage = azureadpage
        self.tcinputs = tcinputs
        self.adminconsole = azureadpage._admin_console
        self.log = self.adminconsole.log
        self.driver = azureadpage.driver
        self.aad_ins = None
        self.aad_types = None
        self.newlib = self.tcinputs['NewAzureadLib']
        self.aad_setup()

    def aad_setup(self):
        """
        setup azure ad connection
        """
        if self.newlib:
            aad_credential = [self.tcinputs['ClientId'],
                              self.tcinputs['ClientPass'],
                              self.tcinputs['TenantName']]
        else:
            aad_credential = [self.tcinputs['TenantName'],
                              self.tcinputs['AdminUser'],
                              self.tcinputs['AdminPassword'],
                              self.tcinputs['ClientId'],
                              self.tcinputs['ClientPass']]
        self.log.debug(f"here is the azure ad connection credential: {aad_credential}")
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.aad_types = self.tcinputs['types']

    def aad_cleanup(self, objs):
        """
        clean up objs created in the test
        Args:
            objs        (dict):    objecst list in each types
        """
        self.log.info(f"remove the {objs} from azure ad")
        for type_ in self.aad_types:
            try:
                self.aad_ins.type_operation(type_, "delete", objs=objs[type_])
            except:
                self.log.info(f"clean up objects failed, please manually check {objs}")
        self.log.debug("clean up job is done")

    def aad_simple_backup(self, backuptype="Incremental", objs=None, clientname=None):
        """
        run azure ad backup
        Args:
            backuptype:  (string)  pick the backup type from "Inc" and "Full"
            objs:       (lists)       objects to compare from previous job
        Return:
            return_obj      (lists)       objects form azure ad check
        """
        client_page_url = self.driver.current_url
        if not self.azureadpage.job_check_bakcup(clientname):
            self.log.debug("return to client page to process backup")
            self.driver.get(client_page_url)

        if backuptype == "Incremental":
            timestamp = int(datetime.datetime.now().timestamp())
            inc_objs = self.aad_ins.group_objs_create(types=self.aad_types,
                                                      prestring=f"inc_{timestamp}")
            self.log.debug(f"additional objects are created:{inc_objs}")
            for type_ in self.aad_types:
                if self.newlib:
                    self.log.debug("this is new library")
                else:
                    self.log.debug(f"There are total {len(objs[type_])} azure\
                                     ad {type_} objects from azure directory.")
            self.log.debug("wait 20 seconds to start the backup")
            sleep(20)

        if self.newlib:
            aad_objs = {}
        else:
            aad_objs = self.aad_ins.group_objs_check(types=self.aad_types)

        if backuptype == "Incremental":
            self.azureadpage.backup()
        elif backuptype == "Full":
            self.azureadpage.backup(backuptype="Full")

        self.log.debug("will wait 20 seconds before browse azure ad objects")
        sleep(20)

        for type_ in self.aad_types:
            self.log.debug(f"check {type_} from browse window")
            totalitem = self.azureadpage.browse(type_, clientname)
            self.log.debug(f"here are {totalitem} objects in type {type_}")

            if self.newlib:
                operation_ins = getattr(self.aad_ins, type_)
                count = operation_ins(operation="count")
                aad_objs[type_] = count
                self.log.debug(f"found total {count} {type_} objects with new azure ad library")

            if backuptype == "Incremental":
                if self.newlib:
                    self.log.debug("using the new library, jsut check the different")
                    self.log.debug(f"{type_} object has {aad_objs[type_]} objects in Azure and \
                                    backup result include {totalitem} entires")
                else:
                    if len(objs[type_]) != totalitem:
                        self.log.debug(f"after create new object, there are {totalitem} \
                                         in browse windows")
                        newobjs_count = totalitem - len(objs[type_])
                        self.log.debug(f"new {newobjs_count} is backup")
                    else:
                        self.log.debug(f"seem the result is match {totalitem}")
                return_obj = inc_objs
            elif backuptype == "Full":
                if self.newlib:
                    self.log.debug("will skip comparing with new library")
                    self.log.debug(f"{type_} object has {aad_objs[type_]} objects in Azure and \
                                    backup result include {totalitem} entires")
                    return_obj = aad_objs
                else:
                    if len(aad_objs[type_]) == totalitem:
                        self.log.info(f"{type_} objects find match number. \
                                        total number is {totalitem}")
                    else:
                        self.log.info(f"browse return {totalitem} objects while azure ad\
                                        return {len(aad_objs[type_])} objects")
                    return_obj = aad_objs
        return return_obj

    def aad_simple_restore(self, objs, clientname=None):
        """
        delete new inc objects then run restore
        Args:
            objs        (dict):    objecst list in each types, example:
        """
        self.log.info("will delete new objects and run restore job")
        self.log.debug(f"will delete the following {objs}")
        if self.newlib:
            before_delete = self.aad_ins.group_objs_check(objs)
        else:
            before_delete = self.aad_ins.group_objs_check(types=self.aad_types)
        for type_ in self.aad_types:
            if self.newlib:
                operation_ins = getattr(self.aad_ins, type_)
                self.log.debug("will use new library to delete object")
                operation_ins(operation="delete", **{"id": objs[type_]['id']})
            else:
                self.aad_ins.type_operation(type_, "delete", objs=objs[type_])
                sleep(30)
                deleted_objs = self.aad_ins.deleted_obj_list(type_)
                self.log.debug(f"here is the deleted objects {deleted_objs}")
        if self.newlib:
            after_delete = self.aad_ins.group_objs_check(objs)
        else:
            after_delete = self.aad_ins.group_objs_check(types=self.aad_types)

        for type_ in self.aad_types:
            self.log.debug(f"There areb {len(before_delete[type_])} objs\
                             in {type_} before delete")
            self.log.debug(f"There are {len(after_delete[type_])} objs\
                             in {type_} after delete")
            objs_name = []
            if self.newlib:
                objs_name.append(objs[type_]['displayName'])
            else:
                if isinstance(objs[type_], list):
                    for item in objs[type_]:
                        objs_name.append(item.display_name)
                else:
                    objs_name.append(objs[type_].display_name)
            self.log.debug(f"convert the objs to name for cv restore {objs_name}")
            self.azureadpage.restore(clientname, type_, objs_name)

        if self.newlib:
            after_restore = self.aad_ins.group_objs_check(objs)
        else:
            after_restore = self.aad_ins.group_objs_check(types=self.aad_types)

        for type_ in self.aad_types:
            if self.newlib:
                if after_restore[type_]['id'] == objs[type_]['id']:
                    self.log.debug(f"{type_} object {objs[type_]['displayName']} is restored with same id")
                else:
                    self.log.debug(f"{type_} object {after_restore[type_]['id']} is not match {objs[type_]['id']} after restore")
                    raise ADException("cvaad", 202, f"after restore is {after_restore} while the object is {objs}")
            else:
                self.log.debug(f"after restore is {after_restore}")