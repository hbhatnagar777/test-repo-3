# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""snapconfigs file for validating IntelliSnap snapshot configuration

SNAPConfigs is the only class defined in this file

SNAPConfigs: snapconfigs class for validating IntelliSnap snapshot configuration

SNAPConfigs:

    __init__()                   --  initializes Snap configs object

    db_validation()              --  Validates snap config in the database

    remote_ma_validation()       --  Remote MA Validation

    func_validation()            --  Functionality Validation of Snapshot Config using log files

"""

from AutomationUtils import logger
from AutomationUtils.machine import Machine


class SNAPConfigs:
    """Configs class to validate snapshot configurations"""


    def __init__(self, commcell, client, agent, tcinputs, snapconstants):
        """Initializes Snapconstants object

            Args:
                commcell        (object)    --  commcell object

                client          (object)    --  client object

                agent           (object)    --  agent object

                tcinputs        (dict)      --  Test case inputs dictionary

                snapconstants   (object)    --  snapconstants object

        """

        self.commcell = commcell
        self.client = client
        self.agent = agent
        self.tcinputs = tcinputs
        self.snapconstants = snapconstants
        self.log = logger.get_log()


    def db_validation(self, config_name, config_value, vendor_name, array_name, config_level):
        """DataBase Validation of the Snapshot Configurations
            Args:
                config_name     (str)       name of the snapshot config
                config_value    (str)       snapshot config value
                vendor_name     (str)       snapshot vendor name
                array_name      (str)       name of the array
                config_level    (str)       snapshot config level
        """

        db_config_value = self.snapconstants.execute_query(self.snapconstants.get_snapconfig_value,
                                                           {'a': config_name,
                                                            'b': vendor_name,
                                                            'c': array_name,
                                                            'd': config_level}, fetch_rows='one')

        self.log.info("DataBase Value for the snapconfig :%s is :%s at level:%s" , config_name, db_config_value, config_level)
        self.log.info("Input Provided Value for the snapconfig :%s is :%s" , config_name, config_value)
        if config_value == db_config_value:
            self.log.info("DataBase validation for the SnapConfig : %s is successful" , config_name)
        else:
            raise Exception("DataBase Validation for SnapConfig: %s failed, DataBase Value is: %s"
                            " and Provided input Value is : %s " , config_name, db_config_value, config_value)

    def remote_ma_validation(self, jobid, logfile_name, str_list, client_machine):
        """Remote MA Validation using logs
            Args:
                jobid           (int)       jobid in which snap config needs to validate
                logfile_name    (str)       log file name in which config needs to validate
                str_list        (list)      String list to search
                client_machine  (obj)       client machine object
        """

        log_output = []
        for string in str_list:
            log_line = client_machine.get_logs_for_job_from_file(jobid, logfile_name, string)
            log_output.append(log_line)

        for output in log_output:
            if output is not None:
                self.log.info("log lines found are : \n%s" , output)
            else:
                raise Exception("*" * 5 +" Remote MA is *NOT* honored during Snap Operation" + "*" * 5)
        self.log.info("*" * 5 +" Remote MA is honored during Snap Operation" + "*" * 5)

    def func_validation(self, config_name, config_value, vendor_name, array_name, jobid, client_machine, options):
        """Functionality Validation of Snapshot Configuration
            Args:
                config_name     (str)       name of the snapshot config
                config_value    (str)       snapshot config value
                                            ex: for Remote MA its the Media Agent Name
                vendor_name     (str)       snapshot vendor name
                array_name      (str)       name of the array
                jobid           (int)       jobid in which snap config needs to validate
                client_machine  (obj)       client machine object
                options         (set)       operations to validate
                                            ex: for Remote MA : {'prepare', 'create', 'map', 'unmap',
                                            'revert', 'delete', 'recon', 'remote-prepare', 'remote-create'}
        """

        if vendor_name == 'NetApp':
            self.log.info("Validating Snap Config for NetApp")
            if config_name == 'Remote Snap MA':
                self.log.info("Validating NetApp Snap Config: Remote Snap MA")
                remote_machine = Machine(self.commcell.clients.get(config_value))
                if client_machine.os_info.upper() == 'WINDOWS':
                    s_optype = 249
                else:
                    s_optype = 248
                if remote_machine.os_info.upper() == 'WINDOWS':
                    d_optype = 715
                else:
                    d_optype = 714
                if 'prepare' in options:
                    self.log.info("Checking if the Remote MA is honoured in *prepare* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [2] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_GetVolumeAndPath]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_GetVolumeAndPath]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'create' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Create* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [3] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_CreateSnap]"
                    str_list = [str1, str2]
                    if client_machine.os_info.upper() == 'WINDOWS':
                        self.remote_ma_validation(jobid, "VssHWProvider.log", str_list, client_machine)
                    else:
                        self.remote_ma_validation(jobid, "CVFSSnap.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_CreateSnap]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'map' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Map* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [6] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_MapSnap]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_MapSnap]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'unmap' in options:
                    self.log.info("Checking if the Remote MA is honoured in *UnMap* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [7] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_UnmapSnap]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_UnmapSnap]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'delete' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Delete* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [5] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_DeleteSnap]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_DeleteSnap]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'revert' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Revert* Snap")
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(222) - Found RemoteMA [{config_value}] for array [{array_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [10] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_Revert]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_Revert]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'remote-prepare' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Remote-prepare* Snap")
                    svm_name = self.snapconstants.execute_query(self.snapconstants.get_svm_name, {'a': array_name}, fetch_rows='one')
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(207) - Found RemoteMA [{config_value}] for array [{svm_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [8] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_GetRelationshipDetails]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_GetRelationshipDetails]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

                if 'remote-create' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Remote-create* Snap")
                    svm_name = self.snapconstants.execute_query(self.snapconstants.get_svm_name, {'a': array_name}, fetch_rows='one')
                    str1 = f"{jobid} CvNetAppArrayOps::runArrayOp(207) - Found RemoteMA [{config_value}] for array [{svm_name}]"
                    str2 = f"{jobid} CvNetAppArrayOps::runArrayOp({s_optype}) - Setting metadata [9] for type[SM_MDT_REQ_TYPE]. Remote Op[OP_CreateRemoteSnaps]"
                    str_list = [str1, str2]
                    self.remote_ma_validation(jobid, "CVMA.log", str_list, client_machine)
                    str3 = [f"{jobid} cvso_execSnapEngineOp({d_optype}) - Request to execute operation[OP_CreateRemoteSnaps]"]
                    self.remote_ma_validation(jobid, "CVMA.log", str3, remote_machine)

        else:
            self.log.info("Validating Snap Config for Non-NetApp")
            if config_name in ['Remote Snap MA', 'Remote Snap MA (CCI engines)']:
                self.log.info("Validating Non-NetApp Remote Snap MA Snap Config")
                remote_machine = Machine(self.commcell.clients.get(config_value))

                if 'prepare' in options:
                    self.log.info("Checking if the Remote MA is honoured in *prepare* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    self.remote_ma_validation(jobid, "CVMA.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)

                if 'create' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Create* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    if client_machine.os_info.upper() == 'WINDOWS':
                        self.remote_ma_validation(jobid, "VssHWProvider.log", str1, client_machine)
                    else:
                        self.remote_ma_validation(jobid, "CVFSSnap.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)

                if 'map' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Map* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    self.remote_ma_validation(jobid, "CVMA.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)

                if 'unmap' in options:
                    self.log.info("Checking if the Remote MA is honoured in *UnMap* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    self.remote_ma_validation(jobid, "CVMA.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)

                if 'delete' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Delete* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    self.remote_ma_validation(jobid, "CVMA.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)

                if 'revert' in options:
                    self.log.info("Checking if the Remote MA is honoured in *Revert* Snap")
                    str1 = [f"{jobid} CVSnapOSUtil::executeOnRemoteMA() - Sending remote exec to Snap MA [{config_value}"]
                    self.remote_ma_validation(jobid, "CVMA.log", str1, client_machine)
                    str2 = [f"{jobid} CVMASnapHandlerInternal::execVolumeSnaps() - Request for execVolumeSnaps Succeeded"]
                    self.remote_ma_validation(jobid, "CVMA.log", str2, remote_machine)
