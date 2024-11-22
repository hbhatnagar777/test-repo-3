# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main module for communicating with cvpysdk for all commvault related operations.

CvOperation class is defined in this file.

CvOperation: Performs Commvault related operations using cvpysdk

CvOperation
==========

    __init__(splunk_object)     --  initialize object of CvOperation class associated with
    splunk object

    add_splunk_client()         --  adds new splunk client and returns the associated client object

    get_client_details()        --  returns a dictionary containing client_obj, instance_obj,
    backupset_obj and agent_obj

    update_client_nodes()       --  updates slave nodes of a splunk client

    update_client_content()     --  updates backup content of a splunk client

    run_backup_copy()           -- Runs backup copy on the specified Splunk client object

    run_backup()                --  runs a backup job for a splunk client and tracks the status
    of this backup job

    run_restore()               --  runs a restore job for a splunk client by taking index to be
    backed up as input and tracks the status of this job

    verify_incr_restore()         --  verifies if the restore was successful for an incremental job by comparing old
    and new event count and bucket count for warm and cold buckets

    verify_restore()            -- verifies if the restore job was successful

    cleanup()                   --  deletes the splunk client created for testcase if
    there are no active jobs associated with the client

"""

import base64
import time
import splunklib.client as splunk_client
import json


class CvOperation():
    """Class for performing commvault operations"""

    def __init__(self, splunk_object):
        """
        Initializes the CvOpetaion object by calling commcell object of cvpysdk.

        Args:
           splunk_object  (obj)  --  instance of splunk class

        Returns:
           object  --  instance of CvOperation class

        """
        self.tc_object = splunk_object.tc_object
        self.splunk_object = splunk_object
        self.commcell = self.tc_object.commcell
        self.tcinputs = self.tc_object.tcinputs
        self.log = self.tc_object.log
        self.new_client_name = splunk_object.new_client_name
        self.client = None
        self.log.info("Cvoperation class initialized")

    def add_splunk_client(self):
        """
        Adds new splunk client by calling comcell object of cvpysdk

         Args:
             Nothing

        Returns:
            client  --  client object of the newly created splunk client

        """
        if self.commcell.clients.has_client(self.new_client_name):
            self.log.info('Client exists. Deleting it and creating')
            self.commcell.clients.delete(self.new_client_name)
        new_client_name = self.tcinputs.get("NewClientName")
        password_temp = self.tcinputs.get("Password")
        password = base64.b64encode(password_temp.encode()).decode("utf-8")
        master_uri = self.tcinputs.get("MasterUri")
        master_node = self.tcinputs.get("MasterNode")
        user_name = self.tcinputs.get("UserName")
        plan = self.tcinputs.get("Plan")
        self.client = self.commcell.clients.add_splunk_client(
            new_client_name, password, master_uri, master_node,
            user_name, plan
        )
        return self.client

    def get_client_details(self, client_object,
                           backupset_name="defultbackupset",
                           subclient_name="default"):
        """
        Returns a dictionary containing client_obj, instance_obj,
        backupset_obj and agent_obj

        Args:
            client_object   (object)    --  splunk client object

            backupset_name  (str)       --  name of the backupset entity
                default: defaultbackupset

            subclient_name  (str)       --  name of the subclient entity
                default: default

        Returns:
             client_details (dict)      --  dictionary containing client_obj, instance_obj,
             backupset_obj and agent_obj

        """

        req_agent = client_object.agents.get("big data apps")
        req_instance = req_agent.instances.get(client_object.client_name)
        req_backupset = req_agent.backupsets.get(backupset_name)
        req_subclient = req_backupset.subclients.get(subclient_name)

        client_details = {
            "client": client_object,
            "agent": req_agent,
            "instance": req_instance,
            "backupset": req_backupset,
            "subclient": req_subclient
        }

        return client_details

    def update_client_nodes(self, client_object, nodes, instance_details=None):
        """
        Updates slave nodes of a splunk client

        Args:
            client_object  (obj)   --  Splunk client object

            nodes          (list)  --  list of Splunk slave nodes

            instance_details (obj)  --  Contains instance_obj

        """
        self.log.info("Starting SplunkNodes Update")

        if instance_details is None:
            req_agent = client_object.agents.get("big data apps")
            req_instance = req_agent.instances.get(client_object.client_name)

        else:
            req_instance = instance_details

        prop_dict = req_instance.properties
        nodes_config = []
        for node in nodes:
            entity_dict = {}
            node_id = self.commcell.clients[node.lower()]['id']
            entity_dict["entity"] = {"clientId": int(node_id), "clientName": node}
            nodes_config.append(entity_dict)
        prop_dict["distributedClusterInstance"]["clusterConfig"] \
            ["splunkConfig"]["nodes"] = nodes_config
        password_temp = self.tcinputs.get("Password")
        password = base64.b64encode(password_temp.encode()).decode("utf-8")
        prop_dict["distributedClusterInstance"]["clusterConfig"] \
            ["splunkConfig"]["splunkUser"]["password"] = password
        req_instance.update_properties(prop_dict)
        self.log.info("Splunk Nodes Update successful")

    def update_client_content(self, client_object, index_list, subclient_details=None):
        """
        Updates the backup content of a splunk client

        Args:
             client_object  (obj)   --  Splunk client object

             index_list     (list)   --  list of index that has to be backed up

             subclient_details (dict)  --  contains subclient_object

        """

        self.log.info("Starting Backup Content Update in SubClient")

        if subclient_details is None:
            req_agent = client_object.agents.get("big data apps")
            req_backupset = req_agent.backupsets.get("defaultbackupset")
            req_subclient = req_backupset.subclients.get("default")
        else:
            req_subclient = subclient_details

        req_subclient.subclient_content = index_list

        self.log.info("Backup Content in SubClient Updated Successfully")

    def run_backup_copy(self, client_object):
        """
                    Runs backup copy on the specified Splunk client object

                    Args:
                         client_object  (obj)   --  Splunk client object

                    Return:
                            str: The job ID of the backup copy job.
        """

        # logic to check if the backup copy job has started
        job_controller_obj = self.commcell.job_controller
        backup_copy_job_flag = False
        total_time_elapsed = 0
        backup_jobid = None
        self.log.info("Waiting For Backup Copy Job To Start")
        while (not backup_copy_job_flag and total_time_elapsed <= 120):
            active_jobs = job_controller_obj.active_jobs(client_name=client_object.client_name)
            for job_id in active_jobs.keys():
                if active_jobs[job_id]["operation"] == "Backup Copy":
                    backup_jobid = job_id
                    backup_copy_job_flag = True
                    break

            if not backup_copy_job_flag:
                time.sleep(5)
                total_time_elapsed = total_time_elapsed + 5

        if backup_copy_job_flag:
            self.log.info("Backup Copy Job Started Successfully With Job ID: %s", str(backup_jobid))
            backup_copy_job_obj = job_controller_obj.get(backup_jobid)

        else:
            self.log.info("Starting Backup Copy Job Explicitly")
            storage_policy_obj = self.commcell.storage_policies.get(self.tcinputs.get("Plan"))
            backup_copy_job_obj = storage_policy_obj.run_backup_copy()
            self.log.info("Backup Copy Job Started Successfully With Job ID: %s", str(backup_copy_job_obj.job_id))

        self.log.info("Waiting For Completion Of Backup Copy Job With Job ID: %s", str(backup_copy_job_obj.job_id))

        if not backup_copy_job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Backup Copy {0} With Error {1}".format(
                    str(backup_copy_job_obj.job_id), backup_copy_job_obj.delay_reason
                )
            )

        if not backup_copy_job_obj.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(backup_copy_job_obj.job_id), backup_copy_job_obj.status
                )
            )

        self.log.info(
            "Successfully Finished Backup Copy Job %s", str(backup_copy_job_obj.job_id)
        )
        return backup_copy_job_obj.job_id

    def run_backup(self, client_object, subclient_details=None, backup_type="Full"):
        """
            Runs backup on the specified Splunk client object. Runs a Full backup by default

            Args:
                 client_object  (obj)   --  Splunk client object

                 subclient_details (obj)  --  Contains subclient_object
                                            Ex: Subclient class instance for Subclient: "default" of Backupset: "defaultbackupset"}

                backup_type(str)       --   Type of backup - Full/Incremental

            Return:
                  tuple: A tuple containing two elements:
                  - str: The job ID of the primary backup job.
                  - str or None: The job ID (as a string) of the backup copy job.
        """

        self.log.info("Starting Snap Backup Job")
        if subclient_details is None:
            req_agent = client_object.agents.get("big data apps")
            req_backupset = req_agent.backupsets.get("defaultbackupset")
            req_subclient = req_backupset.subclients.get("default")
        else:
            req_subclient = subclient_details
        job_obj = req_subclient.backup(backup_type)
        self.log.info("Waiting For Completion Of Snap Backup Job With Job ID: %s",
                      str(job_obj.job_id))
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Snap Backup {0} With Error {1}".format(
                    str(job_obj.job_id), job_obj.delay_reason
                )
            )

        if not job_obj.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_obj.job_id), job_obj.status
                )
            )
        self.log.info(
            "Successfully Finished Snap Backup Job %s", str(job_obj.job_id)
        )
        backupcopy_job_id = self.run_backup_copy(client_object)
        snap_jobid = job_obj.job_id
        return snap_jobid, backupcopy_job_id


    def run_restore(self, client_obj, index_list, subclient_details=None, copy_precedence=None, from_time=None,
                    to_time=None):
        """
        Runs a restore job on the specified Splunk client object

        Args:
             client_obj     (obj)   --  Splunk client object

             index_list     (list)  --  list containing the indexes to be restored

             subclient_details (dict)  --  Contains subclient_obj

             copy_precedence (int)  --  the copy precedence value -- 0 for restore from default copy
                                                                     1 for restore from snap copy
                                                                     2 for restore from primary

        """
        self.log.info("Starting Restore Job")

        if subclient_details is None:
            req_agent = client_obj.agents.get("big data apps")
            req_backupset = req_agent.backupsets.get("defaultbackupset")
            req_subclient = req_backupset.subclients.get("default")
        else:
            req_subclient = subclient_details
        job_obj = req_subclient.restore_in_place(index_list, copy_precedence=copy_precedence, from_time=from_time,
                                                 to_time=to_time)
        self.log.info("Waiting For Completion Of Restore Job With Job ID: %s", str(job_obj.job_id))

        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Restore {0} With Error {1}".format(
                    str(job_obj.job_id), job_obj.delay_reason
                )
            )

        if not job_obj.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_obj.job_id), job_obj.status
                )
            )

        time.sleep(30)
        self.log.info(
            "Successfully Finished Restore Job %s", str(job_obj.job_id)
        )

    def verify_incr_restore(self, total_eventcount, index_name, warm_buckets, cold_buckets):
        """
        Verifies if the restore was successful for an incremental job (when operations like delete, add, roll are performed) by comparing old and new event count and
        bucket count for warm and cold buckets

        Args:
            total_eventcount    (int)   --  old event count

            index_name          (str)   --  name of the index for which we are verifying

            warm_buckets        (list)  --  list of warm buckets of the index

            cold_buckets        (list)  --  list of cold buckets of the index

        Return:
            Nothing
        """
        slave_username = self.tcinputs.get("Slave1SplunkUsername")
        slave_password = self.tcinputs.get("Slave1SplunkPassword")
        slave_ip = self.tcinputs.get("Slave1Ip")
        slave_port = self.tcinputs.get("Slave1Port")
        service = splunk_client.connect(host=slave_ip, port=slave_port,
                                        username=slave_username, password=slave_password)
        index_obj = service.indexes[index_name]
        new_eventcount = index_obj["totalEventCount"]
        # Verifying eventcount
        if int(new_eventcount) == total_eventcount:
            self.log.info("Eventcount Verification Successful")
        else:
            raise Exception("Eventcount Verification Failed")
        # Fetching bucket detials
        bucket_details = json.loads(self.splunk_object.fetch_bucket_details_of_index(index_name=index_name))
        buckets, eventcount = self.splunk_object.retrieve_warm_and_cold_buckets_information(bucket_details)
        # Verifying bucket count
        if ((len(buckets[0]) == len(warm_buckets))
            and len(buckets[1]) == len(cold_buckets)):
            self.log.info("Bucket count Verification Successful")
        else:
            raise Exception("Bucket count Verification Failed")
        self.log.info("Restore Verification Successful")

    def verify_restore(self, total_eventcount, index_name):
        """
        Verifies if the restore was successful by comparing old and new event count

        Args:
            total_eventcount    (int)   --  old event count

            index_name          (str)   --  name of the index for which we are verifying

        """
        slave_username = self.tcinputs.get("Slave1SplunkUsername")
        slave_password = self.tcinputs.get("Slave1SplunkPassword")
        slave_ip = self.tcinputs.get("Slave1Ip")
        slave_port = self.tcinputs.get("Slave1Port")
        service = splunk_client.connect(host=slave_ip, port=slave_port,
                                        username=slave_username, password=slave_password)
        index_obj = service.indexes[index_name]
        new_eventcount = index_obj["totalEventCount"]
        if new_eventcount == total_eventcount:
            self.log.info("Restore Operation Verified Successful")
        else:
            raise Exception("Restore Verification Failed")

    def cleanup(self, client_obj):
        """
         Deletes the splunk client if there are no active jobs

         Args:
                client_obj  (obj)   --  client object of the newly created splunk client

        Exception:
                Raises exception if client deletion is not successful

        """
        time.sleep(5)
        jobcontroller_obj = self.commcell.job_controller
        resp = jobcontroller_obj.active_jobs(client_name=client_obj.client_name)
        if len(resp) == 0:
            if self.commcell.clients.has_client(client_obj.client_name):
                self.log.info('Client exists. Deleting it')
                self.commcell.clients.delete(client_obj.client_name)
            else:
                raise Exception("Cleanup Failed")
        else:
            self.log.info("Active jobs found,So Not Deleting Client")
