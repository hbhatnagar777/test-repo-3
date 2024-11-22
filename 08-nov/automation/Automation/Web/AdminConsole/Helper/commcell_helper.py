# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic tests on Manage - > Commcell page.

Class:
    CommcellHelper()

Functions:
    get_passkey_from_db     -   gets passkey value (commcell level) from DB for testing purpose
    clean_up                -   cleans up only the changes done using this helper

Tests:
    test_about_tile                 -   validates about tile, send logs and view logs redirect links
    test_activity_control_tile      -   validates activity control tile, including various edit options
    test_privacy_tile               -   validates the privacy tile including edit
    test_sla_tile                   -   validates the sla tile
    test_encryption_tile            -   validates the encryption tile (edit not implemented)
    test_passkey_tile               -   validates the passkey tile including edit
    test_security_tile              -   validates the security tile including edit
    test_email_tile                 -   validates the email tile including edit if auth is off
    test_general_tile               -   validates the general tile including all edit options
"""
import functools
import random
import time
from copy import deepcopy
from typing import Union

from cvpysdk.commcell import Commcell as CommcellSDK
from cvpysdk.security.security_association import SecurityAssociation
from dateutil.parser import parse

from AutomationUtils import logger, cvhelper
from AutomationUtils.commonutils import parse_duration
from AutomationUtils.database_helper import CommServDatabase
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep


class CommcellHelper:
    """ Helper for Commcell page """
    test_step = TestStep()

    def __init__(self, admin_console: AdminConsole = None, commcell: CommcellSDK = None) -> None:
        """ Initializes the commcell helper module """
        if not admin_console and not commcell:
            raise Exception("Provide at least one of the parameters")
        if admin_console:
            self.admin_console = admin_console
            self.commcell_page = Commcell(self.admin_console)
        if commcell:
            self.commcell_obj = commcell
            self.csdb = CommServDatabase(commcell)
        self.log = logger.get_log()
        self.cleanup_functions = {}  # need for clean up, to restore initial commcell settings

    # UTILS
    def get_passkey_from_db(self) -> Union[str, None]:
        """
        Gets the passkey from DB entry if its set

        Returns:
            passkey -   if entry is present in DB
            None    -   if no passkey found
        """
        self.csdb.execute('select attrVal from APP_CompanyProp where componentNameId=0 and LEN(attrVal) > 45')
        encrypted_passkey = self.csdb.rows[0][0]
        if encrypted_passkey:
            return cvhelper.format_string(self.commcell_obj, encrypted_passkey)

    def clean_up(self) -> list[str]:
        """
        Cleans up all changes done using instance of this helper

        Returns:
            errors  (list)  -   list of errors during clean up
        """
        errors = []
        self.log.info("Cleaning up changes done by Commcell Helper")
        for cleaner_name, cleaner in self.cleanup_functions.items():
            self.log.info(f"executing cleaner -> {cleaner_name}")
            try:
                cleaner()
            except Exception as exp:
                errors.append(f"failed cleanup {cleaner_name} with error -> {str(exp)}")
                self.log.error(f"failed cleanup with error -> {str(exp)}")
        self.log.info("Cleanup done")
        return errors

    # PAGE LEVEL TEST (ABOUT TILE, VIEW LOGS, SEND LOGS)
    @test_step
    def test_about_tile(self) -> list[str]:
        """
        Tests the About tile, view logs and send logs redirects

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """
        errors = []
        expected_data = {
            self.admin_console.props['label.commserver']: self.commcell_obj.commserv_hostname,
            self.admin_console.props['header.Version']: self.commcell_obj.version,
        }
        if self.commcell_obj.release_name:
            expected_data[self.admin_console.props['label.releaseName']] = self.commcell_obj.release_name
        if (about_tile := self.commcell_page.get_about_details()) != expected_data:
            errors.append(f'About tile = {about_tile} does not match API = {expected_data}')
        # test send logs page
        self.commcell_page.access_sendlogs()
        # new tab is opened by send logs
        self.admin_console.driver.switch_to.window(self.admin_console.driver.window_handles[-1])
        self.admin_console.wait_for_completion()
        if (f'/sendLogs/commCell/{self.commcell_obj.commcell_id}?redirectTo=commCell'
                not in self.admin_console.current_url()):
            errors.append(f'Send logs took to wrong URL.. Got url-> {self.admin_console.current_url()}')
        SendLogs(self.admin_console).select_local_output('just testing send log page integrity')
        self.admin_console.driver.close()
        time.sleep(2)  # wait because tab does not close sometimes
        self.admin_console.driver.window_handles # to update window handles properly
        self.admin_console.driver.switch_to.window(self.admin_console.driver.window_handles[-1])

        # test view logs link
        self.commcell_page.access_viewlogs('EvMgrS.log')
        self.admin_console.wait_for_completion()
        if (f'/viewLogs?clientId={self.commcell_obj.commcell_id}&fileName=EvMgrS.log'
                not in self.admin_console.current_url()):
            errors.append(f'View logs took to wrong URL.. Got url-> {self.admin_console.current_url()}')
        if not (log_data := ViewLogs(self.admin_console).get_log_data()):
            errors.append(f'View logs page maybe didnt load, log data is empty: {log_data}')
        self.admin_console.driver.back()
        self.admin_console.wait_for_completion()
        self.log.info("ABOUT AND REDIRECTIONS VALIDATED SUCCESSFULLY!")
        return errors

    # ACTIVITY CONTROL
    @test_step
    def test_activity_control_tile(self) -> list[str]:
        """
        Tests Activity control tile of commcell page

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """
        api_ui_labels_map = {
            "ALL ACTIVITY": 'All_Job_Activity',
            "DATA MANAGEMENT": 'Data_Backup',
            "DATA RECOVERY": 'Data_Restore',
            "DATA AGING": 'Data_Aging',
            "AUX COPY": 'Auxiliary_Copy',
            "DATA VERIFICATION": 'Data_Verification',
            "SCHEDULER": 'Scheduler',
        }
        api_ui_labels_map = {key: self.admin_console.props[value] for key, value in api_ui_labels_map.items()}

        def disable_without_delay(activity_type):
            self.commcell_obj.activity_control.set(activity_type, 'Enable')  # enable first to remove delays
            self.commcell_obj.activity_control.set(activity_type, 'Disable')

        def get_activity_control_api() -> dict:
            self.commcell_obj.activity_control._get_activity_control_status()
            api_data = {}
            for ac_prop in api_ui_labels_map:
                api_data[ac_prop] = not self.commcell_obj.activity_control.is_enabled(ac_prop)
                if self.commcell_obj.activity_control.reEnableTime:
                    api_data[ac_prop] = self.commcell_obj.activity_control.reEnableTime
            return api_data

        def validate_ui_api_match(ui_data, api_data) -> list[str]:
            errors = []
            for api_key, api_value in api_data.items():
                ui_key = api_ui_labels_map[api_key]
                ui_value = ui_data[ui_key]
                if isinstance(api_value, bool):
                    if api_value != ui_value:
                        errors.append(f"UI shows {ui_key} = {ui_value} But API returns {api_key} = {api_value}")
                else:
                    try:
                        ui_timestamp = parse(ui_value).timestamp()
                    except:
                        errors.append(f'UI shows {ui_key} = {ui_value} which failed to parse')
                        continue
                    if ui_timestamp != api_value:
                        errors.append(
                            f"UI shows {ui_key} = {ui_value} -> {ui_timestamp} But API returns {api_key} = {api_value}")
            return errors

        # getting initial setting and setting up cleanup functions to restore this later
        initial_ac_config = get_activity_control_api()

        # UI Validation 1
        initial_ui_data = self.commcell_page.get_activity_control_details()
        if errors := validate_ui_api_match(initial_ui_data, initial_ac_config):
            self.log.error("Errors during initial validation")
            return errors

        # setting clean up code before making changes
        for ac_label, value in initial_ac_config.items():
            if isinstance(value, bool):
                if value:
                    self.cleanup_functions[f'restore {ac_label} True'] = functools.partial(
                        self.commcell_obj.activity_control.set, ac_label, 'Enable'
                    )
                else:
                    self.cleanup_functions[f'restore {ac_label} False'] = functools.partial(
                        disable_without_delay, ac_label
                    )
            else:
                self.cleanup_functions[f'restore {ac_label} delay {value}'] = functools.partial(
                    self.commcell_obj.activity_control.enable_after_delay,
                    ac_label,
                    value
                )

        # Randomly change toggles
        toggle_options = {True, False, '1 hour', '4 hours', '8 hours', '12 hours', '1 day'}
        random_settings = {
            ui_key: random.choice(list(toggle_options - {ui_value})) for ui_key, ui_value in initial_ui_data.items()
        }
        self.commcell_page.set_activity_setting(random_settings)

        # validate if UI gets updated after the changes made
        updated_ui_data = self.commcell_page.get_activity_control_details()
        update_errors = []
        for ui_key, ui_value in updated_ui_data.items():
            expected_ui_value = random_settings[ui_key]
            if isinstance(expected_ui_value, bool):
                if expected_ui_value != ui_value:
                    update_errors.append(
                        f"{ui_key} Was changed, so expected {expected_ui_value} but its showing {ui_value}")
            else:
                got_seconds_delay = parse(ui_value).timestamp() - time.time()  # this diff will be bigger
                # because we are comparing with now timestamp rather than when toggle was clicked (few min earlier)
                expected_seconds_delay = parse_duration(expected_ui_value)
                delay_error = got_seconds_delay - expected_seconds_delay  # ideally close to 0, but UI takes some time
                if delay_error > 60 * 5:  # allow 5 mins to account for the time since first toggle was clicked
                    update_errors.append(f"key {ui_key} was enabled with delay {expected_ui_value}, so..")
                    update_errors.append(f".expected difference:{expected_seconds_delay}, but got:{got_seconds_delay}")
                    update_errors.append(f"difference is {delay_error}! above 5 mins! UI couldnt take that long!?")
        if update_errors:
            return update_errors

        # validate UI match API
        if errors := validate_ui_api_match(updated_ui_data, get_activity_control_api()):
            self.log.error("Errors during validation after changing toggles")
            return errors
        self.log.info("ACTIVITY CONTROL TILE VALIDATED SUCCESSFULLY!")

    # PRIVACY TILE TEST
    @test_step
    def test_privacy_tile(self) -> list[str]:
        """
        Tests the privacy tile in commcell page

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """
        errors = []
        self.commcell_obj.get_commcell_properties()
        initial_privacy = self.commcell_obj.is_privacy_enabled
        if ((ui_data := self.commcell_page.get_privacy_details()) !=
                (expected_data := {
                    self.admin_console.props['label.adminPrivacyPolicy']: initial_privacy
                })):
            errors.append(f"UI API not matching for passkey tile. UI says: {ui_data} but expected: {expected_data}")
            self.log.error("Initial validation failed for privacy tile")
            return errors
        # CHANGING TOGGLE STATUS
        if initial_privacy:
            self.cleanup_functions['restore_privacy'] = self.commcell_obj.enable_privacy
            self.commcell_page.disable_data_privacy()
        else:
            self.cleanup_functions['restore_privacy'] = self.commcell_obj.disable_privacy
            self.commcell_page.enable_data_privacy()

        updated_ui = self.commcell_page.get_privacy_details()[self.admin_console.props['label.adminPrivacyPolicy']]
        if updated_ui == initial_privacy:
            errors.append(f"UI not changing after the privacy toggle clicked. "
                          f"expected: {not initial_privacy} but UI says: {updated_ui}")
            return errors
        self.commcell_obj.get_commcell_properties()
        if updated_ui != self.commcell_obj.is_privacy_enabled:
            errors.append(f"API not returning what UI is showing. (enable privacy toggle)"
                          f"in UI: {updated_ui} but API says: {self.commcell_obj.is_privacy_enabled}")
            return errors
        # RESTORING ORIGINAL TOGGLE STATUS
        if initial_privacy:
            self.commcell_page.enable_data_privacy()
        else:
            self.commcell_page.disable_data_privacy()

        updated_ui = self.commcell_page.get_privacy_details()[self.admin_console.props['label.adminPrivacyPolicy']]
        if updated_ui != initial_privacy:
            errors.append(f"UI not changing after the privacy toggle clicked. "
                          f"expected: {initial_privacy} but UI says: {updated_ui}")
            return errors
        self.commcell_obj.get_commcell_properties()
        if updated_ui != self.commcell_obj.is_privacy_enabled:
            errors.append(f"API not returning what UI is showing. (enable privacy toggle)"
                          f"in UI: {updated_ui} but API says: {self.commcell_obj.is_privacy_enabled}")
            return errors

        self.log.info("PRIVACY TILE VALIDATED SUCCESSFULLY!")
        del self.cleanup_functions['restore_privacy']

    # SLA TILE TEST
    @test_step
    def test_sla_tile(self) -> list[str]:
        """
        Tests the SLA tile in commcell page

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """
        ui_sla = self.commcell_page.get_sla_details()[self.admin_console.props['label.slaPeriod']]
        api_sla = self.commcell_obj.get_sla_configuration()['slaDays']
        if (ui_sla_proc := parse_duration(ui_sla)) != (api_sla_proc := int(api_sla) * 24 * 60 * 60):
            return [f"SLA of UI ({ui_sla} -> {ui_sla_proc}) does not match API ({api_sla} -> {api_sla_proc})"]
        self.log.info("SLA Tile VALIDATED SUCCESSFULLY!")
        # TODO: Add edit tests

    # ENCRYPTION TILE TEST
    @test_step
    def test_encryption_tile(self) -> list[str]:
        """
        Tests the Encryption tile in commcell page

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """
        ui_enc = self.commcell_page.get_password_encryption_details()[self.admin_console.props['label.kms']]
        api_enc = self.commcell_obj.get_password_encryption_config()["keyProviderName"]
        if ui_enc != api_enc:
            return [f"Encryption of UI ({ui_enc}) does not match API ({api_enc})"]
        self.log.info("PASSWORD ENCRYPTION TILE VALIDATED SUCCESSFULLY!")
        # TODO: Add edit tests

    # PASSKEY TILE TEST
    @test_step
    def test_passkey_tile(self) -> list[str]:
        """
        Tests the passkey tile in commcell page

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """

        def get_passkey_api():
            organization_properties = self.commcell_obj.get_commcell_organization_properties()
            commcell_properties = self.commcell_obj.get_commcell_properties()
            passkey_details = {
                self.admin_console.props['label.allowUsersToEnablePasskey']:
                    commcell_properties["allowUsersToEnablePasskey"],
                self.admin_console.props['label.passkeyText']: False
            }
            if organization_properties['advancedPrivacySettings']['authType'] == 2:
                passkey_details.update({
                    self.admin_console.props['label.passkeyText']: True,
                    self.admin_console.props['label.authorizeForRestore']:
                        organization_properties['advancedPrivacySettings']['passkeySettings'][
                            'enableAuthorizeForRestore']
                })
            return passkey_details

        def validate_api_ui_match():
            api_data = get_passkey_api()
            ui_data = self.commcell_page.get_passkey_details()
            if api_data != ui_data:
                return f"Validation Failed for Passkey Tile, UI: {ui_data} | API: {api_data}"

        initial_config = get_passkey_api()
        if error := validate_api_ui_match():
            return [error]

        allow_user_initial = initial_config[self.admin_console.props['label.allowUsersToEnablePasskey']]
        enable_passkey_initial = initial_config[self.admin_console.props['label.passkeyText']]
        authorize_initial = initial_config.get(self.admin_console.props['label.authorizeForRestore'], False)

        # modifying passkey settings
        self.cleanup_functions[
            'restore_allow_users_passkey'
        ] = functools.partial(self.commcell_obj.allow_users_to_enable_passkey, allow_user_initial)
        if allow_user_initial:
            self.commcell_page.disable_users_can_enable_passkey()
        else:
            self.commcell_page.enable_users_can_enable_passkey()
        # check with UI
        if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.allowUsersToEnablePasskey']] !=
                (not allow_user_initial)):
            return [
                f'allow users to enable passkey setting is not updating after toggling to {not allow_user_initial}!']
        # check with API
        if error := validate_api_ui_match():
            return [error]
        # restore Toggle
        if allow_user_initial:
            self.commcell_page.enable_users_can_enable_passkey()
        else:
            self.commcell_page.disable_users_can_enable_passkey()
        # check with UI
        if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.allowUsersToEnablePasskey']] !=
                allow_user_initial):
            return [f'allow users to enable passkey setting is not updating after toggling to {allow_user_initial}!']
        # check with API
        if error := validate_api_ui_match():
            return [error]
        # clean up not needed if code passed till now
        del self.cleanup_functions['restore_allow_users_passkey']

        passkey = 'Builder!12' if not enable_passkey_initial else self.get_passkey_from_db()
        clean_up_func_passkey = functools.partial(
            self.commcell_obj.set_passkey,
            passkey, 'disable' if not enable_passkey_initial else 'enable'
        )

        if not enable_passkey_initial:
            # Test setting up a passkey
            self.cleanup_functions['restore_enable_passkey'] = clean_up_func_passkey
            self.commcell_page.enable_passkey_for_restore(passkey)
            # check with UI
            if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.passkeyText']] ==
                    enable_passkey_initial):
                return [f'enable passkey setting is not updating after toggling to {not enable_passkey_initial}!']

            # check with API
            if error := validate_api_ui_match():
                return [error]
        else:
            # if authorize was already configged, save it for clean up, or else no need cleanup as passkey will be offed
            self.cleanup_functions['restore_authorize_passkey'] = functools.partial(
                self.commcell_obj.set_passkey,
                passkey, 'authorize' if authorize_initial else 'unauthorize'
            )

        # Test toggling the authorize option
        if authorize_initial:
            self.commcell_page.disable_authorize_for_restore()
        else:
            self.commcell_page.enable_authorize_for_restore(passkey)
        # Check with UI , then Check with API
        if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.authorizeForRestore']] ==
                authorize_initial):
            return [f'authorize passkey is not updating after toggling to {not authorize_initial}!']
        if error := validate_api_ui_match():
            return [error]
        # Toggle back
        if authorize_initial:
            self.commcell_page.enable_authorize_for_restore(passkey)
        else:
            self.commcell_page.disable_authorize_for_restore()
        # Check with UI , then Check with API
        if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.authorizeForRestore']] !=
                authorize_initial):
            return [f'authorize passkey is not updating after toggling to {authorize_initial}!']
        if error := validate_api_ui_match():
            return [error]

        if enable_passkey_initial:
            # clean up not needed if authorize is restored now
            del self.cleanup_functions['restore_authorize_passkey']
            # also test offing the passkey now since it was not tested earlier
            self.cleanup_functions['restore_enable_passkey'] = clean_up_func_passkey
            self.commcell_page.disable_passkey_for_restore(passkey)
            # Check with UI , then Check with API
            if self.commcell_page.get_passkey_details()[self.admin_console.props['label.passkeyText']]:
                return [f'enable passkey is not updating after toggling OFF!']
            if error := validate_api_ui_match():
                return [error]

        # Now we restore the enable passkey to initial setting
        if enable_passkey_initial:
            self.commcell_page.enable_passkey_for_restore(passkey)
        else:
            self.commcell_page.disable_passkey_for_restore(passkey)
        # Check with UI , then Check with API
        if (self.commcell_page.get_passkey_details()[self.admin_console.props['label.passkeyText']] !=
                enable_passkey_initial):
            return [f'enable passkey is not updating after toggling back to {enable_passkey_initial}!']
        if error := validate_api_ui_match():
            return [error]
        # Clean up not needed if COde is executed till here
        del self.cleanup_functions['restore_enable_passkey']
        self.log.info("SUCCESSFULLY VALIDATED PASSKEY TILE!")

    # SECURITY TEST
    @test_step
    def test_security_tile(self) -> list[str]:
        """
        Tests the security tile

        Returns:
            errors  (list)  -   list of errors if any
        """
        def get_random_msp_role():
            """
            Util to fetch a random msp level role
            """
            roles_available = sorted(self.commcell_obj.roles.all_roles)
            while roles_available:
                try:
                    random_msp_role = random.choice(roles_available)
                    roles_available.remove(random_msp_role)
                    if self.commcell_obj.roles.get(random_msp_role).company_name.lower() == 'commcell':
                        return self.commcell_obj.roles.get(random_msp_role)
                except:
                    pass

        # to check if api format -> 'Create Role' is present in
        # ui format -> ['[Custom] - Array Management', 'Master', '[Custom] - Create Role, Edit Role, Delete Role']
        role_present = lambda api_subrole, ui_roles: any(
            api_subrole.lower() in role.lower() for role in ui_roles
        )
        # to check the same but for list of such api_role -> ['Create Role', 'Edit Role', 'Delete Role']
        roles_match = lambda api_role, ui_roles: all(role_present(subrole, ui_roles) for subrole in api_role)

        # now for api full format -> [['Array Management'], ['Create Role', 'Edit Role', 'Delete Role'], ['Master']]
        rolesets_match = lambda api_roles, ui_roles: all(roles_match(api_role, ui_roles) for api_role in api_roles)

        def validate_tile_ui():
            api_data = self.commcell_obj.get_security_associations()
            ui_tile_data = self.commcell_page.get_security_details()
            ui_dialog_data = self.commcell_page.get_security_dialog_associations()
            if (ui_dialog_data | ui_tile_data) != ui_dialog_data:
                incorrect_data = {user: role for user, role in ui_tile_data.items()
                                  if role != ui_dialog_data.get(user)}
                return [
                    'security tile data does not match security dialog data!',
                    f'wrong data from tile ->: {incorrect_data}'
                ]
            errors = []
            for api_user, api_role_sets in api_data.items():
                if api_user not in ui_dialog_data:
                    errors.append(f"User {api_user} missing from security dialog")
                ui_role_sets = ui_dialog_data[api_user]
                if not rolesets_match(api_role_sets, ui_role_sets):
                    errors.append(f"User {api_user} roles dont match. API={api_role_sets} | UI={ui_role_sets}")
            return errors

        initial_state = self.commcell_obj.get_security_associations()
        if errors := validate_tile_ui():
            return errors
        self.log.info("initial security tile validation successfull")
        if len(initial_state) == 0:
            return ["Unable to Test Security Tile, pls have some user role assoc present already!"]

        random_user_or_group = random.choice(sorted(initial_state))
        # below steps are to make the role name in proper title case as displayed in UI
        random_role = get_random_msp_role()
        random_role.refresh()
        random_role = random_role.role_name

        self.log.info(f"Testing Security Tile using user:{random_user_or_group}, role:{random_role}")

        # TESTING CREATION
        self.log.info("adding the user and role")

        self.cleanup_functions[
            'restore_security_assoc'
        ] = functools.partial(
            SecurityAssociation(self.commcell_obj)._add_security_association,
            [{"user_name": random_user_or_group, "role_name": random_role}],
            user=(not self.commcell_obj.user_groups.has_user_group(random_user_or_group)),
            request_type='DELETE'
        )

        self.commcell_page.add_security_associations({random_user_or_group: [random_role]})
        api_assoc = self.commcell_obj.get_security_associations()
        if [random_role] not in api_assoc.get(random_user_or_group, []):
            return [
                f'{random_user_or_group},{random_role} is not returned by API for commcell assoc!',
                'maybe call did not go from UI, or maybe API returned error, either way association failed to ADD!!'
            ]
        if errors := validate_tile_ui():
            return errors
        self.log.info("Add association successfull! proceeding to deletion!")

        # TESTING DELETION
        self.commcell_page.delete_security_associations({random_user_or_group: [random_role]})
        api_assoc = self.commcell_obj.get_security_associations()
        if [random_role] in api_assoc.get(random_user_or_group, []):
            return [
                f'{random_user_or_group},{random_role} is still returned by API for commcell assoc!',
                'maybe delete call did not go from UI, or maybe API returned error, either way association failed to DELETE!!'
            ]
        if errors := validate_tile_ui():
            return errors
        self.log.info("Delete association successfull!")
        del self.cleanup_functions['restore_security_assoc']

    # EMAIL TEST
    @test_step
    def test_email_tile(self) -> list[str]:
        """
        Tests the email settings tile

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """

        def get_email_api_data():
            email_settings = self.commcell_obj.get_email_settings()
            enc = 'None'
            if email_settings.get('startTLS'):
                enc = 'TLS'
            if email_settings.get('enableSSL'):
                enc = 'SSL'

            return {
                self.admin_console.props['label.smtpServer']: email_settings.get('smtpServer'),
                self.admin_console.props['label.smtpPort']: str(email_settings.get('smtpPort')),
                self.admin_console.props['label.senderEmail']: email_settings.get('senderInfo', {}).get(
                    'senderAddress'),
                self.admin_console.props['label.senderName']: email_settings.get('senderInfo', {}).get('senderName'),
                self.admin_console.props['label.encryptionAlgorithm']: enc,
                self.admin_console.props['label.useAuthentication']:
                    email_settings.get('useModernAuth', False) or email_settings.get('useAuthentication', False)
            }

        def validate_email_tile(expected):
            ui_data = self.commcell_page.get_email_details()
            if (expected | ui_data) != expected:
                incorrect_data = {datakey: datavalue for datakey, datavalue in ui_data.items()
                                  if datavalue != expected.get(datakey)}
                return [
                    f'Email tile does not match expected = {expected}!',
                    f'wrong data from tile ->: {incorrect_data}'
                ]

        initial_state = get_email_api_data()
        if errors := validate_email_tile(initial_state):
            return errors
        if initial_state[self.admin_console.props['label.useAuthentication']]:
            self.log.info("Successfully validated Email Tile")
            self.log.info("Avoiding email tile editing because authentication is present")
            return []

        self.cleanup_functions['restore_email'] = functools.partial(
            self.commcell_obj.set_email_settings,
            smtp_server=initial_state[self.admin_console.props['label.smtpServer']],
            sender_name=initial_state[self.admin_console.props['label.senderName']],
            sender_email=initial_state[self.admin_console.props['label.senderEmail']],
            smtp_port=int(initial_state[self.admin_console.props['label.smtpPort']]),
            enable_ssl=initial_state[self.admin_console.props['label.encryptionAlgorithm']] == 'SSL',
            start_tls=initial_state[self.admin_console.props['label.encryptionAlgorithm']] == 'TLS'
        )
        self.log.info("Editing all fields and validating")
        other_alg = ['None', 'TLS', 'SSL']
        other_alg.remove(initial_state[self.admin_console.props['label.encryptionAlgorithm']])
        email_to_set = {
            'SMTP server': 'editedserver.randomaddr.com',
            'SMTP port': '5555',
            'Sender email': 'editedmeail@randomaddr.com',
            'Sender name': 'editedmailname',
            'Encryption algorithm': random.choice(other_alg),
        }
        self.commcell_page.edit_email_settings(email_to_set)
        if errors := validate_email_tile(email_to_set):
            return ['failed validation against edited settings'] + errors
        if errors := validate_email_tile(get_email_api_data()):
            return ['failed validation against API'] + errors
        self.log.info("Successfully validated Email Tile")

    # GENERAL TEST
    @test_step
    def test_general_tile(self) -> list[str]:
        """
        Tests the general settings tile

        Returns:
            errors  (list)  -   list of messages indicating test failures
        """

        def load_api_data() -> tuple[dict, dict, dict]:
            commcell_properties = self.commcell_obj.get_commcell_properties()
            commcell_org_properties = self.commcell_obj.get_commcell_organization_properties()
            workload_region = self.commcell_obj.get_workload_region()
            account_lock = all(val == -1 for val in commcell_properties.get("accountLockSettingsInfo", {}).values())
            logon_data = commcell_properties.get("accountLockSettingsInfo", {})
            tfa_data = commcell_properties.get('twoFactorAuthenticationInfo', {})
            tfa_groups = [ug.get("userGroupName") for ug in tfa_data.get("userGroups", [])]

            tfa_dialog_data = {}
            logon_dialog_data = {}
            general_tile_data = {
                self.admin_console.props['label.enableAuthCode']: commcell_org_properties.get(
                    "enableAuthCodeGen", False
                ),
                "authcode": commcell_org_properties.get("authCode", False),
                self.admin_console.props['label.twoFactorAuthentication']: commcell_properties.get(
                    "enableTwoFactorAuthentication", False
                ),
                self.admin_console.props['label.lockSettings']: not account_lock,
                self.admin_console.props['label.timezone']: self.commcell_obj.commserv_timezone,
                self.admin_console.props['label.workloadRegion']: workload_region or 'Not set'
            }
            if commcell_properties.get("enableTwoFactorAuthentication", False):
                tfa_dialog_data = {
                    'User groups': 'all' if tfa_data.get('mode') == 1 else tfa_groups,
                    'passwordless': tfa_data.get('webAuthn', {}).get('allowPasswordlessLogin', False),
                    'usernameless': tfa_data.get('webAuthn', {}).get('allowUsernamelessLogin', False)
                }
            if not account_lock:
                logon_dialog_data = {
                    'attemptLimit': logon_data.get('failedLoginAttemptLimit'),
                    'attemptWithin': logon_data.get('failedLoginAttemptsWithin') / 60,
                    'lockDuration': logon_data.get('accountLockDuration') / 60,
                    'durationIncrement': logon_data.get('accountLockDurationIncrements') / 60,
                }
            return general_tile_data, tfa_dialog_data, logon_dialog_data

        def validate_ui_api_tile(rendered_ui_tile=None) -> list[str]:
            api_tile = load_api_data()[0]
            if not rendered_ui_tile:
                rendered_ui_tile = self.commcell_page.get_general_details()
            if rendered_ui_tile != api_tile:
                return ['General tile UI shows different from API', f'API = {api_tile}', f'UI = {rendered_ui_tile}']
            return []

        initial_tile, initial_tfa, initial_logon = load_api_data()
        initial_authcode_enabled = initial_tile[self.admin_console.props['label.enableAuthCode']]
        initial_workload_region_set = self.commcell_obj.get_workload_region()
        if errors := validate_ui_api_tile():
            return ['failed initial tile validation'] + errors

        # SETUP THE CLEANUPS AND TESTS
        ultimate_errors = []

        # # AUTHCODE TEST
        if initial_authcode_enabled:
            self.cleanup_functions['restore_authcode_toggle'] = functools.partial(self.commcell_obj.enable_auth_code)
            # # # disabling authcode test
            self.commcell_page.disable_authcode_for_installation()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.enableAuthCode']]:
                ultimate_errors.append('authcode toggle OFF not updated in UI, it says True')
            if ui_tile['authcode']:
                ultimate_errors.append(
                    f'authcode itself still visible -> {ui_tile['authcode']}, even after toggling OFF')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after authcode OFFED'] + ultimate_errors
        else:
            self.cleanup_functions['restore_authcode_toggle'] = functools.partial(self.commcell_obj.disable_auth_code)

        # # # authcode ON test
        self.commcell_page.enable_authcode_for_installation()
        ui_tile = self.commcell_page.get_general_details()
        if not ui_tile[self.admin_console.props['label.enableAuthCode']]:
            ultimate_errors.append('authcode toggle on not updated in UI, it says False')
        if not ui_tile['authcode']:
            ultimate_errors.append('authcode itself is missing, even after toggling ON')
        ultimate_errors += validate_ui_api_tile(ui_tile)
        if ultimate_errors:
            return ['failed after authcode ON'] + ultimate_errors

        if initial_authcode_enabled:
            del self.cleanup_functions['restore_authcode_toggle']  # clean up not needed if was ON initially

        # # # refreshing authcode test
        new_authcode = self.commcell_page.generate_new_authcode()
        if new_authcode == ui_tile['authcode']:
            ultimate_errors.append('Same authcode is returned after authcode refresh, maybe UI is not updated!')
        ultimate_errors += validate_ui_api_tile()
        if ultimate_errors:
            return ['failed after refresh authcode'] + ultimate_errors

        if not initial_authcode_enabled:
            # # # disabling authcode test for the case it was initially off
            self.commcell_page.disable_authcode_for_installation()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.enableAuthCode']]:
                ultimate_errors.append('authcode toggle OFF not updated in UI, it says True')
            if ui_tile['authcode']:
                ultimate_errors.append(
                    f'authcode itself still visible -> {ui_tile['authcode']}, even after toggling OFF')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after authcode ON'] + ultimate_errors
            del self.cleanup_functions['restore_authcode_toggle']  # cleanup not needed as already offed via UI

        # # WORKLOAD REGION TEST
        self.cleanup_functions['restore_workload_region'] = functools.partial(
            self.commcell_obj.set_workload_region, initial_workload_region_set
        )
        # # # set some random workload and just validate tile
        random_region = random.choice(sorted(self.commcell_obj.regions.all_regions))
        self.commcell_page.set_workload_region(random_region)
        ui_tile = self.commcell_page.get_general_details()
        if (ui_region := ui_tile[self.admin_console.props['label.workloadRegion']]) != random_region:
            ultimate_errors.append(f'New region set {random_region} but UI shows {ui_region}')
        ultimate_errors += validate_ui_api_tile(ui_tile)
        if ultimate_errors:
            return ['failed after workload region set'] + ultimate_errors

        # # USER LOGON TEST
        if initial_logon:
            self.cleanup_functions['restore_userlogon'] = functools.partial(
                self.commcell_obj.enable_limit_user_logon_attempts,
                initial_logon['attemptLimit'],
                initial_logon['attemptWithin'] * 60,
                initial_logon['lockDuration'] * 60,
                initial_logon['durationIncrement'] * 60
            )
            # # # off userlogon test
            self.commcell_page.disable_userlogon_limit()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.lockSettings']]:
                ultimate_errors.append('Limit userlogon toggle OFF not updated in UI, it says True')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after off user logon'] + ultimate_errors

        else:
            self.cleanup_functions['restore_userlogon'] = functools.partial(
                self.commcell_obj.disable_limit_user_logon_attempts
            )

        # # # set userlogon test
        if initial_logon:
            settings = deepcopy(initial_logon)
        else:
            settings = {
                'attemptLimit': random.randint(3, 9),
                'attemptWithin': random.randint(20, 40),
                'lockDuration': random.randint(40, 60),
                'durationIncrement': random.randint(2, 5)
            }
        self.commcell_page.enable_userlogon_limit(settings)

        # # # # tile toggle should update
        ui_tile = self.commcell_page.get_general_details()
        if not ui_tile[self.admin_console.props['label.lockSettings']]:
            ultimate_errors.append('Limit userlogon toggle ON not updated in UI, it says False')
        ultimate_errors += validate_ui_api_tile(ui_tile)
        if ultimate_errors:
            return ['failed after ON user logon'] + ultimate_errors

        # # # # dialog data should also match
        ui_dialog = self.commcell_page.get_userlogon_settings()
        api_dialog = load_api_data()[2]
        if not settings == ui_dialog == api_dialog:
            return ['Error in userlogon settings dialog data', f'UI={ui_dialog}',
                    f'API={api_dialog}', f'expected={settings}']

        if initial_logon:
            del self.cleanup_functions['restore_userlogon']  # cleanup not needed as we restored how it was
        else:
            # # # off userlogon test for case when initially was off
            self.commcell_page.disable_userlogon_limit()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.lockSettings']]:
                ultimate_errors.append('Limit userlogon toggle OFF not updated in UI, it says True')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after userlgon toggle OFFED'] + ultimate_errors
            del self.cleanup_functions['restore_userlogon']

        # # TFA TEST!
        if initial_tfa:
            if (target := initial_tfa.get('User groups')) == 'all':
                initial_tfa_group = None
            else:
                initial_tfa_group = [grp.lstrip('Commcell\\') for grp in target]

            self.cleanup_functions['restore_tfa'] = functools.partial(
                self.commcell_obj.enable_tfa,
                user_groups=initial_tfa_group,
                usernameless=initial_tfa.get('usernameless'),
                passwordless=initial_tfa.get('passwordless')
            )
            # # # disable tfa test
            self.commcell_page.disable_tfa()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.twoFactorAuthentication']]:
                ultimate_errors.append('TFA toggle OFF not updated in UI, it says True')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after TFA toggled off'] + ultimate_errors

            # prepare for enable tfa test
            tfa_settings = initial_tfa.copy()
            tfa_settings['User groups'] = initial_tfa_group or 'all'
        else:
            self.cleanup_functions['restore_tfa'] = functools.partial(self.commcell_obj.disable_tfa)
            if not self.commcell_obj.user_groups.has_user_group('dummy_tfa_usergrp'):
                self.commcell_obj.user_groups.add('dummy_tfa_usergrp')
            tfa_settings = {
                'User groups': ['dummy_tfa_usergrp'],
                'usernameless': random.choice([True, False]),
                'passwordless': random.choice([True, False])
            }

        # # # enable tfa test
        self.commcell_page.enable_tfa(tfa_settings)

        if initial_tfa:
            tfa_settings = initial_tfa.copy()
        else:
            tfa_settings['User groups'] = ['Commcell\\dummy_tfa_usergrp']

        # # # # tile toggle should update
        ui_tile = self.commcell_page.get_general_details()
        if not ui_tile[self.admin_console.props['label.twoFactorAuthentication']]:
            ultimate_errors.append('TFA toggle ON not updated in UI, it says False')
        ultimate_errors += validate_ui_api_tile(ui_tile)
        if ultimate_errors:
            return ['failed after ON tfa toggle'] + ultimate_errors

        # # # # dialog data should also match
        ui_dialog = self.commcell_page.get_tfa_details()
        api_dialog = load_api_data()[1]
        if not tfa_settings == ui_dialog == api_dialog:
            return ['Error in tfa settings dialog data', f'UI={ui_dialog}',
                    f'API={api_dialog}', f'expected={tfa_settings}']

        if initial_tfa:
            del self.cleanup_functions['restore_tfa']
        else:
            # # # disable tfa test for initially off case
            self.commcell_page.disable_tfa()
            ui_tile = self.commcell_page.get_general_details()
            if ui_tile[self.admin_console.props['label.twoFactorAuthentication']]:
                ultimate_errors.append('TFA toggle OFF not updated in UI, it says True')
            ultimate_errors += validate_ui_api_tile(ui_tile)
            if ultimate_errors:
                return ['failed after TFA toggled off'] + ultimate_errors
            del self.cleanup_functions['restore_tfa']

    # TODO: Tile tests to add -> Universal Command Centers, Default plans, Settings, Restricted consoles
