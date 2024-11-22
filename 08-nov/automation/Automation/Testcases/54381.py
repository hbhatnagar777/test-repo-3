# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case
"""

import re
import os
import zipfile
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Case to print Clients, Storage policies"
        self.tcinputs = {
            "StoragePolicy": None,
            "StoragePolicyCopy": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.cs_machine = Machine(self.commcell.commserv_name, self.commcell)

    def parse_log(self,
                  client,
                  log_file,
                  regex,
                  jobid=None):
        """
                This function parses the log file in the specified location based on
        the given job id and pattern

        Args:
            client  (str)   --  MA/Client Name on which log is to be parsed

            log_file (str)  --  Name of log file to be parsed

            regex   (str)   --  Pattern to be searched for in the log file

            jobid   (str)   --  job id of the job within the pattern to be searched

        Returns:
           (tuple) --  Result of string searched on all log files of a file name
        """
        found = 0
        matched_string = []
        matched_line = []
        self.client_machine = Machine(client, self.commcell)
        log_path = self.client_machine.client_object.log_directory
        self.log.info("Log path: {0}".format(log_path))
        all_log_files = self.client_machine.get_files_in_path(log_path)
        regex = re.escape(regex)
        self.log.info("Got files in path")
        log_files = [x for x in all_log_files if os.path.splitext(log_file)[0] in x]
        if self.client_machine.os_info == 'UNIX':
            for log in log_files:
                if not jobid:
                    jobid = ''
                command = 'bzgrep "{0}" {1}| grep "{2}"'.format(regex, log, jobid)
                exit1, response, error = self.client_machine.client_object.execute_command(command)
                if exit1 == 0:
                    found = 1
                    matched_line = response.split("\n")
                    matched_string = regex
                else:
                    self.log.info(response)
        else:

            # get log file versions
            for file in log_files:
                self.log.info(file)
                if found == 0:
                    if os.path.splitext(file)[1].lower() is not '.zip':
                        # fh = open(file, encoding="ISO-8859-1")
                        # lines = fh.readlines()
                        lines_str = self.client_machine.read_file(file, search_term=regex)
                        lines = lines_str.split('\n')
                    else:
                        zip_files = zipfile.ZipFile(file)
                        fh = zip_files.open(zip_files.namelist()[0])
                        lines = fh.readlines()
                    if not jobid:
                        self.log.info("Searching for [{0} in file {1}]".format(regex, file))
                        for line in lines:
                            regex_check = re.search(regex, line)
                            if regex_check:
                                matched_line.append(line)
                                matched_string.append(regex_check.group(0))
                                found = 1
                    else:
                        self.log.info("""Searching for string [{0}] for job [{1}] in file [{2}]
                                               """.format(regex, jobid, file))
                        for line in lines:
                            jobid_check = re.search(" {0} ".format(str(jobid)), line)
                            if jobid_check:
                                regex_check = re.search(regex, line)
                                if regex_check:
                                    matched_line.append(line)
                                    matched_string.append(regex_check.group(0))
                                    found = 1
                    # fh.close()
        if found:
            count = len(matched_line)
            self.log.info("Found {0} matching line(s)".format(str(count)))
            return matched_line, matched_string
        else:
            self.log.error("Not found!")
            return None, None

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info("""Running DDB Verification job on {0}
                            """.format(self.tcinputs["StoragePolicy"]))
            sp = self.commcell.storage_policies.get(self.tcinputs["StoragePolicy"])
            job = sp.run_ddb_verification(self.tcinputs["StoragePolicyCopy"],
                                          'Full',
                                          'DDB_VERIFICATION')
            self.log.info("DDB Verification job: " + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run DDB Verification Job: {0}".format(job.delay_reason)
                )
            # listing all the datamovers MAs initiated
            log_file = r'AuxCopyMgr.log'
            log_line = r'Started AuxCopy process on mediaAgent'

            (matched_line, matched_string) = self.parse_log(
                self.commcell.commserv_name,
                log_file,
                log_line,
                job.job_id)

            malist = []
            for line in matched_line:
                self.log.info(line)
                result = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                malist += [result]
            self.log.info(malist)
            chunkinfo = []
            mpid_list = []
            volid_list = []
            chunkid_list = []

            # checking if the mountpaths are local to MA
            for ma in malist:

                # collecting all the chunks verified by each MA
                log_file = r'DataVerf.log'
                log_line = r'Going to validate Sfile for chnk'

                (matched_line, matched_string) = self.parse_log(ma, log_file, log_line, job.job_id)

                for line in matched_line:
                    self.log.info(line)
                    result = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                    chunkinfo += [result]

                split = []

                for chunks in chunkinfo:
                    split = re.split(',', chunks)
                    mpid_list += [split[0]]
                    volid_list += [split[1].strip()]
                    chunkid_list += [split[2].strip()]

                for mp in mpid_list:

                    query = """SELECT MMDC.DeviceAccessType &(16|32|128) DeviceType
                    FROM MMMountPath MMM, MMMountpathToStorageDevice MMMTS,
                    MMDeviceController MMDC, App_Client AC
                    WHERE MMM.MountPathid = MMMTS.MountPathid 
                    AND MMMTS.Deviceid = MMDC.Deviceid AND MMDC.clientid = AC.id 
                    AND MMM.MountPathId = {0} AND AC.name = '{1}'""".format(mp, ma)
                    query_result = self.mmhelper.execute_select_query(query)
                    self.log.info(query_result[0][0])
                    if query_result[0][0] == '0':
                        query = """SELECT MMDC.folder FROM MMMountPath MMM,
                        MMMountpathToStorageDevice MMMTS, MMDeviceController MMDC, App_Client AC 
                        WHERE MMM.MountPathid = MMMTS.MountPathid AND MMMTS.Deviceid=MMDC.Deviceid 
                        AND MMDC.clientid=AC.id AND MMM.MountPathId = {0}
                        AND AC.name = '{1}'""".format(mp, ma)
                        query_result = self.mmhelper.execute_select_query(query)
                        self.log.info(query_result[0][0])
                        if query_result[0][0].startswith("\\"):
                            self.log.info("Path is UNC")
                            # checking if the path is local to any other ma
                            query = """SELECT count (MMDC.Folder) folder FROM MMMountPath MMM,
                            MMMountpathToStorageDevice MMMTS, MMDeviceController MMDC,App_Client AC
                            WHERE MMM.MountPathid = MMMTS.MountPathid
                            AND MMMTS.Deviceid=MMDC.Deviceid AND MMDC.clientid=AC.id 
                            AND MMM.MountPathId in {0}
                            AND MMDC.DeviceAccessType & (16|32|128) not in (16,32,128) 
                            AND MMDC.Folder not like '\\%' """.format(mp)
                            query_result = self.mmhelper.execute_select_query(query)
                            if query_result[0][0] != '0':
                                self.log.info("MP is local to another MA")
                                self.log.error("MP Affinity not verified")
                            else:
                                self.log.info("MP is not local to any other MA")
                                self.log.info("MP Affinity verified")

                        else:
                            self.log.info("Path is Local")
                            self.log.info("MP Affinity verified")
                    else:
                        self.log.info("MP is Data Server IP")
                        self.log.error("MP Affinity not verified")

            self.log.info(mpid_list)
            self.log.info(volid_list)
            self.log.info(chunkid_list)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
