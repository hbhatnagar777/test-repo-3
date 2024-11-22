# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()        --  initialize TestCase class

    setup             --  setup method of this testcase

    check_for_errors  --  checks for the errors in log file

    run()             --  run method of this testcase


    tear_down         -- tear down function of this testcase

    send_mail         -- method that has code for sending mail


"""

"""basic idea of the test case:
Log parsing case to find various errors as deadock/sql errors during MM and dedupe operations."""



"""input json file arguments required:

    "70327":{
            "ClientName": "Name of the media agent/commserver",
            "AdditionalClients" : "Client names / media agent names which are comma seperated"
            "AgentName":"Name of the File System",
            "logFileName" : "Log File Name in which the test case will look for errors",
            "ConfigStrings" : " Strings that act as search string in log file"
            }
  """

import os
import re
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils import mahelper
from AutomationUtils.mailer import Mailer
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Log parsing case to find various errors as deadock/sql errors during MM and dedupe operations."
        self.tcinputs = {
            "ClientName" : None,
            "AgentName":None,
            "logFileName" : None,
            "ConfigStrings" : None

        }
        self.dedup_helper = None
        self.log_file_name = None
        self.body = None
        self.config_strings = None
        self.mach_ob = None
        self.email_content = None
        self.context = None
        self.utility = None
        self.log_file_single = None
        self.client_list = []

    def setup(self):
        """Setup function of this test case"""

        self.log_file_name = self.tcinputs["logFileName"]
        self.log_file_name = self.log_file_name.split(",")

        self.utility = OptionsSelector(self.commcell)
        self.dedup_helper = mahelper.DedupeHelper(self)

        # adding additional clients to clients list if they exist
        additional_client = self.tcinputs.get('AdditionalClients')
        if additional_client:
            self.client_list = additional_client.split(",")

        # adding clients to clients list
        self.client_list.append(self.tcinputs['ClientName'])


    def check_for_errors(self):

        self.config_strings = self.tcinputs["ConfigStrings"]
        self.config_strings = self.config_strings.split(",")
        error_flag = []
        try:
            for self.client in self.client_list:
                # creating machine class object for client
                self.mach_ob = self.utility.get_machine_object(self.client)
                self.log.info(f"Machine object Created Successfully for client {self.client}.")

                # iterating through config_strings and searching for that string in specified log file
                self.log.info("*************************Validations**********************")
                for self.log_file_single in self.log_file_name:
                    self.log.info(self.log_file_single)
                    log_file = self.log_file_single
                    for idx in range(len(self.config_strings)):
                        self.log.info(
                            f"CASE {idx}: Checking  {self.config_strings[idx]}")

                        # declaring necessary variables
                        found = 0
                        matched_string = []
                        matched_line = []
                        regex = self.config_strings[idx].lower()
                        jobid = None
                        escape_regex = True
                        single_file = False
                        log_path = self.mach_ob.client_object.log_directory

                        # refreshing the client object if the log path is none to prevent Invalid Path Exception
                        for i in range(3):
                            if log_path is None:
                                self.mach_ob.client_object.refresh()
                                log_path = self.mach_ob.client_object.log_directory
                        if escape_regex:
                            self.log.info("Escaping regular expression as escape_regex is True")
                            regex = re.escape(str(regex))
                        self.log.info("Log path : {0}".format(str(log_path)))
                        if not single_file:
                            all_log_files = self.mach_ob.get_files_in_path(log_path, recurse=False)
                            self.log.info("Got files in path ")
                            log_files = [x for x in all_log_files if os.path.splitext(log_file)[0].lower() in x.lower()]
                        else:
                            log_files = [self.mach_ob.join_path(log_path, log_file)]

                        if self.mach_ob.os_info == 'UNIX':
                            logfile_index = 0
                            for log in log_files:
                                if os.path.splitext(log)[1].lower() == '.bz2':
                                    command = 'bzip2 -d %s' % (log)
                                    self.log.info("decompressing .bz2 file %s", log)
                                    exit, response, error = self.mach_ob.client_object.execute_command(command)
                                    if exit == 0:
                                        self._log.info("Successfully decompressed log file %s", log)
                                        log_files[logfile_index] = log.replace(r'.bz2', '')
                                    else:
                                        self._log.error("Failed to decompress log file %s", log)
                                logfile_index += 1

                        self.context = ""
                        # get log file versions
                        for file in log_files:
                            if found == 0:
                                lines = ""
                                self.log.info(f"Searching in the file {file}")
                                try:
                                    if os.path.splitext(file)[1].lower() not in ['.zip', '.bz2']:
                                        lines = self.mach_ob.read_file(file).lower().splitlines()
                                    if os.path.splitext(file)[1].lower() == '.zip':
                                        log_dir = self.mach_ob.join_path(self.mach_ob.client_object.install_directory,
                                                                         'Log Files')
                                        base_dir = self.mach_ob.join_path(self.mach_ob.client_object.install_directory,
                                                                          'Base')
                                        command = '"%s%sunzip" -o "%s" -d "%s"' % (base_dir, self.mach_ob.os_sep, file, log_dir)
                                        response = self.mach_ob.client_object.execute_command(command)
                                        if response[0] == 0:
                                            self._log.info('Decompressed log file %s', file)
                                            extracted_file = os.path.splitext(file)[0]
                                            lines = self.mach_ob.read_file(extracted_file).lower().splitlines()
                                        else:
                                            self._log.error('Failed to Decompress log file %s', file)

                                    if not jobid and lines:
                                        self.log.info("Searching for [{0} in file {1}]".format(regex, file))
                                        for line in lines:
                                            line = str(line)
                                            regex_check = re.search(regex, line)
                                            if regex_check:
                                                matched_line.append(line)
                                                matched_string.append(regex_check.group(0))
                                                found = 1
                                        for i, sen in enumerate(lines):
                                            if matched_string:
                                                if matched_string[0] in sen:
                                                    start_index = max(0, i - 10)
                                                    end_index = min(len(lines), i + 11)
                                                    context_lines = lines[start_index:end_index]

                                                    self.context += f"""\n\n*********************************************************************************
                                                                         String is found'{matched_string[0]}' and lines in the log file {file} are:\n\n"""
                                                    for j, context_line in enumerate(context_lines):
                                                        self.context += f" {context_line.strip()}\n"

                                    elif lines:
                                        self.log.info("""Searching for string [{0}] for job [{1}] in file [{2}]
                                                               """.format(regex, jobid, file))
                                        for line in lines:
                                            # required to change a byte stream to string
                                            line = str(line)
                                            jobid_check = re.search(" {0} ".format(str(jobid)), line)
                                            if jobid_check:
                                                regex_check = re.search(regex, line)
                                                if regex_check:
                                                    matched_line.append(line)
                                                    matched_string.append(regex_check.group(0))
                                                    found = 1
                                        for i, sen in enumerate(lines):
                                            if matched_string:
                                                if matched_string[0] in sen:
                                                    start_index = max(0, i - 10)
                                                    end_index = min(len(lines), i + 11)
                                                    context_lines = lines[start_index:end_index]

                                                    self.context += f"""\n\n*********************************************************************************
                                                                        String is found '{matched_string[0]}' and lines in the log file {file} are:\n\n"""
                                                    for j, context_line in enumerate(context_lines):
                                                        self.context += f"{context_line.strip()}\n"

                                except Exception as exp:
                                    self.log.error(f"failed due to {exp}")

                            if found:
                                count = len(matched_line)
                                self.log.info("Found {0} matching line(s)".format(str(count)))
                                found = 0

                        if matched_line:
                            self.body = self.context
                            self.log.info(f"Found: {self.config_strings[idx]}")
                            error_flag += [f"{self.config_strings[idx]}"]

                            # sending email
                            self.send_mail(idx)
                        else:
                            self.log.info("Executed ")
                            self.body = f"The string does not exist in the log file {self.log_file_single} in client machine {self.client}"
                            self.send_mail(idx)
        except Exception as exe:
            self.log.error(f"{exe}")

        if error_flag:
            # if the list is not empty then strings are present, pass the test
            # case
            self.log.info(error_flag)
            raise Exception("Testcase Passed")


    def run(self):
        """Run function of this test case"""
        try:
            self.check_for_errors()

        # handling the exception raised by check_for_errors function
        except Exception as exp:
            self.log.error(
                'TestCase passed')
            self.result_string = str(exp)

    def tear_down(self):
        "delete all the resources for this testcase"
        self.log.info("Tear down function of this test case")
        try:
            self.log.info("TearDown Complete!")
        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR: %s", exp)

    def send_mail(self,i):
        """Sends the status mail with report link"""
        header_html = f'<html><body><div id="wrap"><h2>Client Name :{self.client} and Log File name: {self.log_file_single}</h2>'
        lines = self.body.split('\n')
        if not self.context:
            email_subject = "[FAILED] - "+self.config_strings[i]+" - does not exist."
            self.email_content = f"{self.body}"
        else:
            email_subject = "[SUCCESS] - "+ self.config_strings[i]+" - exists."
            html = "<table style='border-collapse: collapse; border: 1px solid black;margin-top : 20px; margin-bottom : 20px'>\n"
            for line in lines:
                html += f"<tr'><td style='padding-top: 10px;padding-bottom : 10px'>{line}</td ></tr>\n"
            html += "</table>"
            table_html = html

            self.email_content = '{0}{1}'.format(header_html,  table_html,
                                              '</div></body></html>')

        mailer = Mailer(mailing_inputs={},commcell_object=self.commcell)
        mailer.mail(email_subject, self.email_content)
        return


