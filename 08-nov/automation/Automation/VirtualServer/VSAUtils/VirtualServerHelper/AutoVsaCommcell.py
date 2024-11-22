# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Commcell Helper

classes defined:
    AutoVSACommcell   - wrapper for commcell operations
"""

import os
import time

from cvpysdk.job import Job
from cvpysdk.commcell import Commcell
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils import logger, cvhelper
from cvpysdk.client import Clients
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from cvpysdk.subclients.vssubclient import VirtualServerSubclient
from VirtualServer.VSAUtils.VirtualServerConstants import CommcellEntityIds, CommcellEntity


class AutoVSACommcell(object):
    """
    class that act as wrapper for SDK and Testcase

    Methods:
            get_client_id()             - gets the client ID of given client name

            get_hostname_for_client()   - get the Host name for the given client

            get_base_dir()              - get the base directory of client given
                                        (default: Commserv client)

            get_client_os_type()           - get the os info of the client

            check_backup_job_type_expected()   - check the passed job id type and
                                                    passed job type is expeted

            _client_exist_in_cs()       - check if the client exist in CS

            get_job_duration()          - get the job duration of the job passed

            get_job_results_dir()                   - get the job results directory of the client
                                        (default: commserv client)
            get_snap_mount_status()     -   Returns the status of snap mount

            get_synth_backup_job_v2()   -   Returns the Synthful Job ID for v2 client

            get_vm_childjob()         -   Returns the backup job id for the child for v2 clients

            get_vm_parentjob()      - Returns the parent backup job id for the child backup job id for v2 clients

            dev_test_lab  - fetches the value for virtual lab from CS DB

            dev_test_virtual_lab_job - Performs Virtual Lab restore from Dev_Test_Group at Commcell level

            validate_lab_creation - check if lab exists in CS DB

            multi_stream_restore - checks the multi-stream attribute on the restored job.

            get_vm_management_job  - gets vm management job spawned by input job
    """

    def __init__(self, commcell, csdb, **kwargs):
        """
        Initialize the  SDK objects

        Args:
            commcell    (obj)   - Commcell object of SDK Commcell class

            csdb        (obj)   - CS Database object from testcase

        """

        self.metallic_ring_info = kwargs.get("metallic_ring_info", None)
        self.log = logger.get_log()
        self.log_dir = logger.get_log_dir()
        self.commcell = commcell
        self.csdb = csdb
        self.commserv_name = self.commcell.commserv_name
        self.cs_mssql = None
        self.is_metallic = kwargs.get('is_metallic', False)

        if self.metallic_ring_info:
            self.metallic_commcell = Commcell(self.metallic_ring_info['commcell'],
                                              commcell_username = self.metallic_ring_info['user'],
                                              commcell_password = self.metallic_ring_info['password'])
            self.metallic_csdb = CommServDatabase(self.metallic_commcell)
        if not self.is_metallic:
            try:
                self.base_dir = self.get_base_dir()
            except Exception as exp:
                self.log.info("Unable to get the base directorty as it might be a metallic case")

    def get_client_id(self, client_name):
        """
        Get the client ID for the given client

        Args:
                client_name     (str)   - Client name for whihc client Id
                                                                                need to be fetched

        Return:
                client_id   (int)       - Id of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            self.log.info("Getting the client ID for {0} ".format(client_name))
            _client_obj = self.commcell.clients.get(client_name)
            return _client_obj.client_id

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID {0}".format(err))
            raise err

    def run_backup_copy(self, storage_policy, skip_wait = False):
        """
        Run backup copy job for given storage policy


        Args:
            storage_policy   (str)   -- Name of the storage policy

            skip_wait        (bool)   -- Skips to wait for backup job to get completed

        Returns:
            JobID   Backup copy job ID

            Raise Exception::
                    if backup copy Job fails to run

        """
        try:
            storage_policy_object = self.commcell.storage_policies.get(storage_policy)
            query = "SELECT 1 from jmjobsnapshotstats(readuncommitted) where archgrpid = '"+storage_policy_object.storage_policy_id+"' and materializationstatus = 101 and disabled & 1 = 0"
            self.csdb.execute(query)
            output = self.csdb.fetch_all_rows()
            if output != [['']]:
                backupcopyjob = storage_policy_object.run_backup_copy()
                if not skip_wait:
                    if not backupcopyjob.wait_for_completion():
                        raise Exception("Failed to run job with error: "
                                        +str(backupcopyjob.delay_reason))
                    self.log.info("backup copy job triggered and completed successfully")
                return backupcopyjob
            else:
                self.log.info("No snaps to be backup copied")
        except Exception as err:
            self.log.exception("--Failed to run backupcopy job--")
            raise Exception

    def run_aux_copy(self, storage_policy, storage_policy_copy_name, media_agent):
        """
        Run aux copy job for given storage policy


        Args:
            storage_policy   (str)   -- Name of the storage policy

            storage_policy_copy_name (str)      -- storage policy copy name

            media_agent    (str)                 --Media agent on which Aux copy job to run
        Returns:
            JobID   Backup copy job ID

            Raise Exception::
                    if aux copy Job fails to run

        """
        try:
            self.log.info("starting Aux copy job")
            storage_policy_object = self.commcell.storage_policies.get(storage_policy)
            auxcopyjob = storage_policy_object.run_aux_copy(media_agent)
            self.log.info("auxcopy job triggered successfully")
            return auxcopyjob
        except Exception as err:
            self.log.exception("--Failed to run auxcopy job--")
            raise Exception

    def dev_test_lab(self, lab_name, isolated_network=False, **kwargs):
        """
        Fetches the value of vappName and vAppID from CS DB.
        Also validate if the Isolated network is configured in the Lab

        Args:

            lab_name (str) - Virtual App name which is configured under Dev-Test-Group

            isolated_network (bool) - if True then it will check the gateway template for Virtual Lab

            **kwargs : Arbitrary keyword arguments.

        Returns :
            dict with vAppName and vAppID

        Raises :
            Exception if Isolated_Network is to true but template is missing.
        """

        _query = "(select * from App_VirtualApp where name ='{0}')".format(lab_name)
        self.log.info(_query)
        self.csdb.execute(_query)
        _results = self.csdb.fetch_one_row()
        import xmltodict
        import json
        xmldict = xmltodict.parse(_results[4])
        if kwargs.get("snap"):
            copy = xmldict['Api_VirtualAppReq']['vApp']['config']['vmGroups']['vmSequence']
            if isinstance(copy, dict):
                if int(copy['@copyPrecedence']) != 1:
                    raise Exception("incorrect copy precedence is set at Lab policy")
            else:
                for vmName in copy:
                    if int(vmName['@copyPrecedence']) != 1:
                        raise Exception("incorrect copy precedence is set at Lab policy")
        if isolated_network:
            isolated_Network = json.dumps({'vmName': xmldict['Api_VirtualAppReq']['vApp']['policy']
            ['gatewayTemplate']['@vmName']})
            if 'vmName' not in isolated_Network:
                raise Exception("Gateway Template not defined")
        import ast
        vapp_prop = ast.literal_eval(
            json.dumps({'vAppId': xmldict['Api_VirtualAppReq']['vApp']['vAppEntity']['@vAppId'],
                        'vAppName': xmldict['Api_VirtualAppReq']['vApp']['vAppEntity']['@vAppName']}))
        for keys in vapp_prop:
            vapp_prop[keys] = int(vapp_prop[keys])
            break
        return vapp_prop

    def dev_test_virtual_lab_job(self, lab_name, isolated_network=False, **kwargs):
        """
        Performs Virtual Lab restore from Dev_Test_Group at Commcell level

        Args :

            lab_name (str) : lab_name from which Virtual lab job will start

            isolated_network (bool): If true then Lab will be created in Isolated network

            kwargs: Arbitrary keyword arguments

            Returns:
                 Virtual Lab job Id
        """

        if kwargs.get("snap"):
            entity = self.dev_test_lab(lab_name, snap=True, isolated_network=isolated_network)
        else:
            entity = self.dev_test_lab(lab_name, isolated_network=isolated_network)

        self.log.info(entity)
        from cvpysdk.dev_test_group import Dev_Test_Group
        lab_request = Dev_Test_Group(self.commcell)
        try:
            virtual_lab_job = lab_request.dev_test_lab_json(entity)
        except Exception as err:
            self.log.error("Exception in submitting Virtual Lab job : {0}".format(str(err)))
            raise Exception
        if virtual_lab_job:
            self.log.info("Virtual Management job is : " + str(virtual_lab_job.job_id))
            if not virtual_lab_job.wait_for_completion():
                raise Exception("Failed to run Virtual Management job {0} with error: {1}".format(
                    virtual_lab_job.job_id, virtual_lab_job.delay_reason))
        self.log.info("Job Status : {0}".format(virtual_lab_job.status))
        if 'one or more error' in virtual_lab_job.status:
            self.log.error("Virtual Management Job Completed with one or more errors")

        self.log.info("Validate Lab creation")
        self.validate_lab_creation(virtual_lab_job.job_id, lab_name)
        return virtual_lab_job.job_id

    def validate_lab_creation(self, virtual_lab_job, lab_name=None):
        """
        Validates the Virtual Lab creation in CS DB
        Args :
            virtual_lab_job (str) : Virtual Management job ID

            lab_name (str) : Lab policy under Dev-Test-Group
        Raises:
            Exception if the CS DB entry is null
        """
        if not lab_name:
            lab_name = "Lab"
        name = lab_name + "_" + virtual_lab_job
        _query = "(select * from App_VirtualLab where name ='{0}')".format(name)
        self.log.info(_query)
        self.csdb.execute(_query)
        _results = self.csdb.fetch_one_row()
        if len(_results) > 1:
            self.log.info("Virtual Lab created successfully")
        else:
            raise Exception("Virtual Lab Didn't get created")

    def get_control_host_id(self, subclient_name):
        """
        Get the Control Host ID of configured array for the given subclient

        Args:
                subclient_name     (str)   - subclient name for which control host Id
                                             of the configured storage array need to be fetched

        Return:
                control host id   (int)    - id of configured storage array for the given subclient

        Exception:
                if sub client does not exists in CS or no storage array is configured for the subclient

        """
        try:
            _query = "select id from APP_Application where subclientName = '{0}'". \
                format(subclient_name)

            self.csdb.execute(_query)
            AppId = self.csdb.fetch_one_row()
            _query = "select SMSnapId from SMVolume v,SMVolSnapMap vsm where v.AppId='{0}' and  " \
                     "v.SMVolumeId = vsm.SMVolumeId". \
                format(AppId[0])
            self.csdb.execute(_query)
            SMSnapId = self.csdb.fetch_one_row()
            _query = "select ControlHostId from SMSnap  where  SMSnapId='{0}'".format(SMSnapId[0])
            self.csdb.execute(_query)
            ControlHostId = self.csdb.fetch_one_row()
            return ControlHostId[0]

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the control host  ID {0}".format(err))
            raise err

    def get_backup_pending_jobs_to_replicate(self, vm_name):
        """
        Get the backup pending job to replicate for the given client

        Args:
                vm_name     (str)   - vm name for which backup jobs yet to replicate need to be fetched

        Return:
                pending_backup_jobids   (list)       - list of backup job Id's yet to replicate for the vm name given

        Exception:
                if vm name does not exists in CS

        """
        try:
            _query = "select BkpJobsToSync from APP_VSAReplication where sourceName = '{0}'". \
                format(vm_name)
            self.csdb.execute(_query)
            pending_backup_jobids = self.csdb.fetch_one_row()
            pending_backup_jobids = pending_backup_jobids[0].split(',')
            return pending_backup_jobids

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the backup pending jobs to replicate {0}".format(
                    err))
            raise err

    def formulate_solr_query(self, subclient_name, browse_ma):
        """
        Formulate SOLR URL using the VM Datasource value retrieved from cvvscatalog log
        Args:
                subclient_name  (str)   -  subclient name for which  datsourceId
                                             of the configured SOLR need to be fetched.

                browse_ma      (str)   -  MA name where SOLR server is configured.

        Raises:
            Exception:
                if there's any exception while formulating the URL
        """
        try:
            _query = "(select bsp.attrVal from (select bsn.id from APP_BackupSetName bsn inner join APP_Application " \
                     "a on bsn.id = a.backupSet where a.subclientName = '{0}') as B inner join " \
                     "APP_BackupSetProp bsp on B.id = bsp.componentNameId and bsp.attrName = " \
                     "'Indexing datasource id')" \
                .format(subclient_name)
            self.log.info(_query)
            self.csdb.execute(_query)
            data_source_id = self.csdb.fetch_one_row()
            _query = "(SELECT CI.ActualCoreName    FROM SEDataSource DS INNER JOIN SECollectionInfo CI ON DS.CoreId " \
                     "= CI.CoreId AND DS.DatasourceId = {0})".format(data_source_id[0])
            self.csdb.execute(_query)
            data_source_name = self.csdb.fetch_one_row()
            solr_url = "http://" + browse_ma + ":20000/solr/" + data_source_name[0] + \
                       "/select?q=AchiveFileId:"
            self.log.info("Formulated SOLR URL: %s", solr_url)
            return solr_url
        except Exception as exp:
            self.log.exception("Exception when formulating SOLR URL. %s", str(exp))
            raise exp

    def get_child_jobs(self, job_id):
        """

        Fetch all child job ids given parent job id

        Args:
            job_id          (str)   --  Parent Job ID

        Returns:
            child_job_ids   (list)  --  List containing child job IDs

        """
        _query = f"select childJobId from jmjobdatalink where parentJobId={job_id}"
        self.csdb.execute(_query)
        _results = self.csdb.fetch_all_rows()
        child_job_ids = [row[0] for row in _results]
        return child_job_ids

    def get_hostname_for_client(self, client_name=None):
        """
        Get the Host name for the given HostName

        Args:
                client_name     (str)   - Client name for which client Id
                                                                                need to be fetched
                                             default value is  commsev_name

        Return:
                host_name   (int)       - Hostname of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            self.log.info("Getting HostName for Client for %s " % client_name)
            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.client_hostname

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID %s" % err)
            raise err

    def get_instanceno_for_client(self, client_name=None):
        """
        Get the instance number for the given HostName

        Args:
                client_name     (str)   - Client name for which client Id
                                                                                need to be fetched
                                             default value is  commsev_name

        Return:
                instance  (str)       - Instance number of the client name given

        Exception:
                if client does not exists in CS

        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            self.log.info("Getting HostName for Client for %s " % client_name)
            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.instance

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the instance number %s" % err)
            raise err

    def get_client_name_from_hostname(self, host_name):
        """
        Get the Host name for the given HostName

        Args:
                host_name     (str)   - host name  for which client name
                                                                                need to be fetched

        Return:
                client_name   (int)       -client name of the client from the given hostname

        Exception:
                if client does not exists in CS

        """
        try:

            self.log.info("Getting client name for Client for %s " % host_name)
            _query = "select name from APP_Client where net_hostname = '%s'" % host_name

            if self.is_metallic:
                self.metallic_csdb.execute(_query)
                _results = self.metallic_csdb.fetch_one_row()
            else:
                self.csdb.execute(_query)
                _results = self.csdb.fetch_one_row()
            return _results[0]

        except Exception as err:
            self.log.exception(
                "An exception occured in getting the client ID %s" % err)
            raise err

    def statuscheck(self, op_id, entity_id, status, backupsetname=None, clientname=None, jobid=None):
        """
        Check status of backupset, client and job from the data base

        Args:
            op_id  (int)   -   operation id (op_id) user input passed in test case file
                                to check status

            entity_id (int)   -   entity_id passed in test case file to determine status of
                                    backupset/client/job
            backupsetname (list) - backupset name to check status
            clientname  (list)  - client name to check status
            jobid (list) - jobid to check status
            status- deleted, deconfigured, configure, present
        Raise Exception:
                Failed to get status of client/backupset/job from Data base

        """
        try:

            if op_id == CommcellEntityIds.BACKUPSETSTATUS.value:
                if entity_id == CommcellEntity.Backupset.value:
                    for eachname in backupsetname:
                        query = "SELECT status from APP_BackupSetName where Name = '" + eachname + "'"
                        self.csdb.execute(query)
                        output = self.csdb.fetch_all_rows()
                        if output == [['']]:
                            if status == 'deleted':
                                self.log.info('Backupset got deleted which is expected')
                            else:
                                self.log.error('Not expected backupset status. Expected status: ' + status)
                                raise Exception
                        else:
                            if status == 'present':
                                self.log.info("Backupset is present")
            if op_id == CommcellEntityIds.CLIENTSTATUS.value:
                if entity_id == CommcellEntity.client.value:
                    for eachname in clientname:
                        query = "SELECT status from APP_CLIENT where Name = '" + eachname + "'"
                        self.csdb.execute(query)
                        output = self.csdb.fetch_all_rows()
                        if status == 'configured':
                            if output == [['0']]:
                                self.log.info('client is in configure state which is expected')
                            else:
                                self.log.error('client is not in configure state which is not expected')
                                raise Exception
                        elif status == 'deconfigured':
                            if output == [['2']]:
                                self.log.info('client is in deconfigure state which is expected')
                            else:
                                self.log.error('client is not in  deconfigure state which is not expected')
                                raise Exception
                        elif status == 'deleted':
                            if output == [['']]:
                                self.log.info('client got deleted  which is expected')
                            else:
                                self.log.error('client is not in deleted state: ' + status)
                                raise Exception
                        elif status == 'notdeleted':
                            if output != [['']]:
                                self.log.info('client did not get deleted')
                            else:
                                self.log.error('client is in the deleted state: ' + status)
                                raise Exception
            if op_id == CommcellEntityIds.JOBSTATUS.value:
                if entity_id == CommcellEntity.job.value:
                    for eachjob in jobid:
                        query = query = "SELECT distinct jmbkpstats.jobid FROM jmbkpstats INNER " \
                                        "JOIN JMJobDataLink ON jmbkpstats.jobId = JMJobDataLink.parentjobid " \
                                        "INNER JOIN APP_VMProp on jmbkpstats.jobId = APP_VMProp.jobId where " \
                                        "jmbkpstats.jobid = '" + eachjob + "'"
                        self.csdb.execute(query)
                        output = self.csdb.fetch_all_rows()
                        if output == [['']]:
                            if status == 'deleted':
                                self.log.info('Backup job got deleted which is expected')
                            else:
                                self.log.error('Not expected Backup job status. Expected status: ' + status)
                                raise Exception
                        else:
                            if status == 'present':
                                self.log.info("Backupjob is present")
        except Exception as err:
            self.log.exception("--Failed to get the status--")
            raise Exception

    def get_base_dir(self, client_name=None):
        """
        Get the base directory for the commvault installation

        Args:
                client_name     (str)   - Client name for which client Id
                                                                        need to be fetched
                                            default value is    (str)   commsev_name

        Return:
                base_dir    (int)       - installtion base dir of simpana in that client

        Exception:
                if client does not exists in CS
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            _base_dir = os.path.join(_client_obj.install_directory, "Base")
            return _base_dir

        except Exception as err:
            self.log.exception("Error in getting the base directory %s" % err)
            raise err

    def get_client_os_type(self, client_name=None):
        """
        Gets the OS type [Windows / Unix] of the client

        Args:
                client_name     (str)   - Client name for which os info
                                                                        need to be fetched
                                            default value is    commsev_name
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.os_info

        except Exception as err:
            self.log.exception(
                "An error occured in getting the OS version of the client")
            raise err

    def check_backup_job_type_expected(self, job_id, job_type):
        """
        check if the Job Type is expected

        Args:
                job_id      (int)   - job id which needs to be checked

                job_type    (str)   - the job type which the job id provided
                                        to be verified with

        Exception:
                if the job type is not expected

                if the job does not exist

        """
        try:
            _job_info = Job(self.commcell, job_id)
            _job_type_from_cs = _job_info.backup_level
            if (_job_type_from_cs.lower()) == (job_type.lower()):
                self.log.info("Ok.The job was %s" % job_type)
            else:
                raise Exception(
                    "Job type was for the job id {0} is {1} which is not expected".format(
                        job_id, job_type))

        except Exception as errrr:
            self.log.exception(
                "An exception occurred in CheckJobTypeIsExpected")
            raise errrr

    def _client_exist_in_cs(self, client_name):
        """
        check particular client exist in CS

        Args:
                client_name (str)   - client which has to be chacked that it exist in CS

        Return:
                True - If exists

                False- if does not exist
        """
        try:
            return self.commcell.clients.has_client(client_name)

        except Exception:
            return False

    def get_job_duration(self, job_id):
        """
        get the Duration of the particular Job

        Args:
                job_id (int)   -- job id for which duratiuon has to be fetched

        Exception:
                if job does not exist
        """
        try:
            _job_info = Job(self.commcell, job_id)
            _job_duration = (_job_info.end_time - _job_info.start_time)
            return _job_duration

        except Exception as errrr:
            self.log.exception("An exception occurred in GetJobDuration")
            raise errrr

    def multi_stream_restore(self, job_id):
        """
        It will check the rstattribute which gets set in the restore job history for
        multi-stream

        Args:
                job_id (str) -- File level restore jobID

        Exception:
                if rstattribute value is 0
        """
        try:
            _query = "(select * from JMRestoreStats where jobid ='{0}')".format(job_id)
            self.log.info(_query)
            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if '67141632' in _results:
                self.log.info("*****Multi-streams were used during restore******")
            else:
                raise Exception("****Restore completed using single stream*****")
        except Exception as err:
            self.log.exception("File level restore didn't happen via Multi-stream")
            raise err

    def get_job_results_dir(self, client_name=None):
        """
        Get the Job Results Directory

        Args:
                client_name (str)   -- client name for which simapana isntalled
                                            Job results directory has to be fetched
                                default value is     - commserv_name

        Exception:
                if client does not exist in cs
        """
        try:
            if client_name is None:
                client_name = self.commserv_name

            _client_obj = self.commcell.clients.get(client_name)
            self.log.info(
                "Successfully got {0} client object".format(client_name))
            return _client_obj.job_results_directory

        except Exception as err:
            self.log.info("Failed to compute Job results Directory")
            raise err

    def find_primary_copy_id(self, sp_id):
        """
        find the primary copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                primary copy id of that storage policy
        """

        try:
            _query = "select copy from archgroup AG,archGroupCopy AGC where AGC.type = 1 and \
            AGC.isSnapCopy = 0 and  ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred getting Sp details details")

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in find_primary_copy_id ")
            raise err

    def get_vm_management_jobs(self, job_id):
        """
        Gets vmmanagement job spawned by input job

        Args:
                job_id   (int)   : job Id

         Return:
               list of job id

        """

        query = f"select jobId from TM_JobOptions where optionId = {807442144} and value = {job_id}"
        self.csdb.execute(query)
        return [int(job) for job in self.csdb.fetch_all_rows()[0] if job]

    def get_snapshot_metadata_forjob(self, job_id):
        """Gets the snapshot Metadata entry in db for job
            args:
                job_id (str): job_id for which query has to be performed
            return:  (list) : list of all Metadata entry  for JOb


        """
        query = f"select  e.SourceGUID,d.MetaData  from SMMetaData d," \
                f"(select s.SMSnapId,a.SourceGUID from SMVolSnapMap s,SMVolume a" \
                f" where s.SMVolumeId = a.SMVolumeId and a.jobID = {job_id}) e" \
                f" where e.SMSnapId = d.RefId "
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        if not result:
            raise Exception(
                "An exception {0} occurred in executing the query {1}".format(result, query))
        return result

    def execute(self, query):
        """
        Executes the query passed and return the first row of value
        :param query: Query to be executed against CSDB
        :return:
            value : first row of query executed
        """

        try:
            self.csdb.execute(query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception {0} occurred in executing the query {1}".format(_results, query))

            return _results[0]

        except Exception as err:
            self.log.exception("An Aerror occurred in executing the db statements ")
            raise err

    def find_snap_copy_id(self, sp_id: object) -> object:
        """
        find the snap copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                snap copy id of that storage policy
        """

        _query = "select copy from archgroup AG,archGroupCopy AGC where AGC.isSnapCopy = 1 and \
                                    ag.id = AGC.archGroupId and AGC.archGroupId = '%s'" % sp_id

        return self.execute(_query)

    def find_aux_copy_id(self, sp_id, copy_name="Aux"):
        """
        find the aux copy id of the specified storage policy

        Args:
                sp_id   (int)   : storage policy id

        Return:
                aux copy id of that storage policy
        """

        _query = "select copy from archgroup AG,archGroupCopy AGC where \
                            ag.id = AGC.archGroupId and AGC.archGroupId = {0} and AGC.name = '{1}'".format(
            sp_id, copy_name)

        return self.execute(_query)

    def find_app_aware_jobs(self, vsa_backup_job):
        """
        Get the workflow Job and IDA backup job id provided the VSA backup job
        :param vsa_backup_job:  VSA Backup Job ID
        :return:
            workflow_job : Work flow job ID for the VSA backup Job
            IDA_job      : IDA Job id for VSA backup job
        """

        try:
            _query = "select childjobId  from jmVSAAppJobLink \
                            where Parentjobid = %s" % vsa_backup_job
            ida_job_id = self.execute(_query)

            _query1 = "select workFlowjobId  from jmVSAAppJobLink\
                            where Parentjobid = %s" % vsa_backup_job
            workflow_job = self.execute(_query1)

            return ida_job_id, workflow_job

        except Exception as err:
            self.log.exception("An Error {0} occurred in find_aux_copy_id ".format(err))
            raise err

    def check_cbt_status(self, backup_type, subclient_obj, job_id=None):
        """
        Check CBT status for the backed up VMs according to backup type

        Args:
                backup_type    (string) - FULL/INCR/DIFF/SYNTH_FULL
                subclient_obj   (obj) - Subclient sdk object
                job_id         (int) - Job ID for which CBT status is needed
                                         else last jobID is used
        Raise Exception:
                If CBT status for given VM for given backup type is unexpected
        """
        try:
            if job_id is None:
                job_id = subclient_obj.find_latest_job(include_active=False)
            if backup_type == "FULL":
                cbt_status = r'Enabled'
            else:
                cbt_status = r'Used'
            _query = "SELECT attrVal from APP_VMProp where attrName = 'vmCBTStatus' " \
                     " and jobId ={0}".format(job_id._job_id)
            self.csdb.execute(_query)

            _results = self.csdb.fetch_all_rows()

            for result in _results:
                if result[0] != cbt_status:
                    raise Exception(
                        "cbt_status for the VM is not {0}, it is {1}".format(
                            result[0], cbt_status))

            self.log.info("The CBT status for all the VMs is {0} ".format(cbt_status))

        except Exception as err:
            self.log.exception(
                "Exception while checking the CBT status on the recent backuped VMs:" + str(err))
            raise err

    def backup_time_check(self, subclient, full_bkp_time):
        """
            Comapre and verify if time taken by incremental job is not more
            than 60% of as taken by FUll backup job
            Args:
                subclient          (obj):  Corresspoding subclient object
                full_bkp_time      (str):  Time taken by FUll  job

            Returns:
                True            (boolean): if verficiation check succeeds
                False           (boolean): if check fails

            Raises:
                Exception:
                    if failed to perform verificaton check
        """
        try:
            incr_job_id = subclient.find_latest_job(include_active=False)
            _job_info = Job(self.commcell, incr_job_id._job_id)
            total_time = int(_job_info._summary['jobEndTime']) - int(
                _job_info._summary['jobStartTime'])
            if total_time > 0.6 * int(full_bkp_time):
                self.log.info("Time taken verification for incremental backup failed")
                return False
            else:
                self.log.info("Time taken verification for incremental backup succeedded")
                return True

        except Exception as err:
            self.log.exception(
                "Exception while backup time check" + str(err))
            raise err

    def find_job_transport_mode(self, vsa_backup_job):
        """
        Find and return the Transport mode for the job
        Args:
            vsa_backup_job          (str):  Job id

        Returns:
            transport_mode          (str):  Transport mode of the job

        Raises:
            Exception:
                if failed to get the transport mode for the backup job
        """
        try:
            _query = " select attrVal from APP_VMProp where attrName like 'vmTransportMode' and " \
                     "jobid = %s" % vsa_backup_job
            transport_mode = self.execute(_query)
            return transport_mode
        except Exception as err:
            self.log.exception(
                "Exception while getting transport mode for the job " + str(err))
            raise err

    def live_browse_get_ds_info(self, vsa_backup_job):
        """
        To get the list of DS currently mounted

        Args:
            vsa_backup_job          (str):  Job id

        Returns:
            ds_list                 (list): List of DS currently mounted

        Raises:
            Exception:
                if failed to get the browse ds information

        """
        try:
            _query = "select MountDevice from SMVolume where SMVolumeId in " \
                     "(select SMVolumeId from SMSnapResource) and JobId=%s" % vsa_backup_job
            self.csdb.execute(_query)
            ds_list = self.csdb.fetch_all_rows()
            if not ds_list:
                raise Exception("An exception occurred getting server details")
            return ds_list
        except Exception as err:
            self.log.exception(
                "Exception while getting transport mode for the job " + str(err))
            raise err

    def get_snap_mount_status(self, snap_backup_job):
        """
            Returns the status of snap mount

            Args:
                snap_backup_job             (str): Snap Backup Job ID

            Returns:
                The Snap mount status
        """
        _query = f"""select MountStatus from SMVolume WHERE JOBID ='{snap_backup_job}'"""
        mount_status = self.execute(_query)
        return mount_status

    def get_synth_backup_job_v2(self, eachvm):
        """
        Returns the Synthful Job ID for v2 client

        Args:
            eachvm              (str)   : The vm for the which Synthful Job is is to be fetched

        Returns:
            The Synthful Job ID for v2 client
        """
        _query = f"""select jobId from JMBkpJobInfo where bkpLevel = 64 and applicationId in (
        select id from app_application where backupset in (select ChildBackupSetId from app_vmbackupset 
        where vmclientid in (select id from app_client where name = '{eachvm}'))) order by jobId desc"""
        job_id = self.execute(_query)
        if len(job_id) == 0:

            _query = f"""select TOP 1 jobId from JMBkpStats where bkpLevel = 64 and appId in (
                                select id from app_application where backupset in (
                                select ChildBackupSetId from app_vmbackupset where vmclientid in (
                                select id from app_client where name = '{eachvm}'))) order by jobId desc"""
            job_id = self.execute(_query)
            if len(job_id) == 0:
                raise Exception("Couldnt fetch v2 Synthfull backup id")
            else:
                return job_id

    def get_vm_childjob(self, vm, _parentbackupjob):
        """
        Returns  the child backup job id of vm from parent backup job for v2 clients
        Args:
            vm          (str) : the vm name for which the backup job is run
            _parentbackupjob (str) : parent admin backup job id of child job

        Returns:
            The backup job id for the child
        """
        _query = f"""select childJobId from JMJobDataLink where childAppid in (select id from 
                           APP_Application where clientId in (select id from App_client where displayname ='{vm}')) and 
                           parentJobId = '{_parentbackupjob}'"""

        _childjob = self.execute(_query)
        return _childjob

    def get_vm_parentjob(self, _childbackupjob, _linkType):
        """
        Returns  the parent backup job id of vm from child backup job for v2 clients
        Args:
            _childbackupjob          (str) : child backup job id for which parent job id to be found
            _linkType                (int) : link type in JMJobDataLink
        Returns:
            The parent backup job id for the child job id
        """
        _query = f"""select parentjobid from JMJobDataLink WITH (NOLOCK) where childJobId = '{_childbackupjob}' and linkType ='{_linkType}'"""
        _parentjob = self.execute(_query)
        return _parentjob

    def check_if_discovered_client(self, client):
        """
        Returns if the client is a discovered client or not

        Args:
            client      (str): Client to be checked

        Returns:
            True or False {Client is discovered or not}

        """
        _query = f"""select specialClientFlags from APP_Client where name = '{client}'"""

        flag = self.execute(_query)
        if flag == '11':
            return True
        else:
            return False

    def check_v2_indexing(self, client):
        """
        Checks whether the client is v1 or v2

        Args:
            client      (str) : Client to be checked

        Retuns:
           True or False {Client is v2 or not}
        """
        _query = f"""select attrVal from App_ClientProp where componentNameID = 
        (select id from APP_Client where name = '{client}' and attrName = 'IndexingV2_VSA')"""
        attr_val = self.execute(_query)
        if attr_val == '1':
            return True
        else:
            return False

    def get_snap_proxy_mount_status(self, snap_backup_job, copy_id):
        """
            Returns the status of snap proxy mount status from smmount table

            Args:
                snap_backup_job             (str): Snap Backup Job ID
                copy_id                     (int): Copy id of a copy

            Returns:
                The Snap mount status '59' else value other than '59' then it is not mounted
        """
        _query = f"""select MountStatus from SMMountVolume where SMVolumeId in (select SMVolumeId from SMVolume  WHERE 
        JOBID ='{snap_backup_job}' and copyid='{copy_id}') """
        mount_status = self.execute(_query)
        return mount_status

    def mount_type_esxmount_or_proxylessmount(self, snap_backup_job, copy_id):
        """
            Returns value whether mount is esx mount or proxyless mount
            Note:
                (for Proxy mount values: 0, 4,5,6 and for esx mount values: 1,2)
            Args:
                snap_backup_job             (str): Snap Backup Job ID
                copy_id                     (int): Copy id of a copy
            Returns:
                the numberic value which indicates 1,2 are proxyless mount else esx mount
        """
        _query = f"""select MountOptions from SMMountVolume where SMVolumeId in (select SMVolumeId from SMVolume  WHERE 
           JOBID ='{snap_backup_job}' and copyid='{copy_id}') """
        mount_type = self.execute(_query)
        return mount_type

    def get_live_mount_share_name(self, live_mount_job):
        """
        Returns the snap backup job id for the child for v2 clients
        Args:
            live_mount_job          (str) : the job id for which the share name to get

        Returns:
            The share name for the job
        """
        _query = f"""Select shareName from APP_3DFSVSAExportProps where jobId = '{live_mount_job}'"""

        share_name = self.execute(_query)
        return share_name

    def get_parentjob_using_wf(self, work_flow_job_id):
        """
            Gets parent backup copy job id using work flow job id
        Args:
            work_flow_job_id          (str) : work flow job id for which parent job id to be found
        Returns:
            The parent backup job id
        """
        query = "select jobid from JMBkpJobInfo where jobid in" \
                 "(select childJobId from JMJobWf where jobid = '" + work_flow_job_id + "'" \
                 "and childJobId in (select parentjobid from JMJobDataLink where linktype = 7))"
        self.csdb.execute(query)
        parentjob = self.csdb.fetch_all_rows()
        return parentjob[0][0]

    def get_job_extent_restarbility(self, job_id):
        """
        Returns  the extent number for a disk.
        
        For example - VM has 1000 extents to be backed up for a single disk. Suspend the job.
        Upon resuming we get the extent ID for a disk until what extent it got backed up after we do suspend.
        Disk got backed up until extent 300 and we do suspend. upon resuming we get 300(extent ID) along with disk number.
        This is restart string and once the job is completed we no longer see this string in the DB.                   
        SAMPLE - ['1|2208', '3|2485'] - 1 and 3 are  disk numbers and 2208 and 2485 are extent ID's
        
        Args:
            job_id          (str) : job id for which we need extent id
        Returns:
            The extent ID along with disk number
        """
        query = "select attributeValue from JMJobOptions where attributeName = 'Restart string' and  jobid in" \
                    "(select childJobId from JMJobDataLink where parentJobId = '" + job_id + "')"
        self.csdb.execute(query)
        restart_string = self.csdb.fetch_all_rows()
        return restart_string

    def get_archive_fileid(self, jobid):
        """
        Get archive fileid and isvalid values for the each job

        Args:

        job_id  (list)   -   Backup job id

        Returns:
            archive file ID (Dict) -- archfileid
            isValid (Dict)-- isvalid value

        Raise Exception:
                if fails to get archive file ID/isValid
        """
        try:
            archfiles = {}
            for each_job in jobid:
                query = "select id, isValid from archFile where jobid= '" + each_job + "'"
                self.csdb.execute(query)
                queryoutput = self.csdb.fetch_all_rows()
                archfiles[each_job] = queryoutput
            return archfiles
        except Exception as err:
            self.log.exception(
                "Failed to get archivefile ID/Isvalid value:" + str(err))
            raise err

    def get_IndexCache_location(self, Indexservername):
        """
        Get the index cache location for the Given Index Server

        Args:
            indexservername     (str)    --  Index Server name

        Returns:
            (str)                    --    The Index Cache path of the Index Server

        Raises:
            Exception if failed to get Index Cache location
        """
        try:
            query = "select attrVal from app_clientprop where attrName = 'Idx: cache path' and componentNameId=" \
                    "(select id from app_client where name =  '" + Indexservername + "')"
            self.csdb.execute(query)
            if not self.csdb.rows:
                raise Exception('Unable to get IndexCache directory for the Index Server %s',
                                Indexservername)

            return self.csdb.fetch_one_row()[0]

        except Exception as err:
            self.log.exception("Exception while getting IndexCache directory " + str(err))
            raise err

    def get_rfc_archfile_count(self, jobid):
        """
        Get the RFC Archive File count

        Args:
            jobid        (str)    --     Job ID

        Returns:
            (str)    -- count of RFC Arch Files

        Raises:
            Exception if failed to get Arch files
        """
        try:
            _query = "select count(*) from archfile where name ='RFC_AFILE' and jobId=%s" % jobid
            self.csdb.execute(_query)

            if not self.csdb.rows:
                raise Exception("RFC Arch file failed to  create with backup%s ", str(jobid))
            return self.csdb.fetch_one_row()[0]

        except Exception as err:
            self.log.exception("Exception while getting RFC Arch files for the job " + str(err))
            raise err

    def get_Child_subclient_GUID_list(self, jobid):
        """
        Get the list of Child SubClient GUID, Child JobID, Child VM GUID

        Args:
            jobid    (str) -- Parent Job ID

        Returns:
            (list)    -- list of Child SubClient GUID, Child JobID, Child VM GUID

        Raises:
            Exception if failed to get the list
        """
        try:
            _query = "Select a.GUID, b.childJobId, c.GUID from APP_Application a \
                            INNER JOIN JMJobDataLink b \
                            ON a.id = b.childAppid \
                            INNER JOIN App_Client c \
                            ON a.clientId = c.id \
                            where parentJobId = %s" % jobid
            self.csdb.execute(_query)

            child_guid_list = self.csdb.fetch_all_rows()
            if not child_guid_list:
                raise Exception(
                    "Failed to get Child SubClient GUID - ChildJobID list for Parent Job %s ",
                    str(jobid))

            return child_guid_list

        except Exception as err:
            self.log.exception(
                "Exception while getting Child SubClient GUID - ChildJobID list for Parent Job " + str(
                    err))
            raise err

    def get_backup_phase_status(self, backup_job_id):
        """
        Get status of each phase of a Backup

        Args:
            backup_job_id    (string):     backup job ID

        Raises:
            Exception:
                if there's any exception while getting phase status
        """
        try:
            self.log.info("Getting phases for Backup Job %s " % backup_job_id)
            _query = "select Status from JMBkpAtmptStats where jobID = '%s'" % backup_job_id
            self.log.info(_query)
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            self.log.info(_results)
            for each_phase_status in _results:
                self.log.info(each_phase_status)
                if str(each_phase_status[0]) != "1":
                    raise Exception(
                        "Backup job did not complete successfully. One of the phases failed.")
        except Exception as exp:
            self.log.exception("Exception when getting Backup Job details: %s", str(exp))
            raise exp

    def create_pesudo_client(self, name, client_name, vcenter_hostname, vcenter_username, vcenter_password, proxies):
        """
        check if client exists and if exits delete the client before creating new VMware client


        Args:
            name   (list)   -- Name of the client to delete
            client_name (str) -- Name pesudo client
            vcenter_hostname (str) -- Vcenter hostname
            vcenter_hostname (str) -- Vcenter username
            vcenter_password (str) -- Vcenter password
            Proxies (list) -- Proxies clients

        Returns:
            new client object

            Raise Exception::
                    if failed to create pesudo client

        """
        try:
            self.log.info(
                '-checking if client exist and delete if exist-')
            clients = Clients(self.commcell)
            for eachitem in name:
                cliententry = clients.has_client(eachitem)
                if cliententry == True:
                    clients.delete(eachitem)
                    clients.refresh()
                    self.log.info('-Client deleted successfully-')
            self.log.info('-creating new VMware Hypervisor -')
            newclient = clients.add_vmware_client(client_name, vcenter_hostname, vcenter_username, vcenter_password,
                                                  proxies)
            self.log.info('-New Hypervisor created successfully -')
            return newclient
        except Exception as err:
            self.log.error('--Vmware Hypervisor creation failed--')
            raise Exception

    def run_data_aging(self):
        """
        runs data aging job.

        Returns:
            JobID   data aging job ID

            Raise Exception::
                    if data aging Job fails to run
        """
        try:
            agingjob = self.commcell.run_data_aging(copy_name=None,
                                                    storage_policy_name=None)
            if not agingjob.wait_for_completion():
                raise Exception("Failed to run data aging with error: {0}"
                                .format(agingjob.delay_reason))
            self.log.info("backup copy job triggered successfully")
            return agingjob
        except Exception as err:
            self.log.exception("--Failed to run data aging job--")
            raise Exception

    def update_job_time(self, jobid, starttime, endtime, sqlobj):
        """
        updates job start date and end date on DB
        Args:
        job_id  (list)   -   Backup job id to which start and end date to be updated
        starttime (str) -    Startdate in unix timestamp
        endtime (str) -      End date in unix timestamp to update for job
        sqlobj (obj)-         sql server obj
        Raise Exception:
                if fails to update start and end date for a job
        """
        try:
            query = "UPDATE jmbkpstats SET servStartDate = '" + starttime + "', servEndDate ='" + endtime + \
                    "' WHERE jobid = '" + jobid + "'"
            job = sqlobj.execute(query)
        except Exception as err:
            self.log.exception(
                "Failed to update start and end date for a job:" + str(err))
            raise err

    def get_backup_job_archive_files(self, job_id, q_filter=None):
        """
        Given a child backup job, get the associated archive file IDs that have flags 64 or 65600

        Args:
            job_id    (string):     child backup job ID

            q_filter               (string):   Adding any filter to fetch arch file id

        Returns:
            a list of Archive File IDs

        Raises:
            Exception:
                if there's any exception while retrieving the archive file IDs from the CS DB
        """
        try:
            self.log.info("Querying CS DB to get archive file IDs")
            if q_filter:
                _query = f"select id from archFile where jobid = {job_id} and {q_filter}"
            else:
                _query = f"select id from archFile where jobid = {job_id} and name not in" \
                         f" ('IdxLogs_V1', 'RFC_AFILE') order by cTime desc"
            if self.is_metallic:
                from cvpysdk.commcell import Commcell
                from AutomationUtils.database_helper import CommServDatabase
                if self.metallic_ring_info:
                    temp_commcell = Commcell(self.metallic_ring_info['commcell'],
                                             commcell_username=self.metallic_ring_info['user'],
                                             commcell_password=self.metallic_ring_info['password'])
                    temp_csdb = CommServDatabase(temp_commcell)
                    self.log.info(_query)
                    temp_csdb.execute(_query)
                    _results = temp_csdb.fetch_all_rows()
                    archive_file_list = []
                    for archive_file in _results:
                        archive_file_list.append(archive_file[0])
                    return archive_file_list
            else:
                self.log.info(_query)
                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
                archive_file_list = []
                for archive_file in _results:
                    archive_file_list.append(archive_file[0])
                return archive_file_list

        except Exception:
            self.log.exception(
                "Exception when querying the CS DB to retrieve Archive File IDs for Backup Job %s",
                job_id)

    def get_nfs_server_cache(self, ma_name):
        """

        Args:
            ma_name                         (String):   name of the media agent

        Returns:
            path of the nfs server cache

        Raises:
            Exception:
                if it fails to do get nfs server cache
        """
        try:
            _query = '''select IdxAccessPath.path from IdxAccessPath
            inner join IdxCache
            on IdxCache.IdxCacheId = IdxAccessPath.IdxCacheId
            where IdxCache.IdxCacheType = 3 and IdxAccessPath.ClientId in 
            (select id from APP_Client where name like '{}')'''.format(ma_name)
            self.log.info(_query)
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            return _results[0][0]

        except Exception as exp:
            self.log.exception("Exception when querying the CS DB to get nfs server cache {0}: {1}".
                               format(ma_name, exp))

    def get_job_start_end_time(self, job_id):
        """
        Returns the start and end time of the job

        Args:
        job_id  (string) : Job id for which details are to be fetched

        Returns:
            time for the job
        """
        _query = f"""Select servStartDate, servEndDate from JMBkpStats where jobId = {job_id}"""
        self.csdb.execute(_query)
        job_info = self.csdb.fetch_one_row()
        if not job_info:
            raise Exception(
                "An exception occurred while getting job information")
        return job_info

    def get_job_backup_size(self, job_id):
        """
        Returns the backup size

        Args:
        job_id (string) : Job Id for whoch backup size has to be fetched

        Returns:
            size of the jobs
        """
        _query = f"""Select totalBackupSize from JMBkpStats where jobId = {job_id}"""
        self.csdb.execute(_query)
        job_info = self.csdb.fetch_one_row()
        if not job_info:
            raise Exception(
                "An exception occurred while getting job information")
        return job_info

    def add_filter(self, backupsetobj, subclientname, subclientid, vmname):
        """"
        This is used to add the a VM to  filters on the subclient.

        Args:
            backupsetobj - backupset object
            subclientname (str) - name of the subclient to which content to be added
            subclientid  (int) - Id of the subclient to which content to be added
            vname (str) - Vm name to add to subclient filter
        Raise:
              Exception:
                If unable to add VM to filter

        """
        try:
            contentobj = VirtualServerSubclient(backupsetobj, subclientname, None)
            vm_filter = []
            query = "select GUID, displayName  from app_client where name = '" + vmname + "'"
            self.csdb.execute(query)
            result = self.csdb.fetch_all_rows()
            result = result.pop(0)
            virtual_server_dict = {
                'allOrAnyChildren': True,
                'equalsOrNotEquals': True,
                'name': result[0],
                'displayName': result[1],
                'path': result[1],
                'type': 9
            }

            vm_filter.append(virtual_server_dict)
            vs_filter_content = {
                "children": vm_filter
            }
            contentobj._set_subclient_properties("_vmFilter", vs_filter_content)
            self.log.info('VM added to subclient filter successfully')
        except Exception as err:
            self.log.exception(
                "Exception while adding filters to subclient" + str(err))
            raise err

    def get_copy_retention(self, job_id):
        """
        Find copy retention setting from the snap job ID and return the value

        Raise Exception:
                If unable to find snap job or run DB query
        """
        try:
            self.log.info("JOB ID: {}".format(job_id))
            _query1 = "select CopyId from SMVolume where JobId= '%s'" % job_id
            self.csdb.execute(_query1)
            _results1 = self.csdb.fetch_all_rows()
            self.log.info("COPY ID: {}".format(_results1))
            _query = "select retentionJobs from archAgingRule where copyId= '%s'" % _results1[0][0]
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            self.log.info("RETENTION: {}".format(_results))

            return _results[0][0]

        except Exception as err:
            self.log.exception('Exception while validating snaps: ', str(err))
            raise err

    def get_cs_mssql(self, user_name='sqladmin_cv',
                     password=None, dbserver=None, dbname=None,
                     retry_attempts=3, use_pyodbc=True, force=False):
        if self.cs_mssql is None or force:
            if not password:
                cs_machine_obj = Machine(self.commcell.commserv_client)
                encrypted_pass = cs_machine_obj.get_registry_value(r"Database", "pAccess")
                password = cvhelper.format_string(self.commcell, encrypted_pass).split("_cv")[1]
            if not dbserver:
                db_instance = '\\commvault' if not self.commcell.is_linux_commserv else ''
                dbserver = self.commcell.commserv_hostname + db_instance
            if not dbname:
                dbname = "CommServ"
            counter = 1
            while counter < retry_attempts:
                try:
                    self.cs_mssql = MSSQL(dbserver, user_name, password, dbname, use_pyodbc=use_pyodbc
                                          )
                    break
                except Exception as e:
                    self.log.error("Failed to open connection with dbserver:" + dbserver)
                    self.log.info("Exception: " + str(e))
                    time.sleep(60)
                    counter = counter + 1

        if not self.cs_mssql:
            raise Exception(f'Unable to connect with CommServ database [{dbserver}] [{dbname}]')
        return self.cs_mssql

    def get_cloud_vms_to_power_off(self):
        """
        Gets cloud proxies which can be powered off
        Returns (list): list containing dictionary with HostId as key

        """
        if self.cs_mssql and self.cs_mssql.use_pyodbc:
            self.get_cs_mssql(force=True, use_pyodbc=False)
        self.get_cs_mssql(use_pyodbc=False)
        output = self.cs_mssql.execute_stored_procedure('MMGetCloudVMsToPowerOFF', None)
        return output.rows

    def get_cloud_vm_jobs_marked_active_in_db(self, host_id):
        """ Gets jobs which have not yet marked proxies for power off in DB
         Args:
             host_id (int): client id of cloud proxy

         Returns (list):  list of jobs which have not yet marked proxies for power off in DB
        """

        _query1 = "select DISTINCT EntityId from MMPowerMgmtJobToVMMap where  HostId = '%s' and (Flag & 256) =0" % host_id
        self.csdb.execute(_query1)
        _result = self.csdb.fetch_all_rows()
        _result = [int(job[0]) for job in _result if job[0]]
        return _result
