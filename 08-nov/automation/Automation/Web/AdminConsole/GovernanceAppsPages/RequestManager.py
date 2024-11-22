# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the request Manager page.


Classes:

    RequestManager() ---> GovernanceApps() ---> _Navigator() ---> login_page --->
    AdminConsoleBase() ---> object()


RequestManager  --  This class contains all the methods for action in Request
    Manager page and is inherited by other classes to perform GDPR related actions

    Functions:

    add_request()                  --  adds an request
    search_for_request()           -- Searches for an request
    navigate_to_request_details()  -- Navigates to request manager details page
    delete_request()               -- Deletes a specific request
    assign_reviewer_approver()     -- Assign reviewer and approver to a request

"""
from dynamicindex.utils.constants import (DELETE_FROM_BACKUP,
                                          DOCUMENT_CHAINING, REDACTION,
                                          REQUEST_CONFIGURED)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction


class RequestManager:
    """
     This class contains all the methods for action in the Request Manager page
    """

    create = None
    delete = None
    configure = None
    constants = None

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__admin_console.load_properties(self)
        self.create = _CreateRequest(self.__admin_console)
        self.delete = _DeleteRequest(self.__admin_console)
        self.configure = _ConfigureRequest(self.__admin_console)
        self.constants = _RequestManagerConstants()

    @PageService()
    def search_for_request(self, request_name):
        """
        Searches for an request

            Args:
                request_name (str)  - request name to be searched for

            Returns True/False based on the presence of the request
        """
        __flag = False
        self.__table.apply_filter_over_column("Name", request_name)
        if self.__admin_console.check_if_entity_exists("link", request_name):
            __flag = True
        return __flag

    @WebAction()
    def click_request_action(self, request_name, action_name):
        """
        Clicks on an request's action item
            Args:
                request_name (str)  - request action item to be clicked
        """
        self.__table.access_action_item(request_name, action_name)

    def select_request_by_name(self, request_name):
        """
               Select request by request_name
                   Args:
                       request_name (str)  - request name to be selected
               """
        self.__table.access_link(request_name)

    def get_status(self, request_name):
        """
        Get status of request
        Args:
                request_name (str)  - request name
        :return: status
        """
        self.search_for_request(request_name)
        _status = self.__table.get_column_data(
            self.__admin_console.props['label.status']
        )
        return _status


class _RequestManagerConstants:
    """
    __RequestManagerConstants are constants required for request operations
    """
    DELETE = "DELETE"
    EXPORT = "EXPORT"
    entities_list = [
        'Credit card number',
        'US Social Security number',
        'Email']
    approval_url_suffix = "webconsole/forms/?tab=1&filter=true"


class _DeleteRequest:
    """
        Delete a request from request manager
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console

    @PageService()
    def delete_request(self, request_name):
        """
        Delete a request
        :param request_name: Request Name
        """
        _request = RequestManager(self._admin_console)
        _request.click_request_action(
            request_name, self._admin_console.props['label.taskmanager.type.delete'])
        self._admin_console.click_button('Yes')
        self._admin_console.check_error_message()


class _CreateRequest:
    """
            Create a request using request manager
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__dropdown = RDropDown(admin_console)

    @WebAction()
    def _click_add_request(self):
        """
        Click add request
        """
        self.__table.access_toolbar_menu(
            self._admin_console.props['label.taskmanager.add'])

    @WebAction()
    def _select_delete_from_backup(self, enable_option=False):
        """
        Enable delete from backup
        :param enable_option: True to enable
        """
        if enable_option:
            self._admin_console.checkbox_select(
                self._admin_console.props['label.deleteFromBackup']
            )

    @WebAction()
    def _enable_redaction(self, enable_option=False):
        """
        Enable redaction
        :param enable_option: True to enable
        """
        if enable_option:
            self._admin_console.enable_toggle(0)

    @WebAction()
    def _enable_document_chaining(self, enable_option=False):
        """
        Enable document chaining
        :param enable_option: True to enable
        """
        if enable_option:
            self._admin_console.enable_toggle(1)

    @WebAction()
    def _select_request_type(self, request_type):
        """
        Select request type
        :param request_type: Request Type
        """
        if request_type == _RequestManagerConstants.DELETE:
            self._admin_console.select_radio(value=_RequestManagerConstants.DELETE)

        elif request_type == _RequestManagerConstants.EXPORT:
            self._admin_console.select_radio(value=_RequestManagerConstants.EXPORT)

    @WebAction()
    def _search_select_entity(self, entity_type_list):
        """
         Search and select an entity
         :param entity_type_list (list): list of entities to select
        """
        self.__dropdown.select_drop_down_values(
            values=entity_type_list, drop_down_id="EntitiesDropdown")

    @WebAction()
    def _set_input_by_name(self, locator, value):
        """
        Type inputs
        Args:
            locator (str) - locator
            value(str) - value
            """
        self._admin_console.fill_form_by_id(locator, value)

    @WebAction()
    def _set_input_by_xpath(self, locator, value):
        """
        Types input
        Args:
            locator (str) - Input element's xpath
            value(str) - value
        """
        self._admin_console.driver.find_element(By.XPATH, 
            locator).send_keys(value)

    @WebAction()
    def _select_configure_later(self):
        """
        Selects 'configure later' in the create request box
        """
        self._admin_console.click_button_using_id("Cancel")

    @PageService()
    def navigate_to_request_details(self, request_name):
        """
        Navigates to the request manager details page

            Args:
                request_name (str)  - request name details to be navigated
                :raise If request is not found

        """
        _request = RequestManager(self._admin_console)
        try:
            _request.click_request_action(
                request_name, self._admin_console.props['label.taskDetail.detail'])

        except BaseException:
            raise CVWebAutomationException(
                f"The request {request_name} is not present")

    @PageService()
    def add_request(self, request_name, requester, entity_type, entity, request_type, **kwargs):
        """
        Adds a request
            :param request_name    (str)   --  request name to be added
            :param requester    (str)  -- requester
            :param entity_type    (str)  -- entity type e.g. credit card
            :param entity    (str)  -- value of entity
            :param request_type    (str)  -- request type e.g. export or delete
            **kwargs  (dict)  --  Optional arguments.

                Available kwargs options:

                    delete_from_backup  (bool)  -- To delete from backup

                    redaction           (bool)  -- To redact sensitive info

                    document_chaining   (bool)  -- To enable document chaining

            :return _flag (bool) -- Request creation fails or passes
            Raise:
                CVWebAutomationException if request addition failed

        """
        _flag = False
        _delete = _DeleteRequest(self._admin_console)
        _request = RequestManager(self._admin_console)
        _options = [DELETE_FROM_BACKUP, REDACTION, DOCUMENT_CHAINING]
        if _request.search_for_request(request_name):
            _delete.delete_request(request_name)
        else:
            self._admin_console.log.info("Going to create a new request")
        self._click_add_request()
        self._admin_console.wait_for_completion()
        self._set_input_by_name("requestName", request_name)
        self._select_request_type(request_type)
        if request_type == _RequestManagerConstants.DELETE:
            if _options[0] in kwargs and kwargs.get(_options[0]):
                self._select_delete_from_backup()
        elif request_type == _RequestManagerConstants.EXPORT:
            if _options[1] in kwargs and kwargs.get(_options[1]):
                self._enable_redaction()
            if _options[2] in kwargs and kwargs.get(_options[2]):
                self._enable_document_chaining()

        self._set_input_by_name("requestor", requester)
        self._search_select_entity([entity_type])
        if entity:
            locator = f"//label[contains(text(),'{entity_type}')]/following-sibling::div/input"
            self._set_input_by_xpath(locator, entity)
            self._admin_console.driver.find_element(By.XPATH, 
                locator).send_keys(Keys.RETURN)
        self._admin_console.wait_for_completion()
        self._admin_console.click_button_using_id("Next")
        self._admin_console.wait_for_completion()
        self._select_configure_later()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()
        _status = _request.get_status(request_name)
        if 'Request created' in _status:
            _flag = True
        return _flag


class _ConfigureRequest:
    """
        Configure project, reviewer and approver association
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = RDropDown(admin_console)

    @WebAction()
    def _set_project(self, project):
        """
        Sets project
        """
        self.__dropdown.select_drop_down_values(0, values=[project])

    @WebAction()
    def _set_reviewer(self, reviewer):
        """Sets reviewer"""
        self.__dropdown.select_drop_down_values(1, values=[reviewer], partial_selection=True)

    @WebAction()
    def _set_approver(self, approver):
        """
        Sets approvers
        """
        self.__dropdown.select_drop_down_values(2, values=[approver], partial_selection=True)

    @WebAction()
    def _select_approver(self):
        """
        Select approver
        """
        self._admin_console.select_hyperlink(
            self._admin_console.props['label.taskmanager.approvers']
        )

    @WebAction()
    def _select_reviewer(self):
        """
        Select reviewer
        """
        self._admin_console.select_hyperlink(
            self._admin_console.props['label.taskmanager.reviewers']
        )


    @WebAction()
    def _click_request_manager(self):
        """
        Click request manager link
        """
        self._admin_console.select_hyperlink(
            self._admin_console.props['label.taskmanager']
        )

    @PageService()
    def assign_reviewer_approver(self, request_name, approver, reviewer, project_name):
        """
                Searches for an request
                    Args:
                        :param request_name (str)  - request name to be searched for
                        :param approver (str)  - approver
                        :param reviewer (str)  - reviewer
                        :param project_name    (str)  -- project name to be selected
                    Returns True/False based on the presence of the request
                """
        _flag = False
        _request = RequestManager(self._admin_console)
        _request.select_request_by_name(request_name)
        self._admin_console.wait_for_completion()
        self._set_project(project_name)
        self._admin_console.log.info(f"Selected project {project_name}")
        self._set_reviewer(reviewer)
        self._set_approver(approver)
        self._admin_console.click_button_using_id("Submit")
        self._admin_console.wait_for_completion()
        self._click_request_manager()
        self._admin_console.check_error_message()
        _status = _request.get_status(request_name)
        if REQUEST_CONFIGURED in _status:
            _flag = True
        return _flag
