# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
This module provides the helper functions and tests for view logs page


LogsHelper:

    get_machine_log()               -   Gets list of log lines form client machine
    setup_view_logs()               -   Sets up view logs page for given log
    get_ui_log()                    -   Gets the log lines visible in current page
    validate_log_lines()            -   Validates the log lines for single log file
    validate_logs()                 -   Validates lines of all the log files given
    get_random_log_filter()         -   Generates random filter from given log file
    validate_log_filters()          -   Validates log filters are working for all given log files
"""
import os
import random
import time
from difflib import SequenceMatcher
from time import sleep
import re
from cvpysdk.commcell import Commcell
from threading import Thread
from AutomationUtils import logger
from AutomationUtils.commonutils import process_text
from AutomationUtils.constants import TEMP_DIR
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs, ViewLogsPanel
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class LogsHelper:
    """Helper file to perform logs related tests from command center"""
    test_step = TestStep()

    def __init__(self, commcell: Commcell, admin_console: AdminConsole = None, **options):
        """
        Initializes the LogsHelper class

        Args:
            commcell (Commcell)             -   Commcell sdk object
            admin_console (AdminConsole)    -   instance of AdminConsole class
            options:
                validation_delay    (int)   -   seconds delay between validations per log (default: 10)
                validations         (int)   -   number of times to validate each log (default: 2)
                ClientName          (str)   -   name of client to validate view logs for (default: commserv client)
                log_names           (str)   -   comma separated log names to validate (default: cvd.log)
                lines_lag           (str)   -   acceptable number of lines UI has not loaded yet
                log_pattern         (str)   -   regex pattern to use to parse/match valid log lines
        """
        self.ui_log_lines = None
        self.machine_log_lines = None
        self.__admin_console = admin_console
        self.__commcell = commcell
        if admin_console:
            self.__navigator = admin_console.navigator
            self.__view_logs = ViewLogs(admin_console)
            self.__servers = Servers(admin_console)
            self.__view_logs_panel = ViewLogsPanel(admin_console)
        self.log = logger.get_log()
        self.__init_params__(options)

    def __init_params__(self, options: dict) -> None:
        """
        Initializes all logs test params from options given
        """
        self.v_delay = int(options.get('validation_delay') or 30)
        self.v_count = int(options.get('validations') or 2)
        self.lag_lines = int(options.get('lines_lag') or 20)
        
        # default regex pattern for identifying log line 'threadId', 'processId', etc
        default_pattern = "^([+-]?[0-9]+)(( )|(    ))+([+-]?[0]?[xX]?[0-9A-Fa-f]+)(( )|(    ))+((1[0-2]|0?[" \
                          "1-9])/([12][0-9]|[3][01]|0?[1-9]))(( )|(    ))+(([0-2]?[0-9]):([0-5]?[0-9]):([" \
                          "0-5]?[0-9]))(( )|(    ))+([^     ]+)(( )|(    ))+(.*) "
        self.log_pattern = options.get('log_pattern') or default_pattern
        client_name = options.get('ClientName') or self.__commcell.commserv_client.name
        self.client = self.__commcell.clients.get(client_name)
        self.client_machine = Machine(self.client)
        self.log_names = [log_name.strip() for log_name in (options.get('log_names') or 'WebServer.log').split(",")]
        self.log_screenshots_path = os.path.join(TEMP_DIR, 'ui_log_screenshot')

    def get_machine_log(self, log_name: str) -> list:
        """
        Util to get list of log lines from client machine

        Args:
            log_name    (str)   -   name of log file (from log files directory)
        
        Returns:
            log_lines   (list)  -   list of all log lines in file
        """
        self.log.info(f"Collecting Machine Logs for {log_name} from {self.client.name}")
        raw_data = self.client_machine.get_log_file(log_name)
        self.machine_log_lines = str(raw_data).splitlines()
        self.log.info("Machine logs collected successfully")
        return self.machine_log_lines

    def setup_view_logs(self, log_name: str) -> None:
        """
        Sets up View Logs Page for given log name

        Args:
            log_name    (str)   -   name of log to setup view logs page for
        """
        if f'#/viewLogs?clientId={self.client.client_id}&fileName={log_name}' not in self.__admin_console.current_url():
            if not self.__admin_console.current_url().endswith('#/clientGroupDetails/all'):
                self.__navigator.navigate_to_servers()
            self.__servers.view_logs(self.client.display_name)
            self.__view_logs_panel.access_log(log_name)
            sleep(6)

            if len(self.__admin_console.browser.driver.window_handles) > 1:
                # in some cases, open in new tab is the behavior
                self.__admin_console.browser.close_current_tab()
                self.__admin_console.browser.switch_to_latest_tab()

            self.__admin_console.wait_for_completion()

    def get_ui_log(self) -> list:
        """
        Util to get list of log lines visible in UI
        """
        self.log.info("Collecting UI Logs")
        self.ui_log_lines = self.__view_logs.get_log_data()
        self.log.info("Logs from current page collected successfully")
        sc_path = self.log_screenshots_path+"_" + str(time.time()).split(".")[0] + ".png"
        self.log.info(f"Saving screenshot (in case of error) -> {sc_path}")
        self.__admin_console.driver.save_screenshot(sc_path)
        return self.ui_log_lines

    @test_step
    def validate_log_lines(self, log_name: str) -> None:
        """
        Validates log lines are matching for given log file (w.r.t initialized test params)

        Args:
            log_name    (str)   -   name of log file to validate
        """
        self.log.info(f"Validating Log Lines for {log_name}")
        self.setup_view_logs(log_name)
        ui_thread = Thread(target=self.get_ui_log)
        machine_thread = Thread(target=self.get_machine_log, args=(log_name,))
        ui_thread.start()
        machine_thread.start()
        ui_thread.join()
        machine_thread.join()

        if not self.ui_log_lines:
            raise CVTestStepFailure("Failed to ready UI logs! Check if ViewLogs get_log_data works!")
        self.ui_log_lines = [process_text(line.strip()) for line in self.ui_log_lines]
        self.machine_log_lines = [process_text(line.strip()) for line in self.machine_log_lines]

        # WRITE BOTH LOG LINES INTO FILES FOR DEBUGGING PURPOSE
        with open(os.path.join(TEMP_DIR, 'validate_logs_ui_lines.txt'), 'w', encoding='utf-8') as f:
            for line in self.ui_log_lines:
                f.write(line + '\n')
        with open(os.path.join(TEMP_DIR, 'validate_logs_machine_lines.txt'), 'w', encoding='utf-8') as mf:
            for line in self.machine_log_lines:
                mf.write(line + '\n')

        matching_blocks = SequenceMatcher(
            a=self.machine_log_lines, b=self.ui_log_lines, autojunk=False
        ).get_matching_blocks()[:-1]
        self.log.info("Got sequence matcher results: machine blocks [a is machine logs, b is ui logs] := ")
        for block in matching_blocks:
            self.log.info(str(block))
        if len(matching_blocks) != 1:
            self.log.error("Did not get clean single block match! some lines messed up in UI maybe")
            self.log.error(
                "All UI Logs:\n" + "\n".join([
                    f"\n{idx} | {line}" for idx, line in
                    enumerate(self.ui_log_lines)
                ])
            )
            if len(matching_blocks) < 4:  # allow few mismatches
                unmatched_ui_blocks = []
                for block1, block2 in zip(matching_blocks[:-1], matching_blocks[1:]):
                    unmatched_ui_blocks.append((block1.b + block1.size + 1, block2.b - (block1.b + block1.size)))
                self.log.error(f"Unmatched line blocks in UI -> {unmatched_ui_blocks}")
                if all([ui_block[1] < 4 for ui_block in unmatched_ui_blocks]):  # if all unmatched blocks are small
                    if max([block.size for block in matching_blocks]) > 40:  # if main chunk of logs is large
                        # if there is a big match and just tiny erroneous lines around it, we can forgive
                        self.log.warn("Excepting this error as there is a main log chunk and only few small errors")
                    else:
                        raise CVTestStepFailure("Main chunk matched less than 40 lines, and stil has broken fragments!")
                else:
                    raise CVTestStepFailure("Some unmatched sections are more than 3 line errors, cant ignore this!")
            else:
                self.log.error("That's too many broken log fragments not rendered, cannot except this much mismatch")
                raise CVTestStepFailure("Too Many Broken log blocks in UI mismatch with Machine Logs!")
        machine_log_start, ui_log_start, length = matching_blocks[0]
        lagging_lines = len(self.machine_log_lines) - (machine_log_start + length)
        self.log.info(f'Got matched sequence length: {length}')
        self.log.info(f'Got yet to update, lagging lines: {lagging_lines}')
        if lagging_lines > self.lag_lines:
            self.log.error(f"There are {lagging_lines} lines lagging behind actual log lines in UI")
            self.log.error("Last 10 Machine Logs:")
            for log_line in self.machine_log_lines[-10:]:
                self.log.error(log_line)
            self.log.error("All UI Logs:")
            for log_line in self.ui_log_lines:
                self.log.error(log_line)
            raise CVTestStepFailure("Failed to Validate Logs! Too many lagging lines not updated!")
        self.log.info("LOG VALIDATED!")

    @test_step
    def validate_logs(self) -> None:
        """
        Validates lines for all logs given (w.r.t initialized test params and log names)
        """
        for log_name in self.log_names:
            for _ in range(self.v_count):
                self.validate_log_lines(log_name)
                self.log.info(f"sleeping for {self.v_delay} seconds")
                sleep(self.v_delay)
        self.log.info("ALL LOGS SUCCESSFULLY VALIDATED!")

    def get_random_log_filter(self) -> dict:
        """
        Util to get random thread ID, process ID and strings for include and exclude filter

        Returns:
            random_filter   (dict)  -   dict with keys threadId, processId, includeString, excludeString
                                        and random values correspoding to them
        """
        random_line = random.choice(self.machine_log_lines)
        match_obj = re.match(self.log_pattern, random_line)
        for attempt in range(30):
            if match_obj:
                break
            random_line = random.choice(self.machine_log_lines)
            match_obj = re.match(self.log_pattern, random_line)
            if attempt == 29:
                self.log.error("Cannot find valid log line even after 30 attempts!")
                raise CVTestCaseInitFailure("Could not get log line filter params")
        self.log.info("generating filters from random log line:")
        self.log.info(random_line)
        search_filters = [x for x in match_obj.groups() if x and x != ' ']
        search_string = [x.strip() for x in search_filters[-1].split(" ") if len(x) > 2]
        log_filter = {
            'processId': search_filters[0],
            'threadId': search_filters[1],
            'includeString': random.choice(search_string),
            'excludeString': random.choice(search_string)
        }
        self.log.info(f"Generated random filter: {log_filter}")
        return log_filter

    @test_step
    def validate_log_filters(self, pause=True) -> None:
        """
        Validates filters for all given log files (w.r.t initialized test params)

        Args:
            pause   (bool)  -   if True, pauses the logs before applying filters and testing
        """
        for log_name in self.log_names:
            self.setup_view_logs(log_name)
            self.__view_logs.load_complete_file()
            self.get_machine_log(log_name)
            if pause:
                self.__view_logs.pause_logs()
            for _ in range(self.v_count):
                test_filters = self.get_random_log_filter()
                failed_lines = {}
                for filter_name, filter_value in test_filters.items():
                    set_filter = test_filters.copy()
                    for filter_k in set_filter:
                        if filter_k != filter_name:
                            set_filter[filter_k] = None
                    self.__view_logs.set_filters(set_filter, True)
                    filter_readable = f"{filter_name}->{filter_value}"
                    log_lines = self.__view_logs.get_log_data()
                    # process log lines, ignore empty lines
                    empty_lines_ratio = len([line for line in log_lines if line.strip() == '']) / len(log_lines)
                    if empty_lines_ratio > 0.5:
                        self.log.error(f"TOO MANY EMPTY LINES TO IGNORE AFTER {filter_readable}! SEE BELOW...")
                        for line in log_lines:
                            self.log.error(line)
                        raise CVTestStepFailure("Too many empty lines showed up in filter to ignore")
                    if filter_name == 'excludeString':
                        failed_lines[filter_readable] = [
                            line for line in log_lines if filter_value.lower() in line.lower()
                        ]
                    else:
                        failed_lines[filter_readable] = [
                            line for line in log_lines if filter_value.lower() not in line.lower()
                        ]
                for failed_filter in failed_lines:
                    self.log.info(f"Failed lines for filter | {failed_filter} :-")
                    if len(failed_lines[failed_filter]) == 0:
                        self.log.error("None, all lines filtered successfully!")
                    for line in failed_lines[failed_filter]:
                        self.log.error(line)
                    if len(failed_lines[failed_filter]) > self.lag_lines:
                        raise CVTestStepFailure(f"filter failed on lines beyond acceptable limit {self.lag_lines}")
                    else:
                        self.log.error("Skipping as failed lines are within acceptable limit")
        self.log.info("ALL LOG FILTERS VALIDATED!")
