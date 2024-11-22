# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Manage->Commcell page on the AdminConsole

Class:

    Commcell()

Functions:

========================================================================================
Page hyperlinks:
    access_sendlogs                     - click on access send logs button
    access_viewlogs                     - click on access view logs button
========================================================================================

Tile Editing:
- - - - - - - - - - - - - - - Activity Control Tile - - - - - - - - - - - - - - -
    enable_all_job_activity             - enables all activity
    disable_all_job_activity            - disables all activity
    enable_backup                       - enables job activity
    disable_backup                      - disables job activity
    enable_restore                      - enables restores
    disable_restore                     - disables restores
    enable_schedule                     - enables schedules
    disable_schedule                    - disables schedules

- - - - - - - - - - - - - - - General Tile - - - - - - - - - - - - - - -
    enable_authcode_for_installation    - Enables requirement of authCode for installation
    disable_authcode_for_installation   - Disables requirement of authCode for installation
    enable_tfa                          - Enables two factor authentication
    disable_tfa                         - Disables two factor authentication
    enable_userlogon_limit              - Enabled user logon limits
    disable_userlogon_limit             - Disabled user logon limits

- - - - - - - - - - - - - - - Privacy Tile - - - - - - - - - - - - - - -
    enable_data_privacy                 - Enables allowance of users to enable data privacy
    disable_data_privacy                - Disables allowance of users to enable data privacy

- - - - - - - - - - - - - - - Passkey Tile - - - - - - - - - - - - - - -
    enable_passkey_for_restore          - Enabled and sets passkey for restores
    disable_passkey_for_restore         - Disables passkey for restores
    edit_passkey                        - Edits already enabled passkey
    enable_authorize_for_restore        - Enables passkey authorization
    disable_authorize_for_restore       - Disables passkey authorization
    enable_users_can_enable_passkey     - Enables user authorization for passkey setting
    disable_users_can_enable_passkey    - Disables user authorization for passkey setting

- - - - - - - - - - - - - - - Email Tile - - - - - - - - - - - - - - -
    edit_email_settings                 - Edit/Set/Update email settings

- - - - - - - - - - - - - - - Default plans Tile - - - - - - - - - - - - - - -
    edit_default_plans                  - Edit/Set/Update Default plan

- - - - - - - - - - - - - - - Password encryption Tile - - - - - - - - - - - - - - -
    edit_password_encryption            - Edit/Set/Update password encryption

- - - - - - - - - - - - - - - Security Tile - - - - - - - - - - - - - - -
    add_security_associations           - Add security associations
    delete_security_associations        - Delete security associations
    set_show_inherited_association      - Sets to show or hide inherited associations

- - - - - - - - - - - - - - - General Tile - - - - - - - - - - - - - - -
    set_workload_region                 - Sets region of commcell

- - - - - - - - - - - - - - - Universal Command Center Tile - - - - - - - - - - - - - - -
    edit_universal_command_centers      - Selects command center to set as universal

- - - - - - - - - - - - - - - SLA Tile - - - - - - - - - - - - - - -
    edit_sla                            - Sets SLA period

 - - - - - - - - - - - - - - - Restricted Console Tile - - - - - - - - - - - - - - -
    add_restricted_console              - Add Restricted console
    remove_restricted_console           - Removes Restricted console
    reset_restricted_console            - Resets Restricted console
       
========================================================================================
details extraction:
    extract_all_displayed_details       - Retrieves all information displayed in Commcell page
    get_about_details                   - Returns dict with about tile labels
    get_activity_control_details        - Returns dict with activity control labels and toggle states
    get_security_details                - Returns dict with user/groups and roles lists
    get_privacy_details                 - Returns dict with privacy labels and toggle states
    get_email_details                   - Returns dict with email labels and values
    get_passkey_details                 - Returns dict with passkey labels and toggle states
    get_general_details                 - Returns dict with general labels and values, toggles
    get_sla_details                     - Returns dict with sla label and period values
    get_password_encryption_details     - Returns dict with password encryption label and type
    get_universal_command_center_details- Returns list of universal command center hostnames

"""
from time import sleep
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogsPanel
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.dialog import RSecurity, RModalDialog
from Web.AdminConsole.Components.panel import PanelInfo, RPanelInfo, RDropDown, RSecurityPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import PageService, WebAction


class Commcell:
    """ Class for Commcell page of admin console"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.__about_panel = RPanelInfo(self._admin_console, 'About')
        self.__rsecurity = RSecurity(self._admin_console)
        self.__activity_panel = RPanelInfo(self._admin_console, 'Activity control')
        self.__email_panel = RPanelInfo(self._admin_console, 'Email settings')
        self.__general_panel = RPanelInfo(self._admin_console, 'General')
        self.__privacy_panel = RPanelInfo(self._admin_console, 'Privacy')
        self.__passkey_panel = RPanelInfo(self._admin_console, 'Passkey')
        self.__sla_panel = RPanelInfo(self._admin_console, 'SLA')
        self.__password_panel = RPanelInfo(self._admin_console, 'Password encryption')
        self.__security_panel = RSecurityPanel(self._admin_console)
        self.__universal_panel = RPanelInfo(self._admin_console, 'Universal Command Centers')
        self.__default_plans_panel = RPanelInfo(self._admin_console, 'Default plans')
        self.__rc_panel = RPanelInfo(self._admin_console, 'Restricted consoles')
        self.__page_container = PageContainer(self._admin_console, 'commcell')
        self.__rtoggle = Toggle(self._admin_console)
        self.__dialog = RModalDialog(self._admin_console)
        self.__rdrop_down = RDropDown(self._admin_console)
        self._alert = Alert(self._admin_console)

        self.log = logger.get_log()
        self._admin_console.load_properties(self)

    # ------------------------------------ PAGE FUNCTIONS ---------------------------------------
    @PageService()
    def extract_all_displayed_details(self):
        """
            Retrieves all information displayed in Commcell page
        Returns:
            all_details dict() : dictionary containing commcell information displayed in UI
        """
        return {
            'About': self.get_about_details(),
            'Activity control': self.get_activity_control_details(),
            'Security': self.get_security_details(),
            'Privacy': self.get_privacy_details(),
            'Email settings': self.get_email_details(),
            'Passkey': self.get_passkey_details(),
            'General': self.get_general_details(),
            'SLA': self.get_sla_details(),
            'Password encryption': self.get_password_encryption_details(),
            'Restricted consoles': self.get_restricted_consoles()
        }

    @PageService()
    def access_sendlogs(self):
        """access send logs menu"""
        self.__page_container.access_page_action('Send logs')

    @PageService()
    def access_viewlogs(self, log_path):
        """access view logs menu"""
        self.__page_container.access_page_action('View logs')
        ViewLogsPanel(self._admin_console).access_log(log_path)
        self._admin_console.wait_for_completion()

    # ------------------------------------ 'ABOUT' TILE FUNCTIONS ---------------------------------------
    @PageService()
    def get_about_details(self):
        """Returns dict with label and value key from about tile"""
        return self.__about_panel.get_details()

    # ------------------------------------ ACTIVITY CONTROL FUNCTIONS ---------------------------------------
    @PageService()
    def get_activity_control_details(self):
        """Returns dict with each label as key and its toggle from activity control tile"""
        activity_panel_labels = [
            self._admin_console.props[prop_key] for prop_key in [
                'All_Job_Activity', 'Data_Backup', 'Data_Restore',
                'Data_Aging', 'Auxiliary_Copy', 'Scheduler', 'Data_Verification'
            ]
        ]
        return {
            label: True if self.__activity_panel.is_toggle_enabled(label=label)
            else self.__activity_panel.get_toggle_delay(label=label)
            for label in activity_panel_labels
        }

    @PageService()
    def set_activity_setting(self, settings: dict = None):
        """Sets all the toggles to required values

        Args:
            settings    (dict)  -   dict with all toggles to enable/disable
            example:
            {
                'All job activity': True,
                'Data backup': False,
                'Data restore': '1 hour'  --- will be enabled with delay (1 hour/ 4 hours/ 8 hours ...1 day)
                ...
            }
        """
        if settings is None:
            settings = {}
        for toggle_label, value in settings.items():
            if value == True:
                self.__activity_panel.enable_toggle(label=toggle_label)
            elif value == False:
                self.__activity_panel.enable_toggle(label=toggle_label)  # to overwrite existing delays
                self.__activity_panel.disable_toggle(label=toggle_label)
            else:
                self.__activity_panel.disable_toggle(label=toggle_label)
                self.__activity_panel.enable_toggle(label=toggle_label, delay=value)

    # ------------------------------------ GENERAL FUNCTIONS ---------------------------------------

    @PageService()
    def get_general_details(self):
        """Returns dict with label values and also toggle status under general tile"""
        general_panel_labels = [
            self._admin_console.props[prop_key] for prop_key in [
                'label.enableAuthCode', 'label.twoFactorAuthentication', 'label.limitLockSettings'
            ]
        ]

        data = self.__general_panel.get_details()
        data['authcode'] = self.get_visible_authcode()
        data |= {
            label: self.__general_panel.is_toggle_enabled(label=label)
            for label in general_panel_labels
        }

        dirty_keys = [key for key in data if '\n' in key]
        for key in dirty_keys:
            data[key.split('\n')[0]] = data[key]
            del data[key]
        return data

    @PageService()
    def enable_authcode_for_installation(self):
        """Enables requirement of authCode for installation and returns the authcode text"""
        self.__general_panel.enable_toggle(self._admin_console.props['label.enableAuthCode'])
        self._admin_console.wait_for_completion()
        return self.get_visible_authcode()

    @WebAction()
    def get_visible_authcode(self):
        """Returns authcode text if visible, else returns False"""
        try:
            authcode = self._driver.find_element(By.XPATH, '//span[@class="authcode"]')
            return authcode.text
        except NoSuchElementException:
            return False

    def __reload_authcode(self):
        self._driver.find_element(By.XPATH,
                                  '//span[contains(@class,"authcode")]//div[contains(@class,"generateIcon")]'
                                  ).click()

    @PageService()
    def generate_new_authcode(self):
        """Generates new authcode and returns the code text"""
        self.__reload_authcode()
        self.__dialog.click_submit()
        self._admin_console.wait_for_completion()
        return self.get_visible_authcode()

    @PageService()
    def disable_authcode_for_installation(self):
        """Disables requirement of authCode for installation"""
        self.__general_panel.disable_toggle(self._admin_console.props['label.enableAuthCode'])
        self.__dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def enable_tfa(self, tfa_settings=None, wait=40):
        """Enables two factor authentication

        Args:
            tfa_settings (dict): dict with settings to set for tfa, leave empty for default
                    example:
                        {
                            'User groups':'all' or ['group1','group2'...],
                            'Allow passwordless login':True or False,
                            'Allow usernameless login':True or False
                        }
            wait (int) : seconds to wait for user_group to appear in
        """
        if not tfa_settings:
            tfa_settings = {}
        self.__general_panel.enable_toggle(self._admin_console.props['label.twoFactorAuthentication'])
        if tfa_settings:
            if tfa_settings['User groups'] == 'all':
                target = []
            else:
                target = tfa_settings['User groups']
            TFADialog(self._admin_console).set_tfa_options(
                target=target,
                usernameless=tfa_settings.get('Allow usernameless login', False),
                passwordless=tfa_settings.get('Allow passwordless login', False),
                wait=wait
            )
        self.__dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_tfa_details(self):
        """Returns the TFA settings inside the tile"""
        if not self.__general_panel.is_toggle_enabled(label=self._admin_console.props['label.twoFactorAuthentication']):
            return {}
        self.__general_panel.edit_tile_entity(self._admin_console.props['label.twoFactorAuthentication'])
        tfa_data = TFADialog(self._admin_console).read_tfa_options()
        self.__dialog.click_cancel()
        self._admin_console.wait_for_completion()
        return tfa_data

    @PageService()
    def disable_tfa(self):
        """Disables two factor authentication"""
        self.__general_panel.disable_toggle(self._admin_console.props['label.twoFactorAuthentication'])

    @PageService()
    def enable_userlogon_limit(self, userlogon_settings=None):
        """Enables user logon limit (overwrites/edits if already ON)

        Args:
            userlogon_settings (dict) : dict with settings for user logins, empty for default
                    example:
                        {
                            'attemptLimit':5,
                            'attemptWithin':1,
                            'lockDuration':24,
                            'durationIncrement':1  [Optional]
                        }
        """
        if userlogon_settings is None:
            userlogon_settings = {}
        settings_copy = userlogon_settings.copy()
        if self.__general_panel.is_toggle_enabled(label=self._admin_console.props['label.lockSettings']):
            self.__general_panel.edit_tile_entity(self._admin_console.props['label.lockSettings'])
        else:
            self.__general_panel.enable_toggle(self._admin_console.props['label.lockSettings'])
        if userlogon_settings:
            if userlogon_settings.get('durationIncrement'):
                self.__rtoggle.enable(id="toggleLockDurationIncrement")
            else:
                self.__rtoggle.disable(id="toggleLockDurationIncrement")
                if 'durationIncrement' in userlogon_settings:
                    del settings_copy['durationIncrement']

            for key, value in settings_copy.items():
                self._admin_console.fill_form_by_id(key, value)

        self.__dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_userlogon_settings(self):
        """Reads user logon limit details set

        Returns:
            userlogon_settings (dict) : dict with settings for user logins, empty for default
                    example:
                        {
                            'attemptLimit':5,
                            'attemptWithin':1,
                            'lockDuration':24,
                            'durationIncrement':0
                        }
        """
        if not self.__general_panel.is_toggle_enabled(label=self._admin_console.props['label.lockSettings']):
            return {}
        self.__general_panel.edit_tile_entity(self._admin_console.props['label.lockSettings'])
        data = {}
        for key in ['attemptLimit', 'attemptWithin', 'lockDuration', 'durationIncrement']:
            data[key] = float(self.__dialog.get_text_in_field(key))
            if key == 'durationIncrement' and not self.__rtoggle.is_enabled(id="toggleLockDurationIncrement"):
                data[key] = 0
        self.__dialog.click_cancel()
        self._admin_console.wait_for_completion()
        return data

    @PageService()
    def disable_userlogon_limit(self):
        """Disables user logon limit"""
        self.__general_panel.disable_toggle(self._admin_console.props['label.lockSettings'])

    @PageService()
    def set_workload_region(self, region):
        """Sets workload region

        Args:
            region (str): the region name
        """
        self.__general_panel.edit_tile_entity('Workload region')
        self.__rdrop_down.select_drop_down_values(drop_down_id="regionDropdown_", values=[region])
        self._driver.find_element(By.ID, "tile-row-submit").click()

    # ------------------------------------ PRIVACY FUNCTIONS ---------------------------------------
    @PageService()
    def get_privacy_details(self):
        """Returns dict with each label as key and its toggle status as boolean value"""
        return self.__privacy_panel.get_details()

    @PageService()
    def enable_data_privacy(self):
        """Enables allowance of users to enable data privacy"""
        self.__privacy_panel.enable_toggle(self._admin_console.props['label.adminPrivacyPolicy'])

    @PageService()
    def disable_data_privacy(self):
        """Disables allowance of users to enable data privacy"""
        self.__privacy_panel.disable_toggle(self._admin_console.props['label.adminPrivacyPolicy'])

    # ------------------------------------ PASSKEY FUNCTIONS ---------------------------------------
    @PageService()
    def get_passkey_details(self):
        """Returns dict with each label as key and its toggle status as boolean value"""
        passkey_panel_labels = [
            self._admin_console.props[prop_key] for prop_key in [
                'label.passkeyText', 'label.allowUsersToEnablePasskey', 'label.authorizeForRestore'
            ]
        ]
        details = {}
        for label in passkey_panel_labels:
            if label == passkey_panel_labels[-1] and not details[passkey_panel_labels[0]]:
                # avoid authorize toggle if passkey toggle is off
                continue
            details[label] = self.__passkey_panel.is_toggle_enabled(label=label)
        return details

    @PageService()
    def enable_passkey_for_restore(self, passkey):
        """Enables requirement of passkey for restores"""
        self.__passkey_panel.enable_toggle(self._admin_console.props['label.passkeyText'])
        self._admin_console.fill_form_by_id("passkey", passkey)
        self._admin_console.fill_form_by_id("passkey-confirm", passkey)
        self.__dialog.click_submit()
        self._admin_console.check_error_message()  # error when passkey is not strong
        self._admin_console.click_button('Yes')
        self._admin_console.wait_for_completion()

    @PageService()
    def disable_passkey_for_restore(self, passkey):
        """Disables requirement of passkey for restores"""
        self.__passkey_panel.disable_toggle(self._admin_console.props['label.passkeyText'])
        self._admin_console.fill_form_by_id("passkey", passkey)
        self.__dialog.click_submit()
        self._alert.check_error_message(20)  # toast error when passkey is wrong
        self._admin_console.wait_for_completion()

    @PageService()
    def edit_passkey(self, new_passkey, old_passkey):
        """Edit the passkey"""
        self.__passkey_panel.edit_tile_entity(self._admin_console.props['label.passkeyText'])
        self._admin_console.fill_form_by_id("prev-passkey", old_passkey)
        self._admin_console.fill_form_by_id("passkey", new_passkey)
        self._admin_console.fill_form_by_id("passkey-confirm", new_passkey)
        self.__dialog.click_submit()
        self._admin_console.check_error_message()  # error when passkey is not strong
        self._alert.check_error_message(20)  # toast error when passkey is wrong
        self._admin_console.wait_for_completion()

    @PageService()
    def enable_users_can_enable_passkey(self):
        """Enables users to enable passkey"""
        self.__passkey_panel.enable_toggle(self._admin_console.props['label.allowUsersToEnablePasskey'])

    @PageService()
    def disable_users_can_enable_passkey(self):
        """Disables users to enable passkey"""
        self.__passkey_panel.disable_toggle(self._admin_console.props['label.allowUsersToEnablePasskey'])

    @PageService()
    def enable_authorize_for_restore(self, passkey):
        """Enables authorize for restore"""
        self.__passkey_panel.enable_toggle(self._admin_console.props['label.authorizeForRestore'])
        self._admin_console.fill_form_by_id("existingPasskey", passkey)
        self.__dialog.click_submit()
        self._alert.check_error_message(20)  # toast error when passkey is wrong
        self._admin_console.wait_for_completion()

    @PageService()
    def disable_authorize_for_restore(self):
        """Disables authorize for restore"""
        self.__passkey_panel.disable_toggle(self._admin_console.props['label.authorizeForRestore'])

    # ------------------------------------ EMAIL FUNCTIONS ---------------------------------------
    @PageService()
    def get_email_details(self):
        """ Returns dict with labels as keys and its holding text as values"""
        return self.__email_panel.get_details()

    @PageService()
    def edit_email_settings(self, email_settings, test_email=False):
        """
            Edit/Set/Update email settings
        Args:
            email_settings (dict):
                {
                    'SMTP server': String,
                    'SMTP port': integer between 1 and 6100 (both included),
                    'Sender email': String,
                    'Sender name': String,
                    'Encryption algorithm': String,
                    'Use authentication': boolean,
                    'User name': String,
                    'Password': String (Don't include this key if you want to keep same password)
                    Note: Modern authentication support is not implemented
                }
            test_email  (bool)  -   if test email button to press

        """
        self.__email_panel.edit_tile()
        self._admin_console.wait_for_completion()
        if email_settings.get('SMTP server'):
            self._admin_console.fill_form_by_id('smtpServer', email_settings.get('SMTP server'))
        if email_settings.get('SMTP port'):
            self._admin_console.fill_form_by_id('smtpPort', email_settings.get('SMTP port'))
        if email_settings.get('Sender email'):
            self._admin_console.fill_form_by_id('senderAddress', email_settings.get('Sender email'))
        if email_settings.get('Sender name'):
            self._admin_console.fill_form_by_id('senderName', email_settings.get('Sender name'))
        if email_settings.get('Encryption algorithm'):
            self.__rdrop_down.select_drop_down_values(
                drop_down_label=self._admin_console.props['label.encryptionAlgorithm'],
                values=[email_settings.get('Encryption algorithm')]
            )
        if email_settings.get('Use authentication'):
            self.__rtoggle.enable(id="useAuth")
            # split code path here if you want to add modern auth support, for now we assume classic auth
            self._admin_console.select_radio(id='classicAuth')
            self._admin_console.fill_form_by_id('userName', email_settings.get('User name'))
            if email_settings.get('Password'):
                self._admin_console.fill_form_by_id('password', email_settings.get('Password'))
                self._admin_console.fill_form_by_id('password-confirm', email_settings.get('Password'))
        else:
            self.__rtoggle.disable(id="useAuth")

        if test_email:
            self._admin_console.click_button_using_text("Test email")
            self._alert.check_error_message(20)  # toast error when smtp server is wrong
            self._admin_console.wait_for_completion()

        self._admin_console.click_button_using_text("Save")
        self._admin_console.wait_for_completion()
        self.__dialog.click_submit()
        self._admin_console.check_error_message()
        self._admin_console.wait_for_completion()

    # ------------------------------------ PASSWORD ENCRYPTION FUNCTIONS ---------------------------------------
    @PageService()
    def get_password_encryption_details(self):
        """ Returns dict with labels as keys and its holding text as values"""
        return self.__password_panel.get_details()

    @PageService()
    def edit_password_encryption(self, password_encryption):
        """
            Edit/Set/Update password encryption
        Args:
            password_encryption (dict):
                {
                    'Key Management Server': String
                }
        """
        self.__password_panel.edit_tile()
        self._admin_console.wait_for_completion()
        self.__rdrop_down.select_drop_down_values(index=0, values=[password_encryption.get('Key Management Server')])
        self._admin_console.submit_form()
        self._admin_console.check_error_message()

    # ------------------------------------ DEFAULT PLANS FUNCTIONS ---------------------------------------
    @PageService()
    def edit_default_plans(self, default_plan):
        """
            Helper function to Edit/Set/Update Default plan
        Args:
            default_plan (dict):
                {
                    'Server plan': String (Give 'None' if you want no default plans)
                }
        """
        self.__default_plans_panel.edit_tile()
        self._admin_console.wait_for_completion()
        for key, value in default_plan.items():
            if key == 'Server plan':
                self.__rdrop_down.select_drop_down_values(drop_down_id='serverPlan', values=[value])
            elif key == 'Laptop plan':
                self.__rdrop_down.select_drop_down_values(drop_down_id='laptopPlan', values=[value])
            elif key == 'Fs plan':
                self.__rdrop_down.select_drop_down_values(drop_down_id='fsPlan', values=[value])
            elif key == 'Db plan':
                self.__rdrop_down.select_drop_down_values(drop_down_id='dbPlan', values=[value])
        self._admin_console.submit_form()
        self._admin_console.check_error_message()

    # ------------------------------------ SECURITY FUNCTIONS ---------------------------------------
    @PageService()
    def get_security_details(self, inherited_associations=False):
        """Returns dict with username and associations key with list of user and associations values
        Args:
            inherited_associations (bool): returns inherited associations also if true
        """
        self.__set_show_inherited_association(inherited_associations)
        Rtable(self._admin_console, id="securityAssociationsTable").set_pagination('max')
        return self.__security_panel.get_details()

    @WebAction()
    def __set_show_inherited_association(self, setting):
        """sets the show inherited association setting

        Args:
            setting (bool) : whether to show the associations or not
        """
        show_or_hide = ['Hide', 'Show'][setting]
        xpath = f"//a[text()='{show_or_hide} inherited association']"
        try:
            self._driver.find_element(By.XPATH, xpath).click()
        except NoSuchElementException:
            self.log.error("Couldn't find xpath, perhaps association is already set")

    @PageService()
    def get_security_dialog_associations(self):
        """
        Returns the associations inside the security dialog
        """
        self.__security_panel.edit_tile()
        data = self.__rsecurity.get_security_associations()
        self.__rsecurity.click_cancel()
        return data

    @PageService()
    def add_security_associations(self, associations=None):
        """ Method to add security associations

        Args:
            associations (dict) : User and Roles

                eg:
                associations = {
                        'user1' : ['View', 'Alert Owner'],
                        'user2' : ['Master', 'Plan Subscription Role', 'Tenant Operator']
                    }

        """
        if associations is None:
            associations = dict()
        self.__security_panel.edit_tile()
        self.__rsecurity.edit_security_association(associations)

    @PageService()
    def delete_security_associations(self, associations=None):
        """Method to delete security associations"""
        if associations is None:
            associations = dict()
        self.__security_panel.edit_tile()
        self.__rsecurity.edit_security_association(associations, False)

    # ------------------------------------ SLA FUNCTIONS ---------------------------------------
    @WebAction()
    def __click_sla_edit(self):
        """
        Clicks on inline edit in SLA panel
        """
        # self.__sla_panel.edit_tile_entity('SLA period')
        # component web action generic xpath incompatible
        self._driver.find_element(By.XPATH, "//div[@class='action-buttons']//button").click()

    @WebAction()
    def __press_tick(self):
        """
        Clicks on the tick button in line
        """
        button_xp = f"//span[text()='SLA period']" \
                    f"//ancestor::div[contains(@class,'tile-row')]" \
                    f"//div[contains(@class,'action-buttons')]/div[2]"
        self._driver.find_element(By.XPATH, button_xp).click()

    @WebAction()
    def __select_sla_period(self, period):
        """
        Selects the sla period menu item via drop down
        Args:
            period (str):   the SLA period text
        """
        self.__rdrop_down.select_drop_down_values(
            values=[period],
            index=0
        )
        sleep(1)

    @PageService()
    def get_sla_details(self):
        """ Returns dict with labels as keys and its holding text as values"""
        return self.__sla_panel.get_details()

    @PageService()
    def edit_sla(self, period):
        """
        Method to change current SLA period
        Args:
            period (str):   the SLA period to set
                            1 day /2 days /3 days /5 days
                            1 week /2 weeks
                            1 month /3 months
        """
        self.__click_sla_edit()
        self.__select_sla_period(period)
        self.__press_tick()
        self._admin_console.wait_for_completion()

    # ------------------------------------ UNIVERSAL COMMAND CENTER FUNCTIONS ---------------------------------------
    @WebAction()
    def __get_embedded_table_cells(self):
        """
        Gets the cell elements inside Universal Command Center table
        """
        # Rtable does not have id, title, embedded in panel. Using custom xpaths for now.
        cells_xpath = "//span[contains(@class, 'MuiCardHeader-title') " \
                      "and normalize-space()='Universal Command Centers']" \
                      "/ancestor::div[contains(@class, 'MuiCard-root')]" \
                      "//td[contains(@class,'grid-cell')]"
        return [elem.text for elem in self._driver.find_elements(By.XPATH, cells_xpath)][::2]

    @PageService()
    def get_universal_command_center_details(self):
        """Returns list of universal command center hostnames"""
        return self.__get_embedded_table_cells()

    @PageService()
    def edit_universal_command_centers(self, command_centers):
        """
        Selects commcells to use as universal command centers

        Args:
            command_centers (list): list of commcell names
        """
        self.__universal_panel.edit_tile()
        rmd = RModalDialog(self._admin_console)
        rmd.select_dropdown_values("webconsoles", command_centers)
        self._driver.find_element(By.XPATH, "//h4[@class='modal-title']").click()
        rmd.click_submit()

    # ------------------------------------ RESTRICTED CONSOLES FUNCTIONS ---------------------------------------
    @PageService()
    def get_restricted_consoles(self):
        """ Returns dict with labels as keys and its holding text as values"""
        return self.__rc_panel.get_card_content()

    @PageService()
    def add_restricted_console(self, restricted_consoles: list, do_not_inherit: bool = False, wait=True) -> None:
        """
        Add Restricted Consoles

        Args:
            restricted_consoles (list): list of Restricted Console names

                ex:- restricted_consoles = ["Command Center", "API"]
            do_not_inherit (bool): If True, disables Inherit Restricted consoles
            wait (bool): if True, waits for page to load, else returns without waiting
        """
        self.__rc_panel.edit_tile()
        if do_not_inherit:
            self.__dialog.disable_toggle(toggle_element_id='inheritRestrictedConsoles')
        self.__rdrop_down.select_drop_down_values(drop_down_id="consoleType", values=restricted_consoles)
        self.__dialog.click_submit(wait)
        self._admin_console.check_error_message()

    @PageService()
    def remove_restricted_console(self, restricted_consoles: list, do_not_inherit: bool = False) -> None:
        """
        Remove Restricted Consoles

        Args:
            restricted_consoles (list): list of Restricted Console names

                ex:- restricted_consoles = ["Command Center", "API"]
            do_not_inherit (bool): If True, disables Inherit Restricted consoles
        """
        self.__rc_panel.edit_tile()
        if do_not_inherit:
            self.__dialog.disable_toggle(toggle_element_id='inheritRestrictedConsoles')
        self.__rdrop_down.deselect_drop_down_values(drop_down_id="consoleType", values=restricted_consoles)
        self.__dialog.click_submit()
        self._admin_console.check_error_message()

    @PageService()
    def reset_restricted_console(self) -> None:
        """
        Reset Restricted Consoles
        """
        self.__rc_panel.edit_tile()
        self.__dialog.click_button_on_dialog('Reset')
        self._admin_console.check_error_message()    
        

class TFADialog(RModalDialog):
    """ React 2-factor authentication Class """

    def __init__(self, admin_console):
        """ Initialize the React 2-factor authentication Class

        Args:
            admin_console : instance of AdminConsoleBase
        """
        super(TFADialog, self).__init__(admin_console)
        self.rtoggle = Toggle(admin_console)

    @WebAction()
    def __set_target(self, target):
        """Clicks radio button to select all or group
        """
        self._driver.find_element(By.XPATH, f"//*[@id='{target}']").click()

    @WebAction()
    def __get_target(self):
        """
        Finds the selected radio and gets the list items present
        """
        if self._driver.find_element(By.XPATH, f"//*[@id='all']").is_selected():
            return 'all'
        else:
            groups = self._driver.find_elements(
                By.XPATH, self._dialog_xp + "//input[@id='userGroupsListDropdown']/..//div[@role='button']"
            )
            return [group.text for group in groups]

    @WebAction()
    def __search_and_select_group_name(self, value, wait_until=30):
        """Method to search and select user group

        Args:
            value (str)     : Name of user/group
            wait_until(int) : Maximum time to wait till user appears in dropdown
        """
        input_box = self._driver.find_element(By.XPATH,
                                              self._dialog_xp + "//input[@id='userGroupsListDropdown']")
        input_box.send_keys(value)
        user_group_elem = WebDriverWait(self._driver, wait_until).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, f"//li[contains(text(),'{value}')]")
            )
        )
        user_group_elem.click()
        sleep(1)

    @WebAction()
    def __clear_search_box(self):
        """Method to clear the user groups search box if entities already present"""
        self._driver.find_element(By.XPATH,
                                  self._dialog_xp + "//input[@id='userGroupsListDropdown']").send_keys('a')
        try:
            self._driver.find_element(By.XPATH, self._dialog_xp + "//button[@title='Clear']").click()
        except NoSuchElementException:
            self._driver.find_element(By.XPATH,
                                      self._dialog_xp + "//input[@id='userGroupsListDropdown']").send_keys(u'\ue003')

    @PageService()
    def set_tfa_options(self, target=None, passwordless=False, usernameless=False, wait=30):
        """
        Method to set the 2-factor authentication settings in commcell page

        Args:
            target (list) : target user groups, if empty all will apply
            passwordless(bool): allow passwordless login
            usernameless(bool): allow usernameless login
            wait (int)  : seconds to wait for group to appear in dropdown
        """
        if target is None:
            target = []
        if not target:
            self.__set_target('all')
        else:
            self.__set_target('group')
            self.__clear_search_box()
            for user_group in target:
                self.__search_and_select_group_name(user_group, wait)
            self._admin_console.collapse_menus()

        if passwordless:
            self.toggle.enable(id="passwordlessLogin")
        else:
            self.toggle.disable(id="passwordlessLogin")
        if usernameless:
            self.toggle.enable_(id="usernamelessLogin")
        else:
            self.toggle.disable(id="usernamelessLogin")

    @PageService()
    def read_tfa_options(self):
        """
        Reads the TFA options from the open TFA dialog in commcell page

        Returns: dict with same format as input to set_Tfa_options

        example: {
            User groups: 'all' or ['gr1', 'gr2']
            passwordless: True/False,
            usernameless: True/False
        }
        """
        return {
            'User groups': self.__get_target(),
            'passwordless': self.toggle.is_enabled(id="passwordlessLogin"),
            'usernameless': self.toggle.is_enabled(id="usernamelessLogin")
        }
