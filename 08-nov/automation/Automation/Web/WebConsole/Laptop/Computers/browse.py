from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the browse and restore page on the WebConsole

Browse is the only class defined in this file

"""
import time
from Web.Common.page_object import WebAction, PageService
from selenium.common.exceptions import ImeNotAvailableException, NoSuchElementException
from Web.Common.exceptions import CVTimeOutException, CVWebAutomationException
from AutomationUtils import logger
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


class Browse:
    """
    Handles the operations on Browse page of My data application
    """
    def __init__(self, webconsole):
        """Initializes Browse class object"""
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _wait_for_page_load(self):
        """Check if the browse page is loaded"""
        try:
            self._driver.find_element(By.CLASS_NAME, "loadmask-msg")
            return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _drilldown_to_filename(self):
        """drilldown to destination filename"""
        return self._driver.find_elements(By.CLASS_NAME, "drilldown")

    @WebAction()
    def _current_bread_crumb(self, _path):
        """verify current bread crumb values"""
        current_bc = self._driver.find_element(By.CLASS_NAME, "currentbc").text
        if str(current_bc).lower() == str(_path).lower():
            return True
        else:
            raise ImeNotAvailableException("Breadcrumb value states that you are not in folder: {0} "
                                           .format(str(_path)))

    @WebAction()
    def _is_data_available(self):
        """verify file table body has data"""
        xpath = "//tbody[@id='filetablebody']//*/td[@class='ellipsisDiv']"
        table_data = self._driver.find_elements(By.XPATH, xpath)
        if len(table_data) != 0:
            return True
        else:
            return False

    @WebAction()
    def _get_folders_list(self):
        """Get list of folder names"""
        folder_list = []
        xpath = "//tbody[@id='filetablebody']//*/div[@class='folder']"
        folder_objects = self._driver.find_elements(By.XPATH, xpath)
        for each_object in folder_objects:
            self._driver.execute_script('arguments[0].scrollIntoView();', each_object)
            folder_list.append(str(each_object.text))
        return folder_list

    @WebAction()
    def _get_files_list(self):
        """Get list of file names"""
        files_list = []
        xpath = "//tbody[@id='filetablebody']//*/div[@class='fileName']/span"
        file_objects = self._driver.find_elements(By.XPATH, xpath)
        for each_object in file_objects:
            self._driver.execute_script('arguments[0].scrollIntoView();', each_object)
            files_list.append(str(each_object.text))
        return files_list

    @WebAction()
    def _get_date_modified_list(self):
        """Get dates modified list"""
        xpath = "//tbody[@id='filetablebody']//*/td[@class='ellipsisDiv'][1]"
        date_objects = self._driver.find_elements(By.XPATH, xpath)
        return [
            each_object.text for each_object in date_objects
        ]

    @WebAction()
    def _get_size_list(self):
        """Get size list"""
        xpath = "//tbody[@id='filetablebody']//*/td[@class='ellipsisDiv'][2]"
        size_objects = self._driver.find_elements(By.XPATH, xpath)
        return [
            each_object.text for each_object in size_objects
        ]

    @WebAction()
    def _goto_client_favorite_link(self):
        """Go to client favorite link"""
        fav_object = self._driver.find_element(By.XPATH, ".//*[@id='clientFavorites']/a")
        self._driver.get(fav_object.get_attribute("href"))

    @WebAction()
    def _goto_client_recent_documents_link(self):
        """Go to client documents link"""
        fav_object = self._driver.find_element(By.XPATH, ".//*[@id='recentDocs']/a")
        self._driver.get(fav_object.get_attribute("href"))

    @WebAction()
    def _get_favelemnt_list(self):
        """Get list of favorite elements"""
        favelemnt_list = []
        xpath = "//tbody[@id='filetablebody']//*/div[@id='FavoriteStar']"
        favelemnt_object = self._driver.find_elements(By.XPATH, xpath)
        for _each in favelemnt_object:
            self._driver.execute_script('arguments[0].scrollIntoView();', _each)
            favelemnt_list.append(_each)
        return favelemnt_list

    @WebAction()
    def _get_favvalue_list(self, favelemnt_list):
        """Get list of favorite values"""
        value_list = []
        for _each in favelemnt_list:
            self._driver.execute_script('arguments[0].scrollIntoView();', _each)
            value_list.append(str(_each.get_attribute('data-state')))
        return value_list

    @WebAction()
    def _is_folder_data_available(self):
        """verify file folder and recent documents table body has data"""
        xpath = "//tbody[@id='filetablebody']/tr/td"
        no_data = self._driver.find_element(By.XPATH, xpath)
        if no_data.text == 'No data available.':
            return False
        return True

    @WebAction()
    def _click_on_favstart_element(self, fav_star_element):
        """Click/select the required folder as favorite folder"""
        fav_star_element.click()

    @WebAction()
    def _get_recent_folders_list(self):
        """Get list of recent folder names"""
        xpath = "//tbody[@id='filetablebody']//*/a[@class='drilldown']"
        folder_objects = self._driver.find_elements(By.XPATH, xpath)
        return [
            each_object.text for each_object in folder_objects
        ]

    @WebAction()
    def _get_recent_datemodified_list(self):
        """Get list of recent documents date modified list"""
        xpath = "//*/td[@class='sorting_1 ellipsisDiv']"
        folder_objects = self._driver.find_elements(By.XPATH, xpath)
        return [
            each_object.text for each_object in folder_objects
        ]

    @WebAction()
    def _get_recent_size_list(self):
        """Get list of recent documents size list """
        xpath = "//*/td[@class='ellipsisDiv']/div"
        folder_objects = self._driver.find_elements(By.XPATH, xpath)
        return [
            each_object.text for each_object in folder_objects
        ]

    @WebAction()
    def _get_table_elements(self):
        """get table info"""
        elem0 = self._driver.find_element(By.ID, "filetablebody")
        return len(elem0.find_elements(By.CLASS_NAME, "custom-cb"))

    @WebAction()
    def _get_row_data(self, row_idx):
        """Reads the row data"""
        self._comp_xp = "//tbody[@id='filetablebody']"
        row_xp = self._comp_xp + "/tr[%d]/td" % row_idx
        i = 1
        row_data = []
        for cellvalue in self._driver.find_elements(By.XPATH, row_xp):
            self._driver.execute_script('arguments[0].scrollIntoView();', cellvalue)
            if i == 1:
                row_data.append(cellvalue)
                i = i+1
            else:
                row_data.append(cellvalue.text)
        return row_data

    @PageService()
    def get_table_data(self):
        """Read the table data"""
        table_data = []
        table_len = self._get_table_elements()
        for each_row_idx in range(1, table_len+1):
            table_data.append(self._get_row_data(each_row_idx))
        return table_data

    @PageService()
    def get_folder_and_file_lists(self):
        """Get folders and files lists"""
        folders_list = []
        files_list = []
        folder_data = self._get_folders_list()
        total_data = self.get_table_data()
        for each_row in total_data:
            if each_row[1] in folder_data:
                folders_list.append(each_row)
            else:
                files_list.append(each_row)
        return folders_list, files_list

    @WebAction()
    def _get_checkbox_value_list(self, checkbox_element_list):
        """Get list of check box element values"""
        value_list = []
        for _each in checkbox_element_list:
            value_list.append(str(_each.get_attribute('data-state')))
        return value_list

    @WebAction()
    def _click_on_checkbox_element(self, check_box_element):
        """check/select the required file"""
        self._driver.execute_script('arguments[0].scrollIntoView();', check_box_element)
        check_box_element.click()

    @WebAction()
    def _click_more_options_dropdown(self):
        """Click on more options drop down"""
        xpath = r"//a[@id='moreActionsLink']"
        more_options_menu = self._driver.find_element(By.XPATH, xpath)
        more_options_menu.click()

    @WebAction()
    def _click_on_versions(self):
        """Click on versions from more options drop down"""
        versions_option = self._driver.find_element(By.XPATH, "//a[@id='viewVersionsLink']")
        versions_option.click()

    @WebAction()
    def _click_on_delete(self):
        """Click on versions from more options drop down"""
        delete_option = self._driver.find_element(By.XPATH, "//a[@id='euErase']")
        delete_option.click()

    @WebAction()
    def _click_button_dialogue_yes(self):
        """
        Click on popup dialogue yes
        """
        self._driver.find_element(By.XPATH, "//button[text()='Yes']").click()

    @WebAction()
    def _click_on_download_button(self):
        """click on download button"""
        download_button = self._driver.find_element(By.XPATH, "//a[@id='downloadLink']")
        download_button.click()

    @WebAction()
    def _get_all_available_options_inside_modifiedtime(self):
        """Get all available options from modified time search"""
        options = self._driver.find_elements(By.XPATH, "//select[@id='modTime']/option")
        return [option.text for option in options]

    @WebAction()
    def _select_modifiedtime_option(self, modified_time):
        """select required option from modified time search"""
        modified_time_select = Select(self._driver.find_element(By.XPATH, "//select[@id='modTime']"))
        modified_time_select.select_by_visible_text(modified_time)

    @WebAction()
    def _get_all_available_options_inside_filetype(self):
        """Get all available options from file type search"""
        options = self._driver.find_elements(By.XPATH, "//select[@id='extension']/option")
        return [option.text for option in options]

    @WebAction()
    def _select_filetype_option(self, file_type_name):
        """select required option from file type search """
        file_type_select = Select(self._driver.find_element(By.XPATH, "//select[@id='extension']"))
        file_type_select.select_by_visible_text(file_type_name)

    @PageService()
    def wait_for_page_load(self, timeout=60):
        """Wait for the the browse page is loaded"""

        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._wait_for_page_load():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Loading screen [loadmask] did not disappear on page",
            self._driver.current_url
        )

    @PageService()
    def _navigate_to_dest_path(self, _path):
        """navigate to destination path """
        item_found = False
        element_set = self._drilldown_to_filename()

        for each_item in element_set:
            if str(each_item.text).strip().lower() == str(_path).strip(' ').lower():
                self._driver.execute_script('arguments[0].scrollIntoView();', each_item)
                time.sleep(1)
                each_item.click()
                self.wait_for_page_load()
                time.sleep(4)
                item_found = True
                if self._current_bread_crumb(str(_path).strip(' ').lower()):
                    self._log.info("Successfully navigated to: '{0}' ".format(str(_path)))
                else:
                    self._log.error('Unable to verify if navigation was successful or not')
                break
        if not item_found:
            raise ImeNotAvailableException("Item not found")

    @PageService()
    def navigate_to_restore_page(self, dest_path):
        """navigate to restore page """
        self.wait_for_page_load()
        if dest_path != '':
            temp_path = dest_path.replace('/', '\\')
            file_path = temp_path.split('\\')
            if file_path[0] == '':
                file_path.pop(0)
            for _path in file_path:
                self._navigate_to_dest_path(_path)
                self.wait_for_page_load()
        else:
            raise ImeNotAvailableException("navigation path not provided")

    @PageService()
    def read_browse_results(self):
        """Read the browse results"""
        final_res = []
        self.wait_for_page_load()
        time.sleep(1)
        if self._is_data_available()is False:
            _dict = {'checkboxElement': '', 'FolderName': '', 'DateModified': '', 'Size': '',
                     'favStarElement': '', 'FileName': ''}
            _dict['checkboxElement'] = 'NA'
            _dict['FolderName'] = 'NA'
            _dict['DateModified'] = 'NA'
            _dict['Size'] = 'NA'
            _dict['favStarElement'] = 'NA'
            _dict['FileName'] = 'NA'
            final_res.append(_dict)
            return final_res
        else:
            folder_list, file_list = self.get_folder_and_file_lists()
            fav_element_list = self._get_favelemnt_list()
            for idx, _x in enumerate(folder_list):
                _dict = {'checkboxElement': '', 'FolderName': '', 'DateModified': '', 'Size': '',
                         'favStarElement': '', 'FileName': ''}
                _dict['checkboxElement'] = _x[0]
                _dict['FolderName'] = _x[1]
                _dict['DateModified'] = _x[2]
                _dict['Size'] = _x[3]
                _dict['favStarElement'] = fav_element_list[idx]
                _dict['FileName'] = 'NA'
                final_res.append(_dict)

            for _x in file_list:
                _dict = {'checkboxElement': '', 'FileName': '', 'DateModified': '', 'Size': '', 'FolderName': '',
                         'favStarElement': ''}
                _dict['checkboxElement'] = _x[0]
                _dict['FileName'] = _x[1]
                _dict['DateModified'] = _x[2]
                _dict['Size'] = _x[3]
                _dict['favStarElement'] = 'NA'
                _dict['FolderName'] = 'NA'
                final_res.append(_dict)

            return final_res

    @PageService()
    def goto_client_favorite_link(self):
        """Go to client favorite link"""
        self._goto_client_favorite_link()

    @PageService()
    def goto_client_recent_documents_link(self):
        """Go to client recent documents link"""
        self. _goto_client_recent_documents_link()

    @PageService()
    def read_favorites_results(self):
        """Read favorite documents browse result"""
        self._driver.refresh()
        folder_list = []
        fav_element_list = []
        final_res = []
        self.wait_for_page_load()
        time.sleep(1)
        if self._is_folder_data_available()is False:
            _dict = {'FolderName': '', 'DateModified': '', 'Size': '', 'favStarElement': ''}
            _dict['FolderName'] = 'NA'
            _dict['DateModified'] = 'NA'
            _dict['Size'] = 'NA'
            _dict['favStarElement'] = 'NA'
            final_res.append(_dict)
            return final_res
        else:
            folder_list, _file_list = self.get_folder_and_file_lists()
            fav_element_list = self._get_favelemnt_list()
            for idx, _x in enumerate(folder_list):
                _dict = {'FolderName': '', 'DateModified': '', 'Size': '', 'favStarElement': ''}
                _dict['FolderName'] = _x[1]
                _dict['DateModified'] = _x[2]
                _dict['Size'] = _x[3]
                _dict['favStarElement'] = fav_element_list[idx]
                final_res.append(_dict)
            return final_res

    @PageService()
    def selct_folder_as_favorite(self, fav_folder):
        """ select the required folder as favorite folder"""
        res = self.read_browse_results()
        for _each in res:
            if _each['FolderName'] == fav_folder:
                self._click_on_favstart_element(_each['favStarElement'])
                break

    @PageService()
    def remove_folder_as_favorites(self, fav_folder):
        """ select the required folder as favorite folder"""
        self._goto_client_favorite_link()
        res = self.read_favorites_results()
        for _each in res:
            if _each['FolderName'] == fav_folder:
                self._click_on_favstart_element(_each['favStarElement'])
                break

    @PageService()
    def read_recent_documents_results(self):
        """Read recent documents browse result"""
        file_list = []
        final_res = []
        self.wait_for_page_load()
        if self._is_folder_data_available()is False:
            raise CVWebAutomationException(
                "No data available to verify recent documents"
            )
        else:
            _folder_list, file_list = self.get_folder_and_file_lists()
            for _x in file_list:
                _dict = {'FileName': '', 'Folder': '', 'DateModified': '', 'Size': ''}
                _dict['FileName'] = _x[1]
                _dict['Folder'] = _x[2]
                _dict['DateModified'] = _x[3]
                _dict['Size'] = _x[4]
                final_res.append(_dict)
            return final_res

    @PageService()
    def select_required_file(self, file_name):
        """ check the required file """
        res = self.read_browse_results()
        for _each in res:
            if _each['FileName'] == file_name:
                self._click_on_checkbox_element(_each['checkboxElement'])
                break

    @PageService()
    def select_required_folder(self, folder_name):
        """ check the required file """
        res = self.read_browse_results()
        for _each in res:
            if _each['FolderName'] == folder_name:
                self._click_on_checkbox_element(_each['checkboxElement'])
                break

    @PageService()
    def go_to_versions_page(self):
        """go to versions page"""
        self._click_more_options_dropdown()
        time.sleep(1)
        self._click_on_versions()

    @PageService()
    def click_on_delete(self):
        """click on erase data"""
        self._click_more_options_dropdown()
        time.sleep(1)
        self._click_on_delete()
        self._click_button_dialogue_yes()

    @PageService()
    def refresh_browse_data(self):
        """refresh the browser """
        self._driver.refresh()

    @PageService()
    def click_on_download_and_watch_for_notifications(self, wait_time=3):
        """click on download button and watch for notifications"""
        self._webconsole.clear_all_notifications()
        self._click_on_download_button()
        time.sleep(5)
        count = 1
        while count <= wait_time:
            err_msgs = self._webconsole.get_all_error_notifications()
            if err_msgs:
                raise CVWebAutomationException("Error notification [%s] while download request submitted"
                                               % (err_msgs[0]))
            msgs = self._webconsole.get_all_info_notifications()
            if msgs:
                if msgs[0] or msgs[1] != "Download request submitted. Please wait for file(s) to download...":
                    raise CVWebAutomationException("Unexpected notification [%s] while download request submitted"
                                                   % (msgs[1]))
            else:
                raise CVWebAutomationException("Unable to read notification while downloading file or folder")
            self._log.info("Sleeping for {0} seconds".format(10))
            time.sleep(10)
            count = count + 1

    @WebAction()
    def _search_menu_dropdown(self):
        """Click search menu dropdown opener"""
        search_menu = self._driver.find_element(By.XPATH, '//div[@class="arrowWrap"]')
        search_menu.click()

    @WebAction()
    def _search_by_filenme(self, file_name):
        """Search browse result by file name"""
        search_filename = self._driver.find_element(By.XPATH, "//input[@id='filename']")
        search_filename.send_keys(file_name)
        search_filename.send_keys(Keys.ENTER)

    @WebAction()
    def _click_on_gobutton(self):
        """Search browse result by file name"""
        go_button = self._driver.find_element(By.XPATH, "//input[@id='advSearchBtn']")
        go_button.click()

    @WebAction()
    def _clear_the_search(self):
        """Clear the search box"""
        self._driver.find_element(By.XPATH, "//input[@id='filename']").clear()

    @WebAction()
    def _select_file_type_from_searchbox(self):
        """
        Selects file types in search_box
        """
        return Select(self._driver.find_element(By.ID, "extension"))

    @WebAction()
    def _select_modified_from_searchbox(self):
        """
        Selects modified time in search_box
        """
        return Select(self._driver.find_element(By.ID, "modTime"))

    @PageService()
    def search_by_filename(self, file_name):
        """Search browse result by file name"""
        self._search_menu_dropdown()
        time.sleep(1)
        self._search_by_filenme(file_name)
        self._click_on_gobutton()

    @PageService()
    def read_search_results(self):
        """Read the browse results"""
        final_res = []
        self.wait_for_page_load()
        time.sleep(1)
        if self._is_data_available()is False:
            raise CVWebAutomationException(
                "No data available to verify search results"
            )
        else:
            table_list = self.get_table_data()
            for _x in table_list:
                _dict = {'checkboxElement': '', 'FileName': '', 'Folder': '', 'DateModified': '', 'Size': ''}
                _dict['checkboxElement'] = _x[0]
                _dict['FileName'] = _x[1]
                _dict['Folder'] = _x[2]
                _dict['DateModified'] = _x[3]
                _dict['Size'] = _x[4]
                final_res.append(_dict)

            return final_res

    @PageService()
    def search_by_modified_time(self, modified_time):
        """Search browse result by modified time"""
        self._search_menu_dropdown()
        time.sleep(1)
        if modified_time not in self._get_all_available_options_inside_modifiedtime():
            raise CVWebAutomationException("Specified modified time: %s couldn't be found in "
                                           "modified time list", modified_time)
        self._select_modifiedtime_option(modified_time)
        self._click_on_gobutton()

    @PageService()
    def search_by_filetype(self, file_type_name):
        """Search browse result by file Type"""
        self._search_menu_dropdown()
        time.sleep(1)
        if file_type_name not in self._get_all_available_options_inside_filetype():
            raise CVWebAutomationException("Specified file type: %s couldn't be found in "
                                           "file type list", file_type_name)

        self._select_filetype_option(file_type_name)
        self._click_on_gobutton()

    @PageService()
    def clear_the_search(self):
        """Clear the search box"""
        self._search_menu_dropdown()
        time.sleep(1)
        self._clear_the_search()
        file_type_select = self._select_file_type_from_searchbox()
        file_type_select.select_by_visible_text(' ')
        modified_time_select = self._select_modified_from_searchbox()
        modified_time_select.select_by_visible_text(' ')
        self._click_on_gobutton()
