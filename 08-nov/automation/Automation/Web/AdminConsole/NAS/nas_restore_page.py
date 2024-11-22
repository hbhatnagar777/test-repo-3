from selenium.webdriver.common.by import By
#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers Details page.


Classes:

    NASRestorePage() ---> LoginPage() ---> AdminConsoleBase() ---> object()


    NAS_Client_Details  --  This class contains all the methods for running Restores from SubClient
     Level choosing different options

Functions:
    regular_nas_restore()
    regular_fs_restore()
    cifs_server_page_restore()



"""
from Web.Common.page_object import WebAction


class NasRestorePage:
    """
    This class contains all the methods for actions in NAS Restore page
    """
    @WebAction()
    def regular_nas_restore(self, show_deleted_items=False, dest_client=None, dest_path=None):
        """
        Running a Regular NAS Restore

        Args:
            show_deleted_items (boolean)  :   Shows Deleted Items too in Browse if True

            dest_client (str)        :   In Place Restore if 'None' else, Destination Clientname

            dest_path   (str)        :   Output Destination Path; 'None' - if in place Restore

        """
        self.log.info("Dest client is " + str(dest_client) + " dest path is " + str(dest_path))

        if not dest_client and not dest_path:
            self.log.info("Running a Regular NAS Restore")
            self.log.info("Running In  Place Restore")
            if show_deleted_items:
                self.driver.find_element(By.LINK_TEXT, "Show deleted items").click()
                self.wait_for_completion()
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[2]"
                "/div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")

        elif not dest_client or not dest_path:
            self.log.info("Destination Client or Destination Path not specified")
            raise Exception("Destination Client or Destination Path not specified")

        else:
            self.log.info("Running a Regular NAS Restore")
            self.log.info("Running Out of Place Restore")
            if show_deleted_items:
                self.driver.find_element(By.LINK_TEXT, "Show deleted items").click()
                self.wait_for_completion()
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[2]/"
                "div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient path level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")
            self.wait_for_completion()
            self.driver.find_element(By.XPATH, "//*[@class='overwriteLabel']").click()
            self.wait_for_completion()

            if not self.select_value_from_dropdown("destinationServer", dest_client):
                self.wait_for_completion()
            else:
                exp = "Invalid Destination Client"
                raise Exception(exp)

            self.fill_form_by_id("restorePath", dest_path)
        self.submit_form()
        job_id = self.get_jobid_from_popup()
        self.log.info("Restore job " + str(job_id) + " has started")
        self.log.info("Extracted job id is-- " + job_id)
        return int(job_id)

    @WebAction()
    def regular_fs_restore(self, dest_client, dest_path=None, username=None, passwd=None):
        """
        Running a Regular FS Under NAS Restore

        Args:
            dest_client (str)        :   In Place Restore if 'None' else, Destination Clientname

            dest_path   (str)        :   Output Destination Path; 'None' - if in place Restore

            username    (str)        :   Impersonation username

            passwd      (str)        :   Impersonated Username's password

        """

        self.log.info("Dest client is " + str(dest_client) + " dest path is " + str(dest_path))

        if not dest_path:
            self.log.info("Running a Regular FS under NAS  Restore")
            self.log.info("Running In  Place Restore")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[2]/"
                "div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")
            self.wait_for_completion()
        else:
            self.log.info("Running a Regular FS under NAS Restore")
            self.log.info("Running Out of Place Restore")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[2]/"
                "div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")
            self.driver.find_element(By.XPATH, "//*[@class='overwriteLabel']").click()
            self.wait_for_completion()

            if not username:
                self.log.info("No user impersonation")
            else:
                self.driver.find_element(By.XPATH, "*//input[@name='impersonateUserName']").\
                    send_keys(username)
                self.wait_for_completion()
                self.driver.find_element(By.XPATH, "*//input[@name='impersonatePassword']").\
                    send_keys(passwd)
                self.wait_for_completion()

            self.fill_form_by_id("restorePath", dest_path)
            self.wait_for_completion()

        self.select_value_from_dropdown("destinationServer", dest_client)
        self.submit_form()
        job_id = self.get_jobid_from_popup()
        self.log.info("Restore job " + str(job_id) + " has started")
        self.log.info("Extracted job id is-- " + job_id)
        return int(job_id)

    @WebAction()
    def cifs_server_page_restore(self, dest_client, dest_path=None, username=None, passwd=None):
        """
        Running a Regular FS Under NAS Restore

        Args:
            dest_client (str)        :   In Place Restore if 'None' else, Destination Clientname

            dest_path   (str)        :   Output Destination Path; 'None' - if in place Restore

            username    (str)        :   Impersonation username

            passwd      (str)        :   Impersonated Username's password

        """

        self.log.info("Dest client is " + str(dest_client) + " dest path is " + str(dest_path))

        if not dest_path:
            self.log.info("Running a Regular FS under NAS  Restore")
            self.log.info("Running In  Place Restore")
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//div[3]/div[2]/div/span/div/cv-browse/div/div[1]/cv-browse-tree/div/div[2]/"
                "cv-browse-tree/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@id='wrapper']/div[2]/div/span/span/div[1]/div/div/div/div[2]/"
                "div/div[1]/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")
        else:
            self.log.info("Running a Regular FS under NAS Restore")
            self.log.info("Running Out of Place Restore")
            self.log.info("Rendered / level objects")
            self.driver.find_element(By.XPATH, 
                "//div[3]/div[2]/div/span/div/cv-browse/div/div[1]/cv-browse-tree/div/div[2]/"
                "cv-browse-tree/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered volume level objects")
            self.driver.find_element(By.XPATH, 
                "//div[3]/div[2]/div/span/div/cv-browse/div/div[1]/cv-browse-tree/div/div[2]/"
                "cv-browse-tree/div/div[2]/cv-browse-tree/div/div/button").click()
            self.wait_for_completion()
            self.log.info("Rendered subclient level objects")
            self.driver.find_element(By.XPATH, 
                "//*[@class='ui-grid-selection-row-header-buttons ui-grid-icon-ok ng-scope "
                "ng-valid']").click()
            self.wait_for_completion()
            self.select_hyperlink("Restore")
            self.driver.find_element(By.XPATH, "//*[@class='overwriteLabel']").click()
            self.wait_for_completion()

            if not username:
                self.log.info("No user impersonation")
            else:
                self.driver.find_element(By.XPATH, "*//input[@name='impersonateUserName']").\
                    send_keys(username)
                self.wait_for_completion()
                self.driver.find_element(By.XPATH, "*//input[@name='impersonatePassword']").\
                    send_keys(passwd)
                self.wait_for_completion()
            self.fill_form_by_id("restorePath", dest_path)
        if not self.select_value_from_dropdown("destinationServer", dest_client):
            self.wait_for_completion()
        else:
            exp = "Invalid Destination Client"
            raise Exception(exp)
        self.submit_form()
        # self.driver.find_element(By.XPATH, "//div[@class='button-container']
        # //button[.='Submit']").click()
        self.wait_for_completion()
        job_id = self.get_jobid_from_popup()
        self.log.info("Restore job " + str(job_id) + " has started")
        self.log.info("Extracted job id is-- " + job_id)
        return int(job_id)
