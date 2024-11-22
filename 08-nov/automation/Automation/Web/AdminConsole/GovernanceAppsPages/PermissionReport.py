from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Entitlement Management page

Classes:

    PermissionReport() ---> GovernanceApps() ---> object()


PermissionReport --  This class contains all the methods for action in
    Entitlement management page

    Functions:
    selectuser() -- select user filter
    selectextension() -- select extension filter
    filter_ownerextension -- select user and extension filter
    change_file_permission_for_client()  -- change file permission for files of specified client
    change_file_permission_for_clientGrp --change permission for files in client group
    revert_acls - revert all user permission changes that was made during the test

"""
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from Web.AdminConsole.Components.table import Table, CVTable
from Web.AdminConsole.Components.panel import PanelInfo, DropDown
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction


class PermissionReport(GovernanceApps):
    """
     This class contains all the methods for action in Entitlement Management page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__table = Table(self.__admin_console)
        self.__panelinfo = PanelInfo(self.__admin_console)
        self.__cvtable = CVTable(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)

    @WebAction()
    def __expand_tree_node(self, src_path, filename):
        """
        expand_tree_node

            Args:
                src_path (str)  - expand the folder path under file path tree node
                filename (str)  - filename

        """

        src = src_path.split('\\')
        src = [x for x in src if x != ""]
        src.append(filename)

        for fpath in src:

            if self.__admin_console.check_if_entity_exists(
                    "css", "span.loadMoreLink"):
                by_css = By.CSS_SELECTOR
                csstr = "span.loadMoreLink"
                WebDriverWait(
                    self.__admin_console.driver, 30).until(
                        ec.visibility_of_element_located(
                            (by_css, csstr)))
                while True:
                    try:
                        WebDriverWait(
                            self.__admin_console.driver, 30).until(
                                ec.visibility_of_element_located(
                                    (by_css, csstr))).click()
                        print("Load more clicked")
                    except Exception:
                        break

            if self.__admin_console.driver.find_elements(By.CLASS_NAME, 
                    "directory-tree-container"):
                elems = self.__admin_console.driver.find_elements(By.XPATH, 
                    "//div[contains(@class,'directory-tree-container')]" +
                    "//table[contains(@class, 'k-selectable')]//tr//td")

            else:
                raise CVWebAutomationException("failed to find the record")

            j = 1
            for elem in elems:

                fileelem = elem.find_element(By.XPATH, 
                    ".//span[contains(@class,'directory-tree-node')]")

                if fpath.lower() == fileelem.text.lower():
                    try:
                        elem.find_element(By.XPATH, 
                            ".//span[contains(@class,'k-i-expand')]").click()
                    except BaseException:
                        self.__admin_console.driver.execute_script(
                            "arguments[0].scrollIntoView();", fileelem)
                        self.__admin_console.driver.execute_script(
                            "arguments[0].click();", fileelem)

                    self.__admin_console.wait_for_completion()
                    break
                else:
                    j += 1
                    continue

            if j == len(elems) + 1:
                raise CVWebAutomationException(
                    "failed to find the file/folders " + fpath)

    @WebAction()
    def __click_user_permission(self):
        """
        for first user, find an available permission checkbox, click it to allow or deny
        the permission
        """

        uname = self.__table.get_column_data("User")[0]
        self.__table.expand_row(uname)
        self.__click_available_perm(uname)
        return uname

    @WebAction()
    def __click_available_perm(self, uname):
        """
        find a permission for input user which are not gray out, then click it
        Args:
            uname (str)  - user name

        Raise:
            Exception if all permission for the user are not available for modify
        """

        permlist = [
            '_deny_modify',
            '_allow_fullcontrol',
            '_allow_modify',
            '_allow_readandexecute',
            '_allow_read',
            '_allow_write',
            '_deny_write',
            '_deny_read',
            '_deny_readandexecute',
            '_deny_fullcontrol']

        uname = uname.replace('\\', '\\\\')
        flag = 0
        for perm in permlist:
            checkboxid = uname + perm
            element = self.__admin_console.driver.find_element(By.ID, 
                checkboxid)
            if element.is_enabled():
                self.__admin_console.driver.execute_script(
                    "arguments[0].click();", element)
                time.sleep(10)
                flag = 1
                break
        if flag == 0:
            raise CVWebAutomationException(
                "all permission for selected user are gray out")

    @WebAction()
    def __add_new_user(self, new_user):
        """
        add_new_user with read & write permission
        Args:
            new_user (str)  - new user name where read & write permission will be added

        Raise:
            Exception if new user is not found in AD
        """

        # click add user under selected file/folder permissions
        self.__admin_console.access_tile("AddNewUserButton")

        # search user on add user page
        xpath = "//input[contains(@name, 'searchComponent')]"
        if self.__admin_console.check_if_entity_exists("xpath", xpath):
            search = self.__admin_console.driver.find_element(By.XPATH, xpath)
            search.send_keys(new_user)
            time.sleep(30)
        else:
            raise CVWebAutomationException(
                "search user option is not available")

        if self.__admin_console.check_if_entity_exists(
                "xpath", "//div[contains(@class,'result-item')]/h5"):
            self.__admin_console.driver.find_element(By.XPATH, 
                "//div[contains(@class,'result-item')]/h5").click()
            self.__admin_console.click_button("Add")
        else:
            raise CVWebAutomationException(
                "could not find the new use in AD")

    @WebAction()
    def __click_revert_to_point(self, user):
        """click revert to this point action for input user"""
        try:
            self.__table.access_action_item(user, "Revert to this point")
        except BaseException:
            xpath = "//ul[contains(@style,'display: block')]" + \
                "//a[text()='Revert to this point']"
            self.__admin_console.driver.find_element(By.XPATH, 
                xpath).click()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_all_permission(self, tableid):
        """
        select all available permission changes on revert permission page

        Args:
            tableid (str) : table id
        """
        xpath = "//table[contains(@id,'" + tableid + "')]//tbody//tr"
        elems = self.__admin_console.driver.find_elements(By.XPATH, xpath)
        for elem in elems:
            if not elem.find_element(By.XPATH, 
                    ".//following-sibling::input").is_selected():
                element = elem.find_element(By.XPATH, 
                    ".//following-sibling::label")
                self.__admin_console.driver.execute_script(
                    "arguments[0].click();", element)
                time.sleep(10)

    @PageService()
    def change_file_acl_for_client(
            self,
            nwshare_name,
            src_path,
            file_name,
            new_user):
        """
        for selected file/folder, add one new user and change one available permission for first
        users

        Args:
            NWshare_name (str)  - network share name to be selected for client list
            src_path (str)  - the folder path for the file name where permission need be changed
            file_name (str)  - the file name for which permission will be changed
            new_user (str)  - the new user who will be added with read & write permission

        Raise:
            Exception if permission change failed
        """

        # select client and click apply button
        nwshare_names = []
        nwshare_names.append(nwshare_name)
        self.__dropdown.select_drop_down_values(0, nwshare_names)
        self.__admin_console.click_button("Apply")
        self.__admin_console.wait_for_completion()

        # expand the tree node until the specified file/folders
        self.__expand_tree_node(src_path, file_name)

        # for first user's permission, select one permission that is not grayed out
        # then click it to switch on or off
        uname = self.__click_user_permission()

        # add new user with default read/write permissions
        self.__add_new_user(new_user)
        time.sleep(10)

        # click review changes option and apply permission
        self.__admin_console.access_tile('ReviewChangesButton')
        self.__admin_console.click_button("Apply permission")

        # wait for Change permission job to finish. timeout (270seconds)
        i = 0
        while i < 10:
            bodytext = self.__admin_console.driver.find_element(By.CLASS_NAME, 
                "permissionsPreviewModalBody").text
            if bodytext.find("applied successfully") == -1:
                if i == 9:
                    raise CVWebAutomationException(
                        "time out waiting for Change permission job to finish")
                else:
                    time.sleep(30)
                    i += 1
                    continue
            else:
                self.__admin_console.log.info(
                    "Change permission job completed")
                break

        self.__admin_console.click_button("Ok")
        return uname

    @PageService()
    def revert_acls(self, user):
        """
        revert permission changes
        Args:
            user (str) - user name

        Raise:
            Exception if revert permission failed
        """

        # click activity under selected file/folder permissions
        self.__panelinfo.open_hyperlink_on_tile('Activity')
        self.__admin_console.wait_for_completion()

        # click "revert to this point" action for latest permission change
        self.__click_revert_to_point(user)
        # check all checkbox on revert permission page,
        self.__select_all_permission("permissionsMain")
        # click Revert Button
        self.__admin_console.click_button("Revert")

        # wait for revert permission job to finish. timeout (270seconds)
        i = 0
        while i < 10:
            bodytext = self.__admin_console.driver.find_element(By.CLASS_NAME, 
                "permissionsPreviewModalBody").text
            if bodytext.find("reverted successfully") == -1:
                if i == 9:
                    raise CVWebAutomationException(
                        "time out waiting for Change permission job to finish")
                else:
                    time.sleep(30)
                    i += 1
                    continue
            else:
                self.__admin_console.log.info(
                    "revert permission change job completed")
                self.__admin_console.click_button("Ok")
                break
