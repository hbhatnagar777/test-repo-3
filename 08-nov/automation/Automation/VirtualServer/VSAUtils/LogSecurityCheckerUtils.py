# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for validating logs for security by searching for sensitive information.

classes defined:

    Base class:

        LogSecurityChecker              -   Class for validating logs for security by searching for sensitive information.

    Methods:
        convert_utc_to_machine_time()   -   Converts a UTC datetime to the local time of the machine.
        get_client_machine_obj()        -   Retrieves the Machine object for a given client.
        get_client_machine_log_files()  -   Retrieves log files from the client's machine.
        search_log_lines()              -   Searches log lines for specified literals and regex patterns.
        validate_logs_for_security()    -   Validates logs for security by searching for sensitive information.
    
"""

from datetime import datetime, timezone
import os, re
from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from typing import List, Dict, Optional

CONFIG = get_config()


class LogSecurityChecker:
    def __init__(self, commcell):
        """
        Initializes the LogSecurityChecker class.

        Args:
            commcell (Commcell): The Commcell object.
        """
        self.commcell = commcell
        self.log = logger.get_log()
        self.regex_patterns = ""
        self.key_words = []
        if hasattr(CONFIG, "LogSecurityChecker"):
            if hasattr(CONFIG.LogSecurityChecker, 'KeyWords'):
                self.key_words = eval(CONFIG.LogSecurityChecker.KeyWords)
            if hasattr(CONFIG.LogSecurityChecker, 'RegexPattern'):
                self.regex_patterns = CONFIG.LogSecurityChecker.RegexPattern

    @staticmethod
    def convert_utc_to_machine_time(machine_obj: Machine, utc_date_time: datetime) -> str:
        """
        Converts a UTC datetime to the local time of the machine.

        Args:
            machine_obj (Machine): The Machine object representing the target machine.
            utc_date_time (datetime): The local time as a formatted string in the format "%m/%d %H:%M:%S".

        Returns:
            str: The local time as a formatted string.
        """
        machine_zone_time = machine_obj.current_localtime()
        current_utc_time = datetime.now(timezone.utc)
        local_delta = machine_zone_time - current_utc_time.replace(tzinfo=None)
        local_time = utc_date_time + local_delta
        return datetime.strftime(local_time, "%m/%d %H:%M:%S")

    @staticmethod
    def get_client_machine_log_files(machine_obj: Machine, log_directory: Optional[str] = None, **kwargs) -> List[str]:
        """
        Retrieves log files from the client's machine.

        Args:
            machine_obj (Machine): The Machine object representing the client's machine.
            log_directory (str, optional): The directory to search for log files. Defaults to the Commvault log directory.
            **kwargs: Additional keyword arguments.

        Supported kwargs:
            exclude_files (list): List of file names to exclude from the search.
            all_version (bool): If True, include all versions of log files, including rolled over logs and those files which are not yet zipped.

        Returns:
            list: A list of filtered log files.
        """
        log_directory = log_directory if log_directory else machine_obj.client_object.log_directory
        exclude_files = kwargs.get("exclude_files", [])
        filter_regex = r".*\.log.+" if kwargs.get('all_version', False) else r".*\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}\.log.*|.*\.log.+"
        all_files = machine_obj.get_files_in_path(log_directory, recurse=False)
        return [file for file in all_files if not re.search(filter_regex, os.path.basename(file)) and os.path.basename(file) not in exclude_files]
        
    @staticmethod
    def search_log_lines(log_lines: List[str], literals: Optional[List[str]] = None, regex_patterns: Optional[List[str]] = None) -> List[Dict[str, List[str]]]:
        """
        Searches log lines for specified literals and regex patterns.

        Args:
            log_lines (list): The log lines to search.
            literals (list, optional): The literals to search for. Defaults to None.
            regex_patterns (list, optional): The regex patterns to search for. Defaults to None.

        Returns:
            list: A list of dictionaries containing matched log lines and words.
        """
        exposed_logs = []
        compiled_literal_regex = re.compile('|'.join(re.escape(literal) for literal in literals if literal)) if literals else None
        compiled_regex = re.compile('|'.join(filter(None, regex_patterns))) if regex_patterns else None

        for line in log_lines:
            matched_words = []
            if compiled_literal_regex:
                matched_words.extend(compiled_literal_regex.findall(line))
            if compiled_regex:
                matched_words.extend(compiled_regex.findall(line))
            if matched_words:
                exposed_logs.append({'log': line, 'matched_words': matched_words})

        return exposed_logs
    
    def get_client_machine_obj(self, client_name: str) -> Machine:
        """
        Retrieves the Machine object for a given client.

        Args:
            client_name (str): The name of the client.

        Returns:
            Machine: The Machine object for the client.
        """
        client = self.commcell.clients.get(client_name)
        return Machine(client)

    def validate_logs_for_security(self, client_list: List[str], start_time: datetime, end_time: Optional[datetime] = "", **kwargs) -> None:
        """
        Validates logs for security by searching for sensitive information.

        Args:
            client_list (list): The list of clients to validate logs for.
            start_time (datetime): The start time for log validation in UTC.
            end_time (datetime, optional): The end time for log validation in UTC. Defaults to the current time if not specified.
            **kwargs: Additional keyword arguments.

        Supported kwargs:
            literals (list): List of literals to search for in the logs.
            regex_patterns (list): List of regex patterns to search for in the logs.
            exclude_files (list): List of file names to exclude from the search.

        Raises:
            Exception: If sensitive information is found in the logs.
        """
        validation_status = True
        literals = kwargs.get('literals', [])
        regex_patterns = kwargs.get('regex_patterns', [])
        exclude_files = kwargs.get('exclude_files', [])
        literals.extend(self.key_words)
        regex_patterns.extend([self.regex_patterns])

        if not literals and not regex_patterns:
            self.log.error("No literals or regex pattern found for validation. "
                           "Please provide a literal or regex or set it in the config file")
            return

        for client in client_list:
            self.log.info(f"Verifying logs for client {client}")
            machine_obj = self.get_client_machine_obj(client)
            machine_zone_start_time = self.convert_utc_to_machine_time(machine_obj, start_time)
            machine_zone_end_time = self.convert_utc_to_machine_time(machine_obj, end_time) if end_time else ""

            filtered_files = self.get_client_machine_log_files(machine_obj, exclude_files=exclude_files)
            for file in filtered_files:
                filtered_content = machine_obj.get_time_range_logs(file, machine_zone_start_time, machine_zone_end_time)
                log_lines = filtered_content.splitlines()
                exposed_log_lines = self.search_log_lines(log_lines, literals, regex_patterns)
                if exposed_log_lines:
                    self.log.info(f"Sensitive information found in log file: {os.path.basename(file)}")
                    self.log.info(exposed_log_lines)
                    validation_status = False

        if not validation_status:
            self.log.error("Sensitive information found in logs. Please check.")
            raise Exception("Sensitive information found in logs. Log check validation failed.")