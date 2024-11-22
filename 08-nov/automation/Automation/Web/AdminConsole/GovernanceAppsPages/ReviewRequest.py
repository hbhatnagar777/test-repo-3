from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the request Manager page.


Classes:

    ReviewRequest() ---> GovernanceApps() ---> _Navigator() ---> login_page --->
    AdminConsoleBase() ---> object()


ReviewRequest  --  This class contains methods for reviewing actions in Request
    Manager page and is inherited by other classes to perform GDPR related actions

    Functions:

    review_approve_request()        -- Review Approve Request Action
    request_approval()              -- Request approval for a request
    approve_request()               -- Approves a request
    fetch_request_job()             -- Check job information for GDPR task approval
"""

import dynamicindex.utils.constants as cs
from selenium.common.exceptions import (ElementClickInterceptedException,
                                        ElementNotInteractableException)
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rfilter, Rtable
from Web.AdminConsole.GovernanceAppsPages.DataSourceReview import \
    DataSourceReview
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction


class ReviewRequest:
    """
        Review request based on entity and associated sensitive file
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._admin_console.load_properties(self)
        self.log = self._admin_console.log
        self.__table = Rtable(admin_console)
        self.__table_job = Rtable(admin_console, id="activeJobsTable")
        self.__job = Jobs(admin_console)
        self.__app = GovernanceApps(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self.__ds_review = DataSourceReview(self._admin_console)
        self.__page_container = PageContainer(self._admin_console, 'RequestDetails')
        self.table_map = {
            self._admin_console.props['label.datasource.file']:
                {"FilePath": "File Path", "FileName": "Name"},
            self._admin_console.props['label.datasource.onedrive']:
                {"FilePath": "Name", "FileName": "Name"}
        }

    @WebAction()
    def _unclick_reviewed_facet(self, facet_type, facet_name):
        """
        Closes the Review Status facet box in review page
        Args:
            facet_type(str) -- Type of facet box
            facet_name(str) -- Name of the facet label
        """
        xp = f"//label[contains(text(),'{facet_type}')]/following::span[text()='{facet_name}']/parent::div/span[2]"
        if self._admin_console.check_if_entity_exists("xpath", xp):
            self._admin_console.driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def _get_facet_count(self, facet_type, facet_name, facet_text, is_fso=False):
        """
        Get reviewed item count
        Args:
            facet_type      (str):  Type of facet box
            facet_name      (str):  Name of the facet label
            facet_text      (str):  facet text to click the facet (Reviewed / Not Reviewed)
            is_fso          (bool): True for FSO else False
        Returns count string
        """
        self._click_reviewed_facet(facet_text)
        if is_fso:
            xp = f"//*[@id='Request_Manager_Dataset_{facet_type}_']//span[text()='{facet_name}']//following::span[1]"
        else:
            xp = f"//*[contains(text(),'{facet_type}')]/following::span[text()='{facet_name}']/following::span[1]"
        count = str(self._admin_console.driver.find_element(By.XPATH, xp).text)
        self._unclick_reviewed_facet(facet_type, facet_name)
        return count

    @WebAction()
    def _apply_facet_filter(self, facet_type, facet_text):
        """
        Applied Facet Filter provided facet type and value/text.
        Args:
            facet_type      (str):  Type of facet box
            facet_text      (str):  facet text to click the facet (Reviewed / Not Reviewed)
        """
        self.__table.apply_filter_over_column(facet_type, facet_text)

    @WebAction()
    def _get_first_file_path(self, data_source_type):
        """
                                Get first file path in table
                                    Args:
                                        data_source_type(str): Data Source Type
                                    Returns (String) name
                                """
        name = self.__table.get_column_data(
            self.table_map[data_source_type]["FilePath"]
        ).pop(0)
        return name

    @WebAction()
    def _get_first_file_name(self, data_source_type):
        """
                                Get first file name in table
                                    Args:
                                        data_source_type(str): Data Source Type
                                    Returns String name
                                """
        name = self.__table.get_column_data(
            self.table_map[data_source_type]["FileName"]
        ).pop(0)
        return name

    @WebAction()
    def request_approval(self):
        """
        Request approval for a request
        """
        self.__page_container.access_page_action("Request Approval")

    @WebAction()
    def _fill_review_comment(self, comment):
        """
        Fills the review comment field
        :param comment: Comment to be filled
        """
        self._admin_console.fill_form_by_id("ReviewComment", comment)

    @WebAction()
    def _click_accept(self):
        """
        Clicks on accept in the review window
        """
        self._admin_console.click_button_using_text("Accept")

    @WebAction()
    def _click_decline(self):
        """
        Clicks on decline in the review window
        """
        self._admin_console.click_button_using_text("Decline")

    @PageService()
    def _accept_file_with_comment(self, comment):
        """
        Review with comment
        :param comment: Comment
        """
        self._click_accept()
        self._fill_review_comment(comment)
        self._admin_console.click_button_using_id("Save")
        
    @PageService()
    def _decline_file_with_comment(self, comment):
        """
        Declines a file with comment
        :param comment: Comment
        """
        self._click_decline()
        self._fill_review_comment(comment)
        self._admin_console.click_button_using_id("Save")

    @WebAction()
    def _click_complete_review(self):
        """
        Clicks on the 'complete review link'
        """
        self._admin_console.click_button_using_text("Complete Review")

    @PageService()
    def approve_request(self, request_name):
        """
        Approves a request
        Args:
            request_name    (str):  Name of the request
        """
        _request = RequestManager(self._admin_console)
        _request.select_request_by_name(request_name)
        self.__page_container.access_page_action("Approve")

    @PageService()
    def apply_filters(self, filters):
        """
        Applies the filters on the request review page
        Args:
            filters (dict)  -- Filters to be applied before accepting the documents
            Example:
                {'Size': {'1MB to 50MB', '0KB to 1MB'},
                'FileExtension': {'Archives', 'Others'},
                'ModifiedTime': {'4 to 5 Years', '3 to 4 Years', '1 to 2 Years'},
                'CreatedTime': {'4 to 5 Years'}}
        """
        for key in filters:
            values = filters[key]
            for value in values:
                self.log.info(f"Applying Facet Filter with filter_type as {key} & filter_value as {value}")
                self._apply_facet_filter(key, value)

    @WebAction()
    def _review_file(self, comment, filename=None, datasource_type="File system", accept=True, is_fso=False):
        """
        Accept/decline a file
        filename          (str)    -- filename to review
        comment           (str)    -- comment
        datasource_type   (str)    -- datasource type to review
        accept            (bool)   -- accept or decline the file
        is_fso            (bool)   -- True if FSO else False
        """
        if is_fso:
            if accept:
                self._admin_console.select_hyperlink("ACCEPT")
            else:
                self._admin_console.select_hyperlink("DECLINE")
            self._admin_console.driver.find_element(By.ID, "fsoApproveOrDenyReason").clear()
            self._admin_console.driver.find_element(By.ID, "fsoApproveOrDenyReason").send_keys(comment)
            self.__dialog.click_submit()
            self._admin_console.wait_for_completion()
        else:
            filter = {self.table_map[datasource_type]["FileName"]:{filename}}
            self.apply_filters(filter)
            self.__table.select_rows([filename])
            if accept:
                self._accept_file_with_comment(comment)
            else:
                self._decline_file_with_comment(comment)
            try: 
             self.__table.clear_column_filter(self.table_map[datasource_type]["FileName"], filename)
             if self.__ds_review.is_file_preview_present():
                self.__ds_review.close_file_preview()
            except ElementClickInterceptedException as exp:
             self.log.info("Review of all files might have completed.")
    
    def _get_facet_count(self):
        """
        Gets the values from the review status facet
        """
        review_status_facet = self.__dropdown.get_values_of_drop_down(drop_down_id='Review status')
        facet_dict = {}
        for entry in review_status_facet:
            facet_name, value = entry.rsplit(" ", 1)
            value = value.strip("(").strip(")")
            facet_dict[facet_name] = int(value)
        return facet_dict

    @PageService()
    def review_approve_request(
            self, request_name, files=None, datasource_type="File system", is_fso=False, filters=None, db_count=None):
        """
        Reviews & Approves a request from request Manager page
            :param request_name (str)  - request name to be reviewed
            :param files (list) - filename(s) to verify
            :param datasource_type(str)- Data Source Type To review
            :param is_fso(bool)- True if FSO else False
            :param filters(dict)- Filters to be applied before accepting the documents
            :param db_count(int)- number of files after applying filters on db
            :raise if files are not marked reviewed or request status is incorrectly set
       """
        _request = RequestManager(self._admin_console)
        _request.select_request_by_name(request_name)
        reason = "This is an automated review"
        all_files = self.get_file_names()
        if is_fso:
            not_reviewed = self._get_facet_count(
                'contentid', self._admin_console.props['label.taskdetail.notReviewed'],
                facet_text=self._admin_console.props['label.taskdetail.notReviewed'], is_fso=True)
            not_reviewed = not_reviewed[not_reviewed.index('(') + len('('): not_reviewed.index(')')]
            self._admin_console.log.info(f"Not Reviewed {not_reviewed}")
            if filters:
                self.apply_filters(filters)
                self._review_file(reason, is_fso=is_fso)
                self.apply_filters(filters)
                self._review_file(reason, accept=False, is_fso=is_fso)
            else:
                self._review_file(reason, is_fso=is_fso)
            self.__dialog.click_submit()
        else:
            not_reviewed = self._get_facet_count().get(cs.NOT_REVIEWED)
            self._admin_console.log.info(f"Not Reviewed {not_reviewed}")
            # Accept the files
            for file in files:
                self._review_file(reason, file, datasource_type, True)
            # Limitation: Getting files from the first page only
            # Decline the unrequired files
            if not_reviewed > 1:
                not_reviewed = self._get_facet_count().get(cs.NOT_REVIEWED)
                all_files = self.get_file_names()
                for file in all_files:
                    if file not in files:
                        self._review_file(reason, file, datasource_type, False)
            # Move the review to completion
            try:
                self.__dialog.click_submit()
            except ElementNotInteractableException:
                self._click_complete_review()
                self.__dialog.click_submit()
        self._admin_console.navigator.navigate_to_governance_apps()
        self.__app.select_request_manager()
        status = _request.get_status(request_name)
        if "Review completed" not in status:
            raise CVWebAutomationException(f"Incorrect status {status}")
        _request.select_request_by_name(request_name)
        if is_fso:
            not_reviewed = self._get_facet_count('contentid', self._admin_console.props['label.taskdetail.notReviewed'],
                                                 facet_text=self._admin_console.props['label.taskdetail.reviewed'],
                                                 is_fso=True)
            not_reviewed = not_reviewed[not_reviewed.index('(') + len('('): not_reviewed.index(')')]
            accepted = self._get_facet_count('contentid', self._admin_console.props['label.taskpreview.accepted'],
                                             facet_text=self._admin_console.props['label.taskdetail.reviewed'],
                                             is_fso=True)
            accepted = int(accepted[accepted.index('(') + len('('): accepted.index(')')])
            if filters:
                if accepted == db_count:
                    self._admin_console.log.info(f"Accepted Count: {accepted} & DB Count {db_count} Matched")
                else:
                    self._admin_console.log.info(f"Accepted Count: {accepted} & DB Count {db_count} do not Match")
                    raise Exception(f"Accepted Count: {accepted} & DB Count {db_count} do not Match")
            self._admin_console.log.info(f"Not Reviewed: {not_reviewed} & Accepted: {accepted}")
        else:
            facet_dict = self._get_facet_count()
            reviewed = facet_dict.get(cs.REVIEWED)
            not_reviewed = facet_dict.get(cs.NOT_REVIEWED)
            self._admin_console.log.info(f"Reviewed [{reviewed}], Not Reviewed [{not_reviewed}]")
        if int(not_reviewed) != 0:
            self._admin_console.log.error(f'Review failed, after review, number of not reviewed items {not_reviewed}')
            raise CVWebAutomationException(f'Review failed, after review, number of not reviewed items {not_reviewed}')

    @PageService()
    def fetch_request_job(self):
        """
        Check job information for GDPR task approval
        :return: job id (list)
        """
        self.__job.access_active_jobs()
        # job page moved to React

        self.__table_job.apply_filter_over_column_selection(
            self._admin_console.props['label.taskDetail.operation'],
            'GDPR task approval',
            criteria=Rfilter.equals
        )
        _id = self.__table_job.get_column_data("Job Id")
        return _id
    
    @PageService()
    def get_file_names(self, data_source='File system'):
        """
        Returns the list of file names shown on the current page
            Return:
                List of file names
        """
        self.log.info(self.table_map[data_source]["FileName"])
        return self.__table.get_column_data(
            self.table_map[data_source]["FileName"])