# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""
import os
import time
from cvpysdk.client import Client
from Server.DisasterRecovery import drhelper
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.wrapper7z import Wrapper7Z
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Advanced DR options- """

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "DR backup with DBCC log values"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = False
        self.tcinputs = {

            "SqlSaPassword": None,
            "NewDRPath": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            regroot = r"Database"
            regkey = "nMinDBLogUsage"
            filetoinclude = ['Install.log', 'EvMgrS.log']
            clients = []
            client = Client(self.commcell, self.commcell.commserv_name)
            client_machine = WindowsMachine(client.client_name, self.commcell)
            clientlist = self.commcell.clients

            if "NewDRPath" in self.tcinputs and self.tcinputs["NewDRPath"]:
                newpath = self.tcinputs["NewDRPath"]
            else:
                newpath = os.path.join(client.install_directory[0], "\\Automation",
                                       "NewDRPath")

            for key in clientlist.all_clients.keys():
                clients.append(key)
                if len(clients) >= 2:
                    break

            def getdbccvalues():
                dbccquery = "DBCC SQLPERF (LOGSPACE)"
                logspace = {}
                values = drhelperobject.executecvquery(dbccquery)

                for dblog in values.rows:
                    if dblog[0].lower() == 'commserv':
                        if int(dblog[2]) >= 30:
                            logspace['commserv'] = [dblog[2], True]
                        else:
                            logspace['commserv'] = [dblog[2], False]

                    elif dblog[0].lower() == 'historydb':
                        logspace['historydb'] = dblog[2]
                        if int(dblog[2]) >= 30:
                            logspace['historydb'] = [dblog[2], True]
                        else:
                            logspace['historydb'] = [dblog[2], False]

                    elif dblog[0].lower() == 'wfengine':
                        logspace['wfengine'] = dblog[2]

                        if int(dblog[2]) >= 30:
                            logspace['wfengine'] = [dblog[2], True]
                        else:
                            logspace['wfengine'] = [dblog[2], False]
                    else:
                        continue
                return logspace

            drobject = self.commcell.disasterrecovery
            drobject.client_list = clients
            drhelperobject = drhelper.DRHelper(
                self.commcell, self._log, self.tcinputs, killdrjobs=True)

            initialdrpath = drhelperobject.drpath
            logspace = getdbccvalues()
            self._log.info("Move all databases to Recovery FULL")

            for data in logspace.keys():
                query = "ALTER DATABASE {} SET RECOVERY FULL".format(data)
                self._log.info(
                    "query used to alter the database {}".format(query))
                drhelperobject.executecvquery(query)

            drhelperobject.client_machine = client_machine
            self._log.info(
                "Run DR backup only with CommservDB and sendlogfiles")

            for log in filetoinclude:
                drhelperobject.wildcards = drhelperobject.wildcards + \
                    log.replace(".log", "") + ";"

            self._log.info(
                "Changing wild card to {}".format(
                    drhelperobject.wildcards))
            drhelperobject.changedrsettings()

            drobject.backup_type = 'full'
            drobject.ishistorydb = False
            drobject.isworkflowdb = False
            drobject.advbackup = True
            fulldrjob = drobject.disaster_recovery_backup()
            backuplevel = fulldrjob.backup_level

            if not backuplevel.lower().find("full") >= 0:
                self._log.error(
                    "DR backup job type is not full , please check the type job id {},\
                current job type is {} ".format(str(fulldrjob), backuplevel))
                self.status = constants.FAILED
                return
            else:
                self._log.info("Started DR backup job")

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, fulldrjob.delay_reason
                    )
                )

            drobject.validate = False
            drhelperobject.drjob = fulldrjob
            drhelperobject.validateset_folder()
            self._log.info("set_folder is " + drhelperobject.set_folder)
            drdir = drhelperobject.set_folder
            zipfound = False
            logfound = False

            for i in range(2):
                set_folderlist = client_machine.get_folder_or_file_names(
                    drdir, True)
                set_folderlist = ' '.join(
                    set_folderlist.splitlines()).split()[2:]
                sendlogfilelist = []

                for file in set_folderlist:
                    if file.lower().find(".7z") >= 0:
                        sendlogfilelist.append(os.path.join(drdir, file))
                        zipfound = True

                for zipfile in sendlogfilelist:
                    zipobject = Wrapper7Z(
                        self.commcell, client, self._log, zipfile)
                    zipobject.extract()
                    drdir = zipfile.replace(".7z", "")

                    if i == 1:
                        files = client_machine.get_folder_or_file_names(
                            drdir, True)

                        for logfile in filetoinclude:
                            if logfile in files:
                                logfound = True
                                self._log.info(
                                    "{} is available in {}".format(
                                        logfile, drdir))
                            else:
                                raise Exception(
                                    "{} is not available in {}".format(
                                        logfile, drdir))

            if not zipfound:
                raise Exception(
                    ".7z file is not generated in {} ".format(drdir))

            if not logfound:
                raise Exception("log files not generated in {}".format(drdir))

            drobject.drjob = fulldrjob
            drobject.validate = True
            drobject.ignore_list = ["historydb", "wfengine"]
            drhelperobject.validateset_folder()
            highloglevel = True

            for i in range(5):

                if i == 0:
                    drobject.ishistorydb = True
                    drobject.isworkflowdb = False
                    drobject.ignore_list = ["wfengine"]
                    self._log.info(
                        "Run DR backup with history DB and sendlogfiles")

                elif i == 1:
                    drobject.isworkflowdb = True
                    drobject.ishistorydb = False
                    drobject.ignore_list = ["historydb"]
                    self._log.info(
                        "Run DR backup with workflowDB and sendlogfiles")

                elif i == 2:
                    drobject.isworkflowdb = True
                    drobject.ishistorydb = True
                    drobject.ignore_list = []
                    self._log.info(
                        "Run DR backup with all databases and sendlogfiles")

                elif i == 3:
                    drobject.drpath = newpath
                    drhelperobject.changedrsettings()
                    self._log.info(
                        "Run DR backup with new DR path %s" %
                        newpath)

                else:
                    highloglevel = False
                    drobject.isworkflowdb = True
                    drobject.ishistorydb = True

                    for data in logspace.keys():

                        if int(logspace[data][0]) < 30:
                            continue
                        else:
                            if not highloglevel:
                                try:
                                    retcode = client_machine.remove_registry(
                                        regroot, regkey)
                                except BaseException:
                                    self._log.error(
                                        "Failed to remove registry key")
                                self._log.info(
                                    "DB {} with high log level with value {}"
                                    .format(data, str(logspace[data][0])))

                                self._log.info("Verify DR backup with high log level with\
                                 Registry key {0} with value {1}".format(regkey, str(1)))
                                retcode = client_machine.create_registry(
                                    regroot, regkey, 30, reg_type="DWord")

                                if retcode:
                                    self._log.info(
                                        "Created Registry key {0} with value {1}".format(
                                            regkey, str(30)))
                                else:
                                    self._log.error(
                                        "Failed to create Registry key {0} with value {1}".format(
                                            regkey, str(30)))
                                    self.status = constants.FAILED
                                    return

                            highloglevel = True
                            time.sleep(10)

                if highloglevel:
                    drobject.backup_type = 'differential'
                    drobject.advbackup = True
                    diffdrjob = drobject.disaster_recovery_backup()
                    time.sleep(10)
                    drhelperobject.drjob = diffdrjob

                    if not diffdrjob.wait_for_completion():
                        raise Exception(
                            "Failed to run {0} backup job with error: {1}".format(
                                drobject.backup_type, diffdrjob.delay_reason))

                    job_summary = diffdrjob.summary
                    backuplevel = (job_summary['backupLevelName'])

                    if not backuplevel.lower().find("full") >= 0:
                        self._log.error("DR backup job type is not full , please check the type\
                         job id {}, current job type is {} ".format(str(diffdrjob), backuplevel))
                        self.status = constants.FAILED
                        return
                    else:
                        self._log.info(
                            "Differential DR backup job  is converted to Full")

                if i < 4:
                    drhelperobject.validateset_folder()

                if i == 4 and highloglevel:
                    drhelperobject.validateset_folder()
                    newlogspace = getdbccvalues()

                    for data in newlogspace.keys():
                        if int(newlogspace[data][0]) <= 30:
                            continue
                        else:
                            highloglevel = False

                    if highloglevel:
                        self._log.info("None of db log levels are more than 30, OLD Db log sizes\
                         are {} and new DB log sizes are {}".format(logspace, newlogspace))
                    else:
                        self._log.error("One of the DB log size is more than value 30.Old Db log\
                         sizes are {} and new DB log sizes are {}".format(logspace, newlogspace))
                        raise Exception(
                            "One of the DB log size is more than value 30")

            for log in filetoinclude:
                drhelperobject.wildcards.replace(
                    log.replace(".log", "") + ";", "")

            self._log.info(
                "Changing wild card to {}".format(
                    drhelperobject.wildcards))
            drhelperobject.changedrsettings()
            self._log.info(
                "add code to validate sendlog files folder with different wildcards")
        except Exception as exp:
            self._log.error('Failed with error: {}'.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                drhelperobject.drpath = initialdrpath
                drhelperobject.changedrsettings()
                retcode = client_machine.create_registry(
                    regroot, regkey, 99, reg_type="DWord")

                if retcode:
                    self._log.info(
                        "Created Registry key {0} with value {1}".format(
                            regkey, str(99)))
                else:
                    self._log.error(
                        "Failed to create Registry key {0} with value {1}".format(
                            regkey, str(99)))

                retcode = client_machine.remove_registry(regroot, regkey)
            except BaseException:
                self._log.error("Failed to remove registry key")
