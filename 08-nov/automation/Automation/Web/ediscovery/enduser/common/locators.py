# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Xpaths of elements segregated based on the Pages they are present on.

These are the 5 classes defined in this module.

Locators:           Class representing common locators to all the classes.

LoginPageLocators:  Class representing locators occurring on the login page.

MainPageLocators:   Class representing locators occurring on the main page.

SearchPageLocators: Class representing locators occurring on the search page.

CommonSetLocators:  Class representing locators common to all sets.

MainPageLocators:

   set_searchengine()  --  Sets searchengine xpath.

CommonSetLocators:

   __init__()          --  Customizes some xpaths.

   set_jobid()         --  Sets the jobid.


"""
from selenium.webdriver.common.by import By


class Locators(object):
    """Common locators to all the classes."""
    BODY_ELEMENT = (By.TAG_NAME, "body")


class LoginPageLocators(object):
    """Locators occurring on the login page."""
    USERNAME_FIELD = (By.ID, 'x-auto-6-input')
    PASSWORD_FIELD = (By.ID, 'x-auto-7-input')
    LOGIN_BUTTON = (By.ID, 'x-auto-4')
    LOGIN_MENU = (By.ID, 'x-auto-5')


class MainPageLocators(object):
    """Locators occurring on the main page - the page you see just after you login to the site."""
    LOGOUT_BUTTON = (By.XPATH, "//button[contains(text(),'Logout')]")
    LOGGEDIN_USER_TEXT = (By.XPATH, "//b")
    LOGO_IMAGE = (By.CSS_SELECTOR, "img")
    APPLICATIONINITIALIZED_TEXT = (By.XPATH, "//span[contains(text(),'Application initialized')]")
    ADVANCEDSEARCH_BUTTON = (By.XPATH, "//button[text()='Advanced Search']")
    ADVANCEDSEARCH_CLOSE_BUTTON = (By.XPATH, "//div[9]/div/div/div/div/div/table/tbody/tr/td/div")
    BACKUPEXPAND_ARROW = (By.XPATH, "//body/div/div[4]/div/div")
    EXPAND_ARROW = (By.XPATH, "//body/div/div[2]/div/div")
    COLLAPSE_ARROW = (By.XPATH, "//body/div/div[4]/div/div//div")
    MYSETS_BUTTON_TEXT = (By.XPATH, "//button/div[contains(text(),'My Sets')]")
    MYSETS_BUTTON = (By.XPATH, "//button/div[contains(text(), 'My Sets')]/..")
    EVENTS_BUTTON = (By.XPATH, "//button[contains(text(),'Events')]")

    # Advanced-search menu options
    SEARCHOPTIONS_LINK = (By.XPATH, "//span[contains(text(),'Search Options')]")
    SEARCHENGINE_MENU = (By.XPATH, "//div[2]/div/div[2]/div/div/div/div[2]/div/img")
    KEYWORD_LINK = (By.XPATH, "//span[contains(text(),'Keyword')]")
    KEYWORD_TEXTAREA = (By.XPATH, "//label[contains(text(),'Keyword')]/parent::div/div/input")
    SEARCH_SUBMIT_BUTTON = (By.XPATH, "//button[contains(text(),'Submit')]")

    def set_searchengine(self, searchengine):
        """Sets searchengine xpath.

        Args:
            searchengine (str)  --  Name of the searchengine.
        """
        return (By.XPATH, "//div[contains(text(), '" + searchengine + "')]")


class SearchPageLocators(object):
    """Locators occurring on the search page."""
    SEARCHTAB_CLOSE_BUTTON = (By.XPATH, "//li[2]/a")
    SEARCHTAB2_CLOSE_BUTTON = (By.XPATH, "//li[3]/a")
    STATUS_TEXT = (
        By.XPATH,
        "//div[1]/div[3]/div[2]/div[1]/div/table/tbody/tr/td[1]/table/tbody/tr/td/div/span")
    APPLICATIONALERT_TEXT = (By.XPATH, "//html/body/div[9]")
    FILESEMAILS_MENU = (By.XPATH, "//button[contains(text(),'Files / Emails')]")
    FILESEMAILS_BUTTON = (By.XPATH, "//a[contains(text(),'Files / Emails')]")
    FILES_BUTTON = (By.XPATH, "//a[contains(text(), 'Files')]")
    EMAILS_BUTTON = (By.XPATH, "//a[contains(text(),'Emails')]")
    DISPLAY_RESULT_ALL_TEXT = (By.XPATH, "//div/table/tbody/tr/td/table/tbody/tr/td/div")
    DISPLAY_RESULT_FS_TEXT = (By.XPATH, "(//*[contains(text(),'Displaying')])[2]")
    DISPLAY_RESULT_EMAIL_TEXT = (By.XPATH, "(//*[contains(text(),'Displaying')])[3]")
    SAVEQUERY_BUTTON = (By.XPATH, "//button[contains(text(),'Save Query')]")
    EXPORT_TO_BUTTON = (By.XPATH, "//button[contains(text(), 'Export To')]")
    PST_LINK = (By.XPATH, "//a[contains(text(),'PST')]")
    CAB_LINK = (By.XPATH, "//a[contains(text(),'CAB')]")
    NSF_LINK = (By.XPATH, "//a[contains(text(),'NSF')]")
    HTML_LINK = (By.XPATH, "//a[contains(text(),'HTML')]")


class CommonSetLocators(object):
    """Locators common to all the sets."""
    CONTAINER_EXISTS_TEXT = "Container already Exists. Please Use Different Name"
    EXPAND_QUERYSET = (By.XPATH, "//div[3]/div[2]/div/div/span[2]")
    DELETE_BUTTON = (By.XPATH, "//button[contains(text(),'Delete')]")
    DELETE_LAST_BUTTON = (By.XPATH, "(//button[contains(text(),'Delete')])[last()]")
    CONFIRMDELETION_TEXT = (By.XPATH, "//span[contains(text(),'Confirm Deletion')]")
    DELETESELECTED_RADIO_BUTTON = (By.XPATH, "//label[contains(text(),'Selected')]/../input")
    DELETEPAGE_RADIO_BUTTON = (By.XPATH, "//label[contains(text(),'This page')]/../input")
    DELETEALL_RADIO_BUTTON = (By.XPATH, "//label[contains(text(),'All')]/../input")
    SETNAME_EXISTS_TEXT = (By.XPATH, "//span[contains(text(), 'Do you want to use the name')]")
    CONFIRM_BUTTON = (By.XPATH, "//button[contains(text(),'Yes')]")
    SECONDMENU_OK_BUTTON = (By.XPATH, "(//button[contains(text(),'OK')])[2]")
    FIRSTMENU_OK_BUTTON = (By.XPATH, "//button[contains(text(),'OK')]")
    SET_CREATENEW_TEXT = (By.XPATH, "//div[contains(text(),'Create New')]")
    SELECTIONRANGE_SELECTED_RADIO_BUTTON = (
        By.XPATH, "//label[contains(text(),'Selected')]/preceding-sibling::input")
    SELECTIONRANGE_THISPAGE_RADIO_BUTTON = (
        By.XPATH, "//label[contains(text(),'This page')]/preceding-sibling::input")
    SELECTIONRANGE_ALL_RADIO_BUTTON = (
        By.XPATH, "//label[contains(text(),'All')]/preceding-sibling::input")
    JOBSTATUS_TEXT = (By.XPATH, "//span[contains(text(),'Job Status')]")
    JOBSTATUS_REFRESH_BUTTON = (
        By.XPATH, "//*[contains(text(),'Displaying')]/parent::td/parent::tr/td[3]//em/button")
    JOBRUNNING_TEXT = (By.XPATH, "//*[contains(text(),'Running')]")
    JOB_ID_TEXT = ''
    DISPLAY_SET_ITEMS_TEXT = (By.XPATH, "((//div[contains(text(),'Updated')])/parent::td/preceding-sibling::td)[last()]")
    # Sharing permissions
    SHARE_BUTTON = (By.XPATH, "//button[contains(text(),'Share')]")
    SHARE_USERADD_BUTTON = (By.XPATH, "//button[text()='Add']")
    SHARE_USERORGROUP_TEXT = (By.XPATH, "//span[contains(text(),'User or Group')]")
    SHARE_GROUPUSERNAMES_TEXT = (By.XPATH, "//*[contains(text(),'Group/User Names')]")
    SHARE_ADDAPPEND_RADIO_BUTTON = (
        By.XPATH, "//td[div='Add/Append']/following-sibling::td/div/div")
    SHARE_DELETE_RADIO_BUTTON = (By.XPATH, "//td[div='Delete']/following-sibling::td/div/div")
    SHARE_EXECUTE_RADIO_BUTTON = (By.XPATH, "//td[div='Execute']/following-sibling::td/div/div")
    SHARE_VIEW_RADIO_BUTTON = (By.XPATH, "//td[div='View']/following-sibling::td/div/div")
    SHARE_STATUS_TEXT = (By.XPATH, "//span[contains(@class, 'x-status-text')]")
    SHARE_MESSAGE_TEXT = (
        By.XPATH,
        "//html/body/div[1]/div[3]/div[2]/div[1]/div/table/tbody/tr/td[1]/table/tbody/tr/td/div/span")

    # Query set xpaths
    SAVEQUERY_QUERYNAME_INPUT_FIELD = (By.XPATH, "//div[label='Query Name']/div/div/input")
    SAVEQUERYMENU_CLOSE_BUTTON = (
        By.XPATH, "(//*[contains(text(),'Save Query')])[2]/preceding-sibling::div")
    MAXIMUMQUERIES_TEXT = (
        By.XPATH,
        "//span[contains(text(),'Cannot perform operation because you already saved maximum number of queries allowed.')]")
    EXECUTE_PERMISSION_NOT_AVAILABLE = (By.XPATH, "//span[contains(text(),'Execute permission is not available for')]")
    # Export set xpaths
    DOWNLOADNAME_INPUT_FILED = (By.XPATH, "//div[label='Download Name']/div/div/input")
    EXPORTMENU_CLOSE_BUTTON = (
        By.XPATH, "(//*[contains(text(),'Export To')])[2]/preceding-sibling::div")

    # Set specific locators
    SHARE_WITHUSER_TEXT = ''
    SETTYPE_TEXT = ''
    SETTYPE2_TEXT = ''
    SETNAME_TEXT = ''
    EXISTINGSET_NAME = ''
    SETDELETED_TEXT = ''
    SET_EXPAND_ARROW = ''
    DELETESET_RADIO_BUTTON = ''

    QUERYNAME_LINK = ''
    QUERYSAVED_TEXT = ''

    def __init__(self, settype, setname, itemname, username):
        """Customizes some xpaths.

        Args:
            settype  (str)  --  Type of the set.

            setname  (str)  --  Name of the set.

            itemname (str)  --  Name of the item.

            username (str)  --  Name of the user with whom the set is to shared.
        """
        self.SHARE_WITHUSER_TEXT = (By.XPATH, "//span[contains(text(), '" + username + "' )]")
        self.SETTYPE_TAB = (By.XPATH, "//li[2]//span//span")
        self.SETTYPE_TEXT = (By.XPATH, "//span[contains(text(), '" + settype + "')]")
        self.SETTYPE2_TEXT = (By.XPATH, "(//span[contains(text(), '" + settype + "')])[2]")
        self.SETNAME_TEXT = (By.XPATH, "//span[contains(text(), '" + setname + "')]")
        self.SET_EXPAND_ARROW = (By.XPATH, "//div[label='" + settype + "']/div/div/img")
        self.SETDELETED_TEXT = settype + " " + setname + " deleted successfully."
        self.SETTAB = (By.XPATH, "//span[contains(text(),'" + setname + "')]")
        self.EXISTINGSET_NAME = (By.XPATH, "//div[contains(text(),'" + setname + "')]")
        self.CREATENEWSET_INPUT_FIELD = (
            By.XPATH, "//div[label='" + settype + " Name']/div/div/input")
        # Query set custom xpaths
        self.QUERYNAME_LINK = (By.XPATH, "//a[contains(text(),'" + itemname + "')]")
        self.QUERYSAVED_TEXT = "Query " + itemname + " saved successfully."
        self.DELETESET_RADIO_BUTTON = (
            By.XPATH, "//label[contains(text(),'" + settype + "')]/../input")

    def set_jobid(self, jobid):
        """Sets the jobid.

        Args:
            jobid (int)  --  Job id.
        """
        self.JOB_ID_TEXT = (By.XPATH, "//div[contains(text(),'" + jobid + "')]")
