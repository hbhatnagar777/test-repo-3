# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing alert related operations for creation, mail parsing, cleanup of alerts.

AlertHelper and AlertSituations are 2 classes defined in this file

AlertHelper : Class containing utilities for various Alert Generation, Parsing Capabilities
AlertSituations : Class containing functions to trigger various alert situations

AlertHelper :
    __init__() : Initializes the logger object

    initialize_mailbox() : Initializes the mailbox object that will be used for parsing the mail and
    checking for alert notification

    get_alert_details() : Returns the alert dictionary format required by get_alert_json() in Alerts class

    create_alert() : Creates the alert from the given alert data

    check_if_alert_mail_received() : Parses through the mail to check if the Alert notification mail has been received

    check_if_rss_feed_received() : Reads through RSS Folder to check if alert notification was received

    check_if_html_body_contains() : Checks if the html body contains the given patterns

    check_if_console_alert_contains() : Checks if a console alert contains the given patterns

    check_if_alert_saved() : Check if save to disk alert notification was saved

    check_if_event_logged() : Reads through windows event viewer logs to check if alert notification was received

    check_if_snmp_trap_received() : Reads through SentAlerts.log to see if SNMP Trap notification was sent

    check_if_scom_alert_received() : Reads through GalaxySCOM.csv to see if SCOM alert notification was received

    get_sender() : Yields the name of the Alert notification sender

    get_notif_html() : Gets the notification HTML body required in the Alert XML

    get_token_id() : Fetches the token ID for given token rule group

    get_token_type_format() : Fetches the token type and token format for given token ID

    get_ida_app_id() : Fetches the application id for an IDA for a given client

    populate_token_rules_xml() : Populates the token rule part of Alert XML body

    populate_entities_xml() : Populates the Associations part of Alert XML body

    populate_criterias_xml() : Populates the Criterias part of Alert XML body

    populate_notification_xml() : Populates the Notification part of Alert XML body

    get_alert_xml() : Gets the alert XML body required for creating an Alert through QCommand Execute

    create_alert_from_xml() : Creates an Alert using QCommand Execute

    create_criteria_mapping() : Create a list of Criteria Name mappings from a list of criteria IDs

    read_alert_rule() : Reads Alert Rule xml from a default folder in /Automation Directory

    import_alert_rule() : Takes the Alert Rule xml and Imports it into the commcell

    delete_alert_rule() : Deletes a custom alert rule

    set_custom_alert_frequency() : Modifies custom alert Xml to change the Query frequency

    get_custom_query_name() : Gets the query name from a custom alert rule xml

    delete_alert() : Deletes the alert created using Alert Helper

    cleanup() : Performs cleanup for all the objects defined in this class

AlertSituations:
    __init__() : Initializes the logger object

    backup_job() : Runs a backup job on a given subclient

    backup_generated_data() : Generates test data and runs a backup job on generated data

    low_disk_space_settings() : Adds additional settings to trigger low disk space situation

    cleanup_low_disk_space_settings() : Cleans up additional settings added for low disk space situation

    auxiliary_copy_job() : Runs an auxiliary copy job

    no_backup_in_n_days() : Creates the situation for the criteria no backup in last n days

    cleanup_no_backup_in_n_days() : Performs cleanup operations for the situation no backup in last n days

    toggle_commcell_activity() : Enables/Disables All Activity on the commcell

    suspend_in_scan_phase() : Runs a Backup job and suspends it during Scan Phase using JM Service Stop

    admin_job_runtime_threshold() : Runs a Data aging job and suspends it during Running status using JM Service Stop

    restore_runtime_threshold() : Runs a Restore job and suspends it during Running status using JM Service Stop

    put_job_in_queued_state() : Creates a Blackout window and runs a backup job to trigger queued state condition

    create_entities() : Used for creating Entities required by testcases using CVEntities

    cleanup_entities() : Used for cleaning up up created Entities using cleanup map
"""
import time
import html
import uuid
import re
import string
import os
from datetime import datetime, timedelta
from pytz import timezone
from cvpysdk.exception import SDKException
from cvpysdk.policies.storage_policies import StoragePolicy
from AutomationUtils.machine import Machine
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.mail_box import MailBox, EmailSearchFilter
from AutomationUtils import logger, constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.options_selector import CVEntities
from Server.OperationWindow.ophelper import OpHelper


class AlertHelper:
    """
    Class for Alert Creation and other operations
    """
    def __init__(self, commcell_object, category=None, alert_type=None, alert_obj=None):
        """Initialize object of the AlertHelper class.

            Args:
                commcell_object (object)  --  instance of the Commcell class
                category (string) - Category of the alert to be created
                alert_type (string) - Type of the alert to be created
                alert_obj(obj) - existing alert's object for using existing alert.

            Returns:
                object - instance of the AlertHelper class
        """
        self.log = logger.get_log()
        self.alerts_commcell = commcell_object.alerts
        self.commcell_object = commcell_object
        if alert_obj:
            self.alert_category = alert_obj.alert_category
            self.alert_type = alert_obj.alert_type
            self.alert_name = alert_obj.alert_name
        elif category is not None and alert_type is not None:
            if category in constants.ALERT_CATEGORY_TYPE.keys():
                if alert_type in constants.ALERT_CATEGORY_TYPE[string.capwords(category)].keys():
                    self.alert_category = category
                    self.alert_type = alert_type
                else:
                    raise SDKException('Alert', '102', f'Alert Type not found in category {category}')
            else:
                raise SDKException('Alert', '102', 'Alert Category not found')
        else:
            self.alert_type = alert_type
            self.alert_category = category
            self.alert_name = ''
        self.alert_situations = AlertSituations(commcell_object, category=category, alert_type=alert_type)
        self.mailbox = None
        self.search_filter = None
        self.options_selector = OptionsSelector(commcell_object)
        self.params_list = ['1', '2', '3', '4', '5', '7', '8', '10',
                            '11', '12', '13', '14', '16', '17', '18', '19', '20',
                            '21', '22', '26', '27', '28', '29', '30', '31', '32',
                            '38', '39', '46', '47', '51', '52', '53', '54', '55',
                            '57', '58', '60', '63', '65', '66', '67', '68', '69',
                            '70', '71', '72', '73', '74']
        self.data_type = {'int': 0, 'string': 1, 'date': 2}
        self.format_type = {'int': 0, 'string_without_separator': 21, 'DD_MM_YYYYDATE': 9}
        self.alert_details = None
        self.alert_xml = None
        self.alert_xml_dict = None

    def initialize_mailbox(self, **kwargs):
        """Initialize mailbox object.
           Initializes mailbox object with search parameters
        """
        try:
            additional_settings = dict(kwargs.items())
            self.log.info('Initializing Mailbox Object')
            self.mailbox = MailBox()
            self.mailbox.connect()
            # Custom Rules Alert Type name can be fetched from Custom Rule xml
            if 'custom_rule_name' in additional_settings:
                self.alert_type = additional_settings['custom_rule_name']

            # Creating a search filter for the given subject
            subject = 'Alert: {0} Type: {1} - {2}   '.format(self.alert_name,
                                                             self.alert_category,
                                                             self.alert_type)
            self.search_filter = EmailSearchFilter(subject=subject)
            if 'set_unread_only' in additional_settings:
                self.search_filter.set_unread_only(False)
            current = datetime.now(timezone('Asia/Kolkata'))
            self.log.info('Set mail search filter timezone to Asia/Kolkata', current)
            self.search_filter.set_mail_sent_on(current.day, current.month, current.year)
            self.search_filter.set_sender_name(self.get_sender())

        except Exception as excp:
            self.log.error(str(excp))
            raise Exception("Mailbox Initialization Failed")

    def get_alert_details(self, name, notif_type, entities, users, criteria, mail_recipent=None, params_list=None):
        """Creates dictionary of given alert details

            Args:
                name (string)  --  Name of the alert
                notif_type (list) - List of notification types to keep for the alert
                entities (dict) - Entities associated with the alert

                example dictionary :
                    entities={'clients': self.tcinputs['ClientName']}

                users (list) - Users associated with the alert
                criteria (int) - Criteria for the alert
                mail_recipent (string) - Extra mail recipents to receive the alert notification
                params_list (list) - Extra params list if required by the given criteria

            Returns:
                dictionary - Alert data required to create an alert
        """
        alert_details = {
            "alert_type": constants.ALERT_CATEGORY_TYPE[string.capwords(self.alert_category)].get(
                self.alert_type),
            "notif_type": [constants.ALERT_NOTIFICATIONS.get(string.capwords(i)) for i in notif_type],
            "notifTypeListOperationType": 0,
            "alert_severity": 0,
            "nonGalaxyUserOperationType": 0,
            "criteria": criteria,
            "associationOperationType": 0,
            "entities": entities,
            "userListOperationType": 0,
            "users": users,
            "alert_name": name
        }
        # Params list may be needed for some criteria types
        # Check if the criteria being passed requires a params List

        if params_list is not None and str(criteria) in self.params_list:
            alert_details["paramsList"] = params_list

        if mail_recipent is not None:
            alert_details["nonGalaxyList"] = {"nonGalaxyUserList": [{"nonGalaxyUser": mail_recipent}]}

        self.alert_details = alert_details
        self.alert_name = name
        return alert_details

    def create_alert(self):
        """Create an alert from given alert data.
        """
        try:
            self.alerts_commcell.create_alert(self.alert_details)
            self.log.info('Alert Creation Successful')
        except Exception as excp:
            self.log.error(str(excp))
            raise Exception('Alert Could not be created!')

    def check_if_alert_mail_received(self, short_interval, patterns):
        """Reads through mailbox to check if notification was received

            Args:
                short_interval (int)  -  Short time interval to wait for alert notification (in seconds)
                patterns (list) - List containing of patterns to search for in the mail

            Returns:
                bool - If alert mail was received or not
        """
        max_attempts = 5
        attempt = 1
        got_alert_email = False
        condition = None  # Use this variable to keep track of Switch cases
        self.log.info('Wait till Alert Notification is received')

        # Check if Unread only is set to True or False
        if self.search_filter.get_unread_only():  # Only Unread Mails
            # Check if there is a Single Criteria or Multiple Criterias to check
            if isinstance(self.alert_details['criteria'], int):  # Only one alert criteria
                self.log.info('==========================================================')
                self.log.info('Checking Mail for Single Alert Criteria with Unread = True')
                self.log.info('==========================================================')
            condition = 0
        else:  # All mails, Read and Unread
            self.log.info('===========================================================')
            self.log.info('Checking Mail for Single Alert Criteria with Unread = False')
            self.log.info('===========================================================')
            condition = 1

        while attempt <= max_attempts and not got_alert_email:
            # Get Latest Mail UID, which is the last one in the list of UIDs
            filtered = self.mailbox._get_mail_uid_list(self.search_filter, mail_folder='INBOX')
            self.log.info('Attempt [%s] Searching for mail ', attempt)

            if len(filtered) == 0:
                self.log.debug('No Alert mail was found. List contains 0 matching mails')
                attempt += 1
                time.sleep(short_interval)  # Wait for the mail to come in the inbox
            else:  # 'filtered' has some mails for us to check
                if condition is 0:
                    uid_generated = filtered[-1]  # The latest mail is the last one in the UIDs list
                elif condition is 1:
                    uid_generated = filtered  # Take the whole list, iterate through each UID and check mail body
                try:
                    if condition is 0:  # Only check the latest mail
                        got_alert_email = self.mailbox.check_if_mail_body_contains(mail_uid=uid_generated,
                                                                                   pattern_list=patterns)
                    elif condition is 1:  # Iterate through each UID in the filtered list and check if criteria matches
                        # Each iteration of going through all mail UIDS is contributing to 1 attempt only
                        for mail_uid in filtered:
                            got_alert_email = self.mailbox.check_if_mail_body_contains(mail_uid=mail_uid,
                                                                                       pattern_list=patterns)
                            if got_alert_email:  # If Mail found is match break out of the loop
                                break

                    if got_alert_email:
                        self.log.info("Received Alert notification")
                        break
                    attempt += 1
                    time.sleep(short_interval)
                except Exception as email_err:
                    self.log.error('Encountered an error while fetching alert : %s', (str(email_err)))

        # Check if Alert notification was received or not
        if got_alert_email is False:
            self.log.info("No alert mail was received")
            raise Exception("Didn't receive Alert notification")

    def check_if_rss_feed_received(self, short_interval, patterns):
        """Reads through RSS Folder to check if alert notification was received

            Args:
                short_interval (int)  -  Short time interval to wait for alert notification (in seconds)
                patterns (list) - List containing of patterns to search for in the RSS Html Body

            Returns:
                bool - If alert RSS feed was received or not
        """
        max_attempts = 5
        attempt = 1
        got_rss_feed = False
        self.log.info('Wait till Alert Notification RSS Feed is Received')
        try:
            cs_machine = Machine(machine_name=self.commcell_object.commserv_name, commcell_object=self.commcell_object)
            base_folder = self.commcell_object.commserv_client.install_directory + "\\rss\\alertDetail"
            while attempt <= max_attempts and not got_rss_feed:
                self.log.info('Attempt [%s] Searching for RSS Feed ', attempt)

                if attempt > 1:
                    time.sleep(short_interval)

                latest_folder = cs_machine.get_latest_timestamp_file_or_folder(folder_path=base_folder)
                if latest_folder is None:
                    attempt += 1
                else:
                    alert_notif_file = cs_machine.get_files_in_path(latest_folder)
                    if len(alert_notif_file) == 0:
                        attempt += 1
                    else:
                        # Two cases One file or More than One file
                        if len(alert_notif_file) == 1:
                            html_body = cs_machine.read_file(alert_notif_file[0])
                            # Check if Given patterns are present in HTML body or not
                            got_rss_feed = self.check_if_html_body_contains(html_body, patterns)

                            if got_rss_feed:
                                self.log.info('Received RSS Feed Notification')
                                break
                            attempt += 1
        except Exception as excp:
            self.log.error(f'Encountered Exception : {excp}')

        if got_rss_feed is False:
            self.log.info("No alert RSS Feed was received")
            raise Exception("Didn't receive Alert notification")

    def check_if_html_body_contains(self, body, patterns):
        """Parses through the body of the Html and checks the existence
            of the values in the html body

            Args:
                body    (str)  -  Html Body to check
                patterns (list) - List of values to be matched in the mail body

            Returns:
                bool - True if pattern matches else False

            NOTE : It is on the tester on what all values he wants to check for in the Html Body. The function
            performs a hard match
        """
        pattern_match = True
        for match_criteria in patterns:
            if not bool(re.search(match_criteria, body)):
                pattern_match = False
                break

        return pattern_match

    def check_if_console_alert_contains(self, patterns):
        """Function to check if console alert contains the given patterns"""
        # Wait for 100 seconds before starting search
        self.log.info("Wait till console alert is triggered")
        self.alerts_commcell.refresh()
        try:
            # Get feedsList property from console alerts page
            feedsList = self.alerts_commcell.console_alerts(1, 10)['feedsList']
            # Get liveFeedId for the particular console alert
            liveFeedId = list(filter(lambda alert: alert['alertName'] == self.alert_name , feedsList))[0]['liveFeedId']
            console_alert_details = self.alerts_commcell.console_alert(liveFeedId)
            # Parse the description key from console_alert_details
            pattern_match = self.check_if_html_body_contains(body=console_alert_details['description'], patterns=patterns)
        except Exception as excp:
            self.log.info(f"Encountered exception while searching for console alert : {excp}")

        if pattern_match:
            self.log.info("Console alert JSON Received, alert details validated")
        else:
            self.log.info("Console alert details not matching")

    def check_if_alert_saved(self, short_interval, patterns):
        """Reads through Alerts Folder to check if alert notification was saved. Used for save to disk
           alert notifications

            Args:
                short_interval (int)  -  Short time interval to wait for alert notification (in seconds)
                patterns (list) - List containing of patterns to search for in the Alerts Html

            Returns:
                bool - If alert notification was saved or not
        """
        max_attempts = 5
        attempt = 1
        got_saved_alert = False
        self.log.info('Wait till Alert Notification is saved')
        try:
            cs_machine = Machine(machine_name=self.commcell_object.commserv_name, commcell_object=self.commcell_object)
            while attempt <= max_attempts and not got_saved_alert:
                self.log.info('Attempt [%s] Searching for Saved Alert', attempt)
                time.sleep(short_interval)
                # Get base folder
                try:
                    base_folder = self.commcell_object.commserv_client.install_directory + "\\alerts\\" + self.alert_name
                    latest_folder = cs_machine.get_latest_timestamp_file_or_folder(folder_path=base_folder)
                    if latest_folder is None:
                        attempt += 1
                    else:
                        alert_notif_file = cs_machine.get_files_in_path(latest_folder)
                        if len(alert_notif_file) == 0:
                            attempt += 1
                        else:
                            # Two cases One file or More than One file
                            if len(alert_notif_file) >= 1:
                                html_body = cs_machine.read_file(alert_notif_file[0])
                                # Check if Given patterns are present in HTML body or not
                                got_saved_alert = self.check_if_html_body_contains(html_body, patterns)

                                if got_saved_alert:
                                    self.log.info('Received Saved Alert Notification')
                                    break
                                # HTML body doesn't contain the patterns
                                attempt += 1
                except Exception as base_folder_excp:
                    self.log.info(f'Encountered exception while getting folder : {base_folder_excp}')
                    attempt += 1
        except Exception as excp:
            self.log.error(f'Encountered Exception while connecting to machine : {excp}')

        if got_saved_alert is False:
            self.log.info("No saved alert was found")
            raise Exception("Didn't receive Alert notification")

    def check_if_event_logged(self, short_interval, patterns):
        """Reads through Windows Event Viewer logs to check if alert notification was received. Used for save to disk
           Event viewer alert notifications

            Args:
                short_interval (int)  -  Short time interval to wait for alert notification (in seconds)
                patterns (list) - List containing of patterns to search for in the Event log body

            Returns:
                bool - If alert event viewer notification was received or not
        """
        cs_machine_obj = Machine(self.commcell_object.commserv_name, commcell_object=self.commcell_object)
        max_attempts = 5
        attempt = 1
        got_saved_alert = False
        pattern_match = True
        self.log.info('Wait till Alert Notification is Received')
        while attempt <= max_attempts and not got_saved_alert:

            self.log.info('Attempt [%s] Searching for Alert notification in Event Log', attempt)

            if attempt > 1:
                time.sleep(short_interval)

            # Try getting event message
            try:
                message_body = cs_machine_obj.get_event_viewer_logs_message()
                # Parse output to check for patterns
                pattern_match = True
                for match_criteria in patterns:
                    if not bool(re.search(match_criteria, message_body)):
                        pattern_match = False
                        attempt += 1
                        break

                if pattern_match:
                    got_saved_alert = True
                    self.log.info('Received Event Viewer Alert Notification')
                    break
            except Exception as command_execute_excp:
                self.log.error(f'Encountered Exception while executing command : {command_execute_excp}')
                attempt += 1

        if got_saved_alert is False:
            self.log.info("No alert RSS Feed was received")
            raise Exception("Didn't receive Alert notification")

    def check_if_snmp_trap_received(self, wait_interval, patterns, lines_to_search=20):
        """Reads through EvMgrs log file to check if SNMP Trap was sent or not

            Args:
                wait_interval (int)  -  time interval (in seconds) to wait for before searching for alert notification
                patterns (list) - List containing of patterns to search for in the SNMP Trap
                lines_to_search (int) - Searches through the last n lines of EvMgrs log for trap notification

            Returns:
                bool - If snmp trap was sent or not

            Note : The function does a hard wait after which it opens the log file to check if trap was sent or not
        """
        cs_machine_obj = WindowsMachine(self.commcell_object.commserv_name, commcell_object=self.commcell_object)
        got_snmp_trap = True
        self.log.info('Wait till Alert SNMP Trap Notification is Sent')
        time.sleep(wait_interval)
        # Open evmgrs logfile in cs machine
        evmgrs_log = cs_machine_obj.get_log_file(log_file_name='SentAlerts.log')
        # Get last lines_to_search lines, we split on each line
        evmgrs_log = ' '.join(evmgrs_log.split('\n')[-lines_to_search:])
        for pattern in patterns:
            if not bool(re.search(pattern, evmgrs_log)):
                got_snmp_trap = False
                break

        if got_snmp_trap:
            self.log.info('Sent SNMP Trap Alert Notification')
        else:
            self.log.info('Didn\'t send SNMP Trap')
            raise SDKException("Alert", "102", "Didnt send SNMP Trap notification")

    def check_if_scom_alert_received(self, wait_interval, patterns, lines_to_search=10):
        """Reads through GalaxySCOM.csv and validates if given patterns exist in alert notification

            Args:
                wait_interval (int)  -  time interval (in seconds) to wait for before searching for scom notification
                patterns (list) - List containing of patterns to search for in GalaxySCOM.csv
                lines_to_search (int) - Searches through the last n lines of GalaxySCOM.csv for trap notification

            Returns:
                bool - If scom notification was found or not

            Note : The function does a hard wait after which it opens the GalaxySCOM.csv file to check if scom
            notification was found or not
        """
        got_scom_alert = True
        self.log.info('Wait till SCOM Alert notiifcation is received')
        try:
            cs_machine = Machine(machine_name=self.commcell_object.commserv_name, commcell_object=self.commcell_object)
            time.sleep(wait_interval)
            scom_file_path = cs_machine.join_path(self.commcell_object.commserv_client.install_directory, 'Scom',
                                                  'GalaxySCOM.csv')
            # Open scom file and read last lines_to_search lines and see if patterns are found
            scom_file_body = cs_machine.read_file(scom_file_path)
            # Fetch the last lines_to_search from this file
            scom_last_lines = ' '.join(scom_file_body.split('\n')[-lines_to_search:])
            for pattern in patterns:
                if not bool(re.search(pattern, scom_last_lines)):
                    got_scom_alert = False
                    break
        except Exception as excp:
            self.log.error(f'Encountered Exception while validating notification : {excp}')

        if got_scom_alert:
            self.log.info('SCOM Alert received, alert details validated')
        else:
            self.log.info("No saved alert was found")
            raise Exception("Didn't receive Alert notification")

    def get_sender(self):
        """Initialize object of the AlertHelper class.

            Returns:
                string - Sender name for the alert notification mail
        """
        return self.alerts_commcell.get_alert_sender()

    def get_notif_html(self, notif_type):
        """
        Fetches the notification html required to be put in the XML request for given alert type

            Args:
                notif_type (int)  --  Notification ID for which to fetch the notifMessageHtml

            Returns:
                (string) - Returns notiication message html, Escaped notification html

        NOTE : This fetches the notification html where message format Type Email is
               supported otherwise it gets plain text
        """
        message_format_type = 0
        supported_html = [1, 512, 8192]
        if notif_type in supported_html:
            message_format_type = 1
        alert_type = constants.ALERT_CATEGORY_TYPE[string.capwords(self.alert_category)].get(self.alert_type)
        query = f"select * from NTnotificationTemplate where ntalerttypeid={alert_type}" \
                f" and locale=0 and messageType={notif_type} and messageFormatType = {message_format_type};"
        db_response = self.options_selector.update_commserve_db(query)
        # Get index for required column
        column_index = db_response.columns.index('defaultformatString')
        # Extract The format html from the response
        notif_html = db_response.rows[0][column_index]
        # Escape this html to make it suitable for XML request body
        escaped_html = html.escape(f'''{notif_html}''')

        return notif_html, escaped_html

    def get_token_id(self, token_rule_group):
        """
        Fetches the token ID for given token rule group

            Args:
                token_rule_group (string)  --  Token Rule Group name

            Returns:
                (int) - Returns Token ID for given rule group
        """
        query = f'''select MessageID from evlocalemsgs where localeid=0 and message ='<{token_rule_group}>';'''
        db_response = self.options_selector.update_commserve_db(query)
        # Get index for required column
        column_index = db_response.columns.index('MessageID')
        # Extract the MessageID value from the response
        if len(db_response.rows) > 1:
            self.log.error('Response returned more than 1 rows')
            return None
        token_id = db_response.rows[0][column_index]

        return token_id

    def get_token_type_format(self, token_id):
        """
        Fetches the token type and token format for given token ID

            Args:
                token_id (string)  --  Token ID

            Returns:
                (tuple) - Returns Token type and token format values
        """
        query = f'''select * from NTmessageTokensForAlert where tokenID={token_id};'''
        db_response = self.options_selector.update_commserve_db(query)
        # get index for columns
        token_type_col = db_response.columns.index('tokenType')
        token_input_format_col = db_response.columns.index('tokenInputFormat')
        # Extract data from the first row
        return db_response.rows[0][token_type_col], db_response.rows[0][token_input_format_col]

    def get_ida_app_id(self, app_name, client_id):
        """
        Fetches the application ida for given IDA for given client

            Args:
                app_name (string)  --  Application name
                client_id (string) --  Client Id for which given IDA id is to be fetched

            Returns:
                (string) - Returns IDA App ID for given client
        """
        query = f'''select type from APP_iDAType where name='{app_name}' and type in (select appTypeId from APP_IDAName where clientId = {client_id});'''
        db_response = self.options_selector.update_commserve_db(query)
        # Get column index
        type_index = db_response.columns.index('type')
        # Extract data
        if len(db_response.rows) == 0:
            raise SDKException('Response', '102')
        return db_response.rows[0][type_index]

    def populate_token_rules_xml(self, token_rules):
        """Populates the token rule part of Alert XML body

            Args:
                token_rules (list)  --  List of Token Rule dictionaries passed in **kwargs in get_alert_xml()

                example arguments :
                    token_rule=[{'rule': 'LEVEL','value': 'FULL','operator': 0}]
            Returns:
                string - Token rule part for alert xml
        """
        header = '''&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_AlertTokenRuleGroup 
                             groupOperator=&quot;0&quot;&gt;&lt;rules groupOperator=&quot;0&quot;&gt;&lt;rules 
                             groupOperator=&quot;2&quot;&gt;&lt;'''

        token_xml_part = header
        for i, token_rule in enumerate(token_rules):
            rule = token_rule.get('rule')
            operator = token_rule.get('operator')
            value = token_rule.get('value')
            # Fetch token ID for given token rule
            token_id = self.get_token_id(rule)
            # Fetch token type and format
            token_type, token_format = self.get_token_type_format(token_id)
            # Check if last token in token rule or not, the xml body part differs for both
            if i == len(token_rules)-1:
                # Last token rule
                token_xml = f'''alertTokenRule tokenMessage=&quot;{rule}&quot; tokenId=&quot;{token_id}&quot; 
                                tokenType=&quot;{token_type}&quot; tokenFormat=&quot;{token_format}&quot; 
                                value=&quot;{value}&quot; tokenOperator=&quot;{operator}&quot;'''
            else:
                token_xml = f'''alertTokenRule tokenMessage=&quot;{rule}&quot; tokenId=&quot;{token_id}&quot; 
                                tokenType=&quot;{token_type}&quot; tokenFormat=&quot;{token_format}&quot; 
                                value=&quot;{value}&quot; tokenOperator=&quot;{operator}&quot;
                                /&gt;&lt;/rules&gt;&lt;rules groupOperator=&quot;2&quot;&gt;&lt;'''
            token_xml_part += token_xml

        footer = ''' /&gt;&lt;/rules&gt;&lt;/rules&gt;&lt;/CVGui_AlertTokenRuleGroup&gt;'''
        return token_xml_part + footer

    def populate_entities_xml(self, rule_group_xml, entities, ida_types):
        """Populates the Associations part of Alert XML body

            Args:
                rule_group_xml (string)  --  Rule group XML generated through populate_token_rule_xml()
                entities (dict) -- Entites dictionary to be associated with the alert
                ida_types (list) -- List of IDA types for which the alert is to created

            Returns:
                string - Associations part for alert xml
        """
        associations = f'''<alertDetail alertSeverity="0" alertTokenRuleGroupXml="{rule_group_xml}" 
                            checkForEventParams="0" 
                            customQueryDetailsXml="" escalationSeverity="0" eventCriteriaXML="" 
        minJobCountForJobAnomaly="0" periodicNotificationInterval="0" recipient="" senderDisplayName="" senderEmailId=""
         xmlEntityList="&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CommCellTreeNode&gt;&lt;'''
        entities_list = self.alerts_commcell._get_entities(entities)
        for entity in entities_list:
            name_attribute = list(entity.keys())[0]
            id_attribute = list(entity.keys())[1]
            # Check if entity is for a client and if ida types has been specified
            if 'client' in name_attribute and ida_types is not None:
                # Iterate through ida types and populate associations by getting appId
                for ida_type in ida_types:  # IDA Types only apply for clients
                    # Get APP id for each ida for that particular client
                    application_id = self.get_ida_app_id(app_name=ida_type, client_id=id_attribute)
                    association_string = f"associations applicationId=&quot;{application_id}&quot; clientName=&quot;{entity[name_attribute]}&quot; " \
                                         f"clientId=&quot;{entity[id_attribute]}&quot; _type_=&quot;{entity['_type_']}&quot; " \
                                         f"appName=&quot;{ida_type}&quot;&gt;&lt;flags " \
                                         f"exclude=&quot;0&quot; /&gt;&lt;/associations&gt;&lt;"
                    associations += association_string
            else:
                association_string = f"associations {name_attribute}=&quot;{entity[name_attribute]}&quot; " \
                                     f"{id_attribute}=&quot;{entity[id_attribute]}&quot; _type_=&quot;{entity['_type_']}" \
                                     f"&quot;&gt;&lt;flags exclude=&quot;0&quot; /&gt;&lt;/associations&gt;&lt;"
                associations += association_string
        associations += '/CVGui_CommCellTreeNode&gt;">'
        return associations

    def populate_criterias_xml(self, additional_settings, criteria):
        """Populates the Criterias part of Alert XML body

            Args:
                additional_settings (dict)  --  Additional settings dict generated from **kwargs
                passed in get_alert_xml()
                criteria (list)             --  List of Criteria IDs to be selected for the alert

            Returns:
                string - Criterias part for alert xml
        """
        # Additional settings are used for configuring alert notification
        # settings like Delay, Notify Only if condition persists, escalate notification criteria
        criterias = ''
        delay_time_seconds = 0
        persist_time_seconds = 0
        reporting_options = 1
        escalate_criteria = False
        if 'notification_criteria' in additional_settings:
            reporting_enum = 1
            delay_time_seconds = additional_settings['notification_criteria'].get('notify_if_persists', 0)
            persist_time_seconds = additional_settings['notification_criteria'].get('repeat_notif', 0)
            # Either of these conditions could be selected
            for condition in additional_settings['notification_criteria'].keys():
                if condition == 'notify_if_persists':
                    reporting_enum += 256
                elif condition == 'repeat_notif':
                    reporting_enum += 2
                elif condition == 'notify_condition_clears':
                    reporting_enum += 4
            reporting_options = reporting_enum

        # Check if escalation paramaters are provided
        if 'escalation_criteria' in additional_settings:
            reporting_enum_escalation = 0
            escalate_criteria = True
            delay_time_seconds_escalation = additional_settings['escalation_criteria'].get('notify_if_persists', 0)
            persist_time_seconds_escalation = additional_settings['escalation_criteria'].get('repeat_notif', 0)
            # Either of these conditions could be selected
            for condition in additional_settings['escalation_criteria'].keys():
                if condition == 'notify_if_persists':
                    reporting_enum_escalation += 8
                elif condition == 'repeat_notif':
                    reporting_enum_escalation += 2
                elif condition == 'notify_condition_clears':
                    reporting_enum_escalation += 4

        if isinstance(criteria, int):
            current_criteria = f'<criteria criteriaId="{criteria}" criteriaSeverity="0" delayTimeSeconds="{delay_time_seconds}"' \
                               f' esclationLevel="1" persistTimeSeconds="{persist_time_seconds}" reportId="0"' \
                               f' reportingOptions="{reporting_options}" taskId="0" value="" />'
            if escalate_criteria:
                current_criteria += f'<criteria criteriaId="{criteria}" criteriaSeverity="0" ' \
                                    f'delayTimeSeconds="{delay_time_seconds_escalation}"' \
                                       f' esclationLevel="2" ' \
                                    f'persistTimeSeconds="{persist_time_seconds_escalation}" reportId="0"' \
                                       f' reportingOptions="{reporting_enum_escalation}" taskId="0" value="" />'
            criterias += current_criteria
        else:
            # If notification_criteria is in additional settings then set values

            for criteria_id in criteria:
                current_criteria = f'<criteria criteriaId="{criteria_id}" criteriaSeverity="0" ' \
                                   f'delayTimeSeconds="{delay_time_seconds}"' \
                                   f' esclationLevel="1" persistTimeSeconds="{persist_time_seconds}" reportId="0"' \
                                   f' reportingOptions="{reporting_options}" taskId="0" value="" />'
                if escalate_criteria:
                    current_criteria += f'<criteria criteriaId="{criteria}" criteriaSeverity="0" ' \
                                        f'delayTimeSeconds="{delay_time_seconds_escalation}"' \
                                        f' esclationLevel="2" persistTimeSeconds="{persist_time_seconds_escalation}" ' \
                                        f'reportId="0"' \
                                        f' reportingOptions="{reporting_enum_escalation}" taskId="0" value="" />'
                criterias += current_criteria

        return criterias

    def populate_notification_xml(self, notif_type, escalate_notification=False):
        """Populates the Notification part of Alert XML body

            Args:
                notif_type (list) - List of notification types to keep for the alert
                escalate_notification (bool) - Whether the use wants to escalate the notification

            Returns:
                string - Notifications part for alert xml
        """
        notifs = ''
        for notification in notif_type:
            # Get notification html for current notification type
            _, notif_html = self.get_notif_html(notification)
            # Only if alert has escalation criteria inject escalation notification message
            # For RSS Feed, Save Alert to Disk some additional metadeta is needed
            if notification == 1024:  # RSS Feed
                base_location = 'http://' + self.commcell_object.commserv_hostname + ':81/rss'
                selected_channel = 'alerts.rss'
                current = f'''<notifMsgs esclationLevel="1" localeId="0" messageFormat="0" 
                               notifMessage="{notif_html}" notifMessageHtml=""
                               notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                               cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                               <feeds baseLocation="{base_location}" rssFeedLocation="" 
                               selectedChannel="{selected_channel}" seperateIndex="0" />
                               <entity _type_="0" />
                               </notifMsgs>'''
                if escalate_notification:
                    current += f'''<notifMsgs esclationLevel="2" localeId="0" messageFormat="0" 
                                    notifMessage="{notif_html}" notifMessageHtml=""
                                    notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                                    cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                                    <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                                    <entity _type_="0" />
                                    </notifMsgs>'''

            elif notification == 512:  # Save to Disk
                base_location = self.commcell_object.commserv_client.install_directory + '\\alerts'
                current = f'''<notifMsgs esclationLevel="1" localeId="0" messageFormat="1" 
                               notifMessageHtml="{notif_html}"
                               notifOptions="0" notifType="{notification}"><saveAlertToDisk 
                               alertLocation="{base_location}"
                               cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                               <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                               <entity _type_="0" />
                               </notifMsgs>'''
                if escalate_notification:
                    current = f'''<notifMsgs esclationLevel="2" localeId="0" messageFormat="1" 
                                   notifMessageHtml="{notif_html}"
                                   notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                                   cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                                   <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                                   <entity _type_="0" />
                                   </notifMsgs>'''
            elif notification == 8:  # Event Viewer
                current = f'''<notifMsgs esclationLevel="1" localeId="0" messageFormat="0" notifMessage="{notif_html}" 
                               notifMessageHtml="&lt;p&gt; &lt;/p&gt;"
                               notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                               cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                               <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                               <entity _type_="0" />
                               </notifMsgs>'''
                if escalate_notification:
                    current += f'''<notifMsgs esclationLevel="2" localeId="0" messageFormat="0" notifMessage="{notif_html}" 
                                    notifMessageHtml="&lt;p&gt; &lt;/p&gt;"
                                    notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                                    cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                                    <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                                    <entity _type_="0" />
                                    </notifMsgs>'''
            elif notification == 4:  # SNMP Trap
                current = f'''<notifMsgs esclationLevel="1" localeId="0" messageFormat="0" notifMessage="{notif_html}" 
                               notifMessageHtml="&lt;p&gt; &lt;/p&gt;"
                               notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                               cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                               <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                               <entity _type_="0" />
                               </notifMsgs>'''
                if escalate_notification:
                    current += f'''<notifMsgs esclationLevel="2" localeId="0" messageFormat="0" notifMessage="{notif_html}" 
                                    notifMessageHtml="&lt;p&gt; &lt;/p&gt;"
                                    notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                                    cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                                    <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                                    <entity _type_="0" />
                                    </notifMsgs>'''
            else:
                current = f'''<notifMsgs esclationLevel="1" localeId="0" messageFormat="1" notifMessageHtml="{notif_html}"
                               notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                               cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                               <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                               <entity _type_="0" />
                               </notifMsgs>'''
                if escalate_notification:
                    current += f'''<notifMsgs esclationLevel="2" localeId="0" messageFormat="1" notifMessageHtml="{notif_html}"
                                    notifOptions="0" notifType="{notification}"><saveAlertToDisk alertLocation=""
                                    cvpassword="" impersonateUser="0" loginName="" password="" useNetworkShare="0" />
                                    <feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0" />
                                    <entity _type_="0" />
                                    </notifMsgs>'''
            notifs += current
        return notifs

    def get_alert_xml(self, name, notif_type, entities, criteria, mail_recipent=None, **kwargs):
        """Creates Request XML of given alert details. Calls subfunctions for populating subsections of the XML.
           Compiles all subsection XMLs into a final one, which is used for creating the Alert.

            Args:
                name (string)  --  Name of the alert
                notif_type (list) - List of notification types to keep for the alert
                entities (dict) - Entities associated with the alert

                example dictionary :
                    entities={'clients': self.tcinputs['ClientName']}

                criteria (list) - List of Criteria IDs to be selected for the alert
                to_users_mail (list) - List of Users to include in To for the alert notification mail
                to_usergroups_mail (list) - List of Usergroups to include in To for the alert notification mail
                mail_recipent (list) - List of extra mail recipents to receive the alert notification
                **kwargs (dict) - Additional arguments which the user may want for his alert

            Returns:
                string - Alert XML string required for QEXECUTE COMMAND
        """
        additional_settings = dict(kwargs.items())
        notif_type = [constants.ALERT_NOTIFICATIONS.get(string.capwords(i)) for i in notif_type]
        # The Request XML is divided into parts, certain parts are populated as required based on the inputs
        # HEADER FOR THE REQUEST
        header = '''<?xml version="1.0" encoding="UTF-8"?>
                    <CVGui_AlertCreateReq ownerId="1">
                       <processinginstructioninfo>
                          <user _type_="13" userId="1" userName="admin" />
                          <locale _type_="66" localeId="0" />
                          <formatFlags continueOnError="0" elementBased="0" filterUnInitializedFields="0" 
                          formatted="0" ignoreUnknownTags="1" skipIdToNameConversion="1" skipNameToIdConversion="0" />
                    </processinginstructioninfo>'''

        # TOKEN RULE FILTERS
        rule_group_xml = ""
        if 'token_rule' in additional_settings:
            # Only supports one token Rule at present
            token_rule = additional_settings.get('token_rule')
            rule_group_xml = self.populate_token_rules_xml(token_rules=token_rule)

        # ENTITY ASSOCIATIONS
        ida_types = None
        if 'ida_types' in additional_settings:
            ida_types = additional_settings.get('ida_types')
        associations = self.populate_entities_xml(rule_group_xml, entities, ida_types=ida_types)

        # SOME ADDITIONAL OPTIONS ARE SET HERE AS WELL AS BASIC ALERT DETAILS
        status = 0  # Default value for not having send individual notifications for this alert
        if 'send_individual_notif' in additional_settings:
            status = 16
        current_time = datetime.now().timestamp()
        alert_options = f'''<alert GUID="" createdTime="{current_time}" description="" escNotifType="0" 
                             notifType="{sum(notif_type)}" organizationId="0" origCCId="0" status="{status}">
                             <alert id="0" name="{name}" />
                             <alertCategory id="{constants.CATEGORY_ID[self.alert_category]}" name="{self.alert_category}" />
                             <alertType id="{constants.ALERT_CATEGORY_TYPE[string.capwords(self.alert_category)].get(
                             self.alert_type)}" name="{self.alert_type}" />
                             <creator id="1" name="admin" />
                             </alert>'''

        # EMAIL TO : USERS, USERGROUPS
        if 'to_users_mail' in additional_settings:
            to_recipents_xml = ''
            for user in additional_settings.get('to_users_mail'):
                # Try fetching id for user and populating into to_recipents_xml
                try:
                    user_id = self.commcell_object.users.get(user).user_id
                    to_recipents_xml += f'''<userList id1="{user_id}" id2="1" name="{user}" />'''
                except Exception as fetch_excp:
                    self.log.info(f'Couldn\'t fetch user id for user {user}')

            alert_options += to_recipents_xml

        if 'to_usergroups_mail' in additional_settings:
            to_recipents_xml = ''
            for user_group in additional_settings.get('to_usergroups_mail'):
                # Try fetching usergroup id for usergroup and populating into to_recipents_xml
                try:
                    usergroup_id = self.commcell_object.user_groups.get(user_group).user_group_id
                    to_recipents_xml += f'''<userGroupList id1="{usergroup_id}" id2="1" name="{user_group}" />'''
                except Exception as fetch_excp:
                    self.log.info(f'Couldn\'t fetch usergroup id for usergroup {user_group}\n'
                                  f'Encountered Exception : {fetch_excp}')
            alert_options += to_recipents_xml

        # ESCALATION RECIPENTS
        if 'escalation_recipent' in additional_settings:
            if isinstance(additional_settings.get('escalation_recipent'), str):
                alert_options += f'''<nonGalaxyUserList id1="0" id2="2" 
                                     name="{additional_settings.get('escalation_recipent')}" />'''
            elif isinstance(additional_settings.get('escalation_recipent'), list):
                for to_recipent in additional_settings.get('escalation_recipent'):
                    alert_options += f'''<nonGalaxyUserList id1="0" id2="2" name="{to_recipent}" />'''

        # ALERT CRITERIAS
        criterias = self.populate_criterias_xml(additional_settings, criteria)

        # NOTIFICATION MESSAGE BODY
        escalate_notification = 'escalation_criteria' in additional_settings
        notifs = self.populate_notification_xml(notif_type, escalate_notification)

        # GENERAL ALERT INFO
        general_info = '''<locale localeID="0" localeName="" />
                          <reportingParams delayTimeSeconds="0" persistTimeSeconds="0" reportingOptions="0" />
                          <appTypeFilters />
                          <securityAssociations processHiddenPermission="0" />
                          <alertProperties />'''

        # EXTRA MAIL NOTIFICATION RECIPENTS
        recipents = ''
        # These are mail recipents in the cc
        if mail_recipent is not None:
            for cc_recipent in mail_recipent:
                recipent_string = f'''<nonGalaxyUserListCc id1="0" id2="1" name="{cc_recipent}" />'''
                recipents += recipent_string

        # FOOTER
        footer = '''</alertDetail>
                    </CVGui_AlertCreateReq>'''

        self.alert_xml = header + associations + alert_options + criterias + notifs + general_info + recipents + footer
        # We create a dictionary as this will be needed when creating the alert and for error checking
        self.alert_xml_dict = {'alert_name': name, 'alert_xml': self.alert_xml, 'criteria': criteria}
        self.alert_name = name
        self.alert_details = self.alert_xml_dict
        return self.alert_xml_dict

    def get_custom_alert_xml(self, name, notif_type, query_id=None, mail_recipent=None, **kwargs):
        """Creates a custom alert using given data"""
        additional_settings = dict(kwargs.items())
        notif_type = [constants.ALERT_NOTIFICATIONS.get(string.capwords(i)) for i in notif_type]
        # The Request XML is divided into parts, certain parts are populated as required based on the inputs

        # HEADER FOR THE REQUEST
        if 'custom_query_details' in additional_settings:
            header = f'''<?xml version="1.0" encoding="UTF-8"?>
                                <CVGui_AlertCreateReq ownerId="1">
                                <alertDetail alertSeverity="3" checkForEventParams="0" 
                                customQueryDetailsXml="{additional_settings.get('custom_query_details')}"
                                escalationSeverity="3" eventCriteriaXML="" minJobCountForJobAnomaly="0" 
                                periodicNotificationInterval="0" recipient="" senderDisplayName="" 
                                senderEmailId="" 
                                xmlEntityList="&lt;?xml version='1.0' 
                                encoding='UTF-8'?&gt;&lt;CVGui_CommCellTreeNode /&gt;">'''
        else:
            header = f'''<?xml version="1.0" encoding="UTF-8"?>
                        <CVGui_AlertCreateReq ownerId="1">
                        <alertDetail alertSeverity="3" checkForEventParams="0" 
                        customQueryDetailsXml="&lt;?xml version='1.0' 
                        encoding='UTF-8'?&gt;&lt;CVGui_CustomQueryDetailsForAlert queryId=&quot;{query_id}&quot; 
                        additionalQueryInfo=&quot;&amp;lt;?xml version='1.0' 
                        encoding='UTF-8'?&gt;&amp;lt;CVGui_QueryAdditionalInfo /&gt;&quot; /&gt;" 
                        escalationSeverity="3" minJobCountForJobAnomaly="0" 
                        xmlEntityList="&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CommCellTreeNode /&gt;">'''

        if 'associated_at_commcell_level' in additional_settings:
            header = re.sub('CVGui_CommCellTreeNode /&gt;">',
                            f'''CVGui_CommCellTreeNode&gt;&lt;associations _type_=&quot;125&quot; /&gt;&lt;/CVGui_CommCellTreeNode&gt;">''', header)

        # ALERT CRITERIAS
        # Criteria = 75 For custom Alerts
        criterias = self.populate_criterias_xml(additional_settings, criteria=75)

        # GENERAL INFO
        general_info = '''<locale localeID="0"/>'''

        # SOME ADDITIONAL OPTIONS ARE SET HERE AS WELL AS BASIC ALERT DETAILS
        status = 0  # Default value for not having send individual notifications for this alert
        if 'send_individual_notif' in additional_settings:
            status = 16
        current_time = datetime.now().timestamp()
        alert_options = f'''<alert GUID="" createdTime="{current_time}" description="" escNotifType="0" 
                             notifType="{sum(notif_type)}" organizationId="0" origCCId="0" status="{status}">
                             <alert id="0" name="{name}" />
                             <alertCategory id="{constants.CATEGORY_ID[self.alert_category]}" name="{self.alert_category}" />
                             <alertType id="{constants.ALERT_CATEGORY_TYPE[string.capwords(self.alert_category)].get(
                             self.alert_type)}" name="{self.alert_type}" />
                             <creator id="1" name="admin" />
                             </alert>
                             <appTypeFilters/>'''

        # EMAIL TO : USERS, USERGROUPS
        if 'to_users_mail' in additional_settings:
            to_recipents_xml = ''
            for user in additional_settings.get('to_users_mail'):
                # Try fetching id for user and populating into to_recipents_xml
                try:
                    user_id = self.commcell_object.users.get(user).user_id
                    to_recipents_xml += f'''<userList id1="{user_id}" id2="1" name="{user}" />'''
                except Exception as fetch_excp:
                    self.log.info(f'Couldn\'t fetch user id for user {user}, Encountered exception : {fetch_excp}')

            alert_options += to_recipents_xml

        if 'to_usergroups_mail' in additional_settings:
            to_recipents_xml = ''
            for user_group in additional_settings.get('to_usergroups_mail'):
                # Try fetching usergroup id for usergroup and populating into to_recipents_xml
                try:
                    usergroup_id = self.commcell_object.user_groups.get(user_group).user_group_id
                    to_recipents_xml += f'''<userGroupList id1="{usergroup_id}" id2="1" name="{user_group}" />'''
                except Exception as fetch_excp:
                    self.log.info(f'Couldn\'t fetch usergroup id for usergroup {user_group}')
            alert_options += to_recipents_xml

        # NOTIFICATION MESSAGE BODY
        escalate_notification = 'escalation_criteria' in additional_settings
        notifs = self.populate_notification_xml(notif_type, escalate_notification)

        # EXTRA MAIL NOTIFICATION RECIPENTS
        recipents = ''
        # These are mail recipents in the cc
        if mail_recipent is not None:
            for cc_recipent in mail_recipent:
                recipent_string = f'''<nonGalaxyUserListCc id1="0" id2="1" name="{cc_recipent}" />'''
                recipents += recipent_string

        # FOOTER
        footer = '''</alertDetail>
                    </CVGui_AlertCreateReq>'''

        self.alert_xml = header + criterias + general_info + alert_options + notifs + recipents + footer
        # We create a dictionary as this will be needed when creating the alert and for error checking
        self.alert_xml_dict = {'alert_name': name, 'alert_xml': self.alert_xml, 'criteria': 75, "query_id": query_id}
        self.alert_name = name
        self.alert_details = self.alert_xml_dict
        return self.alert_xml_dict

    def create_alert_from_xml(self):
        """Creates a new Alert for CommCell using QCommand Execute

        Returns:
            object  -  instance of the Alert class for this new alert

        Raises:
            SDKException:
                if input argument is not an instance of dict

                if alert with given name already exists

                if failed to create an alert

                if response is not success

                if response is empty

        NOTE : This function assumes that get_alert_xml() has been called earlier to populate the alert_xml_dict,
               otherwise by default alert_xml_dict is initialized to None

        """
        if not isinstance(self.alert_xml_dict, dict):
            raise SDKException('Alert', '101')

        # required alert json
        alert_xml = self.alert_xml_dict.get('alert_xml')
        alert_name = self.alert_xml_dict.get('alert_name')
        if self.alerts_commcell.has_alert(alert_name):
            raise SDKException('Alert', '102', 'Alert "{0}" already exists.'.
                               format(alert_name))

        post_alert = self.alerts_commcell._services['EXECUTE_QCOMMAND']
        self.log.info('Creating Alert {0}'.format(self.alert_name))
        flag, response = self.alerts_commcell._cvpysdk_object.make_request(
            'POST', post_alert, alert_xml)

        if flag:
            if response.json():
                alert_id = str(response.json()["alertId"])

                if alert_id:
                    self.alerts_commcell.refresh()
                    self.log.info('Alert Creation Successful')
                    return self.alerts_commcell.get(alert_name)

                error_message = ""
                error_dict = response.json()['errorResp']
                if 'errorMessage' in error_dict:
                    error_message = error_dict['errorMessage']

                if error_message:
                    raise SDKException(
                        'Alert', '102', 'Failed to create Alert\nError: "{}"'.format(error_message))
                else:
                    raise SDKException('Alert', '102', "Failed to create Alert")
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self.alerts_commcell._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def create_criteria_mapping(self, criteria_id_list):
        """
        Create a list of Criteria Name mappings from a list of criteria IDs

            Args:
                criteria_id_list (list)  --  List of criteria IDs for which criteria names are to be returned

            Returns:
                (list) - Returns Criteria Names list corresponding to criteria IDs list
        """
        criteria_names = []
        for criteria_id in criteria_id_list:
            criteria_names.append(constants.CRITERIA_ID.get(criteria_id))
        return criteria_names

    def read_alert_rule(self, rule_name):
        """
        Reads the Alert Rule XML from default folder and returns it

            Args:
                rule_name (str)  --  Name of the Alert Rule xml to look for

            Returns:
                (str) - Alert rule xml body if found
        """
        rule_xmls_path = os.path.join(constants.AUTOMATION_DIRECTORY ,'Server','Alerts','CustomAlertXml')
        self.log.info(f"Looking in {rule_xmls_path} for Alert Rule {rule_name}")
        file_required = os.path.join(rule_xmls_path, rule_name)
        try:
            with open(file_required, 'r') as file:
                xml_request = file.read()
            return xml_request
        except Exception as e:
            self.log.error(str(e))
            raise Exception(f"Alert Rule xml {file_required} could not be read")

    def import_alert_rule(self, rule_name, xml_request):
        """Creates Alert Rule using Rule XML POST to QExecuteCommand"""
        if not isinstance(xml_request, str):
            raise SDKException('Alert', '101')

        post_alert_rule = self.alerts_commcell._services['EXECUTE_QCOMMAND']
        self.log.info('Creating Alert Rule {0}'.format(rule_name.split(".")[0]))
        flag, response = self.alerts_commcell._cvpysdk_object.make_request(
            'POST', post_alert_rule, xml_request)

        if flag:
            if response.json():
                query_id = str(response.json()["queryId"])
                error_code = response.json()["response"]["errorCode"]

                if query_id and error_code == 0:
                    self.log.info('Alert Rule Creation Successful')
                    return query_id

                error_message = ""
                error_dict = response.json()['errorResp']
                if 'errorMessage' in error_dict:
                    error_message = error_dict['errorMessage']

                if error_message:
                    raise SDKException(
                        'Alert', '102', 'Failed to create Alert Rule\nError: "{}"'.format(error_message))
                else:
                    raise SDKException('Alert', '102', "Failed to create Alert Rule")
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self.alerts_commcell._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def delete_alert_rule(self, rule_name, query_id):
        """
        Deletes the imported alert rule

            Args:
                rule_name (str)  --  Name of the Alert Rule
                query_id (int) -- Query id of the imported custom alert rule

            Returns:
                None if Deletion successful else raises exception
        """
        delete_rule_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no" ?><App_QueryOperationRequest queryOp="2"><processinginstructioninfo><user _type_="13" userId="1" userName="admin"/><locale _type_="66" localeId="0"/><formatFlags continueOnError="0" elementBased="0" filterUnInitializedFields="0" formatted="0" ignoreUnknownTags="1" skipIdToNameConversion="1" skipNameToIdConversion="0"/></processinginstructioninfo><queryEntity queryId="{query_id}" queryName="{rule_name}"/></App_QueryOperationRequest>'''
        if not isinstance(rule_name, str) or not isinstance(query_id, str):
            raise SDKException('Alert', '101')

        post_alert_rule = self.alerts_commcell._services['EXECUTE_QCOMMAND']
        self.log.info('Deleting Alert Rule : {0}'.format(rule_name.split(".")[0]))
        flag, response = self.alerts_commcell._cvpysdk_object.make_request(
            'POST', post_alert_rule, delete_rule_xml)

        if flag:
            if response.json():
                error_code = response.json()["errorCode"]

                if error_code == 0:
                    self.log.info('Alert Rule Deletion Successful')
                    return None

                error_message = ""
                error_dict = response.json()
                if 'errorMessage' in error_dict:
                    error_message = error_dict['errorMessage']

                if error_message:
                    raise SDKException(
                        'Alert', '102', 'Failed to Delete Alert Rule\nError: "{}"'.format(error_message))
                else:
                    raise SDKException('Alert', '102', "Failed to Delete Alert Rule")
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self.alerts_commcell._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def set_custom_alert_frequency(self, custom_rules_xml, query_frequency=180):
        """
        Modifies the custom alert xml to change the custom rule frequency

            Args:
                custom_rules_xml (str)  --  custom alert xml
                query_frequency (int) -- The query frequency (in seconds) to set in the custom rule xml

            Returns:
                (str) - Modified custom rule xml
        """
        modified_xml = re.sub('freq_subday_interval=&quot;\d+&quot;',
                              f'freq_subday_interval=&quot;{query_frequency}&quot;',
                              custom_rules_xml)
        return modified_xml

    def get_custom_query_name(self, custom_alert_xml):
        """
        Gets the Query Name from custom alert xml using Regex

            Args:
                custom_alert_xml (str)  --  custom alert xml

            Returns:
                (str) - Query name
        """
        match = re.search('queryName=".*"', custom_alert_xml).group(0)
        query_name = match.split('"')[1]
        return query_name

    def delete_alert(self, alert_name):
        """
        Attempts to delete the alert
        Exception:
            if alert deletion failed
        """
        self.log.info('Attempting to delete alert : {0}'.format(alert_name))
        try:
            self.alerts_commcell.delete(alert_name)
            self.log.info('Alert Deletion Successful')
            return True
        except Exception as excp:
            self.log.info(f"Alert Deletion encountered an exception {excp}")

    def cleanup(self):
        """Performs cleanup specific to alerts, notification parsing objects
        """
        # Alert Cleanup
        self.log.info("Deleting the Alert")
        self.alerts_commcell.delete(self.alert_details.get("alert_name"))
        self.log.info("Alert deleted successfully")
        # Mailbox Cleanup
        if self.mailbox is not None:
            self.log.info("Disconnecting Mailbox")
            self.mailbox.disconnect()

        if self.alert_xml_dict is not None and "query_id" in self.alert_xml_dict:
            # Custom rule -> Delete the rule
            try:
                self.delete_alert_rule(rule_name=self.alert_type,
                                       query_id=self.alert_xml_dict.get("query_id"))
            except Exception as rule_deletion_excp:
                self.log.info(f"Encountered exception while custom rule deletion : {rule_deletion_excp}")


class AlertSituations:
    """
    Class  which contains all Alert triggering situation functions

    Define different functions corresponding to different situations that may be required
    """
    def __init__(self, commcell_object, category=None, alert_type=None):
        """Initialize object of the AlertHelper class.

            Args:
                commcell_object (object)  --  instance of the Commcell class
        """
        self.log = logger.get_log()
        self.commcell_object = commcell_object
        self.alert_category = category
        self.alert_type = alert_type
        self.commserv_client = self.commcell_object.commserv_client
        self.cs_machine_obj = Machine(self.commserv_client)
        self._utility = None
        self._entities = None

    def backup_job(self, client, subclient, backup_type):
        """Initialize object of the AlertHelper class.

            Args:
                client (object)  - Client object
                subclient (object) - Subclient object
                backup_type (string) - backuptype

            Returns:
                Runs a backup job on the given subclient, returns the Cache
        """
        cache = {}

        # Backup Phase
        self.log.info('Starting Backup Phase')
        self.log.info('Create Machine Class object')

        client_machine = Machine(machine_name=client.client_name,
                                 commcell_object=self.commcell_object)

        self.log.info('Read subclient content')
        self.log.info('Subclient Content : %s', subclient.content)

        self.log.info('Starting Subclient {0} Backup'.format(backup_type).center(20, '*'))
        job = subclient.backup(backup_type)
        self.log.info('Started %s backup with Job ID : %s', backup_type, str(job.job_id))
        cache['job_id'] = str(job.job_id)
        cache['client_machine'] = client_machine
        if job.wait_for_completion() is False:
            raise Exception(
                'Failed to run {0} backup job with error {1}'.format(backup_type, job.delay_reason),
                cache
            )
        self.log.info('Successfully finished %s backup job', backup_type)

        return cache

    def backup_generated_data(self, client, subclient, backup_type, size=10):
        """Initialize object of the AlertHelper class.

            Args:
                client (object)  - Client object
                subclient (object) - Subclient object
                backup_type (string) - backup-type
                size (int) - Size of backup data to generate

            Returns:
                Generates test data, runs a backup job on the generated data, returns the Cache
        """
        cache = {}
        options_selector = OptionsSelector(self.commcell_object)
        client_machine = None
        test_data_path = None
        # Backup Phase
        self.log.info('Starting Backup Phase')
        self.log.info('Read subclient content')
        self.log.info('Subclient Content : %s', subclient.content)

        if string.capwords(backup_type) == 'Full':
            self.log.info('Creating Machine Class Object')
            client_machine = Machine(machine_name=client.client_name,
                                     commcell_object=self.commcell_object)

            drive = options_selector.get_drive(client_machine, size=1)
            if drive is None:
                raise Exception("No free space to genereate test data")
            # Generate folder with current timestamp in drive
            test_data_path = client_machine.create_current_timestamp_folder(folder_path=drive)

            self.log.info('Add test data path to subclient content')
            subclient.content = [test_data_path]

            self.log.info('Generating test data at %s', test_data_path)
            client_machine.generate_test_data(test_data_path, file_size=size)

        self.log.info('*' * 10 + 'Starting Subclient {0} Backup'.format(backup_type) + '*' * 10)
        job = subclient.backup(backup_type)
        self.log.info('Started %s backup with Job ID : %s', backup_type, str(job.job_id))
        if job.wait_for_completion() is False:
            raise Exception(
                'Failed to run {0} backup job with error {1}'.format(backup_type, job.delay_reason)
            )
        cache['job_id'] = str(job.job_id)
        cache['client_machine'] = client_machine
        cache['test_data_path'] = test_data_path

        self.log.info('Successfully finished %s backup job', backup_type)

        return cache

    def low_disk_space_settings(self):
        """
            Used for adding additional settings to trigger low space criteria. Works for triggering this criteria
            in both Clients and MediaAgents.
        """
        # Add Additional Settings to the commcell
        self.log.info('Adding setting for Running System directory space check thread at given minutes')
        self.commcell_object.add_additional_setting(category='QMachineMaint',
                                                    key_name='nTimer_SystemDirSpaceCheck',
                                                    data_type='INTEGER',
                                                    value='1')
        self.commcell_object.add_additional_setting(category='QMachineMaint',
                                                    key_name='nTimer_DirSpaceCheck',
                                                    data_type='INTEGER',
                                                    value='1')
        self.log.info('Setting added successfully')
        self.log.info('Adding Additional setting for Min Free Space Percentage')
        self.commcell_object.add_additional_setting(category='QMachineMaint',
                                                    key_name='nMinFreeSpacePercentage',
                                                    data_type='INTEGER',
                                                    value='99')
        self.commcell_object.add_additional_setting(category='CommServeDB.GxGlobalParam',
                                                    key_name='Client Offline Alert Notification Interval',
                                                    data_type='INTEGER',
                                                    value='0')
        self.log.info('Setting added successfully')

    def cleanup_low_disk_space_settings(self):
        """
            Used for cleaning up additional settings added for low disk space criteria situation
        """
        # Remove Additional Settings
        self.log.info('Removing Additional Setting')
        self.commcell_object.delete_additional_setting(category='QMachineMaint',
                                                       key_name='nTimer_SystemDirSpaceCheck')
        self.commcell_object.delete_additional_setting(category='QMachineMaint',
                                                       key_name='nTimer_DirSpaceCheck')
        self.commcell_object.delete_additional_setting(category='QMachineMaint',
                                                       key_name='nMinFreeSpacePercentage')
        self.commcell_object.delete_additional_setting(category='CommServeDB.GxGlobalParam',
                                                       key_name='Client Offline Alert Notification Interval',)
        self.log.info('Settings Removed successfully')

    def auxiliary_copy_job(self, storage_policy_name, copy_name):
        """Runs an Auxillary Copy Job for Given Storage Policy"""
        storage_policy = StoragePolicy(self.commcell_object, storage_policy_name=storage_policy_name)
        self.log.info(
            '*' * 10 + 'Starting Auxillary Copy Backup for Storage Policy {0} Copy {1}'.format(storage_policy_name,
                                                                                               copy_name) + '*' * 10)
        job = storage_policy.run_aux_copy(storage_policy_copy_name=copy_name, all_copies=False)
        self.log.info('Started Auxillary Copy Job with ID : %s', str(job.job_id))
        if job.wait_for_completion() is False:
            raise Exception(
                'Failed to run Auxillary Copy Job with error {0}'.format(job.delay_reason)
            )
        cache = {'job_id': str(job.job_id)}
        return cache

    def no_backup_in_n_days(self, n):
        """Creates situation for criteria : No backup in last N days

            Args:
                n (int)  - N value for criteria, no backup in last N days

            Returns:
                Creates the alert situation required to trigger this criteria

            Note : For triggering this properly make sure windows time service startup type is set to disabled
        """
        # Add Additional Setting to the commcell
        self.log.info('Adding Additional Setting')
        self.commcell_object.add_additional_setting(category='CommServDB.GxGlobalParam',
                                                    key_name='client Offline Alert Notification Interval',
                                                    data_type='INTEGER',
                                                    value='0')
        self.log.info('Setting added Successfully')

        # Stop windows time service on CS Machine
        self.log.info('Initialize Commserve Machine Object')
        self.log.info('Disabling Windows Time service and stopping Time service on Commserve machine')
        self.cs_machine_obj.toggle_time_service(stop=True)
        self.log.info('Changing Date on Commserve machine')
        try:
            # Set Windows Time service startup type to "disabled" before this so that time change retains
            self.cs_machine_obj.add_days_to_system_time(days=n)
        except Exception as time_change_excp:
            self.log.error(time_change_excp)

    def cleanup_no_backup_in_n_days(self):
        """Performs cleanup operations after triggering situation for no backup in last n days"""
        self.log.info('Setting startup type of Windows Time Service to Automatic and Starting Time Service')
        self.log.info('Disabling Windows Time service and stopping Time service on Commserve machine')
        self.cs_machine_obj.toggle_time_service(stop=False)

        # Remove Additional Setting
        self.log.info('Removing Additional Setting')
        self.commcell_object.delete_additional_setting(category='CommServDB.GxGlobalParam',
                                                       key_name='client Offline Alert Notification Interval')
        self.log.info('Setting removed successfully')

    def toggle_commcell_activity(self, activity_name="ALL ACTIVITY", enable=True):
        """Enables/Disables Given activity on the Commcell

            Args:
                activity_name (str) - Name of commcell activity to Enable/Disable
                enable (bool)  - Boolean value for whether to enable or disable activity on commcell
        """
        if enable:
            try:
                self.log.info(f"Enabling {activity_name} Activity")
                activity_control = self.commcell_object.activity_control
                activity_control.set(activity_name, "Enable")
                self.log.info(f"{activity_name} activity enabled successfully")
            except Exception as excp:
                self.log.error(f"Encountered excp while enabling {activity_name} activity {excp}")
        else:
            try:
                self.log.info(f"Disabling {activity_name} Activity")
                activity_control = self.commcell_object.activity_control
                activity_control.set(activity_name, "Disable")
                self.log.info(f"{activity_name} activity disabled successfully")
            except Exception as excp:
                self.log.error(f"Encountered excp while disabling {activity_name} activity {excp}")

    def suspend_in_scan_phase(self, subclient, backup_type, phase_check_interval=5, wait_time=300):
        """Runs a Backup job and suspends it during Scan Phase using JM Service Stop

            Args:
                subclient (object) - Subclient object
                backup_type (string) - backuptype
                phase_check_interval (int) - Interval at which to check if job is in scan phase
                wait_time (int) - Time to wait for job in scan phase before JM Svc restart

            Returns:
                Runs a backup job on the given subclient, stops job at scan phase and resumes after condition trigger
        """
        suspended = False
        service_name = "GxJobMgr(Instance001)"
        # Backup Phase
        self.log.info('Starting Backup Phase')
        self.log.info('Create Machine Class object')

        self.log.info('Read subclient content')
        self.log.info('Subclient Content : %s', subclient.content)

        self.log.info('Starting Subclient {0} Backup'.format(backup_type).center(20, '*'))
        job = subclient.backup(backup_type)
        self.log.info('Started %s backup with Job ID : %s', backup_type, str(job.job_id))

        # Check Job Phase at every phase_check_interval seconds
        time.sleep(10)
        while not suspended:
            # Check job phase
            if job.phase.lower() == 'scan':
                # Stop Job manager service
                self.log.info(f"Stopping Service {service_name} on Commserve ")
                self.commserv_client.stop_service(service_name=service_name)
                suspended = True
            time.sleep(phase_check_interval)

        self.log.info(f"Suspending job {job.job_id} in Scan Phase for {wait_time}seconds")
        time.sleep(wait_time)
        # Start Job manager service
        self.log.info(f"Starting Service {service_name} on Commserve ")
        self.commserv_client.start_service(service_name=service_name)
        if job.wait_for_completion() is False:
            raise Exception(
                'Failed to run {0} backup job with error {1}'.format(backup_type, job.delay_reason)
            )

        self.log.info('Successfully finished %s backup job', backup_type)

    def admin_job_runtime_threshold(self, status_check_interval=5, wait_time=240):
        """Runs a Data aging job and suspends it during Running status using JM Service Stop

            Args:
                status_check_interval (int) - Interval at which to check if job is in running status
                wait_time (int) - Time to wait for job in running phase before JM Svc restart

            Returns:
                Runs a Data aging job , suspends job at running status and resumes it after condition trigger
        """
        suspended = False
        service_name = "GxJobMgr(Instance001)"
        # Data Aging Phase
        self.log.info('Starting Data Aging Job Backup')
        # Run Data Aging Job
        data_aging_job = self.commcell_object.run_data_aging()
        self.log.info('Started Data aging job with Job ID : %s', str(data_aging_job.job_id))

        # Check Job Phase at every phase_check_interval seconds
        time.sleep(5)
        while not suspended:
            # Check job phase
            if data_aging_job.status.lower() == 'running':
                # Stop Job manager service
                self.log.info(f"Stopping Service {service_name} on Commserve ")
                self.commserv_client.stop_service(service_name=service_name)
                suspended = True
            time.sleep(status_check_interval)

        self.log.info(f"Suspending job {data_aging_job.job_id} in Running status for {wait_time}seconds")
        time.sleep(wait_time)
        # Start Job manager service
        self.log.info(f"Starting Service {service_name} on Commserve ")
        self.commserv_client.start_service(service_name=service_name)
        if data_aging_job.wait_for_completion() is False:
            raise Exception(
                'Failed to run Data Aging job with error {0}'.format(data_aging_job.delay_reason)
            )

        self.log.info('Successfully finished Data Aging job')

    def restore_runtime_threshold(self, client, subclient, status_check_interval=4, wait_time=240):
        """Runs a Restore job and suspends it during Running Phase using JM Service Stop

            Args:
                client (object)  - Client object
                subclient (object) - Subclient object
                status_check_interval (int) - Interval at which to check if job is in running status
                wait_time (int) - Time to wait for job in running phase before JM Svc restart

            Returns:
                Runs an in-place Restore job on the given subclient, stops job at running phase
                and resumes after condition trigger
        """
        # Run backup on subclient
        self.backup_job(client=client, subclient=subclient, backup_type="FULL")
        sublcient_content = subclient.content

        # Run an inplace restore job and stop when job reaches running state
        suspended = False
        service_name = "GxJobMgr(Instance001)"

        self.log.info('Starting Subclient Content {0} Restore', str(subclient.content))
        job = subclient.restore_in_place(paths=sublcient_content)
        self.log.info('Started %s Restore job with Job ID : %s', str(job.job_id))

        # Check Job Phase at every phase_check_interval seconds
        time.sleep(4)
        while not suspended:
            # Check job phase
            if job.status.lower() == 'running':
                # Stop Job manager service
                self.log.info(f"Stopping Service {service_name} on Commserve ")
                self.commserv_client.stop_service(service_name=service_name)
                suspended = True
            time.sleep(status_check_interval)

        self.log.info(f"Suspending job {job.job_id} in Running Phase for {wait_time}seconds")
        time.sleep(wait_time)
        # Start Job manager service
        self.log.info(f"Starting Service {service_name} on Commserve ")
        self.commserv_client.start_service(service_name=service_name)
        if job.wait_for_completion() is False:
            raise Exception(
                'Failed to run {0} Restore job with error {0}'.format(job.delay_reason)
            )

        self.log.info('Successfully finished Restore job')

    def put_job_in_queued_state(self, tc_obj, client, subclient, backup_type, wait_time=300):
        """Creates a Blackout window and runs a backup job to trigger queued state condition

            Args:
                tc_obj (object) - Testcase object
                client (object)  - Client object
                subclient (object) - Subclient object
                backup_type (string) - backuptype
                wait_time (int) - Time to wait (in seconds) before deleting blackout window and resuming jobs

            Returns:
                Runs a backup job on the given subclient, returns the Cache
        """
        cache = {}
        op_helper = OpHelper(testcase=tc_obj, entity_level=self.commcell_object, initialize_sch_helper=False)
        # Create blackout window
        start_date = (datetime.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        op_window = op_helper.testcase_rule(operations=["FULL_DATA_MANAGEMENT"], start_date=start_date)

        # Backup Phase
        self.log.info('Starting Backup Phase')
        self.log.info('Create Machine Class object')

        client_machine = Machine(machine_name=client.client_name,
                                 commcell_object=self.commcell_object)

        self.log.info('Read subclient content')
        self.log.info('Subclient Content : %s', subclient.content)

        self.log.info('Starting Subclient {0} Backup'.format(backup_type).center(20, '*'))
        time.sleep(10)
        job = subclient.backup(backup_type)
        self.log.info('Started %s backup with Job ID : %s', backup_type, str(job.job_id))
        self.log.info('Current job status (Job ID {}): {}'.format(job.job_id, job.status))

        self.log.info(f"Waiting for {wait_time}seconds before deleting blackout window and resuming job")
        time.sleep(wait_time)

        # Delete blackout window
        self.log.info("Deleting Operation Window")
        op_helper.delete(name=op_window.name)

        self.log.info('Current job status (Job ID {}): {}'.format(job.job_id, job.status))

        cache['job_id'] = str(job.job_id)
        cache['client_machine'] = client_machine

        return cache

    def aux_copy_failed_consecutively(self,
                                      client,
                                      subclient,
                                      backup_type,
                                      storage_policy_name,
                                      copy_name,
                                      wait_time=180):
        """Runs a backup job on subclient, Creates a Blackout window, Runs a aux-copy job and stops JM service mid-way
           to trigger aux-copy failed consecutively alert

            Args:
                client (object)  - Client object
                subclient (object) - Subclient object
                backup_type (string) - backuptype
                storage_policy_name (string) - Name of storage policy for Aux-Copy
                copy_name (string) - Name of secondary copy for which to run Aux-Copy
                wait_time (int) - Time to wait (in seconds) before deleting blackout window and resuming jobs

            Returns:
                Runs a backup job on the given subclient, returns the Cache
        """
        suspended = False
        service_name = "GxJobMgr(Instance001)"
        status_check_interval = 2

        # Backup Phase
        self.backup_job(client=client, subclient=subclient, backup_type=backup_type)

        # Run aux copy
        storage_policy = StoragePolicy(self.commcell_object, storage_policy_name=storage_policy_name)
        self.log.info(
            '*' * 10 + 'Starting Auxillary Copy Backup for Storage Policy {0} Copy {1}'.format(storage_policy_name,
                                                                                               copy_name) + '*' * 10)
        job = storage_policy.run_aux_copy(storage_policy_copy_name=copy_name, all_copies=False)
        self.log.info('Started Auxillary Copy Job with ID : %s', str(job.job_id))

        # Check Aux-cop Job Phase at every phase_check_interval seconds
        time.sleep(5)
        while not suspended:
            # Check job phase
            if job.status.lower() == 'waiting':
                # Stop Job manager service
                self.log.info(f"Stopping Service {service_name} on Commserve ")
                self.commserv_client.stop_service(service_name=service_name)
                suspended = True
            time.sleep(status_check_interval)

        self.log.info(f"Suspending job {job.job_id} in Waiting Phase for {wait_time}seconds")
        time.sleep(wait_time)
        # Start Job manager service
        self.log.info(f"Starting Service {service_name} on Commserve ")
        self.commserv_client.start_service(service_name=service_name)
        if job.wait_for_completion() is False:  # Exepcted as job will be killed after JM Service restart
            self.log.error('Failed to run Auxillary Copy Job with error {0}'.format(job.delay_reason))

        cache = {'job_id': str(job.job_id)}
        return cache

    def restore_job_pending_state_threshold(self, client, subclient, wait_time=240):
        """Runs a Backup Job, followed by a Restore job with wrong content paths to trigger job pending state

            Args:
                client (object)  - Client object
                subclient (object) - Subclient object
                wait_time (int) - Time to wait for Restore job in pending phase before killing the job

            Returns:
                Runs an in-place Restore job on the given subclient, stops job at running phase
                and resumes after condition trigger
        """
        # Run backup on subclient
        self.backup_job(client=client, subclient=subclient, backup_type="FULL")
        random_file_name = f'''{str(uuid.uuid4())}.txt'''
        sublcient_content = [random_file_name]

        self.log.info(f'Starting Subclient Restore for Content : {str(sublcient_content)}')
        job = subclient.restore_in_place(paths=sublcient_content)
        self.log.info('Started %s Restore job with Job ID : %s', str(job.job_id))

        # Check Job Phase at every phase_check_interval second
        self.log.info(f"Suspending job {job.job_id} in Pending Phase for {wait_time}seconds")
        time.sleep(wait_time)
        # Kill Job
        self.log.info(f"Killing restore job {job.job_id}")
        job.kill()

    def create_entities(self, testcase_obj, content=None):
        """
        Creates required entities for Custom alert rules automation
        Args:
            testcase_obj (obj) - test case object to be used for entity creation
            content (list) - List containing paths for content in created subclient

        Returns:
            (obj) --subclient object with the required entities

        """
        # Create subclient
        # Creating subclient entity on test case subclient
        self._entities = CVEntities(self.commcell_object)
        self._utility = OptionsSelector(self.commcell_object)
        ready_ma = self._utility.get_ma()
        # create disk library
        entity_inputs = {
            'target':
                {
                    'client': testcase_obj.client.client_name,
                    'agent': testcase_obj.agent.agent_name,
                    'instance': testcase_obj.instance.instance_name,
                    'backupset': testcase_obj.backupset.backupset_name,
                    'mediaagent': ready_ma
                },
            'disklibrary': {
                'name': "disklibrary_" + ready_ma,
                'mount_path': self._entities.get_mount_path(ready_ma),
                'cleanup_mount_path': True,
                'force': False,
                },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + ready_ma,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                    'force': False,
                },
            'subclient':
                {
                    'name': 'testSC' + str(testcase_obj.id),
                    'force': True
                }
        }

        if content is not None:
            entity_inputs.get("subclient")["content"] = content
        return self._entities.create(entity_inputs)

    def cleanup_entities(self, entity_map):
        """
        Cleans up created entities using an entity map dict
        Args:
            entity_map (dict)  - Created entities dict returned by entities.create()
        """
        try:
            self._entities.delete(entity_map)
        except Exception as entity_cleanup_excp:
            self.log.info(f"Encountered Exception while cleaning up entities : {entity_cleanup_excp}")
