from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the actions common to Edge drive applications go here"""

import os
import time
from selenium.webdriver.support.ui import Select

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import (
    CVTimeOutException,
    CVTestStepFailure
)
from Web.Common.page_object import (
    WebAction,
    PageService
)
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from Server.JobManager.jobmanager_helper import JobManager
from cvpysdk.job import JobController

SHARE_TYPE = {
    "collab": "collabShareLi",
    "shared_with_me": "sharedWithMeLi",
    "shared_by_me": "sharedByMeLi",
    "public_links": "publicShareLi"
}


class EdgeDrivePage:
    """ Contains all Web Actions and Page services related to Edge drive."""
    def __init__(self, webconsole):
        self.webconsole = webconsole
        self.browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self.log = logger.get_log()

    @WebAction()
    def goto_drive(self):
        """ go to Edge drive page """
        self.webconsole.goto_mydata()
        self._driver.find_element(By.LINK_TEXT, "Drive").click()
        self.webconsole.wait_till_load_complete(timeout=180)

    @WebAction()
    def upload_to_edge(self, list_of_files, commcell, client_name):
        """ upload file to edge drive

        Args:
            list_of_files   (list)     -- list of files to be uploaded

            commcell (str)          -- Instance of commcell class

            client_name (str)       -- edge drive client name

        Returns:
            None
        """

        for file in list_of_files:
            self.log.info("uploading file to edge drive :%s" % file)
            upload = self._driver.find_element(By.XPATH, "//input[@type='file']")
            upload.click()
            upload.send_keys(file)
            self.webconsole.wait_till_load_complete()

        self.validate_backup_job_for_upload(commcell, client_name)

    @WebAction()
    def upload_new_version_private_share(self, file_name, upload_file_path):
        """ upload new version of the file in the private share
        Args:
            file_name   (str)     -- name of the file in edge drive to create new version

            upload_file_path (str)     -- file path to upload the file

        Returns:
            None
        """
        self.log.info("uploading new version of the file %s" % file_name)
        self._driver.find_element(By.CLASS_NAME, "shareFolderLink").click()
        time.sleep(5)
        self._driver.find_element(By.ID, SHARE_TYPE["shared_with_me"]).click()

        file_table = self._driver.find_elements(By.XPATH, "//tbody[@id='sharesBody']/tr")
        for file in file_table:
            file_name_in_share = file.find_element(By.XPATH, "./td").text
            if file_name_in_share == file_name.split('.')[0]:
                file.find_element(By.XPATH, "./td/a").click()
                self._driver.find_element(By.CLASS_NAME, "mfp-close").click()
                time.sleep(5)

                self._driver.find_element(By.ID, "moreActionsLink").click()

                upload_new_version = self._driver.find_element(By.XPATH, "//input[@type='file']")
                self._driver.find_element(By.ID, "uploadNewVersionLink").click()
                upload_new_version.send_keys(upload_file_path)
                time.sleep(5)
                return
        raise Exception("File %s was not found in shared_with_me tab" % file_name)

    @WebAction()
    def upload_new_version_public_share(self, public_link, upload_file_path):
        """ upload new version of the file in the private share
        Args:
            public_link (str)        -- Public link address

            upload_file_path (str)   -- file path to upload new version of the file

        Returns:
            None
        """
        browser = BrowserFactory().create_browser_object()
        browser.open()
        browser.driver.get(public_link)
        time.sleep(10)

        browser.driver.find_element(By.CLASS_NAME, "mfp-close").click()

        browser.driver.find_element(By.ID, "moreActionsLink").click()
        upload_new_version = browser.driver.find_element(By.XPATH, "//input[@type='file']")
        browser.driver.find_element(By.ID, "uploadNewVersionLink").click()
        upload_new_version.send_keys(upload_file_path)
        time.sleep(5)
        browser.close()

    @PageService()
    def validate_backup_job_for_upload(self, commcell, client_name):
        """ Validate the Backup job after the file upload

        Args:
            commcell (str)          -- Instance of commcell class

            client_name (str)       -- edge drive client name

        Returns:
            None
        """
        max_attempts = 150
        job_controller = JobController(commcell)

        attempt = 0
        while True:
            active_bkp_jobs = job_controller.active_jobs(client_name=client_name, job_filter="Backup")
            if not active_bkp_jobs:
                attempt += 1
                time.sleep(2)
            else:
                break

            if attempt == max_attempts:
                self.log.warning("No Backup Jobs found running after the upload.")
                return

        # TODO: we need to find a precise way to find the particular Job for the current Upload
        job_manager = JobManager(_job=list(active_bkp_jobs.keys())[0], commcell=commcell)
        job_manager.wait_for_state()
        self.log.info("Backup Job %s is successfully completed for upload" % active_bkp_jobs)

    @WebAction()
    def search_drive(self, file_name):
        """ search file in edge drive

        Args:
            file_name   (str)     -- full name to search in edge drive

        Returns:
            None
        """
        search = self._driver.find_element(By.ID, "pgsearch")
        search.clear()
        search.send_keys(file_name)

        search = self._driver.find_element(By.ID, "searchButtonNew")
        search.click()
        self.webconsole.wait_till_load_complete()

    @WebAction()
    def delete_file(self, file_name):
        """ delete file in edge drive

        Args:
            file_name   (str)     -- full name to delete from edge drive

        Returns:
            None
        """
        self.search_drive(file_name)
        select = self._driver.find_element(By.XPATH, f"//span[./text()='{file_name}']/../../../td[1]/div")
        select.click()

        self._driver.find_element(By.ID, "moreActionsLink").click()
        self._driver.find_element(By.ID, "deleteLink").click()
        self._driver.find_element(By.CLASS_NAME, "okSaveClick").click()
        self.webconsole.wait_till_load_complete()

    @WebAction()
    def create_public_link(self, file_name, share_access_type="view"):
        """ create public share for given file

        Args:
            file_name   (str)     -- full name to delete from edge drive

            share_access_type (str) -- share type to be created. Expected : view or edit

        Returns:
            on Success, link for the public share of the given file path
        """
        self.log.info("creating public link for file %s" % file_name)
        self.search_drive(file_name)
        select = self._driver.find_element(By.XPATH, f"//span[./text()='{file_name}']/../../../td[1]/div")
        select.click()

        self._driver.find_element(By.ID, "publicLink").click()
        time.sleep(5)

        self._driver.switch_to.frame(0)
        # think of using dictonary with key and value as below strings to avoid duplicate code
        if share_access_type == "view":
            link = self._driver.find_element(By.ID, 'publicViewLink').get_attribute("value")
            self._driver.find_element(By.ID, "cancelButton").click()
        else:
            menu = self._driver.find_element(By.ID, "editM")
            menu.click()
            link = self._driver.find_element(By.ID, 'publicUploadLink').get_attribute("value")
            self._driver.find_element(By.ID, "cancelButtonEdit").click()
        self.log.debug("public link %s with access type %s" % (link, share_access_type))
        return link

    @WebAction()
    def create_private_share(self, file_name, galaxy_user, edit_user_priv=False):
        """ create private share
        Args:
            file_name   (str)     -- full name to delete from edge drive

            galaxy_user (str)     -- Commcell user to create the private share

            edit_user_priv (bool) -- option to create share with edit access

        Returns:
            None
        """
        self.log.info("creating private share for file %s" % file_name)
        self.search_drive(file_name)
        select = self._driver.find_element(By.XPATH, f"//span[./text()='{file_name}']/../../../td[1]/div")
        select.click()

        self._driver.find_element(By.ID, "shareLink").click()
        self._driver.switch_to.frame(0)

        textbox = self._driver.find_element(By.ID, "field")
        textbox.send_keys(galaxy_user)
        time.sleep(5)
        self._driver.find_element(By.ID, "userSuggestions").click()
        if edit_user_priv:
            self._driver.find_element(By.ID, "userPrivileges").click()
            self._driver.find_element(By.CLASS_NAME, "editModeLI").click()
        self._driver.find_element(By.ID, "addButtonDiv").click()

        self._driver.find_element(By.CLASS_NAME, "okSaveButton").click()
        self.webconsole.wait_till_load_complete()

    @WebAction()
    def files_in_share_folder_link(self, share_type, download_file=''):
        """ check if files or folders present in share link
        Args:
            share_type   (str)     -- sharing type listed for Edge user
                For Expected values please refer SHARE_TYPE constant in this file

            download_file (str)     -- download file present in shares

        Returns:
            List of files available in corresponding shares type
        """
        if share_type not in SHARE_TYPE:
            self.log.error("invalid share_type %s" % share_type)

        self._driver.find_element(By.CLASS_NAME, "shareFolderLink").click()
        time.sleep(5)
        self._driver.find_element(By.ID, SHARE_TYPE[share_type]).click()

        file_list = []
        file_table = self._driver.find_elements(By.XPATH, "//tbody[@id='sharesBody']/tr")
        if file_table is not None:
            for file in file_table:
                file_name = file.find_element(By.XPATH, "./td").text
                file_list.append(file_name)

                if download_file == file_name:
                    file.find_element(By.XPATH, "./td").click()

        return file_list

    @WebAction()
    def download_file_folder(self, file_name):
        """download file or folder from edge drive panel
        Args:
            file_name   (str)     -- file or folder name exists in edge drive

        Returns:
           None
        """
        self.search_drive(file_name)
        self.select_file_folder(file_name)
        self._driver.find_element(By.ID, "downloadLink").click()

    @WebAction()
    def delete_private_share(self, file_name):
        """delete private share link
        Args:
            file_name   (str)     -- delete private share for the given file name

        Returns:
           None
        """
        self.search_drive(file_name)
        select = self._driver.find_element(By.XPATH, f"//span[./text()='{file_name}']/../../../td[1]/div")
        select.click()
        self._driver.find_element(By.ID, "shareLink").click()
        self._driver.switch_to.frame(0)
        time.sleep(5)
        self._driver.find_element(By.ID, "deleteButton").click()
        self._driver.find_element(By.CLASS_NAME, "okSaveClick").click()

    @WebAction()
    def download_public_link(self, public_link, file_name):
        """download file from public share

        Args:
            public_link   (str)        -- link for the file to be downloaded

            file_name (str)            -- name of the file in the share

        Returns:
            None
        """
        browser = BrowserFactory().create_browser_object()

        # delete file if already present in download folder
        file_path = os.path.join(browser.get_downloads_dir(), file_name)
        if os.path.exists(file_path):
            self.log.debug("deleting existing file %s in download dir" % file_path)
            os.remove(file_path)

        browser.open()
        browser.driver.get(public_link)
        time.sleep(10)
        browser.driver.find_element(By.XPATH, "//a[@title='Download']").click()
        browser.close()

    @PageService()
    def wait_for_file_download(self,
                               file_name,
                               download_dir=None,
                               timeout_period=100,
                               sleep_time=5):
        """ wait for the file to download

        Args:
            file_name   (str)       -- name of the file expected to be downloaded

            download_dir (str)      -- download directory for the browser

            timeout_period (int)    -- max time to wait for file to download

            sleep_time  (int)       -- time to wait to check for file existence

        Returns:
            None
        """
        if download_dir is None:
            browser = BrowserFactory().create_browser_object()
            download_dir = browser.get_downloads_dir()

        file_path = os.path.join(download_dir, file_name)
        cur_time = 0
        while cur_time < timeout_period:
            if not os.path.exists(file_path):
                time.sleep(sleep_time)
                cur_time += sleep_time
            else:
                self.log.info("file %s downloaded successfully" % file_name)
                return True
        mesg = "file %s was not found in %s download directory" % (file_name, download_dir)
        raise CVTimeOutException(timeout_period, mesg)

    @PageService()
    def validate_restore_job(self, commcell, client_name):
        """ Validate restore Job for corresponding download or restore action

        Args:
            commcell (str)          -- Instance of commcell class

            client_name (str)      -- edge drive client name where restore Job will be triggered

        Returns:
            None
        """
        max_attempts = 150
        job_controller = JobController(commcell)

        attempt = 0
        while True:
            active_restore_jobs = job_controller.active_jobs(client_name=client_name, job_filter="Restore")
            if not active_restore_jobs:
                attempt += 1
                time.sleep(2)
            else:
                break

            if attempt == max_attempts:
                self.log.warning("No Restore Jobs found running after the restore.")
                return

        # TODO: we need to find a precise way to find the particular Job for the current restore
        job_manager = JobManager(_job=list(active_restore_jobs.keys())[0], commcell=commcell)
        job_manager.wait_for_state()
        self.log.info("Restore Job %s is successfully completed for restore" % active_restore_jobs)

    @WebAction()
    def select_file_folder(self, file_or_folder_name):
        """ Select file or folder in edge drive panel

        Args:
            file_or_folder_name (str)   -- file or folder name which needs to be selected

        Returns:
            None
        """
        self.search_drive(file_or_folder_name)
        select = self._driver.find_element(By.XPATH, f"//span[./text()='{file_or_folder_name}']/../../../td[1]/div")
        select.click()

    @PageService()
    def create_edge_test_data(self, data_type, file_folder_name, data_path=None):
        """ creates test data for edge drive test

        Args:
            data_type (str)          -- file or folder based on which upload data will be created

            file_folder_name (str)   -- file or folder name which will be used to create data

            data_path (str)          -- path where test data need to be created

        Returns:
            None
        """
        client_machine_obj = Machine()
        if data_path is None:
            upload_path = client_machine_obj.join_path(client_machine_obj.tmp_dir, file_folder_name)
        else:
            upload_path = client_machine_obj.join_path(data_path, file_folder_name)

        if client_machine_obj.check_directory_exists(upload_path):
            client_machine_obj.remove_directory(upload_path)

        if data_type == "file":
            client_machine_obj.create_file(upload_path, content=file_folder_name)
        else:
            client_machine_obj.generate_test_data(upload_path, dirs=1)
            
        return upload_path

    @PageService()
    def validate_restore_checksum(self,
                                  src_machine_obj,
                                  dest_machine_obj,
                                  source_path,
                                  restore_path,
                                  exp_success_restore=True):
        """ perform restore file to commcell client on the given client path

        Args:
            src_machine_obj (str)     -- machine object of source test data

            dest_machine_obj (str)    -- machine object of restore client

            source_path    (str)      -- path from where test data was originally uploaded

            restore_path (str)        -- path on restore client where data was restored

            exp_success_restore (str) -- flag to check if checksum should match or not

        Returns:
            None
        """

        if not dest_machine_obj.check_file_exists(restore_path):
            raise CVTestStepFailure("restored data %s didn't found on client %s" % (restore_path, dest_machine_obj))
        else:
            self.log.info("restored data %s found on client %s" % (restore_path, dest_machine_obj))

        file_path_diff = src_machine_obj.compare_folders(dest_machine_obj, source_path, restore_path)

        if exp_success_restore:
            if file_path_diff:
                raise CVTestStepFailure("restored data didn't match. checksum difference:%s" % file_path_diff)
            else:
                self.log.info("restored data verified successfully on restore path")
        else:
            if file_path_diff:
                self.log.info("restore is not successful in case of no overwrite as expected")
            else:
                raise CVTestStepFailure("Data is overwritten while restore. However no overwrite is selected."
                                        "checksum difference:%s" % file_path_diff)

    @WebAction()
    def restore_to_commcell_client(self,
                                   commcell,
                                   file_name,
                                   edge_client_name,
                                   restore_client_name,
                                   source_local_path=None,
                                   restore_path=None,
                                   overwrite=False,
                                   clear_destination_path=True):
        """ perform restore file to commcell client on the given client path

        Args:
            commcell (str)             -- Instance of commcell class

            file_name (str)            -- File or folder name in the edge drive to be restored

            edge_client_name    (str)  -- edge client name on which restore Job will be triggered

            restore_client_name (str)  -- restore commcell client name

            source_local_path (str)    -- source local path where test data was generated

            restore_path (str)         -- restore path on restore client

            overwrite  (bool)          -- Flag to select overwrite option in restore

            clear_destination_path (bool) -- Flag to clear destination file before restore


        Returns:
            None
        """
        src_machine_obj = Machine()
        restore_machine_obj = Machine(restore_client_name, commcell)

        if restore_path is None:
            restore_path = restore_machine_obj.tmp_dir
            restored_file = restore_machine_obj.join_path(restore_machine_obj.tmp_dir, file_name)
        else:
            restored_file = restore_machine_obj.join_path(restore_path, file_name)

        if source_local_path is None:
            source_local_path = src_machine_obj.join_path(src_machine_obj.tmp_dir, file_name)
        else:
            source_local_path = src_machine_obj.join_path(source_local_path, file_name)

        if restore_machine_obj.check_file_exists(restored_file) and clear_destination_path:
            self.log.debug("deleting %s on remote client %s" % (restored_file, restore_client_name))
            restore_machine_obj.remove_directory(restored_file)

        self.log.info("restoring file %s to client %s" % (restored_file, restore_client_name))
        self.select_file_folder(file_name)
        self._driver.find_element(By.ID, "restoreLink").click()
        time.sleep(5)
        self._driver.switch_to.frame(0)

        dropdown_list = Select(self._driver.find_element(By.XPATH, "//select[@id='destCompList']"))
        dropdown_list.select_by_visible_text(restore_client_name)

        self._driver.find_element(By.ID, "destinationPath").send_keys(restore_path)

        if overwrite:
            self._driver.find_element(By.XPATH, "//span[@class='overwriteCB']/div[1]").click()

        self._driver.find_element(By.ID, "restoreButton").click()

        self.validate_restore_job(commcell, edge_client_name)

        self.validate_restore_checksum(src_machine_obj,
                                       restore_machine_obj,
                                       source_local_path,
                                       restored_file,
                                       clear_destination_path)

    @WebAction()
    def restore_to_network_path(self,
                                commcell,
                                file_name,
                                edge_client_name,
                                restore_client_name,
                                dest_network_path,
                                impro_username,
                                impro_password,
                                restore_client_path,
                                source_local_path=None,
                                overwrite=False,
                                clear_destination_path=True):
        """ perform restore file to network path as given remote user

        Args:
            commcell (str)             -- Instance of commcell class

            file_name (str)            -- File or Folder name in the edge drive to be restored

            edge_client_name    (str)  -- edge client name on which restore Job will be triggered

            restore_client_name (str)  -- restore client name

            dest_network_path (str)    -- network path to perform restore

            impro_username (str)       -- Username to access UNC path

            impro_password (str)       -- Password to access UNC path

            restore_client_path (str)  -- machine file path on restore client for validation

            source_local_path (str)    -- source local path where test data was generated

            overwrite  (bool)          -- Flag to select overwrite option in restore

            clear_destination_path (bool) -- Flag to clear destination file before restore


        Returns:
            None
        """
        source_machine_obj = Machine()
        # make sure destination machine and connector machine are in the same domain
        restore_machine_obj = Machine(restore_client_name,  # dest_network_path.split('\\')[-1],
                                      username=impro_username,
                                      password=impro_password)
        restore_machine_obj = Machine(restore_client_name, commcell)

        restored_file = restore_machine_obj.join_path(restore_client_path, file_name)
        if restore_machine_obj.check_file_exists(restored_file) and clear_destination_path:
            restore_machine_obj.delete_file(restored_file)

        if source_local_path is None:
            source_local_path = source_machine_obj.join_path(source_machine_obj.tmp_dir, file_name)

        self.select_file_folder(file_name)
        self._driver.find_element(By.ID, "restoreLink").click()
        time.sleep(5)
        self._driver.switch_to.frame(0)

        dropdown_list = Select(self._driver.find_element(By.XPATH, "//select[@id='destCompList']"))
        dropdown_list.select_by_visible_text("Network Path")

        self._driver.find_element(By.ID, "destinationPath").send_keys(dest_network_path)
        self._driver.find_element(By.ID, "iun").send_keys(impro_username)
        self._driver.find_element(By.ID, "iup").send_keys(impro_password)
        self._driver.find_element(By.ID, "iup2").send_keys(impro_password)

        if overwrite:
            self._driver.find_element(By.XPATH, "//span[@class='overwriteCB']/div[1]").click()

        self._driver.find_element(By.ID, "restoreButton").click()

        self.validate_restore_job(commcell, edge_client_name)

        self.validate_restore_checksum(source_machine_obj,
                                       restore_machine_obj,
                                       source_local_path,
                                       restored_file,
                                       clear_destination_path)
