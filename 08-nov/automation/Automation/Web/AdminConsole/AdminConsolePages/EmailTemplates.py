# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Email Templates page on the AdminConsole

Class:
    EmailTemplates()

Functions:
    create_mail_template()          --    Method to create mail template

    edit_mail_template()            --    Method to edit mail template

    action_delete_mail_template()   --    Method to delete mail template

    preview_mail_template()         --    Method to trigger and validate preview of mail template

    get_preview_contents()          --    Method to get contents in preview pane

    open_mail_template()            --    Method to open mail template

    send_test_mail()                --    Method to send test email
"""
from selenium.webdriver.common.by import By
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.table import CVTable, Table, Rtable


class EmailTemplates:
    """
    Class for Email Template page
    """

    def __init__(self, adminpage_obj):

        self.__adminpage_obj = adminpage_obj
        self.__adminpage_obj.load_properties(self)
        self.__driver = adminpage_obj.driver
        self.__navigator = self.__adminpage_obj.navigator
        self.__cvtable = CVTable(self.__adminpage_obj)
        self.__table = Table(self.__adminpage_obj)
        self.__rtable = Rtable(self.__adminpage_obj)

    @WebAction()
    def __open_custom_address_fields(self):
        """Expands the customized address fields panel"""
        custom_address_fields_xpath = "//span[contains(text(),'Customized address fields')]"
        self.__driver.find_element(By.XPATH, custom_address_fields_xpath).click()

    @WebAction()
    def __restore_system_default_subject(self):
        """Clicks on the restore system default link for the subject field"""
        if self.__adminpage_obj.check_if_entity_exists(
                "xpath", "//label[contains(text(),'Subject')]/small/a"):
            self.__driver.find_element(By.XPATH, 
                "//label[contains(text(),'Subject')]/small/a").click()

    @WebAction()
    def __restore_system_default_body(self):
        """Clicks on the restore system default for the body field"""
        if self.__adminpage_obj.check_if_entity_exists(
                "xpath", "//label[contains(text(),'Body')]/small/a"):
            self.__driver.find_element(By.XPATH, 
                "//label[contains(text(),'Body')]/small/a").click()

    @WebAction()
    def __switch_to_preview_iframe(self):
        """Switches the driver to the preview iframe"""

        preview_iframe_xpath = "//div[contains(@class,'modal-dialog')]//iframe"
        self.__driver.switch_to.frame(self.__driver.find_element(By.XPATH, preview_iframe_xpath))

    @WebAction()
    def __switch_to_body_iframe(self):
        """Switches to template body iframe"""
        body_iframe_xpath = "//td[@class='k-editable-area']/iframe[@class='k-content']"
        self.__driver.switch_to.frame(self.__driver.find_element(By.XPATH, body_iframe_xpath))

    @WebAction()
    def __switch_out_of_iframe(self):
        """Switch to content outside iframe"""
        self.__driver.switch_to.default_content()

    @WebAction()
    def __return_preview_subject_content(self):
        """Returns content from the subject field"""
        return self.__driver.find_element(By.XPATH, "//div[contains(@class,'subject')]").text

    @WebAction()
    def __return_body_content(self):
        """Returns body editor contents"""
        body_editor_content = self.__driver.find_element(By.XPATH, "//body[@contenteditable='true']").text
        body_editor_content = body_editor_content.replace("\n", " ")
        return body_editor_content

    @WebAction()
    def __return_subj_content(self):
        """Returns content of subject input"""
        return self.__driver.find_element(By.ID, "templateSubject").get_attribute("value")

    @WebAction()
    def __return_preview_body_object(self):
        """Returns an object of the body element"""
        return self.__driver.find_element(By.XPATH, 
            "//div[@class='emailBody']/div/table/tbody/tr/td")

    @WebAction()
    def __return_object_links(self, elem_obj):
        """Return links in element object"""

        return elem_obj.find_elements(By.XPATH, ".//a")

    @WebAction()
    def is_template_default(self, template_name):
        """ Return True/false if template is default/not default """

        default_col_xpath = f"//a[text()='{template_name}']/ancestor::div[@class='ui-grid-canvas']/div/div/div[5]"
        if self.__driver.find_element(By.XPATH, default_col_xpath):
            return True
        else:
            return False

    @WebAction()
    def __populate_body(self, text_content, append_content=False):
        """
        Fill the header or footer body with text content

        Args:
            text_content    (str): Content to be used in header/footer
        """
        if not append_content:
            self.__driver.find_element(By.XPATH, "//body").clear()
        self.__driver.find_element(By.XPATH, "//body").send_keys(text_content)

    @PageService()
    def create_mail_template(self,
                             template_name,
                             template_desc,
                             template_type,
                             template_locale,
                             template_company=None,
                             from_name=None,
                             from_email=None,
                             cc=None,
                             bcc=None,
                             subject=None,
                             body=None
                             ):
        """
        Method to create a mail template

        Args:
            template_name        (str)     :   Name of the template to be created
            template_desc        (str)     :   Text message describing the template
                                                attribute/utility
            template_type        (str)     :   Type of email template to be created
            template_company     (str)     :   Name of the company for which template is created
            template_locale      (str)     :   Locale of email template to be created
            from_name            (str)     :   value for "from name" in custom address fields
            from_email           (str)     :   value for "from email" in custom address fields
            cc                   (str)     :   value for "cc" in custom address fields
            bcc                  (str)     :   value for "bcc" in custom address fields
            subject              (str)     :   Email subject
            body                 (str)     :   Email body

        Returns:
            None

        Raises:
            Exception:
                if fails to create email template
        """

        self.__adminpage_obj.select_hyperlink("Add template")
        self.__adminpage_obj.fill_form_by_id("templateName", template_name)
        self.__adminpage_obj.fill_form_by_id("templateDesc", template_desc)
        self.__adminpage_obj.select_value_from_dropdown("templateType", template_type)

        if template_type != "Add company":
            self.__adminpage_obj.select_value_from_dropdown("templateCompany", template_company)
        self.__adminpage_obj.select_value_from_dropdown("templateLocale", template_locale)
        if from_name or from_email or cc or bcc:

            self.__open_custom_address_fields()

            if from_name:
                self.__adminpage_obj.fill_form_by_id("templateFromName", from_name)
            if from_email:
                self.__adminpage_obj.fill_form_by_id("templateFromEmail", from_email)
            if cc:
                self.__adminpage_obj.fill_form_by_id("templateCc", cc)
            if bcc:
                self.__adminpage_obj.fill_form_by_id("templateBcc", bcc)

        if subject:
            self.__adminpage_obj.fill_form_by_id("templateSubject", subject)
        else:
            self.__restore_system_default_subject()
            self.__adminpage_obj.click_button("Yes")

        if body:
            self.__switch_to_body_iframe()
            self.__populate_body(body)
            self.__switch_out_of_iframe()
        else:
            self.__restore_system_default_body()
            self.__adminpage_obj.click_button("Yes")

        self.__adminpage_obj.submit_form()

    @PageService()
    def action_edit_mail_template(self,
                                  old_template_name,
                                  new_template_name,
                                  template_desc,
                                  template_locale,
                                  from_name=None,
                                  from_email=None,
                                  cc=None,
                                  bcc=None,
                                  subject=None,
                                  body=None):
        """
        Method to edit a mail template

        Args:

            old_template_name    (str)   :   Name of the template to be edited
            new_template_name    (str)   :   New name of the template
            template_desc        (str)   :   Text message describing the template attribute/utility
            template_locale      (str)   :   Locale of email template
            from_name            (str)   :   value for "from name" in custom address fields
            from_email           (str)   :   value for "from email" in custom address fields
            cc                   (str)   :   value for "cc" in custom address fields
            bcc                  (str)   :   value for "bcc" in custom address fields
            subject              (str)   :   Email Subject
            body                 (str)   :   Email body

        Returns:
            None

        Raises:
            Exception:
                if fails to edit mail template
        """

        self.__cvtable.access_action_item(old_template_name, "Edit")

        if new_template_name:
            self.__adminpage_obj.fill_form_by_id("templateName", new_template_name)
        if template_desc:
            self.__adminpage_obj.fill_form_by_id("templateDesc", template_desc)
        if template_locale:
            self.__adminpage_obj.select_value_from_dropdown("templateLocale", template_locale)
        if from_name or from_email or cc or bcc:

            self.__open_custom_address_fields()

            if from_name:
                self.__adminpage_obj.fill_form_by_id("templateFromName", from_name)
            if from_email:
                self.__adminpage_obj.fill_form_by_id("templateFromEmail", from_email)
            if cc:
                self.__adminpage_obj.fill_form_by_id("templateCc", cc)
            if bcc:
                self.__adminpage_obj.fill_form_by_id("templateBcc", bcc)

        if subject:
            self.__adminpage_obj.fill_form_by_id("templateSubject", subject)

        if body:
            self.__switch_to_body_iframe()
            self.__populate_body(body, append_content=True)
            self.__switch_out_of_iframe()

        self.__adminpage_obj.submit_form()

    @PageService()
    def action_delete_mail_template(self, template_name):
        """
        Method to delete a mail template

        Args:
            template_name    (str)     : Name of the template to be deleted

        Returns:
            None

        Raises:
            Exception:
                if fails to delete email template
        """
        self.__cvtable.access_action_item(template_name, 'Delete')
        self.__adminpage_obj.click_button_using_text("Yes")
        notification = self.__adminpage_obj.get_notification()

        if f"{template_name} has been deleted" in notification:
            self.__adminpage_obj.log.info("Email template was deleted successfully")
        else:
            raise Exception(f"Email template {template_name} was not deleted")

    @PageService()
    def action_set_template_as_default(self, template_name):
        """
        Method to set template as default.

        Args:
            template_name   (str): Name of template to be set as default

        Returns:
            None
        """

        self.__cvtable.search_for(template_name)
        self.__cvtable.access_action_item(template_name, "Make default")
        self.__adminpage_obj.wait_for_completion()

    def is_template_present(self, template_name):
        """Checks if template is present"""

        self.__cvtable.search_for(template_name)
        if self.__adminpage_obj.check_if_entity_exists("link", template_name):
            return True
        else:
            return False

    @PageService()
    def preview_mail_template(self, template_name):
        """
        Method to validate preview of mail template is displayed correctly

        Args:
            template_name    (str)    : Name of the template to be previewed

        Returns:
            None

        Raises:
            Exception:
                if preview isn't displayed correctly
        """

        self.open_mail_template(template_name)
        self.__adminpage_obj.wait_for_completion()

        self.__adminpage_obj.click_button("Preview email")
        self.__adminpage_obj.wait_for_completion()

        self.__switch_to_preview_iframe()

        subject = self.__return_preview_subject_content()
        body = self.__return_preview_body_object()

        if not subject:
            exp = "Mail subject is previewed as empty"
            self.__adminpage_obj.log.exception(exp)
            raise Exception(exp)
        if not body.text:
            exp = "Mail body is previewed as empty"
            self.__adminpage_obj.log.exception(exp)
            raise Exception(exp)
        hyperlinks = self.__return_object_links(body)
        for link in hyperlinks:
            try:
                link.click()
                self.__adminpage_obj.log.error(
                    "Link should not be clickable in Email Template Preview")
                break

            except Exception as exp:
                if "not clickable" in str(exp):
                    pass

        self.__switch_out_of_iframe()
        self.__adminpage_obj.click_button("OK")

    @PageService()
    def get_preview_contents(self):
        """
        Method to get text contents from preview template pane

        Returns:
            preview_contents(dict) : Dict of contents of preview template pane
        """

        self.__switch_to_preview_iframe()

        preview_contents = dict()
        preview_contents["subject"] = self.__return_preview_subject_content()
        preview_contents["body"] = self.__return_preview_body_object().text

        self.__switch_out_of_iframe()
        self.__adminpage_obj.click_button("OK")

        return preview_contents

    @PageService()
    def get_editor_contents(self):
        """
        Get contents from subject input and body editor

        Returns:
            editor_content (dict) : dictionary containing contents of
                                    mail template subject and body
        """

        editor_content = dict()
        editor_content['subject'] = self.__return_subj_content()
        self.__switch_to_body_iframe()
        editor_content['body'] = self.__return_body_content()
        self.__switch_out_of_iframe()

        return editor_content

    @PageService()
    def open_mail_template(self, template_name):
        """
        Method to open mail template

        Args:
            template_name    (str)    : Name of the template to be opened

        Raises:
            Exception:
                if fails to open mail template
        """

        self.__rtable.access_link(template_name)
        self.__adminpage_obj.wait_for_completion()

    @PageService()
    def send_test_mail(self, template_name):
        """
        Method to test mail

        Args:
            template_name    (str)    : Name of the template to be previewed

        Raises:
            Exception:
                if fails to send test mail
        """
        self.open_mail_template(template_name)
        self.__adminpage_obj.click_button("Send test email")
        self.__adminpage_obj.click_button_using_text("Yes")
        message_displayed = self.__adminpage_obj.get_notification()

        if "Email sent successfully" in message_displayed:
            self.__adminpage_obj.log.info("Test email successful")

        else:
            raise Exception("Could not confirm test email")
        self.__adminpage_obj.wait_for_completion()

    @WebAction()
    def add_image_to_mail_template(self, file_path):
        """
        Method to add image to mail template

        Args:
            file_path(str)    : File path of the image to be added

        Raises:
            Exception:
                if fails to add image to mail template
        """
        self.__driver.find_element(By.XPATH, 
            "//span[@class='k-tool-icon k-icon k-i-upload-image']").click()
        self.__driver.find_element(By.ID, 'files').send_keys(file_path)

        if self.__adminpage_obj.check_if_entity_exists(
                "xpath", "//li[@class='k-file k-file-invalid']"):
            exp = self.__driver.find_element(By.XPATH, 
                "//li[@class='k-file k-file-invalid']/span[2]/span[2]").text
            self.__adminpage_obj.click_button('Cancel')
            raise Exception(exp)
