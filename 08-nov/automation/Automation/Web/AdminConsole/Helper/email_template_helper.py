# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on email templates page.

Class:

    EmailTemplateHelper

Functions:

    modify_email_header()               -- Method for modifying email header
    add_email_template()                -- Method for creating email template
    modify_email_template()             -- Method for editing email template
    delete_email_template()             -- Method for deleting email template
    verify_email_template_contents()    -- Method for verifying email template contents
    is_template_present()               -- Method for checking if template
                                            with the given name is present
    set_template_as_default()           -- Method to set template as default
    template_send_test_email()          -- Method to send test mail for the given template

"""

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.EmailHeaderFooter import EmailHeaderFooter
from Web.AdminConsole.AdminConsolePages.EmailTemplates import EmailTemplates
from Web.AdminConsole.Components.table import CVTable


class EmailTemplateHelper:

    def __init__(self, admin_console):
        """
            Initializes the security helper module

        """
        self.log = logger.get_log()
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__driver = admin_console.driver

        self._template_name = "test_template_54737"
        self._new_template_name = "test_template_54737_modified"
        self._template_desc = "Test 54737 template description"
        self._template_type = "Add company"
        self._template_locale = "English"
        self._template_company = None
        self._custom_option_from_name = "test_from_name_value"
        self._custom_option_from_email = "test_from_email_value"
        self._custom_option_cc = "testcc_value@abcd.com"
        self._custom_option_bcc = "testbcc_value@abcd.com"

        self._email_header = "Test email header test 54737"
        self._email_footer = "Test email footer test 54737"
        self._append_content = False
        self._template_body = "Body content for email template test 54737"
        self._template_subject = "Subject content for email template test 54737"

        self.__template_obj = EmailTemplates(self.__admin_console)
        self.__template_header_footer_obj = EmailHeaderFooter(self.__admin_console)
        self.__cvtable = CVTable(self.__admin_console)

    @property
    def template_name(self):
        """Gets the template name."""
        return self._template_name

    @template_name.setter
    def template_name(self, value):
        """Sets the template name."""
        self._template_name = value

    @property
    def new_template_name(self):
        """Gets the new template name."""
        return self._new_template_name

    @new_template_name.setter
    def new_template_name(self, value):
        """Sets the template name."""
        self._new_template_name = value

    @property
    def template_desc(self):
        """Gets the template description."""
        return self._template_desc

    @template_desc.setter
    def template_desc(self, value):
        """Sets the template description."""
        self._template_desc = value

    @property
    def template_type(self):
        """Gets the template type."""
        return self._template_type

    @template_type.setter
    def template_type(self, value):
        """Sets the template type."""
        self._template_type = value

    @property
    def template_locale(self):
        """Gets the template locale."""
        return self._template_locale

    @template_locale.setter
    def template_locale(self, value):
        """Sets the template locale."""
        self._template_locale = value

    @property
    def template_company(self):
        """Gets the template company."""
        return self._template_company

    @template_company.setter
    def template_company(self, value):
        """Sets the template company."""
        self._template_company = value

    @property
    def template_subject(self):
        """Gets the template subject."""
        return self._template_subject

    @template_subject.setter
    def template_subject(self, value):
        """Sets the template subject."""
        self._template_subject = value

    @property
    def template_body(self):
        """Gets the template body."""
        return self._template_body

    @template_body.setter
    def template_body(self, value):
        """Sets the template body."""
        self._template_body = value

    @property
    def custom_option_from_name(self):
        """Gets the value for "from name". Custom address field."""
        return self._custom_option_from_name

    @custom_option_from_name.setter
    def custom_option_from_name(self, value):
        """Sets the "from name" value. Custom address field."""
        self._custom_option_from_name = value

    @property
    def custom_option_from_email(self):
        """Gets the value for "from email". Custom address field."""
        return self._custom_option_from_email

    @custom_option_from_email.setter
    def custom_option_from_email(self, value):
        """Sets the value for "from email". Custom address field."""
        self._custom_option_from_email = value

    @property
    def custom_option_cc(self):
        """Gets the value for "cc". Custom address field."""
        return self._custom_option_cc

    @custom_option_cc.setter
    def custom_option_cc(self, value):
        """Sets the value for "cc". Custom address field."""
        self._custom_option_cc = value

    @property
    def custom_option_bcc(self):
        """Gets the value for "bcc". Custom address field."""
        return self._custom_option_bcc

    @custom_option_bcc.setter
    def custom_option_bcc(self, value):
        """Sets the value for "bcc". Custom address field."""
        self._custom_option_bcc = value

    @property
    def email_header(self):
        """Gets the value for email header."""
        return self._email_header

    @email_header.setter
    def email_header(self, value):
        """Sets the value for email header."""
        self._email_header = value

    @property
    def email_footer(self):
        """Gets the value for email footer."""
        return self._email_footer

    @email_footer.setter
    def email_footer(self, value):
        """Sets the value for email footer."""
        self._email_footer = value

    @property
    def append_to_header_footer(self):
        """Determines whether to append to header/footer content or to replace old content"""
        return self._append_content

    @append_to_header_footer.setter
    def append_to_header_footer(self, value):
        self._append_content = value

    def modify_email_header_footer(self):
        """Adds email header and footer"""
        self.__navigator.navigate_to_email_templates()
        self.__admin_console.select_hyperlink("Email header and footer configuration")
        self.__template_header_footer_obj.modify_email_header_footer(self.email_header,
                                                                     self.email_footer,
                                                                     self.append_to_header_footer)

        self.__admin_console.select_hyperlink("Email templates")

    def add_email_template(self):

        """Method for adding an email template"""

        self.__navigator.navigate_to_email_templates()
        self.__template_obj.create_mail_template(self.template_name,
                                                 self.template_desc,
                                                 self.template_type,
                                                 self.template_locale,
                                                 self.custom_option_from_name,
                                                 self.custom_option_from_email,
                                                 self.custom_option_cc,
                                                 self.custom_option_bcc
                                                 )

    def modify_email_template(self):
        """Method to edit email template"""

        self.__navigator.navigate_to_email_templates()
        self.__template_obj.action_edit_mail_template(self.template_name,
                                                      self.new_template_name,
                                                      self.template_desc,
                                                      self.template_locale,
                                                      self.custom_option_from_name,
                                                      self.custom_option_from_email,
                                                      self.custom_option_cc,
                                                      self.custom_option_bcc
                                                      )
        self._template_name = self.new_template_name

    def delete_email_template(self):
        """Method for deleting email template"""

        self.__navigator.navigate_to_email_templates()
        self.__template_obj.action_delete_mail_template(self.template_name)

        self.__navigator.navigate_to_email_templates()
        if self.__template_obj.is_template_present(self.template_name):
            raise Exception("Email template is still visible on Email templates page")
        else:
            self.log.info("Email template deletion confirmed from Email templates page")

    def verify_email_template_contents(self):
        """Verify editor contents against preview contents"""

        self.__navigator.navigate_to_email_templates()
        self.__cvtable.access_action_item(self.template_name, "Edit")

        editor_contents = self.__template_obj.get_editor_contents()
        editor_contents['subject'] = "Subject : " + editor_contents['subject']
        editor_contents['subject'] = \
            editor_contents['subject'].replace("$TENANT_COMPANY_NAME$", "[Tenant company name]")
        self.__admin_console.click_button("Preview email")

        preview_contents = self.__template_obj.get_preview_contents()
        preview_contents['subject'] = preview_contents['subject'].replace("\n", " ")
        preview_contents['body'] = preview_contents['body'].replace("\n", " ")

        body_token_list = ['$EMAIL_HEADER$', '$RECIPIENT_NAME$', '$TENANT_COMPANY_NAME$',
                           '$USERNAME$', '$ADMINISTRATOR_NAME$', '$EMAIL_FOOTER$']
        token_replacement_list = [self.email_header, '[Recipient name]', '[Tenant company name]',
                                  '[User name]', '[Administrator name]', self.email_footer]

        for token, string in zip(body_token_list, token_replacement_list):
            editor_contents['body'] = editor_contents['body'].replace(token, string)

        self.log.info("Preview content: " + str(preview_contents))
        self.log.info("Editor content: " + str(editor_contents))

        for key, value in editor_contents.items():

            if editor_contents[key] == preview_contents[key]:
                self.log.info(f"Values for {key} matches")
            else:
                raise Exception(f"Values for {key} don't match")

        self.__admin_console.select_breadcrumb_link_using_text("Email templates")

    def set_template_as_default(self):
        """Marks the template with the given name as default"""
        self.__navigator.navigate_to_email_templates()
        self.__template_obj.action_set_template_as_default(self.template_name)
        if self.__template_obj.is_template_default(self.template_name):
            self.log.info("Template is successfully marked as default")
        else:
            raise Exception("Failed to mark template as default")

    def template_send_test_mail(self):
        """Sends a test mail for the template"""

        self.__navigator.navigate_to_email_templates()
        self.__template_obj.send_test_mail(self.template_name)
        self.__admin_console.select_breadcrumb_link_using_text("Email templates")
