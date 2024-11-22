#  -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing nas operations

NASHelper is the only class defined in this file

NASHelper: Helper class to perform nas operations

NASHelper:
    __init__()                                --  initializes nas helper object

    _get_client_credentials()                 --  returns the client credentials

    _get_cluster_client_info()                --  returns the cluster client info

    _get_test_data_path()                     --  returns test data path on controller machine

    ignore_files_list()                       --  returns the ignore files/patterns list

    copy_test_data()                          --  copies test data to destination client

    get_attribute_value_from_xml()            --  returns the attribute value

    get_snap_name_from_job()                  --  returns the snap name for specified job

    validate_if_smtape_backup()               --  validates if specified job was smtape backup

    validate_if_smtape_restore()              --  validates if specified job was smtape restore

    get_nas_client()                          --  returns NASClient object for specified filer

    validate_volume_status()                  --  validates if volume status is as specified

    validate_windows_restored_content()       -- Validates windows restored content with that of
    on filer

    validate_filer_restored_content()         -- Validates restored content on filer with that
    of on windows

    validate_filer_to_filer_restored_content()-- Validates restored content on filer with that of
    on another filer

    calculate_deduperatio                     --  Calculates DedupeRatio
"""

import shutil
import random
import string
import time
import re
import os
import xml.etree.ElementTree as ET

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, cvhelper
from AutomationUtils.database_helper import get_csdb
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from .nasclient import NetAPPClient, NetAPPClusterClient, IsilonClient, HuaweiClient, VnxCelerraVDMClient, NutanixClient
from .nasclient import UnityVnxCelerraClient, HNASClient


class NASHelper(object):
    """Helper class to perform nas operations"""

    def __init__(self, csdb=None):
        """Initializes nashelper object and gets the commserv database object if not specified

            Args:
                csdb    (object)    --  commserv database object using which we can
                                            query commserv db
                    default: None

        """
        self.log = logger.get_log()
        if csdb:
            self._csdb = csdb
        else:
            self._csdb = get_csdb()

        self._ignore_files_list = [
            '~snapshot', 'rstab*', 'restore_symbol*', 'RST_SH*', 'rst*', '.etc', 'lost+found',
            '$__NDMP__', '$__CFN__', '.snapshot', '.ckpt*'
        ]

    def _get_client_credentials(self, client_id, filer_type):
        """Returns the client credentials

            Args:
                client_id   (int)   --  id of the client for which the credentials
                                            are to be read from database

            Returns:
                (str, str)  -   username and password of the client

            Raises:
                Exception:
                    if failed to get client credentials

        """
        cur = []
        #Adding support for NUTANIX 
        #Need to check this filer type first as it requires different queries
        if filer_type.upper() == "NUTANIX":
            query : str = (f"SELECT attrVal from APP_ClientProp where componentNameId = {client_id} and attrName like '%control host%'")
            self._csdb.execute(query)
            result:list[int|str] = self._csdb.fetch_one_row()
            if len(result) >= 1:
                ControlHostId : int = result[0]
                query = (f"select SMHostUserName, SMHostPassword from SMControlHost WHERE ControlHostId = {ControlHostId}")
                self._csdb.execute(query)
                result = self._csdb.fetch_one_row()
                if(len(result) >= 2):
                    username:str = result[0]
                    password:str = result[1]
                    return username, password
                else :
                    raise Exception("Username and password not found in SMControlHost Table")
            else :
                raise Exception("Nutanix Control Host ID not found in database")
        elif filer_type != "":
            # Check if client credentials can be found in SMControlHost
            query = ("SELECT SMHostUserName, SMHostPassword, SMHostName FROM SMControlHost "
                     "WHERE ClientId = '{0}'").format(client_id)

            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            # validate credentials specified or not
            if len(cur) >= 3:
                if cur[1] != '3':
                    return cur[0], cur[1], cur[2]
            else:
                self.log.info("Client credentials not found in SMControlHost")
        elif len(cur) >= 1:
            # Check if client credentials can be found in MMNDMPHostInfo
            query = ("SELECT Login,Password FROM MMNDMPHostInfo WHERE "
                     "ClientId = '{0}'").format(str(client_id))
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            query1 = "select net_hostname from APP_Client where id = '{0}'".format(str(client_id))
            self._csdb.execute(query1)
            cur1 = self._csdb.fetch_one_row()
            # validate credentials specified or not
            if len(cur) >= 2:
                if cur[1] != '3':
                    return cur[0], cur[1], cur1[0]
        else:
            raise Exception(
                "Client credentials are not specified. Please specify them from commcell GUI.")

    def _get_cluster_client_info(self, client_obj):
        """Returns cluster client name and id

            Args:
                client_obj      (object)    --  python sdk client object whose credentials
                                                    are to be read

            Returns:
                (str, str)  -   username and password of the client

            Raises:
                Exception:
                    if no cluster is selected for this client

                    if specified client is not cluster client

        """
        if 'nasClusterProperties' in client_obj._properties['pseudoClientInfo']:
            nas_cluster_prop = client_obj._properties['pseudoClientInfo']['nasClusterProperties']

            self.log.info("Check if the specified client is cluster/ vserver")
            if 'vServerName' not in nas_cluster_prop:
                self.log.info("This might be a cluster machine")
                return client_obj.client_name, client_obj.client_id

            self.log.info("This might be a vserver")
            if 'selectedCluster' in nas_cluster_prop:
                cluster_client_name = nas_cluster_prop['selectedCluster']['name']
                cluster_client_id = nas_cluster_prop['selectedCluster']['id']
                self.log.info("Selected cluster client name: %s", cluster_client_name)
                self.log.info("Selected cluster client id: %s", cluster_client_id)

                return cluster_client_name, cluster_client_id
            else:
                raise Exception("No cluster is selected for this client")
        else:
            raise Exception("Make sure the specified client is cluster client")

    def _get_test_data_path(self, local_machine, size):
        """Returns the test data path on this machine

            Args:
                local_machine   (object)    --  controller machine object which can be used to
                                                    perform operation on controller machine

                size            (int)       --  size of test data that is to be generated

            Returns:
                str     -   path where test data is generated

            Raises:
                Exception:
                    if failed to generate test data on controller machine
        """
        drives_dict = local_machine.get_storage_details()
        if local_machine.os_info == "WINDOWS":
            for drive in drives_dict.keys():
                if not isinstance(drives_dict[drive], dict):
                    continue

                if float(drives_dict[drive]['available']) >= size:
                    return drive + ":\\" +''.join(random.choices(string.ascii_uppercase, k=7))
        elif local_machine.os_info == "UNIX":
            if float(drives_dict['available']) >= size:
                return "/"+''.join(random.choices(string.ascii_uppercase, k=7))

        raise Exception("Failed to get test data path")

    @property
    def ignore_files_list(self):
        """Treats the ignore files list as read-only property"""
        return self._ignore_files_list

    def copy_test_data(self, nas_client, path):
        """Copies test data to specified path on nas client

            Args:
                nas_client  (object)    --  object for nas filer where test data is to be copied

                path        (str)       --  path where test data is to be copied

        """
        test_data_size = 10

        test_data_path = self._get_test_data_path(nas_client._local_machine, test_data_size)
        nas_client._local_machine.generate_test_data(test_data_path, file_size=test_data_size)

        self.log.info("Generated Test Data at path: " + test_data_path)

        nas_client.copy_folder(test_data_path, path)
        self.log.info("Copying test data to: " + path)

        shutil.rmtree(test_data_path)

    def generate_and_copy_files(self, nas_client, path):
        """Copies test files to specified path
        
            Args:
                nas_client  (object)    -- object for nas filer where test files to be copied
                
                path        (str)       -- path where test files is to be copied
                
            return:
                
                result      (str)       -- path where test files are created
                
        """
        test_data_size = 10

        test_data_path = self._get_test_data_path(nas_client._local_machine, test_data_size)
        file_path1 = f"{test_data_path}\\textfile1.txt"
        file_content = 'New file is created'
        nas_client._local_machine.create_file(file_path1, file_content)
        file_path2 = f"{test_data_path}\\textfile2.txt"
        file_content = 'New file is created2'
        nas_client._local_machine.create_file(file_path2, file_content)

        nas_client.copy_folder(test_data_path, path)
        self.log.info("Copying test data to: " + path) 

        shutil.rmtree(test_data_path)
        result = test_data_path.lstrip(test_data_path[0:3])
        
        return result

    def copy_test_data_to_proxy(self, proxy, path):
        """Copies test data to specified path on unix client

            Args:
                Proxy  (object)    --  object for unix proxy client where test data is to be copied

                path   (str)       --  path where test data is to be copied

        """
        test_data_size = 10
        test_data_path = self._get_test_data_path(proxy, test_data_size)
        proxy.generate_test_data(
            test_data_path, file_size=test_data_size, hlinks=False, slinks=False)
        self.log.info("Generated Test Data at path: " + test_data_path)
        self.log.info("Folder %s will be copied to %s", test_data_path, path)
        proxy.copy_folder(test_data_path, path, '-f')
        self.log.info("Copying test data to: " + path)
        proxy.remove_directory(test_data_path)

    def get_snap_name_from_job(self, job_id):
        """Returns snap name for specified job

            Args:
                job_id  (int)   --  id of the job of which the snap name is to be determined

            Returns:
                str     -   name of the snap created during the specified job id

            Raises:
                Exception:
                    if failed to get snap name for the specified job id

        """
        query = "SELECT UniqueIdentifier FROM SMSnap WHERE SMSnapId = (SELECT SMSnapId FROM \
            SMVolSnapMap WHERE SMVolumeId = (SELECT SMVolumeId FROM SMVolume WHERE \
            JobId='{0}'))".format(job_id)

        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            return str(cur[0])
        else:
            raise Exception("Failed to get snap name for job id: {0}".format(job_id))

    def validate_if_smtape_backup(self, job_id):
        """Validates if performed job was smtape backup job

            Args:
                job_id      (int)   --  id of the backup job which is to be
                                            verified if was ran as smtape

            Raises:
                Exception:
                    if failed to validate if specified job was ran as smtape

        """
        self.log.info("Validating if %d job was SMTAPE backup job", job_id)
        query = "SELECT name,objName1 FROM archFile WHERE jobId = {0}".format(job_id)

        try:
            self._csdb.execute(query)
            rows = self._csdb.fetch_all_rows()
            self.log.info(str(rows))
            for row in rows:
                if not ("CV_BUTYPE=smtape" in str(row[1]) and "TYPE=smtape" in str(row[1])):
                    if str(row[1]) != "N/A":
                        raise Exception("This is not a SMTape job")

            self.log.info("Successfully validated SMTAPE backup job")
        except Exception as exp:
            raise Exception("Failed to validate if smtape job with error: " + str(exp))

    def validate_if_smtape_restore(self, job_id):
        """Validates if performed job was smtape restore

            Args:
                job_id      (int)   --  id of the restore job which is to be
                                            verified if was ran as smtape

            Raises:
                Exception:
                    if failed to validate if specified job was ran as smtape

        """
        self.log.info("Validating if %d job was SMTAPE restore", job_id)
        query = "select Message from EvLocaleMsgs where LocaleID = 0 and MessageID IN \
        (select messageId from evMsg where jobId_l = {0})".format(job_id)

        try:
            self._csdb.execute(query)
            rows = self._csdb.fetch_all_rows()
            self.log.info("Validating if SMTAPE Restore")
            self.log.info(str(rows))
            smtape_restore = False
            for row in rows:
                if "SMTAPE restore" in row[0]:
                    smtape_restore = True
                    break
            if not smtape_restore:
                raise Exception("This is not a SMTape  restorejob")

            self.log.info("Successfully validated SMTAPE restore job")
        except Exception as exp:
            raise Exception("Failed to validate if smtape restore job with error: " + str(exp))

    def get_nas_client(self, client_obj, agent_obj, filer_type=None, is_cluster=False, is_vdm=False):
        """Returns the NAS client object

            Args:
                client_obj  (object)    --  python sdk client object

                filer_type  (str)       --  type of the filer for which object is to be created

                is_cluster  (bool)      --  returns cluster client object if specified true

            Returns:
                object   -  nas client object for the specified client object

        """
        filer_type = self.nas_vendor(client_obj)
        agent_type = agent_obj.agent_name
        if filer_type.upper() == "NETAPP":
            if is_cluster:
                cluster_client_name, cluster_client_id = self._get_cluster_client_info(client_obj)
                user, password, _ = self._get_client_credentials(int(cluster_client_id),
                                                                 filer_type)
                return NetAPPClusterClient(
                    cluster_client_name, client_obj._commcell_object, agent_obj, user,
                    cvhelper.format_string(client_obj._commcell_object, password)
                )
            else:
                user, password, _ = (self._get_client_credentials(int(client_obj.client_id),
                                                                  filer_type))
                return NetAPPClient(
                    client_obj.client_name, client_obj._commcell_object, agent_obj, user,
                    cvhelper.format_string(client_obj._commcell_object, password)
                )
        elif filer_type.upper() == "ISILON":
            self.log.info("filer type is :%s", filer_type)
            user, password, controlhost = (self._get_client_credentials(int(client_obj.client_id),
                                                                        filer_type))
            return IsilonClient(client_obj.client_name, client_obj._commcell_object, agent_obj,
                                user, cvhelper.format_string(client_obj._commcell_object, \
                                                             password), controlhost)
        elif filer_type.upper() == "HUAWEI":
            user, password, controlhost = (self._get_client_credentials(int(client_obj.client_id),
                                                                        filer_type))
            return HuaweiClient(client_obj.client_name, client_obj._commcell_object, agent_obj,
                                user, cvhelper.format_string(client_obj._commcell_object, \
                                                             password), controlhost)
        elif (filer_type.upper() == "DELL EMC VNX/CELERRA" or filer_type.upper() == "DELL EMC UNITY")and is_vdm is False:
            user, password, controlhost = self._get_client_credentials(int(client_obj.client_id),
                                                                       filer_type)
            return UnityVnxCelerraClient(client_obj.client_name, client_obj._commcell_object,
                                         agent_obj, user, cvhelper.format_string
                                         (client_obj._commcell_object, password), controlhost)
        elif filer_type.upper() == "DELL EMC VNX/CELERRA" and is_vdm is True:
            user, password, controlhost = self._get_client_credentials(int(client_obj.client_id),
                                                                       filer_type)
            return VnxCelerraVDMClient(client_obj.client_name, client_obj._commcell_object,
                                         agent_obj, user, cvhelper.format_string
                                         (client_obj._commcell_object, password), controlhost)					  
        elif filer_type.upper() == "HNAS":
            self.log.info("filer type is :%s", filer_type)
            user, password, controlhost = self._get_client_credentials(int(client_obj.client_id),
                                                                       filer_type)
            return HNASClient(client_obj.client_name, client_obj._commcell_object, agent_obj,
                              user, cvhelper.format_string(client_obj._commcell_object, password),
                              controlhost
                              )
        # Adding supprot for NUTANIX FILER           
        elif filer_type.upper() == "NUTANIX":
            self.log.info(f"Filer Type is {filer_type}")
            #Nutanix does not require control host
            user, password = self._get_client_credentials(int(client_obj.client_id),
                                                                       filer_type)
            return NutanixClient(
                    client_obj.client_name, client_obj._commcell_object, agent_obj, user,
                    cvhelper.format_string(client_obj._commcell_object, password)
                )

    def nas_vendor(self, client_obj):
        """Returns the vendor type of Client

            Args:
                client_obj  (object)    --  python sdk client object

            Returns:
                str   -  nas vendor type string for the specified client object

        """
        filer_type = None
        query = f"SELECT attrVal from APP_ClientProp where componentNameId = " \
                f"{int(client_obj.client_id)} " \
                "and attrName = 'NAS OS Type'"
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur[0]:
            if int(cur[0]) == 18:
                filer_type = "Isilon"
            elif int(cur[0]) == 2:
                filer_type = "Netapp"
            elif int(cur[0]) == 32:
                filer_type = "Huawei"
            elif int(cur[0]) == 1:
                filer_type = "Dell EMC VNX/Celerra"
            elif int(cur[0]) == 33:
                filer_type = "Dell EMC Unity"
            elif int(cur[0]) == 9:
                filer_type = "HNAS"
            elif int(cur[0]) == 37:
                filer_type = "Azure NetApp Files"
            elif int(cur[0]) == 34:
                filer_type = "Nutanix"

        return filer_type

    def validate_volume_status(self, volume_obj, required_status):
        """Validates the volume status for specified volume

            Args:
                volume_obj      (object)    --  volume class object of the volume whose
                                                    status is to be verified

                required_status (str)       --  expected status of the specified volume object

            Raises:
                Exception:
                    if volume status is not as expected for specified volume object

        """
        self.log.info(
            "Validate if %s volume status is %s", volume_obj.name, required_status
        )

        if volume_obj.status.upper() != required_status.upper():
            raise Exception(
                "{0} volume status is not {1}".format(volume_obj.name, required_status)
            )

        self.log.info("Successfully validated volume status")

    def validate_windows_restored_content(self,
                                          nas_client,
                                          windows_restore_client,
                                          windows_restore_location,
                                          subclient_content,
                                          files=None,
										  filter_content=[]):
        """Validates the windows restored content

            Args:
                nas_client                  (object)    --  nas client object on which the restored
                                                                content is to be verified

                windows_restore_client      (object)    --  machine class object for windows client
                                                                where the content was restored

                windows_restore_location    (str)       --  path on windows machine where content
                                                                was restored

                subclient_content           (list)      --  subclient content obtained from the
                                                                python sdk subclient object

                filter_content              (list)      -- content to be skipped during validation

            Raises:
                Exception:
                    if failed to validate restored content

        """
        self.log.info("Validate Restored content")
        self.log.info("ignoring list:" + str(self.ignore_files_list+filter_content))
        diff = []
        for content in subclient_content:
            _, volume_name = nas_client.get_path_from_content(content, files=files)
            if files is None:
                restore_path = windows_restore_location + "\\" + volume_name
                diff += nas_client.compare_folders(windows_restore_client,
                                                   content,
                                                   restore_path,
                                                   ignore_files=(self.ignore_files_list+filter_content))
            else:
                restore_path = windows_restore_location + "\\" + volume_name[1]
                diff += nas_client.compare_files(windows_restore_client,
                                                 content,
                                                 restore_path,
                                                 files=files)

        if diff != []:
            self.log.error(
                "Restore validation failed. List of different files \n%s", diff
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self.log.info("Successfully validated restored content")

    def validate_filer_restored_content(self,
                                        nas_client,
                                        windows_restore_client,
                                        windows_restore_location,
                                        subclient_content,
                                        filer_restore_location=None,
                                        files=None):
        """Validates the restored content on different filer

            Args:
                nas_client                  (object)    --  nas client object on which the restored
                                                                content is to be verified

                windows_restore_client      (object)    --  machine class object for windows client
                                                                where the content was restored

                windows_restore_location    (str)       --  path on windows machine where content
                                                                was restored

                subclient_content           (list)      --  subclient content obtained from the
                                                                python sdk subclient object

                filer_restore_location      (str)       --  path on the filer where content is
                                                                restored
                        default: None

            Raises:
                Exception:
                    if failed to validate restored content

        """
        self.log.info("Validate Restored content")
        diff = []
        for content in subclient_content:
            _, volume_name = nas_client.get_path_from_content(content, files=files)
            if files is None:
                if filer_restore_location:
                    filer_destination_path = filer_restore_location + "/" + volume_name
                else:
                    filer_destination_path = content
                windows_restore_path = windows_restore_location + "\\" + volume_name
                diff += windows_restore_client.compare_folders(
                    nas_client, windows_restore_path, filer_destination_path,
                    ignore_files=self.ignore_files_list)
            else:
                if filer_restore_location:
                    filer_destination_path = filer_restore_location + "/" + volume_name[1]
                else:
                    filer_destination_path = content
                windows_restore_path = windows_restore_location + "\\" + volume_name[1]
                res = nas_client.compare_files(windows_restore_client,
                                               filer_destination_path,
                                               windows_restore_path,
                                               files=files)
                if res is False:
                    diff += [content]

        if diff != []:
            self.log.error(
                "Restore validation failed. List of different files \n%s", diff
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self.log.info("Successfully validated restored content")

    def validate_filer_to_filer_restored_content(self,
                                                 nas_client,
                                                 subclient_content,
                                                 filer_restore_location=None,
                                                 filter_content=[],
                                                 verify_files=False):
        """Validates the restored content on destination filer with that of source filer

            Args:
                nas_client                  (object)    --  nas client object on which the restored
                                                                content is to be verified

                subclient_content           (list)      --  subclient content obtained from the
                                                                python sdk subclient object

                filer_restore_location      (str)       --  path on the filer where content is
                                                                restored
                        default: None
                        
                filter_content              (list)      --  List of filter content to be ignored
                
                verify_files                (bool)      --  when files needs to be verified
                
                        default: False

            Raises:
                Exception:
                    if failed to validate restored content

        """
        self.log.info("Validate Restored content")
        diff = []
        for content in subclient_content:
            _, volume_name = nas_client.get_path_from_content(str(content))
            if filer_restore_location != '' and nas_client._agent.upper() == 'NDMP' and not verify_files:
                filer_destination_path = "{0}/{1}".format(filer_restore_location, volume_name)
            elif filer_restore_location != '' and nas_client._agent.upper() == 'NDMP' and verify_files:
                filer_destination_path = filer_restore_location
            elif filer_restore_location != '' and nas_client._agent.upper() == 'FILE SYSTEM':
                filer_destination_path = "{0}\{1}".format(filer_restore_location, volume_name)
            else:
                filer_destination_path = content
            diff += nas_client.compare_folders(nas_client,
                                               content,
                                               filer_destination_path,
                                               ignore_files=(self.ignore_files_list+filter_content))
        if diff != []:
            self.log.error(
                "Restore validation failed. List of different files \n%s", diff
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )
        self.log.info("Successfully validated restored content")

    def calculate_deduperatio(self, job):
        """ Function to generate dedupe ratio
            Arg:
            Job         (Object)    -- job object for which dedupe ratio needs to be calculated
        """
        query = "SELECT SUM(ISNULL(S.sizeOnMedia, 0)) FROM JMJobDataStats S WHERE S.commCellId = 2 AND S.jobId =" + job.job_id + " AND S.auxCopyJobId = 0"
        self._csdb.execute(query)
        sizeOnMedia = self._csdb.fetch_one_row()
        query1 = "SELECT totalUncompBytes FROM JMBkpStats WHERE jobId = " + job.job_id + "AND commCellId = 2"
        self._csdb.execute(query1)
        unCompBytes = self._csdb.fetch_one_row()
        self.log.info(sizeOnMedia[0])
        self.log.info(unCompBytes[0])
        if (int(unCompBytes[0]) > int(sizeOnMedia[0])):
            dedupeRatio = ((int(unCompBytes[0]) - int(sizeOnMedia[0])) / (int(unCompBytes[0]) * 1.0)) * 100
            self.log.info(f"Dedupe ratio is {dedupeRatio}")
            return dedupeRatio
        else:
            raise Exception(
                "Testcase failed as the dedupe ratio is low"
            )

    def _get_restart_string(self, job_id, all_streams=False):
        """Returns the restart string for specified job

            job_id      (int) :  job id whose restart string needs to be checked

            all_streams (bool):  Set the value to True, if all streams needs to be restarted

        Return:

            offset      (list):  List of offset values calculated from restart string

        """
        query = "SELECT restartString FROM JMJobInfo WHERE jobid='{0}'".format(job_id)
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        self.log.info("hereee")
        if cur and cur[0]:
            self.log.info(f"in _get_restart_string {cur}")
            xml = cur[0].split("|")
            self.log.info(f"Restart string from DB is {xml}")
            offset = []
            for i in range(len(xml)-1):
                if xml[i] is not None:
                    offset.append(self._get_attribute_value_from_xml(xml[i], "ValidRestartString", "restartByteOffset"))
                    self.log.info(f"offsets are {offset}")
                for x in range(len(offset)):
                    if all_streams is True and offset[x] is None:
                        raise Exception(
                            "Some of paths seems to be completed before restart string is set")
                    elif all_streams is False and offset[x] is None:
                        self.log.info("Some of the paths seems to be completed")
                        offset[x] = 0
            return offset
        else:
            return []

    def _wait_for_restartable_point(self, job, all_streams=False, streams=3):
        """Pauses the test case till it finds restartable point"""
        try:
            while True:
                restart_string = self._get_restart_string(int(job.job_id), all_streams=all_streams)
                i = 0
                self.log.info(f"Restart string received is {restart_string}")
                if sum(map(int, restart_string)) != 0:
                    for item in restart_string:
                        if int(item) > 0 and all_streams is False:
                            self.log.info("Restart string is set for a stream")
                            return restart_string
                        elif int(item) > 0 and all_streams is True:
                            i += 1
                            self.log.info(f"offset is {item}")
                            self.log.info("checking all the streams...")
                    if i is streams:
                        return restart_string
                self.log.info("Waiting for Restart String to set")
                time.sleep(5)

                if job.is_finished:

                    self.log.info("Job finished skip restart string job")
                    return 0
        except Exception as exp:
            self.log.error("Failed to wait till restart point:" + str(exp))
            raise Exception("Failed to wait till restart point:" + str(exp))

    def _get_attribute_value_from_xml(self, input_xml, element, attribute):
        """Returns the attribute value from specified xml"""
        xml = ET.fromstring(input_xml)
        elem = xml.find(element)
        self.log.info(elem)
        if elem is not None:
            self.log.info(elem.get(attribute))
            return elem.get(attribute)

    def _resume_job(self, job):
        """Resumes the specified job"""
        job.resume()

        while str(job.status).lower() != "running":
            self.log.info("Waiting for job status to change to running")
            time.sleep(20)

        self.log.info("Resumed job")

    def _check_restart_offset(self, job_id, restart_offset):
        """
        Validates the restart offset value

        job_id          (int) : Job id whose restart string needs to be checked

        restart_offset  (list) : List of restart byte offsets of all streams

        """
        new_restart_offset = self._get_restart_string(job_id)
        self.log.info("Restart offset before resuming: " + str(restart_offset))
        self.log.info("Restart offset after resuming: " + str(new_restart_offset))
        if new_restart_offset != restart_offset:
            raise Exception("Restart String was reset to: " + str(new_restart_offset))
        time.sleep(5)

    def run_restartable_backup(self, job, all_streams=False, streams=3):
        """Executes the restartable backup case
            job         (obj) : Job object of job which needs to be restarted

            all_streams (bool) : Set the value to True, if all streams needs to be restarted

            streams     (int)  : stream count of backup job

        """
        self.log.info("Check for Restartable String. Will wait till the flag is set.")
        restart_offset = self._wait_for_restartable_point(job, all_streams, streams=streams)

        if job.is_finished:
            return

        self.log.info("restartable point flag is set")

        self.log.info("Pause the job")
        job.pause()
        time.sleep(20)

        self.log.info("Check if job status is suspended")
        if job.is_finished:
            self.log.info("Job finished skip the case")
            return

        while str(job.status).lower() != "suspended":
            self.log.info("Waiting for job status to change to suspended")
            time.sleep(20)

        time.sleep(5)
        self.log.info(str(job.delay_reason))
        self._resume_job(job)
        self._check_restart_offset(int(job.job_id), restart_offset)
        if job.is_finished:
            self.log.info("Job finished skip the case")
            return
        self.log.info("Wait for job completion")
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup job with error: {0}".format(job.delay_reason)
            )
        self.log.info("Successfully finished backup job")

    def get_bkpcpyjob_from_snapjob(self, job):
        """
        Returns the corresponding backup copy job id of corresponding snap job id

        Input:
            Job     (obj):  Job object of snap job whose backup copy job id is needed

        Return:
            jobid   (list): List containing backup copy job id

        """
        query = "SELECT childJobId FROM JMJobWF WHERE processedJobId = '{0}'".format(job.job_id)
        self._csdb.execute(query)
        jobid = self._csdb.fetch_one_row()
        return jobid

    def prev_attempt_stats(self, job, sp_ma):
        """
        This function verifies whether backup stats are carried from previous attempt before suspending

            job (obj) : Restarted backup job id

            sp_ma: (obj): Machine class object of MA where backup ran
        """
        str1 = sp_ma.get_logs_for_job_from_file(job.job_id, "NasBackup.log", "Current attempt starting job statistics:")
        self.log.info(f"string is {str1}")
        a = str1.split("[")
        b = []
        for item in a:
            b.append(item.split("]"))
        if int(b[-2][0]) > 0 and int(b[-1][0]) > 0:
            self.log.info(f"Previous attempt's stats are considered. File count:{b[-2][0]}, ByteCount:{b[-1][0]}")
        else:
            self.log.info("Seems like previous attempt's stats are not carried to latest attempt")

    def get_backupjob_appsize(self, job):
        """
        Calculates backup job application size from DB

        job     (obj):  Job object for which app size needs to be calculated

        Return:

            appsize_gb (int): Application size of job in GB rounded off to 1 digit
        """
        query = "select unCompSize from JMJobDataStats where jobId='{0}' and dataType=1".format(job.job_id)
        self._csdb.execute(query)
        appsize = self._csdb.fetch_one_row()
        appsize_gb = int(appsize[0])/(1024*1024*1024)
        return round(appsize_gb, 1)

    def sum_bytecount_all_streams(self, sp_ma, job):
        """
        Calculates sum of bytecount from all streams in the final backup attempt

        sp_ma    (obj) : Machine class object of storage policy MA

        job      (obj) : Job object for which sum of all stream's bytecount needs to be calculated

        Return:
            d     (int) : sum of all stream's bytecount in last backup attempt in GB rounded off by 1 digit

        """
        str1 = sp_ma.get_logs_for_job_from_file(job.job_id, "NasBackup.log", "Total paths that need to be backed up")
        a = str1.split('[')
        streams = int((a[-1].replace('].', '')))
        str1 = sp_ma.get_logs_for_job_from_file(job.job_id, "NasBackup.log", "Final file/dir count")
        self.log.info(f"string received is {str1}")
        a = str1.split("Final byte count")
        d = []
        for i in range(1, streams+1):
            b = a[-i].split(']')
            c = b[0].replace(' [', '')
            d.append(c)
        self.log.info(f"Stream Bytecount in GB is {(sum(map(int, d)))/(1024*1024*1024)}")
        return round((sum(map(int, d)))/(1024*1024*1024), 1)

    def run_backup(self, subclient, backup_type):
        """Starts backup job"""
        self.log.info("*" * 10 + f" Starting Subclient {backup_type} Backup " + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started %s backup with Job ID: %s", backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(backup_type, job.delay_reason))
        return job

    def get_copy_precedence(self, storage_policy, storage_policy_copy):
        """Returns the copy precedence value
           Args:
               storage_policy      (str)  --  Storage policy name

               storage_policy_copy (str)  --  storage policy copy name

           Return:
                string : copy precedence value """

        self._csdb.execute(
            "select copy from archGroupCopy where archGroupId in (select id from archGroup where \
            name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
        cur = self._csdb.fetch_one_row()
        return cur[0]

    def random_data_restore(self, nas_client, content):
        """Returns random files\folders from a network locatio

                Args:
                    nas_client       (obj)   --  nas client object

                    content          (list)  --  list of subclient content paths

                Returns:
                    rand_dirs        (list)  --  list of directories

                    rand_files       (list)  --  list of files   """

        rand_dirs = []
        rand_files = []
        for vol in content:
            self.log.info("path getting iterated is %s", vol)
            network_path, _ = nas_client.get_path_from_content(vol)
            obj = os.scandir(path=network_path)
            dirs = []
            files = []
            for entry in obj:
                if entry.is_dir():
                    dirs += [entry.name]
                elif entry.is_file():
                    files += [entry.name]
            if len(dirs) > 2:
                dirs_rand = random.sample(dirs, k=2)
                for dir in dirs_rand:
                    if dir != '~snapshot':
                        rand_dirs.append(vol+'/'+dir)
                self.log.info("Final random dirs list is %s", rand_dirs)
            if len(files) > 2:
                files_rand = random.sample(files, k=2)
                for file in files_rand:
                    if (re.search('restore_symboltable', file) or re.search('rstab', file)) is None:
                        rand_files.append(vol+'/'+file)
                self.log.info("Final random files list is %s", rand_files)
        return rand_dirs, rand_files

    def run_auxcopy(self, sp, copy, mediaagent):
        """Runs Aux copy operation for given Storage policy copy """
        self.log.info("*" * 10 + " Run Aux Copy job " + "*" * 10)
        job = sp.run_aux_copy(copy, mediaagent)
        self.log.info("Started Aux Copy job with Job ID: %s ", job.job_id)

        if not job.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: "+ job.delay_reason)

        self.log.info("Successfully finished Aux Copy Job")

    def run_max_incs(self, subclient):
        """Function to run maximum incrementals for NetApp C mode"""
        for i in range(31):
            self.run_backup(subclient, "INCREMENTAL")
        try:
            job = subclient.backup("INCREMENTAL")
            self.log.info(f"job is {job.job_id} ")
            if not job.wait_for_completion():
                self.log.info("Incremental job failed, failure reason is...")
                self.log.info(job.pending_reason)
                string1 = "Exceeded maximum number of consecutive incremental backups on file server. Starting new [DIFFERENTIAL] job"
                if string1 in job.pending_reason:
                    self.log.info("Max incremental limit i.e 32 reached, hence auto start diff job")
            time.sleep(500)
            jobid, jobtype = self.get_latest_backup_jid(subclient)
            self.log.info(f"Job type of {jobid} is {jobtype}")
            if jobtype == "4":
                self.log.info("After max incrementals, differential job is auto started")

        except Exception as exp:
            self.log.info(f"Exception raised with error {exp}")
            raise Exception(f"Exception raised with error {exp}")

    def get_latest_backup_jid(self, subclient):
        """Get latest job id and job type of a given subclient"""
        query1 = f"select top(1) jobid,bkpLevel from jmbkpstats where appId in (select id from app_application where subclientName='{subclient.name}') ORDER BY jobid desc"
        self.log.info(f"query is {query1}")
        self._csdb.execute(query1)
        res1 = self._csdb.fetch_one_row()
        self.log.info(f"Latest jobid returned is {res1[0]}")
        return res1[0], res1[1]

    def get_data_connect_ip(self, job, MAMachine):
        """Get the IP used for NDMP DATA CONNECT"""
        self.log.info("Getting the IP used for DATA CONNECT..")
        line1 = MAMachine.get_logs_for_job_from_file(job.job_id, "NasBackup.log", "--- address")
        self.log.info(f"Filtered log lines are {line1}")
        a = line1.split('[')
        b = a[1].split(']')
        return(b[0])

    def create_entities(self, commcell, id, mediaagent):
        # Create entities for disklibrary and storagepolicy
        self.log.info("Creating entities for disklibrary and storagepolicy")
        self.commcell = commcell
        self.entities = CVEntities(self.commcell)

        # Create disklibrary
        disklibrary_inputs = {
            'disklibrary': {
                'name': "disklibrary_test_" + mediaagent,
                'mediaagent': mediaagent,
                'mount_path': self.entities.get_mount_path(mediaagent),
                'username': '',
                'password': '',
                'cleanup_mount_path': True,
                'force': False
            }
        }
        self.disklib_props = self.entities.create(disklibrary_inputs)

        self.log.info("Creating disk library using media agent {0}".format(mediaagent))

        # create storage policy
        storagepolicy_inputs = {
            'target': {
                'library': "disklibrary_test_" + mediaagent,
                'mediaagent': mediaagent,
                'force': False
            },
            'storagepolicy': {
                'name': "storagepolicy_" + id + "_" + mediaagent,
                'dedup_path': None,
                'incremental_sp': None,
                'retention_period': 3,
            },
        }
        self.log.info(" Creating storage policy using library {0}".format("disklibrary_test_" + mediaagent))
        self.entity_props = self.entities.create(storagepolicy_inputs)
        return self.disklib_props, self.entity_props

    def delete_entities(self, commcell, disklib_props, entity_props):
        self.log.info("Deleting entities for disklibrary and storagepolicy")
        self.commcell = commcell
        self.entities = CVEntities(self.commcell)
        self.entities.delete(disklib_props)
        self.entities.delete(entity_props)

    def delete_nre_destinations(self, client=None, path=None):
        self.log.info("Deleting NRE restore destination paths")
        try:
            client.remove_directory(path)
        except:
            self.log.info(f"Encountered an exception while deleting {path}")
            pass

    def restore_to_selected_machine(self, options_selector, windows_client=None, linux_client=None, size=5120):
        self.log.info("Restore data to user selected machine")
        if windows_client:
            #windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            try:
                drive = options_selector.get_drive(windows_client, size)
            except OSError:
                self.log.info("No drive found")
            dir_path = drive + options_selector._get_restore_dir_name()
            windows_client.create_directory(dir_path)

            self.log.info(
                "Windows Restore Client obtained: %s", windows_client.machine_name
            )
            self.log.info("Windows Restore location: %s", dir_path)
            windows_restore_client = windows_client
            windows_restore_location = dir_path
            return windows_restore_client, windows_restore_location

        elif linux_client:
            try:
                mount_path = options_selector.get_drive(linux_client, size)
            except OSError:
                self.log.info("No drive found")

            dir_path = mount_path + options_selector._get_restore_dir_name()
            linux_client.create_directory(dir_path)

            self.log.info(
                "Linux Restore Client obtained: %s", linux_client.machine_name
            )
            self.log.info("Linux Restore location: %s", dir_path)
            linux_restore_client = linux_client
            linux_restore_location = dir_path
            return linux_restore_client, linux_restore_location

    def verify_trueup(self, mamachine, job):
        str1 = "The job is qualified for TrueUp"
        str2 = "Job qualified for TrueUp as TrueUp rules are met"
        line1 = mamachine.get_logs_for_job_from_file(job, "FileScan.log", str1)
        line2 = mamachine.get_logs_for_job_from_file(job, "FileScan.log", str2)
        self.log.info(f"line1 is {line1}")
        self.log.info(f"line2 is {line2}")
        if line1.find(str1) or line2.find(str2):
            self.log.info("Trueup ran fine for the incremental job")
            return 1
        else:
            self.log.info("True up is not enabled, failing the TC")
            return 0