# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Commcell Migration operations

CCMHelper: Helper class to perform Commcell Migration operations

CCMHelper:
    __init__()                  --  initializes CCM helper object

    create_destination_commcell()  --  creates the destination commcell object

    get_active_mediaagent()     --  returns the online available media agent

    run_ccm_export()            --  start a CCM Export job

    create_entities()           --  Creates all the required entities for test case execution

    clean_entities()            --  Cleans up the created entities as part of this run.

    run_ccm_import()            --  start a CCM Import job

    get_latest_subclient()      --  Returns the latest subclient object for provided client

    get_jobs_for_subclient()    --  Returns list of jobs available for a provided subclient.

    set_libary_mapping()        --  Sets all the required library mapping settings post Migration

    get_barcode_list()          --  Returns barcode list for provided subclient

    restore_by_job()            --  Submits as restore by job with provided jobs of a backupset.


CCMVSAHelper: Helper class to perform VM Merge cases for CCM

CCMVSAHelper:
    __init__()                  --  initializes the CCMVSAHelper object along with all test parameters

    setup_entities()            --  Sets up all VM entities from given test params required for testing CCM Merge

    setup_job()                 --  Sets up backup jobs required for testing CCM Merge

    setup_ccm_folder()          --  Sets up CCM Folders and network shares from given test params required for testing

    perform_ccm_operation()     --  Performs CCM export/import operation test step

    verify_non_client_merge()   --  Verifies non client entities migrated successfully

    verify_jobs_merge()         --  Verifies jobs have migrated successfully

    get_client_jobs()           --  Gets job history details of client using qcommand
"""
from base64 import b64encode
from datetime import datetime
from deepdiff import DeepDiff

from cvpysdk.commcell import Commcell
from cvpysdk.constants import VSAObjects
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from dateutil.relativedelta import relativedelta

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from AutomationUtils.database_helper import CommServDatabase, MSSQL
from AutomationUtils.constants import Agents
from Server.Alerts.alert_helper import AlertHelper
from Server.OperationWindow.ophelper import OpHelper
from Server.serverhelper import ServerTestCases
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class CCMHelper(object):
    """Helper class to perform Commcell Migration related operations"""

    def __init__(self, testcase):
        """Initialize instance of the CCMHelper class."""
        self.testcase = testcase
        self._destination_cs = None
        self.server = ServerTestCases(self.testcase)
        self.log = testcase.log
        self.entities = CVEntities(self.testcase)
        self._csdb = None
        self._mssql = None
        self._option_selector = None

    def create_destination_commcell(self, destination_cs_name,
                                    cs_user_name, cs_password):
        """Returns the destination commcell object

        Args:

            destination_cs_name     (str)   --      destination commcell host name

            cs_user_name            (str)   --      destination commcell user name

            cs_password             (str)   --      destaintion commcell password
        
        Returns:
            destination_commcell    (obj)   --      instance of the commcell class

        """

        try:

            self._destination_cs = Commcell(destination_cs_name,
                                            cs_user_name,
                                            cs_password)
            return self._destination_cs

        except Exception as excp:

            self.log.error('destination commcell object creation failed : %s',
                           str(excp))
            raise Exception('destination commcell object creation failed : %s',
                            str(excp))

    @property
    def destination_cs(self):
        """Returns destination commcell object"""
        if self._destination_cs is None:
            raise Exception("Destination Commcell object is not initialized.")
        return self._destination_cs

    @property
    def option_selector(self):
        """Returns the option selector instance"""
        if self._option_selector is None:
            self._option_selector = OptionsSelector(self.testcase.commcell)
        return self._option_selector

    def get_active_mediaagent(self):
        """"Returns the active MediaAgent Instance"""

        utility = self.option_selector
        return utility.get_ma('windows')

    def run_ccm_export(self, export_location, client_names=None, other_entities=None, options=None, commcell=None):

        """Return the CCM Ecport job instance

        Args:           
            export_location     ( str )     -       location to perform CCM Export

            commcell            (obj)       -       commcell object

            client_names        ( list )    -       list of clients to be exported
                    [
                        client_1,

                        client_2
                    ]

            other_entities      ( list )    -       list of other entities to be exported
                    [
                        "schedule_policies",

                        "users_and_user_groups",

                        "alerts"
                    ]   

            options             ( dict )    --      Contains options used to perform CCM Export.
                    {
                        "pathType":"Local",

                        "otherSqlInstance":True,

                        "userName":"UserName",

                        "password":"",

                        "otherSqlInstance": False,

                        "sqlInstanceName":"SQLInstanceName",

                        "sqlUserName":"SQLUserName",

                        "sqlPassword":"SQLPassword",

                        "Database":"commserv",

                        "captureMediaAgents":True,

                        "captureSchedules":True,

                        "captureActivityControl":True,

                        "captureOperationWindow":True,

                        "captureHolidays":True,

                        "csName": "CommservName",

                        "clientIds": [client_id1, client_id2],  # required only when exporting clients using sql instance

                        "autopickCluster":False
                    }

         Returns:
             CCM Export job instance

        """

        if options is None:
            options = {}

        ccmobj = self.testcase.commcell.commcell_migration if not commcell else commcell

        if client_names is None and other_entities is None:
            raise Exception("Both client and other entities cannot be none")

        if options.get("pathType", "").lower() == "network" and \
                ("userName" not in options or "password" not in options):
            raise Exception("Username or Password for the network export path are not provided")

        opt_dic = {
            'pathType': options.get("pathType", 'Local'),
            'userName': options.get("userName", ""),
            'password': options.get("password", ""),
            "otherSqlInstance": options.get("otherSqlInstance", False),
            "sqlInstanceName": options.get("sqlInstanceName", ""),
            "sqlUserName": options.get("sqlUserName", ""),
            "sqlPassword": options.get("sqlPassword", ""),
            "captureMediaAgents": options.get('captureMediaAgents', True),
            "capture_schedules": options.get("captureSchedules", True),
            "capture_activity_control": options.get("captureActivityControl", True),
            "capture_opw": options.get("captureOperationWindow", True),
            "capture_holidays": options.get("captureHolidays", True),
            "csName": options.get("csName", self.testcase.commcell.commserv_name),
        }

        if "clientIds" in options:
            opt_dic["clientIds"] = options["clientIds"]

        return ccmobj.commcell_export(export_location=export_location,
                                      client_list=client_names,
                                      other_entities=other_entities,
                                      options_dictionary=opt_dic
                                      )

    def create_entities(self, mountpath_location=None, mountpath_user_name=None, mountpath_user_password=None,
                        tape_library=None, options=None):

        """Creates all the required entities for a client

        Args:
            mountpath_location          ( str )     -   UNC Location for the mount path

            mountpath_user_name         ( str )     -   UNC path user name

            mountpath_user_password     ( str )     -   UNC path password

            tape_library                ( str)      -   Tape library name

        Returns:

            returns all the entities created.

        """

        try:
            available_ma = self.get_active_mediaagent()
            if options is None:
                options = {}

            all_inputs = {
                'target':
                    {
                        'client': self.testcase.client.client_name,
                        'agent': options.get('agent', "File System"),
                        'instance': options.get('instance', "defaultinstancename"),
                        'mediaagent': available_ma,
                        'force': True
                    },
                'backupset': None,
                'subclient': {'content': [self.testcase.client.log_directory], },
                'storagepolicy': None
            }

            if mountpath_location is not None:
                disk_lib = {'disklibrary': {
                    'mount_path': mountpath_location,
                    'username': mountpath_user_name,
                    'password': mountpath_user_password,
                    'cleanup_mount_path': True, }}

                all_inputs.update(disk_lib)

            elif tape_library is not None:
                query = ("select top 1 DrivePoolName from MMdrivepool where MasterPoolId"
                         " in(select MasterPoolId from MMMasterPool where libraryid in"
                         " (select LibraryId from MMLibrary where AliasName"
                         " ='{0}'".format(tape_library) + "))")

                result = self.option_selector.exec_commserv_query(query)
                drivepool_name = str(result[1][0][0])

                tape_lib = {'storagepolicy': {
                    'library': tape_library,
                    'mediaagent_name': self.testcase.commcell.commserv_name,
                    'drivepool': drivepool_name,
                    'scratchpool': 'Default Scratch',
                    'istape': True
                }}

                all_inputs.update(tape_lib)
            else:
                raise Exception("Unable to find required library")

            created_entities = self.entities.create(all_inputs)
            backupset = created_entities["subclient"]["backupset"]
            subclient_name = created_entities["subclient"]["name"]
            subclient = backupset.subclients.get(subclient_name)

            job = subclient.backup()
            self.log.info("started backup job for subclient: {%s"
                          "with job id: %s", subclient_name,
                          str(job.job_id))
            if job.wait_for_completion():
                self.log.info("Backup Job id: %s "
                              "completed successfully", str(job.job_id))
            else:
                self.log.error("Backup Job id: %s failed/ killed",
                               str(job.job_id))

        except Exception as excp:
            self.log.error('Entities creation failed : %s',
                           str(excp))
            raise Exception('Entities creation failed : %s',
                            str(excp))

    def clean_entities(self):
        """Clean the entities created in this run"""

        self.entities.cleanup()

    def run_ccm_import(self, import_location, options=None):
        """Return the CCM Import job instance

        Args:
            import_location     ( str )     -       location to perform CCM Import
            options
            {
                "pathType": "Network",

                "userName" : "username",
                
                "password": "password",
                
                "forceOverwrite": False,
                
                "failIfEntityAlreadyExists": False,

                "deleteEntitiesNotPresent": False,

                "deleteEntitiesIfOnlyfromSource": False,

                "forceOverwriteHolidays": False,

                "mergeHolidays": True,

                "forceOverwriteOperationWindow": False,

                "mergeOperationWindow": False,

                "forceOverwriteSchedule": False,

                "mergeSchedules": True
            }
            
         Returns:
             CCM Import job instance

        """

        if options is None:
            options = {}

        opt_dic = {'pathType': options.get("pathType", "Local"),
                   'userName': options.get("userName", ""),
                   'password': options.get("password", ""),
                   'forceOverwrite': options.get('forceOverwrite', False),
                   'failIfEntityAlreadyExists': options.get('failIfEntityAlreadyExists', False),
                   'deleteEntitiesNotPresent': options.get('deleteEntitiesNotPresent', False),
                   "deleteEntitiesIfOnlyfromSource": options.get("deleteEntitiesIfOnlyfromSource", False),
                   "forceOverwriteHolidays": options.get("forceOverwriteHolidays", False),
                   "mergeHolidays": options.get("mergeHolidays", True),
                   "forceOverwriteOperationWindow": options.get("forceOverwriteOperationWindow", False),
                   "mergeOperationWindow": options.get("mergeOperationWindow", False),
                   "forceOverwriteSchedule": options.get("forceOverwriteSchedule", False),
                   "mergeSchedules": options.get("mergeSchedules", True)
                   }

        return self.destination_cs.commcell_migration.commcell_import(import_location,
                                                                      opt_dic)

    @property
    def csdb_destination(self):
        """Returns the commcell cs DB object"""
        try:
            if self._csdb is None:
                self._csdb = CommServDatabase(self.destination_cs)

            return self._csdb
        except Exception as excp:
            self.log.error(excp)
            raise Exception("csdb object creation failed",
                            str(excp))

    def get_latest_subclient(self, client_name=None, destination_commcell=False, **kwargs):
        """Return the latest subclient instance for a client

        Args:
            client_name             (str/obj)       -       name/instance of the client

            destination_commcell    (str/obj)       -       name/instance of the destination commcell

            kwargs:
                agent               (enum)
                Ex: agent=Agents.VIRTUAL_SERVER

        Returns:
            latest subclient object for client

        """
        if destination_commcell:

            query = ("select top(1) app.subclientName,bs.name, c.name from APP_Application app,"
                     " APP_BackupSetName bs, APP_Client c where bs.id = app.backupSet"
                     " and app.clientId =")
            if client_name is None:
                query += "c.id order by app.refTime desc"
            else:
                client_id = self.destination_cs.clients[client_name]['id']
                query += client_id + "order by app.refTime desc"

            self.csdb_destination.execute(query)
            subclient_name = self.csdb_destination.fetch_all_rows()[0][0]
            backupset_name = self.csdb_destination.fetch_all_rows()[0][1]
            c_name = self.csdb_destination.fetch_all_rows()[0][2]
            agent = self.destination_cs.clients.get(c_name).agents.get(kwargs.get("agent", Agents.FILE_SYSTEM).value)
            backupset = agent.backupsets.get(backupset_name)
            return backupset.subclients.get(subclient_name)
        else:
            query = ("select top(1) app.subclientName,bs.name,"
                     " c.name from APP_Application app, APP_BackupSetName bs,"
                     " APP_Client c where bs.id = app.backupSet and app.clientId=c.id"
                     " and app.clientId =")
            if client_name is None:
                query += "c.id order by app.refTime desc"
            else:
                client_id = self.testcase.commcell.clients[client_name]['id']
                query += client_id + " order by app.refTime desc"

            result = self.option_selector.exec_commserv_query(query)
            subclient_name = str(result[1][0][0])
            backupset_name = str(result[1][0][1])
            c_name = str(result[1][0][2])
            agent = self.testcase.commcell.clients.get(c_name).agents.get(
                kwargs.get("agent", Agents.FILE_SYSTEM).value)
            backupset = agent.backupsets.get(backupset_name)
            return backupset.subclients.get(subclient_name), backupset

    def get_jobs_for_subclient(self, sub_client):
        """returns the jobid list for a provided subclient"""

        query = ("select distinct jobId from JMjobdatastats where dataType=2 and appid="
                 " {0}".format(sub_client.subclient_id))

        result = self.option_selector.exec_commserv_query(query)
        jobs_list = result[1][0]
        for i in range(0, len(jobs_list)):
            jobs_list[i] = int(jobs_list[i])
        return jobs_list

    @property
    def mssql_destination(self):
        """Returns MSSQL instance for a destination cs"""
        if self._mssql is None:
            sql_server = ""
            if self.destination_cs.is_linux_commserv:
                sql_server = self.testcase.tcinputs["DestinationCSHostName"]
            else:
                sql_server = self.testcase.tcinputs["DestinationCSHostName"] + "\\commvault"
            self._mssql = MSSQL(sql_server,
                                self.testcase.tcinputs["SQLUserName"],
                                self.testcase.tcinputs["SQLPassword"],
                                "CommServ",
                                as_dict=False)
        return self._mssql

    def set_libary_mapping(self, source_commcell_name):
        """Sets all the required library mappings post CCM

        Args:

            source_commcell_name    (str)   --      sourcce commcell name

        """
        query = "Select id from App_Client where ID = (Select top 1 ClientID from MMHost where OfflineReason = 0)"
        self.csdb_destination.execute(query)
        ma_id = self.csdb_destination.fetch_all_rows()[0][0]
        query = "update CCMLibraryAnswers set TargetMediaAgentId={0} where SourceCommCellName='{1}'".format(
            ma_id, source_commcell_name)
        self.mssql_destination.execute(query)
        self.mssql_destination.execute_storedprocedure("CCMSetLibrariesAccessible", None)
        query = "UPDATE MMConfigs SET nMin = 1, value = 2 WHERE name = " \
                "'MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN' "
        self.mssql_destination.execute(query)
        dest_commcell_client = self.destination_cs.clients.get(self.destination_cs.commserv_name)
        dest_commcell_client.restart_service("GXMLM(" + dest_commcell_client.instance + ")")

    def get_barcode_list(self, subclient_id):
        """Returns barcode list for provided subclient

        Args:

            subclient_id            (int)   --      Subclient id of a subcient

        Returns:

            list of barcode's for a provided subclient id

        """

        query = """select Mediaid from MMMedia where MediaId in 
                        (select MediaId from MMVolume where VolumeId in 
                            ( select volumeId from archChunk where id in 
                                (select archChunkId from archChunkMapping where jobId in
                                    (select jobId from JMJobDataStats where appId = {} )))) and MediaTypeId =8990""".format(
            subclient_id)

        result = self.option_selector.exec_commserv_query(query)
        return result[1][0]

    def tape_import(self, media_list, foreign_media_import=False):
        """Run the tape import with the provided bar codes

        Args:

            media_list              (list)  --      list of barcodes needed to be imported

        """
        try:
            query = ("select DP.DrivePoolId, MP.LibraryId from MMDrivePool DP, MMMasterPool MP"
                     " where DP.MasterPoolId = MP.MasterPoolId and MP.LibraryId in ( select LibraryId from"
                     " MMMedia where MediaId = {0} )".format(media_list[0]))

            result = self.option_selector.exec_commserv_query(query)
            drive_pool_id = int(result[1][0][0])
            library_id = int(result[1][0][1])

            if foreign_media_import:
                if not self._destination_cs:
                    self.log.error("Foreign Commcell is not created")
                    raise Exception("Foreign Commcell is not created")
                ccmobj = self._destination_cs.commcell_migration

            else:
                ccmobj = self.testcase.commcell.commcell_migration
            job = ccmobj.tape_import(library_id, media_list, drive_pool_id)

            self.log.info("started tape import job "
                          "with job id: %s", job.job_id)
            if job.wait_for_completion():
                if job.status != "Completed":
                    raise Exception("Tape import job not completed successfully")
                self.log.info("Tape Import Job id: %s "
                              "completed successfully", str(job.job_id))
            else:
                self.log.error("Tape Import Job id: %s failed/ killed",
                               str(job.job_id))

        except Exception as excp:
            self.log.error('Failed to start tape import with error : %s',
                           str(excp))
            raise Exception('Failed to start tape import with error : %s',
                            str(excp))

    def restore_by_job(self, backupset, jobs_list):
        """Run the restore by job for the provided backupset with specified jobs

        Args:
            backupset               (instance)      --      instance of the backupset class.

            jobs_list               (list)          --      list of the job available for restore.

        """
        try:
            restore_job = backupset.restore_out_of_place(client=self.testcase.tcinputs["ClientName"],
                                                         destination_path="{}Restore".format(
                                                             self._option_selector.get_drive()),
                                                         paths=[], fs_options={"index_free_restore": True},
                                                         restore_jobs=jobs_list)

            self.log.info("started Restore by job "
                          "with job id: %s", restore_job.job_id)
            if restore_job.wait_for_completion():
                self.log.info("Restore by Job id: %s "
                              "completed successfully", str(restore_job.job_id))
            else:
                self.log.error("Restore by Job id: %s failed/ killed",
                               str(restore_job.job_id))

        except Exception as excp:
            self.log.error('Failed to start Restore with error : %s',
                           str(excp))
            raise Exception('Failed to start Restore with error : %s',
                            str(excp))


class CCMVSAHelper:
    """
    Helper class for handling CCM merge testcases for v1 and v2 VM combinations
    """

    def __init__(self, commcell_obj: Commcell, source: bool, index_type: int, tcinputs: dict):
        """
        Initialize instance of the CCMVSAHelper class

        Args:
            commcell_obj    (Commcell)  -   Commcell sdk object
            source  (bool)              -   True if Given commcell object is of source CS
            index_type  (int)           -   indexing v1 or v2, 1 or 2
            tcinputs    (dict):-

            unique options to this instance of helper,
            nested inside tcinputs under key 'source_options' or 'dest_options'

                media_agent (str)   -   name of media agent to use
                                        default: cs client name
                mount_path  (str)   -   mount path to create
                                        default: will be created in free drive of machine
                library (str)       -   name of library to create/re-use
                                        default: source_lib/dest_lib
                policy  (str)       -   name of storage policy to create/re-use
                                        default: source_policy/dest_policy

                pseudo_client   (str)   -   name of pseudoclient to create/re-use
                                            default: source_vcenter_vx/dest_vcenter_vx
                                            (x is 1 or 2, depending on v1 or v2)
                vcenter_proxy   (str)   -   name of vcenter proxy client to use
                                            default: cs client name
                backupset       (str)   -   name of backupset to create/re-use
                                            default: source_backupset/dest_backupset
                subclient       (str)   -   name of subclient to create/re-use
                                            default: source_subclient/dest_subclient

                fs_client       (str)   -   name of fs client to re-use
                                            default: source_fsclient/dest_fsclient
                                            note: if install new client, this input is not used
                fs_backupset    (str)   -   name of backupset to create/re-use
                                            default: source_fsbackupset/dest_fsbackupset
                fs_subclient    (str)   -   name of the subclient to create/re-use
                                            default: source_fssubclient/dest_fssubclient
                fs_content      (str)   -   content to set for the fs subclient if not already set
                                            default: C:\\Users\\Administrator\\Documents

                fsmachine_hostname  (str)   -   client machine IP or hostname to install FS agent
                fsmachine_username  (str)   -   client machine username
                fsmachine_password  (str)   -   client machine password
                defaults are taken from config["Laptop"]["Install"]["windows"],

            options shared between source and destination cs helpers

                share_name          (str)   -   name of the UNC share to create/re-use
                export_location     (str)   -   path to parent folder/share where export will be performed
                import_location     (str)   -   path to parent folder/share where import will read dump from
                [Note: only one of the two locations must be a UNC network share path!]

                [Below options must be given! All others are optional]
                vcenter_hostname    (str)   -   vcenter hostname
                vcenter_username    (str)   -   vcenter username
                vcenter_password    (str)   -   vcenter password
                above 3 defaults from config["Laptop"]["Install"]["HyperV..."],

                discovered_vm       (str)   -   VM name to back up as content

                share_username  (str)   -   username to access UNC share for export/import location
                share_password  (str)   -   password to access UNC share for export/import location
                above 2 defaults taken from config["Laptop"]["Install"]["Network..."],
        """
        self.cs_machine = Machine(commcell_obj.commserv_client)
        self.backup_job = None
        self.fs_job = None
        self.alert_obj = None
        self.opw_obj = None
        self.scp_obj = None
        self.sch_obj = None
        self.user_obj = None
        self.ug_obj = None
        self.vcenter_subclient = None
        self.fs_subclient = None
        self.fs_client = None
        self.pseudo_client = None
        self.log = logger.get_log()
        self.prefix = "source" if source else "dest"
        self.prefix2 = "export" if source else "import"
        self.commcell_obj = commcell_obj
        free_drive = OptionsSelector.get_drive(self.cs_machine, max_size=True)

        # COMMON INPUTS DEFAULTS
        config = get_config()

        defaults = {
            "vcenter_hostname": config.Laptop.Install.HyperVHostname,
            "vcenter_username": config.Laptop.Install.HyperVUser,
            "vcenter_password": config.Laptop.Install.HyperVPasswd,
            "discovered_vm": "",
            "agent": "Virtual Server",
            "instance": "VMware",

            "export_location": config.Laptop.Install.NetworkPath,
            "share_name": "autoimports",
            "share_username": config.Laptop.Install.NetworkUser,
            "share_password": config.Laptop.Install.NetworkPassword,

            "source_obj": None,
            "dest_obj": None
        }
        if not source:
            defaults["import_location"] = f"{free_drive}:\\autoimports"

        # COMMON INPUTS POINTING REFERENCE
        defaults.update(tcinputs)
        tcinputs.update(defaults)
        self.common_options = tcinputs
        # now common_options points to global tcinputs while also updated with defaults

        # UNIQUE INPUTS DEFAULTS
        self.unique_options = {
            "media_agent": commcell_obj.commserv_client.client_name,
            "mount_path": f"{free_drive}:\\{self.prefix}_lib",
            "library": f"{self.prefix}_lib",
            "policy": f"{self.prefix}_policy",

            "pseudo_client": f"{self.prefix}_vcenter_v{index_type}",
            "vcenter_proxy": commcell_obj.commserv_client.client_name,
            "backupset": f"{self.prefix}_backupset",
            "subclient": f"{self.prefix}_subclient",

            "fs_client": f"{self.prefix}_fsclient",
            "fs_agent": "File System",
            "fs_backupset": f"{self.prefix}_fsbackupset",
            "fs_subclient": f"{self.prefix}_fssubclient",
            "fs_content": "C:\\Users\\Administrator\\Documents",

            "fsmachine_hostname": config.Laptop.Install.windows.Machine_host_name,
            "fsmachine_username": config.Laptop.Install.windows.Machine_user_name,
            "fsmachine_password": config.Laptop.Install.windows.Machine_password,
        }
        # more unique inputs (names for non-client entities)
        for non_client in [
            'schedule_policy', 'user_name', 'user_group', 'operation_window', 'alert_name', 'schedule_name'
        ]:
            self.unique_options[non_client] = OptionsSelector.get_custom_str(non_client)
        self.unique_options['user_password'] = OptionsSelector.get_custom_password(9, True)

        # UNIQUE INPUTS POINTING REFERENCE
        self.unique_options.update(tcinputs.get(f'{self.prefix}_options', {}))
        tcinputs[f'{self.prefix}_options'] = self.unique_options
        # now unique_options points to correct nested dict inside tcinputs, while also updated with the default values

        # set the indexing v2 or v1
        commcell_obj.add_additional_setting(
            'CommServDB.GxGlobalParam',
            'UseIndexingV2forNewVSAClient',
            'BOOLEAN',
            'true' if index_type == 2 else 'false'
        )
        self.is_indexing_v2 = (index_type == 2)

        # add self to tcinputs so dest instance can also access
        self.common_options[f'{self.prefix}_obj'] = self

    # setup utils

    def _setup_vcenter(self) -> None:
        """
        Util for setting up Vcenter client

        Returns:
            None
        """
        self.log.info("Setting up vcenter")
        if self.commcell_obj.clients.has_client(self.unique_options["pseudo_client"]):
            self.log.info("Found pseudo client already exists, checking indexing type")
            self.pseudo_client = self.commcell_obj.clients.get(self.unique_options["pseudo_client"])
            is_v2 = self.pseudo_client.properties['clientProps']['isIndexingV2VSA']
            if not is_v2 == self.is_indexing_v2:
                self.log.error("Existing Pseudoclient does not match indexing required for this Test")
                self.log.error("Delete/Rename existing client or provide non existing client name to create new")
                raise CVTestCaseInitFailure("Pseudoclient exists, but different indexing")
            else:
                self.log.info("It matches required indexing type as well, reusing it")
        else:
            self.log.info("Creating pseudo client")
            for required_param in ["vcenter_hostname", "vcenter_username", "vcenter_password"]:
                if not self.common_options[required_param]:
                    raise CVTestCaseInitFailure("Unable to create pseudoclient, Please provide vcenter creds!")

            self.pseudo_client = self.commcell_obj.clients.add_vmware_client(
                self.unique_options["pseudo_client"],
                self.common_options["vcenter_hostname"],
                self.common_options["vcenter_username"],
                self.common_options["vcenter_password"],
                [self.unique_options["vcenter_proxy"]]
            )
        self.log.info("Vcenter pseudo client setup!")

    def _setup_vmsubclient(self) -> None:
        """
        Util for setting up VM subclient

        Returns:
            None
        """
        bkpsets = self.pseudo_client.agents.get(self.common_options["agent"]) \
            .instances.get(self.common_options["instance"]).backupsets
        if bkpsets.has_backupset(self.unique_options["backupset"]):
            self.log.info("Resuing existing backupset")
            bkpset = bkpsets.get(self.unique_options["backupset"])
        else:
            self.log.info("Creating backupset")
            bkpset = bkpsets.add(self.unique_options["backupset"])
        self.log.info("Backupset setup successfully!")
        subcls = bkpset.subclients
        if subcls.has_subclient(self.unique_options["subclient"]):
            self.vcenter_subclient = subcls.get(self.unique_options["subclient"])
            self.log.info("Found existing subclient, checking content")
            if not self.common_options["discovered_vm"]:
                self.common_options["discovered_vm"] = self.vcenter_subclient.content[0]['display_name']
            elif self.common_options["discovered_vm"].lower() == \
                    self.vcenter_subclient.content[0]['display_name'].lower():
                self.log.info("It has same content required, reusing")
            else:
                self.log.error(
                    f"subclient {self.unique_options['subclient']} already exists but with different content")
                raise CVTestCaseInitFailure(f"Please provide tcinput 'subclient' nested inside '{self.prefix}_options'"
                                            "with a new name to create a new subclient to avoid overwriting content")
            if self.fs_subclient:  # if the fs agent was setup first, use its storage
                self.log.info("Changing to policy of FS subclient")
                self.vcenter_subclient.storage_policy = self.fs_subclient.storage_policy
            self.unique_options["policy"] = self.vcenter_subclient.storage_policy
            self._setup_storage()
        else:
            self.log.info("Creating subclient")
            self._setup_storage()
            self.vcenter_subclient = subcls.add_virtual_server_subclient(
                self.unique_options["subclient"],
                [{
                    'equal_value': True,
                    'allOrAnyChildren': True,
                    'display_name': self.common_options["discovered_vm"],
                    'type': VSAObjects.VMName
                }],
                storage_policy=self.unique_options["policy"]
            )
        self.log.info("Vcenter Subclient setup successfully!")

    def _setup_fsclient(self) -> None:
        """
        Util for setting up a client with FS agent, using remote install if required

        Returns:
            None
        """
        self.log.info("Setting up FS client")
        fs_client_name = self.unique_options["fs_client"]
        if self.unique_options["fsmachine_hostname"]:
            fs_client_name = self.unique_options["fsmachine_hostname"]
        if self.commcell_obj.clients.has_client(fs_client_name):
            self.log.info("Found fs client already exists")
            self.fs_client = self.commcell_obj.clients.get(fs_client_name)
            self.log.info(f"Reusing existing client {self.fs_client.client_name}")
            self.unique_options["fs_client"] = self.fs_client.client_name
            if self.fs_client.agents.has_agent('File System'):
                self.log.info("Found FS Agent already exists, reusing")
                self.log.info("FS client setup!")
                return
            else:
                self.log.info("No FS agent, will attempt install software")
        else:
            self.log.info("No Client exists, attempting install software")
        for required_param in ["fsmachine_hostname", "fsmachine_username", "fsmachine_password"]:
            if not self.unique_options[required_param]:
                raise CVTestCaseInitFailure("Unable to install fs client, Please provide machine creds!")
        install_job = self.commcell_obj.install_software(
            client_computers=[self.unique_options["fsmachine_hostname"]],
            windows_features=[WindowsDownloadFeatures.FILE_SYSTEM.value],
            username=self.unique_options["fsmachine_username"],
            password=b64encode(self.unique_options["fsmachine_password"].encode()).decode(),
            allowMultipleInstances=True
        )
        self.log.info(f"Install Job Launched Successfully, Will wait until Job: {install_job.job_id} Completes")
        if install_job.wait_for_completion():
            self.log.info("Install Job Completed successfully")
        else:
            job_status = install_job.delay_reason
            self.log.error(f"Install Job failed with an error: {job_status}")
            raise CVTestCaseInitFailure(job_status)

        self.log.info("Refreshing Client List on the CS")
        self.commcell_obj.refresh()
        self.log.info("Initiating Check Readiness from the CS")
        if self.commcell_obj.clients.has_client(self.unique_options["fsmachine_hostname"]):
            self.fs_client = self.commcell_obj.clients.get(self.unique_options["fsmachine_hostname"])
            if self.fs_client.is_ready:
                self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Client failed Registration to the CS")
            raise Exception(f"Client: {self.unique_options['fsmachine_hostname']} failed registering to the CS, "
                            f"Please check client logs")
        self.log.info("FS client setup!")

    def _setup_fssubclient(self) -> None:
        """
        Util to setup subclient for given fs client

        Returns:
            None
        """
        bkpsets = self.fs_client.agents.get(self.unique_options["fs_agent"]).backupsets
        if bkpsets.has_backupset(self.unique_options["fs_backupset"]):
            self.log.info("Resuing existing fs backupset")
            bkpset = bkpsets.get(self.unique_options["fs_backupset"])
        else:
            self.log.info("Creating fs backupset")
            bkpset = bkpsets.add(self.unique_options["fs_backupset"])
        self.log.info("FS Backupset setup successfully!")
        subcls = bkpset.subclients
        if subcls.has_subclient(self.unique_options["fs_subclient"]):
            self.fs_subclient = subcls.get(self.unique_options["fs_subclient"])
            self.log.info("Found existing fs subclient, reusing!")
            self.unique_options["fs_content"] = self.fs_subclient.content[0]
            if self.vcenter_subclient:  # if vm was setup first, use its storage
                self.log.info("Changing to policy of VM subclient")
                self.fs_subclient.storage_policy = self.vcenter_subclient.storage_policy
            self.unique_options["policy"] = self.fs_subclient.storage_policy
            self._setup_storage()
        else:
            self.log.info("Creating subclient")
            self._setup_storage()
            self.fs_subclient = subcls.add(
                self.unique_options["fs_subclient"],
                storage_policy=self.unique_options["policy"],
            )
            self.fs_subclient.content = [self.unique_options["fs_content"]]
        self.log.info("FS Subclient setup successfully!")

    def _setup_non_clients(self) -> None:
        """
        Util to setup non client entities
        Schedule Policy, User, User group, Alert, Op window, schedule

        Returns:
            None
        """
        self._setup_storage()
        self.log.info("Storage is setup, entities can be setup now")

        # schedule policy
        self.log.info(f"Creating schedule policy {self.unique_options['schedule_policy']}")
        self.scp_obj = self.commcell_obj.schedule_policies.add(
            self.unique_options["schedule_policy"],
            'Auxiliary Copy',
            [{'storagePolicyName': self.unique_options["policy"]}],
            [
                {
                    "freq_type": 'daily',
                    "active_start_time": '12:00',
                    "repeat_days": 7
                }, {
                "maxNumberOfStreams": 0,
                "useMaximumStreams": True,
                "useScallableResourceManagement": True,
                "totalJobsToProcess": 1000,
                "allCopies": True,
                "mediaAgent": {"mediaAgentName": self.unique_options["media_agent"]}
            }
            ]
        )
        self.log.info("Schedule policy created successfully")

        # user
        self.log.info(f"Creating User {self.unique_options['user_name']}")
        self.user_obj = self.commcell_obj.users.add(
            self.unique_options["user_name"],
            f'{self.unique_options["user_name"]}@email.com',
            self.unique_options["user_name"], None,
            self.unique_options["user_password"], False, None,
            {
                'assoc1':
                    {
                        'storagePolicyName': [self.unique_options["policy"]],
                        'role': ['View']
                    }
            }
        )
        self.log.info("User created successfully")

        # user group
        self.log.info(f"Creating User group {self.unique_options['user_group']}")
        self.ug_obj = self.commcell_obj.user_groups.add(
            self.unique_options["user_group"], None,
            [self.unique_options["user_name"], "admin"],
            {
                'assoc1':
                    {
                        'storagePolicyName': [self.unique_options["policy"]],
                        'role': ['View']
                    }
            }
        )
        self.log.info("Created User group successfully")

        # alert
        self.log.info(f"Creating alert {self.unique_options['alert_name']}")
        alert_helper = AlertHelper(self.commcell_obj, 'Media Management', 'Library Management')
        alert_helper.get_alert_details(
            self.unique_options["alert_name"],
            ['Event Viewer'],
            {'disk_libraries': self.unique_options["library"]},
            ['admin'], 22
        )
        alert_helper.create_alert()
        self.alert_obj = self.commcell_obj.alerts.get(self.unique_options["alert_name"])
        self.log.info("Alert created successfully")

        # operation window
        self.log.info(f"Creating operation window {self.unique_options['operation_window']}")
        op_helper = OpHelper(None, self.commcell_obj, initialize_sch_helper=False)
        date_arg = (datetime.now() + relativedelta(years=1)).strftime("%d/%m/%Y")
        time1 = datetime.now().strftime("%H:%M")
        time2 = (datetime.now() + relativedelta(hours=1)).strftime("%H:%M")
        time3 = (datetime.now() + relativedelta(hours=5)).strftime("%H:%M")
        self.opw_obj = op_helper.add(
            self.unique_options["operation_window"],
            date_arg, date_arg,
            ["FULL_DATA_MANAGEMENT", "DR_BACKUP"],
            ["SUNDAY", "SATURDAY"],
            [time1, time2],
            [time2, time3]
        )
        self.log.info("Operation window created successfully")

        # schedule
        subclient = self.fs_subclient or self.vcenter_subclient
        if subclient:
            self.log.info(f"Creating backup schedule {self.unique_options['schedule_name']} for {subclient}")
            self.sch_obj = subclient.backup(
                "Full",
                schedule_pattern={
                    "freq_type": 'weekly',
                    "active_start_date": (datetime.today() + relativedelta(years=1)).strftime("%m/%d/%Y"),
                    "active_start_time": (datetime.now() + relativedelta(hours=4)).strftime("%H:%M"),
                    "repeat_weeks": 1,
                    "weekdays": ['Monday', 'Tuesday']
                }
            )
            self.sch_obj.name = self.unique_options["schedule_name"]
            self.sch_obj.refresh()
            self.log.info("Schedule created successfully")
        else:
            self.log.info("Skipping schedule creation as no subclients are setup")
        self.log.info("----- ALL ENTITIES SETUP SUCCESSFULLY ------")

    def _setup_storage(self) -> None:
        """
        Util for setting up Storage

        Returns:
            None
        """
        if self.commcell_obj.storage_policies.has_policy(self.unique_options["policy"]):
            self.log.info("Reusing existing storage policy")
            sp = self.commcell_obj.storage_policies.get(self.unique_options["policy"])
            self.unique_options["library"] = sp.library_name
            if not self.commcell_obj.disk_libraries.has_library(self.unique_options["library"]):
                raise CVTestCaseInitFailure("Given policy is using non-existing library!")
            lib = self.commcell_obj.disk_libraries.get(self.unique_options["library"])
            self.unique_options["media_agent"] = lib.media_agents_associated[0]
            if not self.commcell_obj.media_agents.has_media_agent(self.unique_options["media_agent"]):
                raise CVTestCaseInitFailure("Given library is using non-existing media agent!")
        else:
            self.log.info("Creating storage policy")
            if self.commcell_obj.disk_libraries.has_library(self.unique_options["library"]):
                self.log.info("Reusing existing library")
                lib = self.commcell_obj.disk_libraries.get(self.unique_options["library"])
                self.unique_options["media_agent"] = lib.media_agents_associated[0]
                if not self.commcell_obj.media_agents.has_media_agent(self.unique_options["media_agent"]):
                    raise CVTestCaseInitFailure("Given library is using non-existing media agent!")
            else:
                self.log.info("Creating library")
                if not self.commcell_obj.media_agents.has_media_agent(self.unique_options["media_agent"]):
                    raise CVTestCaseInitFailure(f"No media agent found with name {self.unique_options['media_agent']}")
                self.commcell_obj.disk_libraries.add(
                    self.unique_options["library"],
                    self.unique_options["media_agent"],
                    self.unique_options["mount_path"],
                )
            self.log.info("Library Setup successfully!")
            self.commcell_obj.storage_policies.add(
                self.unique_options["policy"],
                self.unique_options["library"],
                self.unique_options["media_agent"]
            )
        self.log.info("Storage policy setup successfully!")

    # test steps

    def setup_entities(self, vm: bool = True, fs: bool = False, non_client: bool = False) -> None:
        """
        Function to setup required backup entities for given commcell using init options

        Args:
            vm          (bool)  -   setup VM client if True (default: True)
            fs          (bool)  -   setup FS client if True (default: False)
            non_client  (bool)  -   setup non-client entities if True   (default: False)
                                    (Schedules, Holidays, Blackout window, Subclient policy, User, User groups)

        Returns:
            None
        """
        if vm:
            self._setup_vcenter()
            self._setup_vmsubclient()
        if fs:
            self._setup_fsclient()
            self._setup_fssubclient()
        if non_client:
            self._setup_non_clients()

    def setup_job(self, vm: bool = True, fs: bool = False) -> None:
        """
        Function to setup backup job in given commcell only if job is not already migrated

        Args:
            vm  (bool)  -   Will backup VM if True  (default: True)
            fs  (bool)  -   Will backup FS if True  (default: False)

        Returns:
            None
        """
        if self.vcenter_subclient and vm:
            self.log.info("Checking if VM job will be required")
            if not self.common_options["dest_obj"].verify_jobs_merge(vm=True):
                self.log.info("Source vm jobs are same as dest, new job needed to test")
                self.backup_job = self.vcenter_subclient.backup("Full")
                self.log.info(f"Started job {self.backup_job.job_id}")
                if self.backup_job.wait_for_completion():
                    self.log.info("VM Backup Successfull!")
                else:
                    raise CVTestCaseInitFailure("VM Backup job Failed!")
            else:
                self.log.info("Existing VM job has not migrated, no need new VM job")
        if self.fs_subclient and fs:
            self.log.info("Checking if FS job will be required")
            if not self.common_options["dest_obj"].verify_jobs_merge(vm=False, fs=True):
                self.log.info("Source fs jobs are same as dest, new job needed to test")
                schedule_obj = self.unique_options.get("sch_obj")
                if schedule_obj:
                    self.fs_job = self.commcell_obj.job_controller.get(int(schedule_obj.run_now()))
                else:
                    self.fs_job = self.fs_subclient.backup("Full")
                self.log.info(f"Started job {self.fs_job.job_id}")
                if self.fs_job.wait_for_completion():
                    self.log.info("FS Backup Successfull!")
                else:
                    raise CVTestCaseInitFailure("FS Backup job Failed!")
            else:
                self.log.info("Existing FS job has not migrated, no need new FS job")

    def setup_ccm_folder(self) -> None:
        """
        Function to setup CCM import/export folders from given inputs

        Returns:
            None
        """
        prefix3 = "import" if self.prefix2 == "export" else "export"
        directory = self.common_options[f"{self.prefix2}_location"]
        other_directory = self.common_options[f"{prefix3}_location"]

        # handle case when export and import locations are local directories given
        if (directory and not directory.startswith("\\\\")) and \
                (other_directory and not other_directory.startswith("\\\\")):
            self.log.error("Both export and import folders are local directories!")
            self.log.error("Cannot continue as Machine to machine folder transfer not implemented yet")
            raise CVTestCaseInitFailure("Please provide one of the 2 locations as remote share"
                                        " or leave empty for automated UNC path")

        # handle case when 1 location is not a local directory
        if not directory or directory.startswith("\\\\"):
            # as this is/will be UNC path, ensure password
            if not self.common_options["share_password"]:
                raise CVTestCaseInitFailure("Network share username and password required!")

            if not directory:  # Make sure UNC can be automated from the other directory given
                self.log.info(f"No location given for {self.prefix2}, remote share will be automated")
            else:
                self.log.info("Given location is a remote share")

            if other_directory and not other_directory.startswith("\\\\"):
                self.log.info(f"CCM {self.prefix2} will be done using UNC path")
            else:
                raise CVTestCaseInitFailure("Give at least one local directory! for export/import locations")
            return

        # finally the case when given directory is local folder
        if self.cs_machine.is_directory(directory) != 'False':
            self.log.info(f"Found {self.prefix2} directory")
        else:
            self.log.info(f"Creating {self.prefix2} directory")
            self.cs_machine.create_directory(directory)
        share_name = self.cs_machine.get_share_name(directory)
        if share_name:
            self.log.info("Found directory already shared")
            self.common_options["share_name"] = share_name
        else:
            self.log.info(f"Creating network share for {self.prefix2} folder")
            self.cs_machine.share_directory(
                self.common_options["share_name"],
                directory
            )

        if not other_directory:
            unc_path = f"\\\\{self.cs_machine.ip_address}\\{self.common_options['share_name']}"
            self.common_options[f"{prefix3}_location"] = unc_path
            self.log.info(f"Assuming UNC path for {prefix3} location as, {unc_path}")

        self.log.info(f"{self.prefix2} location setup and shared successfully!")

    def perform_ccm_operation(self, ccm_options: dict = None, other_entities: list = None) -> None:
        """
        Function to perform CCM Import/Export of available entities

        Args:
            ccm_options (dict)      -   options to pass for ccm export or import    (default: None)
            other_entities  (list)  -   list of non client entities to also export  (default: None)
                                        (see commcell_migration.commcell_export for list elements)

        Returns:
            None
        """
        if ccm_options is None:
            ccm_options = dict()
        network_dict = {
            "pathType": "Network",
            "userName": self.common_options["share_username"],
            "password": self.common_options["share_password"]
        }
        # NEED TO HANDLE THIS ONE DIFFERENTLY FOR SOURCE AND DESTINATION INSTANCE
        if self.prefix == "source":
            self.common_options["export_dump"] = OptionsSelector.get_custom_str("dump_")
            dump_folder = f'{self.common_options["export_location"]}\\{self.common_options["export_dump"]}'
            if dump_folder.startswith("\\\\"):  # check if folder is unc share
                ccm_options.update(network_dict)
            self.log.info(f"Starting CCM Export to folder {dump_folder}")
            client_list = []
            if self.vcenter_subclient:
                if self.is_indexing_v2:
                    client_list.append(self.common_options["discovered_vm"])
                else:
                    client_list.append(self.pseudo_client.client_name)
            if self.fs_subclient and self.fs_client.client_name not in client_list:
                client_list.append(self.fs_client.client_name)

            export_job = self.commcell_obj.commcell_migration.commcell_export(
                dump_folder,
                client_list,
                ccm_options,
                other_entities
            )
            self.log.info(f"Started ccm export job {export_job.job_id}")
            if export_job.wait_for_completion():
                self.log.info("Export job successfull!")
            else:
                raise CVTestStepFailure("CCM EXport job failed!")
        else:
            dump_folder = f'{self.common_options["import_location"]}\\{self.common_options["export_dump"]}'
            if dump_folder.startswith("\\\\"):  # check if folder is unc share
                ccm_options.update(network_dict)
            self.log.info(f"Starting CCM Import from folder {dump_folder}")
            import_job = self.commcell_obj.commcell_migration.commcell_import(
                dump_folder,
                ccm_options
            )
            self.log.info(f"Started ccm import job {import_job.job_id}")
            if import_job.wait_for_completion():
                self.log.info("Import successfull!")
            else:
                raise CVTestStepFailure("CCM Import job failed!")
        self.commcell_obj.refresh()

    def verify_non_client_merge(self) -> list[str]:
        """
        Verifies the non client entities have merged without changes into dest CS

        Returns:
            errors  (list)  -   list of error messages indicating what failed to merge
        """
        errors = []
        errors.extend(self._verify_schedule_policy())
        errors.extend(self._verify_user())
        errors.extend(self._verify_usergroup())
        errors.extend(self._verify_alert())
        errors.extend(self._verify_op_window())
        errors.extend(self._verify_schedule())
        return errors

    def verify_jobs_merge(self, vm: bool = True, fs: bool = False) -> list[str]:
        """
        Verifies all jobs of client are present in dest CS

        Args:
            vm  (bool)  -   verifies VM jobs merge if True  (default: True)
            fs  (bool)  -   verifies FS jobs merge if True  (default: False)

        Returns:
            errors  (list)  -   list of error strings indicating what jobs did not merge
        """
        errors = []
        if vm:
            vm_client = self.common_options["discovered_vm"]
            self.log.info("Verifying VM Jobs have merged")
            dest_jobs = set(self.get_client_jobs(vm_client).keys())
            src_jobs = set(
                self.common_options["source_obj"].get_client_jobs(vm_client).keys())
            if src_jobs | dest_jobs == dest_jobs:
                if src_jobs:
                    self.log.info("All jobs of VM in source CS are merged to CS of destination")
                else:
                    self.log.info("No jobs to verify merge, neither CS has VM job")
            else:
                missing_jobs = src_jobs - dest_jobs
                errors.append(f"Jobs of source VM failed to merge! missing->{missing_jobs}")
        if fs:
            fs_client = self.common_options["source_options"]["fs_client"]
            self.log.info("Verifying FS Jobs have merged")
            dest_jobs = set(self.get_client_jobs(fs_client).keys())
            src_jobs = set(
                self.common_options["source_obj"].get_client_jobs(fs_client).keys())
            if src_jobs | dest_jobs == dest_jobs:
                if src_jobs:
                    self.log.info("All jobs of FS in source CS are merged to CS of destination")
                else:
                    self.log.info("No jobs to verify merge, neither CS has FS job")
            else:
                missing_jobs = src_jobs - dest_jobs
                errors.append(f"Jobs of source FS failed to merge! missing->{missing_jobs}")
        return errors

    # test steps to be implemented

    """
    def verify_restore(self):
        TODO: Verifies migrated jobs can be used for restore without failure

    def verify_name_change(self):
        TODO: Verifies migrated client can be permanently installed on dest CS using name change

    def verify_namechange_prop(self):
        TODO: Verifies migrated clients with flag can be blocked from performing name change

    def verify_new_backup(self):
        TODO: Verifies the permanenly migrated client can be backed up using dest storage

    def clean_up(self):
        TODO: Util to try and clean up as much entities as possible
    """

    # other utils

    def get_client_jobs(self, client_name: str) -> dict:
        """
        Util to Get client jobs using qcommand to verify java GUI jobs listing

        Args:
            client_name (str)   -   name of client to view job history for

        Returns:
            client_jobs (dict)  -   dict of jobs of client with job id key and other data value
                                    as would be visible in java console
        """
        if not self.commcell_obj.clients.has_client(client_name):
            self.log.info(f"client {client_name} not found, so no jobs")
            return {}
        gui_resp = self.commcell_obj.execute_qcommand(
            f'qlist jobhistory -c {client_name}'
        )
        lines = gui_resp.text.split('\n')
        table = [line.split() for line in lines if line and '--' not in line]
        headers = table[0]
        data = {}
        for row in table[1:]:
            job_id = row[headers.index('JOBID')]
            data[job_id] = {
                headers[col_idx]: row[col_idx]
                for col_idx in range(len(headers))
                if headers[col_idx] != 'JOBID'
            }
        return data

    # non client merge utils

    def _expected_mismatch(self, obj, path: str) -> bool:
        """
        function to determine what entity properties should not be compared after migration

        Args:
            obj     (any)   -   the value stored in any private/public attribute inside a class
            path    (str)   -   the path to access that private/public variable

        Returns:
            True    -   if that comparison of that path is expected to fail and can be ignored
            None    -   if comparison must be done for that path
        """
        # ids may change and root commcell object should not be compared as it's expected to differ after migration
        if 'id' in path.lower() or 'commcell_object' in path.lower():
            return True
        # API endpoints/urls may change as the ID is changed, so ignore comparing those
        if isinstance(obj, str) and 'http://' in obj:
            return True
        # associations may not be preserved if the associated object is not migrated, so ignore while validating
        if 'assoc' in path.lower():
            return True

        src_policy = self.common_options["source_options"].get("policy")
        src_library = self.common_options["source_options"].get("library")
        has_policy = self.commcell_obj.storage_policies.has_policy(src_policy)
        # if associated library or policy did not migrate, ignore the differences due to that as its expected
        if not has_policy:
            if src_library.lower() in str(obj).lower() or src_policy.lower() in str(obj).lower():
                return True

    def _list_of_diffs(self, obj_diff) -> list[str]:
        """
        Util to get list of error messages indicating what properties did not merge among the entities

        Args:
            obj_diff    -   a deepdiff object with comparison results

        Returns:
            errors  (list)  -   list of error strings indicating what did not match
        """
        errors = []
        for diff_type in obj_diff:
            errors.append(f'---------{diff_type}---------')
            if isinstance(obj_diff[diff_type], dict):
                for k, v in obj_diff[diff_type].items():
                    errors.append(f'{k} = {v}')
            elif isinstance(obj_diff[diff_type], list):
                for diff_elem in obj_diff[diff_type]:
                    errors.append(diff_elem)
            else:
                errors.append(obj_diff[diff_type])
        return errors

    def _verify_schedule_policy(self) -> list[str]:
        """
        Util to get list of failures on schedule policy migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_scp = self.common_options["source_obj"].scp_obj
        if src_scp:
            if self.commcell_obj.schedule_policies.has_policy(src_scp.schedule_policy_name):
                dest_scp = self.commcell_obj.schedule_policies.get(src_scp.schedule_policy_name)
                obj_diff = DeepDiff(src_scp, dest_scp, exclude_obj_callback=self._expected_mismatch)
                errors = self._list_of_diffs(obj_diff)
                if errors:
                    errors.insert(0, "Schedule policies do not match!")
            else:
                errors.append("Schedule policy did not get migrated!")
        return errors

    def _verify_user(self) -> list[str]:
        """
        Util to get list of failures on user migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_user = self.common_options["source_obj"].user_obj
        if src_user:
            if self.commcell_obj.users.has_user(src_user.user_name):
                dest_user = self.commcell_obj.users.get(src_user.user_name)
                obj_diff = DeepDiff(src_user, dest_user, exclude_obj_callback=self._expected_mismatch)
                errors = self._list_of_diffs(obj_diff)
                if errors:
                    errors.insert(0, "Users do not match!")
            else:
                errors.append("User did not get migrated!")
        return errors

    def _verify_usergroup(self) -> list[str]:
        """
        Util to get list of failures on usergroup migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_ug = self.common_options["source_obj"].ug_obj
        if src_ug:
            if self.commcell_obj.user_groups.has_user_group(src_ug.user_group_name):
                dest_ug = self.commcell_obj.user_groups.get(src_ug.user_group_name)
                obj_diff = DeepDiff(src_ug, dest_ug, exclude_obj_callback=self._expected_mismatch)
                errors = self._list_of_diffs(obj_diff)
                if errors:
                    errors.insert(0, "User groups do not match!")
            else:
                errors.append("Usergroup did not get migrated!")
        return errors

    def _verify_alert(self) -> list[str]:
        """
        Util to get list of failures on alerts migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_alert = self.common_options["source_obj"].alert_obj
        if src_alert:
            if self.commcell_obj.alerts.has_alert(src_alert.alert_name):
                dest_alert = self.commcell_obj.alerts.get(src_alert.alert_name)
                # alert object has an alerts object stored, need to avoid comparing the total alerts
                obj_diff = DeepDiff(src_alert, dest_alert,
                                    exclude_paths='root._alerts_obj',
                                    exclude_obj_callback=self._expected_mismatch)
                errors = self._list_of_diffs(obj_diff)
                if errors:
                    errors.insert(0, "Alerts do not match!")
            else:
                errors.append("Alert did not get migrated!")
        return errors

    def _verify_op_window(self) -> list[str]:
        """
        Util to get list of failures on op window migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_opw = self.common_options["source_obj"].opw_obj
        if src_opw:
            try:
                dest_opw = self.commcell_obj.operation_window.get(name=src_opw.name)
            except Exception as exp:
                errors.append("Error during get operation window, likely did not get migrated!")
                errors.append(exp)
                return errors
            obj_diff = DeepDiff(src_opw, dest_opw, exclude_obj_callback=self._expected_mismatch)
            errors = self._list_of_diffs(obj_diff)
            if errors:
                errors.insert(0, "Alerts do not match!")
        return errors

    def _verify_schedule(self) -> list[str]:
        """
        Util to get list of failures on schedule migration

        Returns:
            errors  -   list of error strings indicating what failed to match
        """
        errors = []
        src_sch = self.common_options["source_obj"].sch_obj
        if src_sch:
            if self.commcell_obj.schedules.has_schedule(src_sch.name):
                dest_sch = self.commcell_obj.schedules.get(src_sch.name)
                # schedule object has an instance of class object
                # exclude it, as we do not want to compare the entity that has schedule
                # but only compare the schedule properties
                obj_diff = DeepDiff(src_sch, dest_sch,
                                    exclude_obj_callback=self._expected_mismatch,
                                    exclude_paths=['root.class_object'])
                errors = self._list_of_diffs(obj_diff)
                if errors:
                    errors.insert(0, "Schedules do not match!")
            else:
                errors.append("Schedule did not get migrated!")
        return errors
