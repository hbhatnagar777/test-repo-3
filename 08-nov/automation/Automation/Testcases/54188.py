# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
import time
import matplotlib.pyplot as plt
import pandas as pd
from cvpysdk.job import Job, JobController
from AutomationUtils import logger, constants, database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.mailer import Mailer
from Server.Scheduler import schedulerhelper
from Server import serverhelper
from Server.JobManager.jobmanager_helper import JobManager
from Laptop.laptophelper import LaptopHelper
from FileSystem.FSUtils.fshelper import  FSHelper
class TestCase(CVTestCase):
    '''feature description
    Gets the cpu performance counters when prescan , filescan and clbackup is running in given
    interval of time for given totaltime
    '''
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "CPU usage validation for prescan,filescan,clbackup"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.DATAPROTECTION
        self.tcinputs = {
            "StoragePolicyName": None,
            "receiver": None,
            }
        self.helper = None
        self.runid = None
        self._entities = None
        self._schedule_creator = None
        self.cs_machine_obj = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None
        self.storage_policy = None
        self.sqlusername = None
        self.sqlpassword = None
    def setup(self):
        """Setup function of this test case"""
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def getrecentbatchnumber(self):
        """Gets the recent batch number from DB """

        self._csdb = self.getCommserveDbObject(self.sql_username, self.sql_password, self.commservename, "cpuperformance")
        sql = '''select OSINFO as OS,ServicePack,Process,max(batchno) BatchNo
                from perf group by osinfo,servicepack,process'''
        response = self._csdb.execute(sql)
        df = pd.DataFrame(columns=['ServicePack', 'Process', 'OS', 'BatchNo'])
        for row in response.rows:
            df = df.append({'ServicePack':row.get('ServicePack'), 'Process':row.get('Process'),
                            'OS':row.get('OS'), 'BatchNo':row.get('BatchNo')}, ignore_index=True)
        #df=int(df.query('process=="'+process+'" and servicepack=="'+servicepack+'" and os=="'+osinfo+'"')['batchno'])
        return df#['BatchNo']==0 if df.empty else df

    def parseoutputfiles(self, machine, output_path, service_pack):
        """PArses the output files and return it in a data frame """
        files_list = machine.get_items_list(data_path=output_path)
        self.log.info(files_list)
        if output_path in files_list:
            files_list.remove(output_path)
        final_df = pd.DataFrame(columns=['DateTimeStamp', 'CPU', 'ServicePack', 'Process', 'OS'])

        batchno_df = self.getrecentbatchnumber()
        for file in files_list:
            content = machine.read_file(file)
            content = content.split('\n')
            os_info = None
            if machine.os_info == 'WINDOWS':
                content.pop(0)
            else:
                os_info == 'MAC'
            os_info = machine.os_info
            for line in content:
                line = line.replace('"', '')
                line = line.replace("\r", '')
                self.log.info(line)
                if line != ' ' and line != '':
                    if line.split(',')[1].replace('\n', '') != '0' and line.split(',')[1].replace('\n', '') != '0.0' and line.split(',')[1].replace('\n', '') != ' ':
                        self.log.info(line)
                        datetimestamp = line.split(',')[0]
                        proc = file.split('-')[3].replace('.csv', '')
                        cpu = float(line.split(',')[1].replace('\n', ''))
                        self.log.info(batchno_df)

                        if batchno_df.query('Process=="'+proc+'" and ServicePack=="'+service_pack+'" and OS=="'+os_info+'"')['BatchNo'].empty:
                            batchno = 1
                        else:
                            batchno = int(batchno_df.query('Process=="'+proc+'" and ServicePack=="'+service_pack+'" and OS=="'+os_info+'"')['BatchNo'])+1
                        final_df = final_df.append({'DateTimeStamp':datetimestamp, 'CPU':cpu, 'ServicePack':service_pack,
                                                   'Process':proc, 'OS':os_info, 'BatchNo':batchno}, ignore_index=True)
                        self.log.info(batchno)
        self.log.info(final_df)
        return final_df

    def getCommserveDbObject(self, username, password, commservename, instancedb):
        """Gives the MSSQL connection object """
        CS_DB_server = "{}\COMMVAULT".format(commservename)
        self.log.info("Connecting to CS DB")

        self._csdb = database_helper.MSSQL(CS_DB_server, username, password, instancedb)

        self.log.info("Connection to CS DB is established")
        return self._csdb

    def updateperfintoDb(self, final_df, client_name, osinfo):
        """it will updates the perf counters into DB """
        self._csdb = self.getCommserveDbObject(self.sql_username, self.sql_password, self.commservename, "CommServ")
        query = "SELECT name FROM master.sys.databases"
        response = self._csdb.execute(query)
        self.log.info(response.rows)
        for row in response.rows:
            if row.get('name') == "cpuperformance":
                exists = 1
                self.log.info("DB exists")
                break
        if not exists:
            self.log.info("DB not exists and creating")
            self._csdb.execute("create database cpuperformance")

        self._csdb = self.getCommserveDbObject(self.sql_username, self.sql_password, self.commservename, "cpuperformance")
        query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG='cpuperformance'"
        response = self._csdb.execute(query)
        exists = 0
        self.log.info(response.rows)
        if response.rows:
            for row in response.rows:
                if row.get('TABLE_NAME') == "perf":
                    exists = 1
                    self.log.info("Table exists")
                    break
        if not exists:
            self.log.info("Table not exists and creating")
            self._csdb.execute('''CREATE TABLE perf
               (
                client        varchar(50)        NOT NULL,
                process      varchar(50)        NOT NULL,
                Servicepack        varchar(50)        NOT NULL,
                datetimestamp        Datetime        NOT NULL,
                cpu        FLOAT     NOT NULL,
                osinfo    varchar(50)    NOT NULL,
                BatchNo    INT    NOT NULL,
                LoadDate    Datetime    DEFAULT    getdate()
               );''')

        for row in final_df.iterrows():
            datetimestamp, CPU, servicepack, process, batchno = row[1][0], float(row[1][1]), str(row[1][2]), str(row[1][3]), int(row[1][5])
            self._csdb.execute("insert into perf VALUES('{0}','{1}','{2}','{3}',{4},'{5}','{6}')".format(str(client_name), process, servicepack, datetimestamp, CPU, str(osinfo), batchno))

    def generateplotfromdb(self, sps_to_report, file_path):
        """Gnerates plot by getting counters from DB"""

        self._csdb = self.getCommserveDbObject(self.sql_username, self.sql_password, self.commservename, "cpuperformance")
        sql = '''SELECT
                ID,SP_RANK, CPU, SERVICEPACK,PROCESS,OS,BATCHNO
                FROM
                (
                SELECT RANK()OVER(PARTITION BY PROCESS, SERVICEPACK, OSinfo ORDER BY DATETIMESTAMP) AS ID
                , DENSE_RANK()OVER(ORDER BY SERVICEPACK) AS SP_RANK
                , CAST(ROUND(CPU,0) AS INT) AS CPU, SERVICEPACK, PROCESS, osinfo AS OS,BATCHNO,
                DENSE_RANK()OVER(PARTITION BY PROCESS, SERVICEPACK, OSinfo ORDER BY BATCHNO DESC) AS BN_RANK
                 FROM perf
                ) AS A
                WHERE A.BN_RANK=1 AND A.SP_RANK<=
            '''+str(sps_to_report)+ 'ORDER by ID'
        #Passing the result set into df
        response = self._csdb.execute(sql)
        self.log.info(response.rows)

        df = pd.DataFrame(columns=['ID', 'SP_RANK', 'CPU', 'SERVICEPACK', 'PROCESS', 'OS'])

        for row in response.rows:
            df = df.append({'ID':row.get('ID'), 'SP_RANK':row.get('SP_RANK'), 'CPU':row.get('CPU'),
                            'SERVICEPACK':row.get('SERVICEPACK'), 'PROCESS':row.get('PROCESS'), 'OS':row.get('OS')}, ignore_index=True)
        #Extracting unique list of service pack values from the data
        sp_list = df.SERVICEPACK.unique()
        process_list = df.PROCESS.unique()
        df_avg = df[['SERVICEPACK', 'PROCESS', 'OS', 'CPU']]
        df_avg.CPU = df_avg.CPU.astype(float)
        df_avg.SERVICEPACK = df_avg.SERVICEPACK.astype(str)
        df_avg.PROCESS = df_avg.PROCESS.astype(str)
        df_avg.OS = df_avg.OS.astype(str)

        df_avg = df_avg.groupby(['OS', 'PROCESS', 'SERVICEPACK']).mean()
        self.log.info(df_avg)
        self.log.info(df_avg.to_html())
        items = LaptopHelper.generate_email_body(self, df)

        width, height = 24, 16
        plt.figure(figsize=(20, 10), facecolor='white', edgecolor='k')
        fig = plt.figure(frameon=False)
        fig.set_size_inches(width, height)
        colors = ['tab:blue', 'tab:orange', 'tab:red', 'tab:cyan', 'tab:brown', 'tab:pink', 'tab:green',
                  'tab:purple', 'tab:olive']
        sp_list_with_colors = []
        for sp_id in range(len(sp_list)):
            sp_list_with_colors.append((sp_list[sp_id], colors[sp_id]))
        self.log.info(sp_list_with_colors)
        for process in process_list:
            for env in ['WINDOWS', 'MAC']:
                for sp in sp_list_with_colors:
                    windows_df = df.query('PROCESS=="'+process+'" and SERVICEPACK=="'+sp[0]+'" and OS=="'+env+'"')[['ID', 'CPU']]
                    plt.xlabel('Units of Time', fontsize=30)
                    plt.ylabel('CPU Usage', fontsize=30)
                    if 'WINDOWS' in env:
                        plt.plot('ID', 'CPU', data=windows_df, marker='o', markersize=12, linewidth=5, label=sp[0]+' '+env, color=sp[1])
                    else:
                        plt.plot('ID', 'CPU', data=windows_df, marker='o', markersize=12, linewidth=5, label=sp[0]+' '+env, linestyle='dashed', color=sp[1])

            #Applying cos
            plt.xticks(fontsize=22, rotation=0)
            plt.yticks(fontsize=22, rotation=0)
            plt.title(process.upper()+"'s CPU usage across service packs", fontsize=30)
            plt.legend(fontsize=25)
            filepath = file_path + "_" + process + ".png"
            fig.savefig(filepath)
        return items

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        self.sql_username = str(self.tcinputs['sqlUsername'])
        self.sql_password = str(self.tcinputs['sqlPassword'])
        self.commservename = str(self.commcell.commserv_hostname)
        machine = Machine(client_name, self._commcell)
        server = serverhelper.ServerTestCases(self)
        self._client = self._commcell.clients.get(client_name)
        service_pack = str("sp"+self._client.service_pack)
        receiver = self.tcinputs['receiver']
        os_info = None
        try:
            # Initialize test case inputs

            self.log.info("Started executing %s testcase", str(self.id))
            from AutomationUtils.config import get_config
            laptop_config = get_config().Laptop
            client_data = laptop_config._asdict()['UserCentricClient']._asdict()
            client = client_data[machine.os_info].ClientName
            client = client_name if not client else client
            subclient_obj  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            subclient_name = "default"
            backupset_name = "defaultbackupset"
            FSHelper.populate_tc_inputs(self, False)
            test_path = self._utility.create_directory(machine)
            log.info("**STARTING RUN FOR OPTIMIZED SCAN**")
            log.info("Step2.1,Create subclient if it doesn't exist.")
            subclient_content = ['%Documents%', '%Desktop%', '%Pictures%', '%Music%']
            subclient_obj.content = subclient_content
            perfname = {"WINDOWS":"typeperf", "UNIX":"bash"}
            os_info = None
            if self.slash_format in '/':
                documentspath = "/Users/cvadmin/Documents/Inc1"
            else:
                documentspath = "C:\\Users\\admin\\Documents\\Inc1"
            self.log.info("Creatign testdata for first backup under %s", documentspath)
            self._utility.create_directory(machine, documentspath)
            machine.generate_test_data(documentspath, hlinks=False, slinks=False, sparse=False)

            if machine.os_info == "WINDOWS":
                machine.update_registry('EventManager', value='FileScan_DEBUGWAITTIME', data=20, reg_type='DWord')
                machine.update_registry('EventManager', value='clBackup_DEBUGWAITTIME', data=30, reg_type='DWord')
            else:
                machine.update_registry('EventManager', value='FileScan_DEBUGWAITTIME', data=20, reg_type='Dword')
                machine.update_registry('EventManager', value='clBackupParent_DEBUGWAITTIME', data=30, reg_type='Dword')

            logfile_to_check = ["ScanCheck.log", "FileScan.log", "clBackup.log"]
            templog_dictory = "C:\\ScanCheck_logs"
            substring = str(self.runid)
            validatelog = self.client.log_directory + self.slash_format + logfile_to_check[0]
            log.info('Creating schedule if it doesnt exists')
            sch_obj = self._schedule_creator.create_schedule(
                'subclient_backup',
                schedule_pattern={
                    'freq_type': 'automatic',
                    'min_interval_hours': 0,
                    'min_interval_minutes': 2
                },
                subclient=subclient_obj,
                backup_type="Incremental",
                wait=False)
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)

            #self.waitforactviejob()
            job_obj = JobManager.get_active_job_object(self, client)
            job_obj.wait_for_completion()
            server.rename_remove_logfile(machine, validatelog, templog_dictory, substring)
            machine.create_file(validatelog, "testdata")
            output_path = self._utility.create_directory(machine)
            #if self._utility.validate_logs(client_machine=machine, validatelog=validatelog, linetovalidate=None):
                #self._utility.sleep_time(60, "waiting until the next scancheck starts")
            machine.generate_test_data(documentspath, hlinks=False, slinks=False, sparse=False)
                #self._utility.sleep_time(40, "waiting until the next scancheck starts")
            machine.get_cpu_usage(client=self._client, interval=1, totaltime=1000, processname='cvd',
                                  outputpath=str(output_path+self.slash_format+service_pack+"-prescan.csv"), wait_for_completion=False)
            log.info("Check whether the job started due to changes in files")
            job_obj = JobManager.get_active_job_object(self, client)
            log.info("Killing the scancheck cpu performance counter process as the job started")
            machine.kill_process(process_name=perfname.get(machine.os_info))
            jm_obj = JobManager(job_obj, self.commcell)

            log.info("Check whether the scan phase started ")
            jm_obj.wait_for_phase(phase="Scan", total_attempts=500, check_frequency=3)
            machine.get_cpu_usage(client=self._client, interval=1, totaltime=1000, processname='ifind',
                                  outputpath=str(output_path+self.slash_format+service_pack+"-scan.csv"), wait_for_completion=False)

            log.info("Check whether the backup phase started ")
            jm_obj.wait_for_phase(phase="backup", total_attempts=500, check_frequency=3)
            log.info("Killing the filescan cpu performance counter process as the backup phase started")
            machine.kill_process(process_name=perfname.get(machine.os_info))

            machine.get_cpu_usage(client=self._client, interval=1, totaltime=1000, processname='clBackup',
                                  outputpath=str(output_path+self.slash_format+service_pack+"-clbackup.csv"), wait_for_completion=False)
            jm_obj.wait_for_phase(phase="Archive Index", total_attempts=500, check_frequency=1)

            log.info("Killing the clBackup cpu performance counter process as the backup phase completed")
            machine.kill_process(process_name=perfname.get(machine.os_info))
            final_df = self.parseoutputfiles(machine, output_path, service_pack)

            if machine.os_info == 'WINDOWS':
                os_info = 'WINDOWS'
            else:
                os_info = 'MAC'
            self.updateperfintoDb(final_df, client_name, os_info)
            data = self.generateplotfromdb(2, "c:\\cpu")
            mail = Mailer({'receiver':receiver}, commcell_object=self.commcell)
            mail.mail("Laptop CPU performance", data)

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            self._schedule_creator.cleanup_schedules()
            machine.remove_directory(test_path)
            machine.remove_directory(documentspath)
            machine.kill_process(process_name=perfname.get(machine.os_info))
