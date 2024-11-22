# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for content analyzer related operations

    ContentAnalyzerHelper:

        __init__(testcase)                    --  Initialize the ContentAnalyzerHelper object

        validate_tppm_setup                   --  Validates whether dynamic tppm exists between index server
                                                        and content analyzer client

        install_content_analyzer()            --  Install content analyzer on Fresh machine

        validate_autoshutdown()               --  Validates whether auto shutdown of python process works or not

        setup_autoshutdown()                  --  Setup auto shutdown timer registry for python process

        check_all_python_process()            --  Checks whether all python process is up and running on CA client

        generate_entity_config()              --  generates the entity caconfig value for the given input

        check_extracted_entity_with_src()     --  cross verifies whether extracted entities are part of source data

        get_latest_extractingat_solr()        --  gets the latest extracting at value from solr for given subclient list

        get_latest_forward_time_db()          --  gets latest forward ref time value from CS db for given subclient list

        monitor_offline_entity_extraction()   --  monitors the offline CI'ed docs entity extraction job progress

        move_zip_data_to_client()             --  Moves zip's extracted files to remote client

        get_classifier_info()                 --  Returns classifier info for the given attribute

        is_classifier_model_data_exists()     --  Checks whether classifier model data exists on client or not

        split_zip_file()                      --  Splits zip file into two separate zip files

        add_folder_to_zip()                   --  Adds folder to the zip file

        validate_multiple_ca_node_request()   --  Verifies whether crawl job is pushing request to multiple CA nodes or not

        set_ca_debug_level()                  --  Sets debug level for Content Analyzer log file

"""
import time
import os
import datetime
import json
import base64
import shutil
import zipfile
from cvpysdk.deployment.install import Install
from cvpysdk.deployment import deploymentconstants as install_constants
from cvpysdk.deployment.download import Download
from cvpysdk.deployment.deploymentconstants import DownloadOptions as download_constants
from cvpysdk.deployment.deploymentconstants import DownloadPackages as pkg_constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from Server.JobManager.jobmanager_helper import JobManager
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.search_engine_util import SearchEngineHelper
from dynamicindex.utils.constants import CONTENT_ANALYZER, INDEX_STORE, WINDOWS, UNIX


class ContentAnalyzerHelper():
    """ contains helper class for content analyzer related operations"""

    def __init__(self, tc_object):
        self.commcell = tc_object.commcell
        self.csdb = tc_object.csdb
        self.log = tc_object.log
        self.ca_process_name = "python"
        self.tc_object = tc_object
        self._python_process_count = 16
        self.ca_log_name = "ContentAnalyzer.log"

    def set_ca_debug_level(self, ca_nodes, level):
        """Sets debug level for Content Analyzer log file

            Args:

                    ca_nodes    (list)      --  List of Content Analyzer nodes

                    level       (int)       --  debug log level

                Returns:

                    None

                Raises:

                    Exception:

                        if failed set debug level
        """
        for node in ca_nodes:
            ca_service_name = dynamic_constants.CA_SERVICE_NAME_UNIX
            restart_required = True
            machine_obj = Machine(machine_name=node, commcell_object=self.commcell)
            if machine_obj.os_info.lower() == "windows":
                ca_service_name = dynamic_constants.CA_SERVICE_NAME_WINDOWS
                restart_required = False
            machine_obj.set_logging_debug_level(service_name=ca_service_name, level=level)
            self.log.info(f"Successfully set debug level on CA - {node} with level - {level}")
            # For unix CA, we need to restart service so that debug level gets honored
            if restart_required:
                client_obj = self.commcell.clients.get(node)
                self.log.info(f"Restarting client as it is Unix CA - {node}")
                client_obj.restart_service()

    def validate_multiple_ca_node_request(
            self,
            job_id,
            ca_nodes,
            expected_state='completed',
            time_limit=30,
            ca_nodes_down=None):
        """Verifies whether crawl job is pushing request to multiple CA nodes

                Args:

                    job_id      (str)       --  SDG crawl job id

                    ca_nodes    (list)      --  List of Content Analyzer nodes configured in plan

                    expected_state (str)    --  job state to finish for. Default : completed

                    ca_nodes_down   (list)  --  List of content analyzer node which is down

                Returns:

                    None

                Raises:

                    Exception:

                        if failed to check log file for pattern

                        if CA node didnt receive request

        """
        pattern = f"_{job_id}_"
        request_count = {}
        machine_objs = {}
        for node in ca_nodes:
            machine_objs[node] = Machine(machine_name=node, commcell_object=self.commcell)
            request_count[node] = 0
        self.log.info(f"Created machine objects for multiple CA nodes. Pattern to look - {pattern}")
        self.log.info(f"Going to Monitor Job started with id {job_id}")
        job_manager = JobManager(_job=job_id, commcell=self.commcell)
        job_obj = job_manager.job
        time_limit = time.time() + time_limit * 60
        while True:
            job_status = job_obj.status.lower()
            self.log.info(f"Job Status - {job_status}")
            if time.time() >= time_limit or job_status in ['killed', 'failed']:
                raise Exception(f"Timeout happened or job Killed/Failed. Please check logs")
            for node in ca_nodes:
                log_lines = machine_objs[node].get_logs_for_job_from_file(
                    log_file_name=self.ca_log_name, search_term=pattern)
                current_count = 0
                if log_lines:
                    current_count = len(log_lines.split('\r\n'))
                self.log.info(
                    f"Current pattern count matching is [{current_count}] on client [{node}]. Older count is [{request_count[node]}]")
                # if log rolls over at end of job, then probably we will see no request.
                # To avoid this corner case, update request count only if current count is
                # greater than 0
                if current_count > 0:
                    request_count[node] = current_count
                self.log.info(f"Request count for node[{node}] is [{request_count[node]}]")
            if (job_status == expected_state):
                self.log.info(f"Job reached Expected State : {expected_state}")
                break
            time.sleep(10)
        final_msg = ""
        for node in ca_nodes:
            if request_count[node] == 0:
                if ca_nodes_down:
                    if node not in ca_nodes_down:
                        raise Exception(f"Working CA node [{node}] didn't receive any request")
                    else:
                        self.log.info(f"Stopped CA node [{node}] didn't receive any request as expected")
                else:
                    raise Exception(f"CA node [{node}] didn't receive any request")
            log_msg = f"Request count Stats - Node [{node}] count [{request_count[node]}]"
            final_msg = f"{final_msg} | {log_msg} "
            self.log.info(log_msg)
        self.tc_object.result_string = final_msg

    def add_folder_to_zip(self, folder, zip_name, extension, force_folder_struct=False, delete_after_zip=False):
        """Adds folder to the zip file

            Args:

                folder              (str)       --  Folder path which needs to be zipped

                extension           (str)       --  Zip file format

                zip_name            (str)       --  Name of the zip file

                force_folder_struct (bool)      --  Specify whether to maintain folder structure in zip file or not

                delete_after_zip    (bool)      --  Specifies whether to delete the folder after zipping

            Returns:

                None

            Raises:

                Exception:

                        if failed to create zip file

        """
        base_dir = folder
        if not force_folder_struct:
            base_dir = os.path.basename(os.path.normpath(folder))
        self.log.info("Base directory for zip : %s", base_dir)
        self.log.info("Zip folder : %s", folder)
        self.log.info("Zipping file name : %s", zip_name)
        shutil.make_archive(base_name=zip_name, root_dir=os.path.dirname(folder), format=extension, base_dir=base_dir)
        if delete_after_zip:
            shutil.rmtree(folder)

    def split_zip_file(self, zip_file, split_count=2, doc_count=None):
        """Splits zip file into two separate zip files

            Args:

                zip_file            (str)       --      Zip file path

                split_count         (int)       --      specifies split count for zip split

                doc_count           (int)       --      No of documents to be in each splited zip file

            Returns:

                list        --  containing separated zip file paths

        """
        zip_file_paths = []
        self.log.info("Splitting zip file into [%s]", split_count)
        if not zipfile.is_zipfile(zip_file):
            raise Exception("Not a valid zip file")
        zip_obj = zipfile.ZipFile(zip_file, 'r')
        total_elements = len(zip_obj.namelist())
        bucket_count = int(float(total_elements / split_count))
        if doc_count:
            self.log.info("Ignoring Split count as Document count is set by caller as : %s", doc_count)
            bucket_count = int(doc_count)
        ops = OptionsSelector(self.commcell)
        temp_folder = os.path.join(AUTOMATION_DIRECTORY, "Temp")
        folder = os.path.join(temp_folder, f"Automation_CAHelper_{ops.get_custom_str()}")
        os.makedirs(folder)
        index = 0
        for element in range(total_elements):
            index = index + 1
            zip_info = zip_obj.getinfo(zip_obj.namelist()[element])
            if zip_info.is_dir():
                self.log.info("Ignoring Directory : %s", zip_info.filename)
                continue
            zip_obj.extract(zip_obj.namelist()[element], folder)
            if index > bucket_count or element == total_elements - 1:
                self.log.info("Split size reached. Compress it")
                file_name = os.path.join(temp_folder, f"Split_zip_{ops.get_custom_str()}_{element}")
                self.add_folder_to_zip(folder=folder, zip_name=file_name, force_folder_struct=False,
                                       delete_after_zip=True, extension="zip")
                zip_file_paths.append(f"{file_name}.zip")
                index = 0
                if not element == total_elements - 1:
                    # deleting folder after zipping. Recreate it again
                    os.makedirs(folder)
        self.log.info("Splited zipped paths : %s", zip_file_paths)
        zip_obj.close()
        return zip_file_paths

    def get_classifier_info(self, name, attribute):
        """Returns classifier info for the given param

            Args:

                name            (str)       --  Name of the classifier

                attribute       (str)       --  attribute whose info has to be returned

            Returns:

                str     --  classifier's attribute value

            Raises:
                Exception:

                    if failed to find classifier

                    if failed to find classifier attribute

                    if entity is not a classifier
        """
        # Refresh always so that we get latest xml for classifiers
        self.log.info("Refreshing Activate Entity before fetching details")
        self.commcell.activate.entity_manager().refresh()
        if not self.commcell.activate.entity_manager().has_entity(name):
            raise Exception("Classifier entity not found")
        entity_obj = self.commcell.activate.entity_manager().get(name)
        if dynamic_constants.CLASSIFIER_ENTITY_TYPE != entity_obj.entity_type:
            raise Exception("Not a valid classifier entity")
        entity_xml = entity_obj.entity_xml
        if dynamic_constants.CLASSIFIER_DETAILS_JSON_NODE not in entity_xml:
            raise Exception("Classifier details info missing")
        classifier_details = entity_xml[dynamic_constants.CLASSIFIER_DETAILS_JSON_NODE]
        if attribute not in classifier_details:
            raise Exception("Attribute not found")
        self.log.info(f"Attribute = [{attribute}] & value = {classifier_details[attribute]}")
        return str(classifier_details[attribute])

    def is_classifier_model_data_exists(self, name, trained_only=True, model_info=None, skip_solr=False):
        """checks whether classifier model experiment ML data folder exists or not

            Args:

                name                (str)       --  Name of the classifier

                trained_only        (bool)      --  Bool to specify whether to check this only
                                                        for trained CA or for Sync CA as well

                skip_solr           (bool)      --  Bool to specify whether to skip solr train data check or not
                                                            Default : False

                model_info          (dict)      --  containing model data info
                                                        Default : None [Force fetch info from CS DB]

                                    Example : {
                                    "CAUsedInTraining": "
                                                        {
                                                        "caUrl": "http://yokosolinux.sna.commvault.com:22000",
                                                        "clientId": 34, "cloudName": "YokosoLinux_ContentAnalyzer",
                                                        "cloudId": 9,
                                                        "lastModelTrainTime": 1606387881
                                                        }",
                                    "modelURI": "../ContentAnalyzer/bin/classifier_models/custom_trained_models/mlruns/5/0a9e610a56d04f128fd63c1afbf0f982/artifacts",
                                    "entity_id": 101
                                        }

            Returns:

                  bool      --  to denote model folder exists on client

                  dict      --  containing model data location on both trained & sync nodes
        """
        sync_result = []
        classifier_info = {}
        trained_ca = None
        model_uri = None
        entity_id = None
        if model_info is None:
            trained_ca = self.get_classifier_info(name=name, attribute=dynamic_constants.CLASSIFIER_ATTRIBUTE_CA_USED)
            model_uri = self.get_classifier_info(name=name, attribute=dynamic_constants.CLASSIFIER_ATTRIBUTE_MODEL_URI)
            entity_obj = self.commcell.activate.entity_manager().get(name)
            entity_id = entity_obj.entity_id
            classifier_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_CA_USED] = trained_ca
            classifier_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_MODEL_URI] = model_uri
            classifier_info[dynamic_constants.CLASSIFIER_ENTITY_ID] = entity_id
        else:
            trained_ca = model_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_CA_USED]
            model_uri = model_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_MODEL_URI]
            entity_id = model_info[dynamic_constants.CLASSIFIER_ENTITY_ID]
        trained_ca = trained_ca.replace("'", "\"")
        trained_ca_json = json.loads(trained_ca)
        trained_client_id = trained_ca_json[dynamic_constants.CLASSIFIER_ATTRIBUTE_CLIENTID]
        self.log.info("Trained CA client id : %s", trained_client_id)
        trained_client_obj = self.commcell.clients.get(trained_client_id)
        trained_client_name = trained_client_obj.client_name
        install_dir = trained_client_obj.install_directory
        self.log.info("Trained CA client Name : %s", trained_client_name)
        self.log.info("Trained CA Install directory : %s", install_dir)
        model_folder = model_uri.replace("..", install_dir)
        # Form folder to MLrun ID
        model_folder = os.path.dirname(os.path.dirname(model_folder))
        self.log.info("Trained CA model Folder : %s", model_folder)
        trained_client_machine_obj = Machine(machine_name=trained_client_name, commcell_object=self.commcell)
        if trained_client_machine_obj.check_directory_exists(directory_path=model_folder):
            self.log.info("Model data exists on client : %s", trained_client_name)
            sync_result.append('True')
        else:
            self.log.info("Model data not exists on trained client : %s", trained_client_name)
            sync_result.append('False')
        if not skip_solr:
            dataset_response = trained_client_machine_obj.get_api_response_locally(
                api_url=f"{dynamic_constants.CLASSIFIER_SOLR_DATASET_ENTITY_QUERY}{entity_id}")
            dataset_response = json.loads(dataset_response)
            if int(dataset_response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]) > 0:
                self.log.info("Dataset solr core contains data for this entity")
                sync_result.append('True')
            else:
                self.log.info("Dataset solr core does not contains data for this entity")
                sync_result.append('False')
            dataset_info_response = trained_client_machine_obj.get_api_response_locally(
                api_url=f"{dynamic_constants.CLASSIFIER_SOLR_DATASET_INFO_ENTITY_QUERY}{entity_id}")
            dataset_info_response = json.loads(dataset_info_response)
            if int(dataset_info_response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]) > 0:
                self.log.info("Dataset info solr core contains data for this entity")
                sync_result.append('True')
            else:
                self.log.info("Dataset info solr core does not contains data for this entity")
                sync_result.append('False')
        else:
            self.log.info("Skipping trained model data check on content extractor Solr")
        if not trained_only:
            self.log.info("Option to validate all CA's is Set")
            sync_ca = None
            # find all synced CA's
            if model_info is None:
                sync_ca = self.get_classifier_info(name=name, attribute=dynamic_constants.CLASSIFIER_ATTRIBUTE_SYNC_CA)
                classifier_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_SYNC_CA] = sync_ca
            else:
                sync_ca = model_info[dynamic_constants.CLASSIFIER_ATTRIBUTE_SYNC_CA]
            sync_ca = sync_ca.replace("'", "\"")
            sync_ca_json = json.loads(sync_ca)
            for content_analyzer in sync_ca_json[dynamic_constants.CLASSIFIER_SYNC_CA_LIST_JSON_NODE]:
                client_id = content_analyzer[dynamic_constants.CLASSIFIER_ATTRIBUTE_CLIENTID]
                self.log.info("Synced CA client id : %s", client_id)
                client_name = self.commcell.clients.get(client_id).client_name
                machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell)
                if model_info is None:
                    experiment = f"{name}_{entity_id}".lower()
                    self.log.info("Experiment name formed : %s", experiment)
                    api = f"{dynamic_constants.CLASSIFIER_ML_API}{experiment}"
                    response = machine_obj.get_api_response_locally(api_url=api)
                    response = response.strip()
                    self.log.info("API Response : %s", response)
                    response_json = json.loads(response)
                    model_folder = response_json[dynamic_constants.CLASSIFIER_EXPERIMENT][dynamic_constants.CLASSIFIER_ARTIFACT_LOCATION]
                    if machine_obj.os_info.lower() == dynamic_constants.UNIX:
                        model_folder = model_folder.replace("file:/", "")
                    else:
                        model_folder = model_folder.replace("file:///", "")
                    # put this info into classifier info dict
                    classifier_info[f"{client_id}_{dynamic_constants.CLASSIFIER_ATTRIBUTE_MODEL_URI}"] = model_folder
                else:
                    model_folder = model_info[f"{client_id}_{dynamic_constants.CLASSIFIER_ATTRIBUTE_MODEL_URI}"]
                self.log.info("Model folder got : %s", model_folder)
                if machine_obj.check_directory_exists(directory_path=model_folder):
                    self.log.info("Model data exists on client : %s", client_name)
                    sync_result.append('True')
                else:
                    self.log.info("Model data not exists on client: %s", client_name)
                    sync_result.append('False')
        self.log.info("Classifier Info's : %s ", classifier_info)
        self.log.info("Result list : %s", sync_result)
        result = all(elem == sync_result[0] for elem in sync_result)
        if result:
            self.log.info("Is exists matched for all CA nodes - %s", str(result))
            return 'True' == sync_result[0], classifier_info
        raise Exception("Classifier CA model folder exists status is of mixed type. Please check")

    def move_zip_data_to_client(self, client_name, zip_file, extract_file_count=0):
        """Moves zip file to remote client and unzip

            Args:

                client_name         (str)       --  Name of the client

                zip_file            (str)       --  zip file path on controller

                extract_file_count  (int)       --  Specifies how many files to extract from zip file

            Returns:

                  str   --  Destination folder path on client where data was copied
        """
        machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell)
        ops = OptionsSelector(self.commcell)
        drive = ops.get_drive(machine=machine_obj)
        temp_name = f"CAHelper_{ops.get_custom_str()}"
        destination_folder = f"{drive}Automation_{temp_name}"
        folder = os.path.join(AUTOMATION_DIRECTORY, "Temp", temp_name)
        os.makedirs(folder)
        self.log.info("Extracting zip file on controller")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            if not extract_file_count:
                self.log.info("Extracting all files inside zip")
                zip_ref.extractall(folder)
            else:
                self.log.info(f"Extracting {extract_file_count} files from zip")
                list_Of_files = zip_ref.namelist()
                index = 0
                for file_name in list_Of_files:
                    if file_name.endswith("/"):
                        continue
                    self.log.info(f"Extracting File : {file_name}")
                    zip_ref.extract(file_name, folder)
                    index = index + 1
                    if index == extract_file_count:
                        break
        self.log.info("Copying extracted content from controller to remote client : %s", folder)
        machine_obj.copy_from_local(local_path=folder, remote_path=destination_folder,
                                    threads=20, raise_exception=True)
        self.log.info("Folder copy done")
        self.log.info("Deleting locally extracted zip content folder : %s", folder)
        shutil.rmtree(folder)
        return destination_folder

    def validate_tppm_setup(self, content_analyzer, exists=True):
        """ Validates whether dynamic tppm entry exists between source index server and destination CA client

                Args:

                    content_analyzer    (int/str)   --      Name of the content analyzer client or client id

                    exists              (bool)      --      Specifies whether tppm entry should exists or not in table
                                                                     Default : True

                Returns:

                    None

                Raises:

                    Exception:

                            if input is not valid

                            if failed to query CS db

                            if tppm validation fails

        """

        self.log.info(f"Going to validate whether tppm exists - {exists} for  "
                      f"client - {content_analyzer}")
        client_id = None
        if isinstance(content_analyzer, str):
            content_analyzer_obj = self.commcell.content_analyzers.get(content_analyzer)
            client_id = content_analyzer_obj.client_id
        else:
            client_id = content_analyzer
        self.log.info(f"Content Analyzer object initialized")
        _query = f"select count(*) as TotalTPPM from app_firewalltppm where tppmtype={dynamic_constants.TPPM_TYPE} " \
                 f"and fromEntityType={dynamic_constants.CLIENT_ENTITY_ID} and " \
                 f"toEntityType={dynamic_constants.CLIENT_ENTITY_ID} and " \
                 f"fromEntityId={client_id} and " \
                 f"toEntityId={client_id} and toPortNumber={dynamic_constants.DEFAULT_CA_PORT}"
        self.log.info(f"Querying CS db - {_query}")
        self.csdb.execute(_query)
        tppm = int(self.csdb.fetch_one_row()[0])
        if exists:
            if tppm == 0 or tppm > 1:
                raise Exception(f"No TPPM or Duplicate TPPM entry exists. Count from Table : {tppm}")
            self.log.info(f"TPPM entry exists from source client id : {client_id} "
                          f"to destination client id : {client_id}")
        else:
            if tppm >= 1:
                raise Exception(f"TPPM entry exists. Count from Table : {tppm}")
            self.log.info(f"TPPM entry does not exists from source client id : {client_id} "
                          f"to destination client id : {client_id}")
        if exists:
            self.log.info("Going to Fetch network configuration summary for this CA client and validate tppm")
            ca_client_obj = self.commcell.clients.get(client_id)
            if dynamic_constants.TPPM_CONFIG not in ca_client_obj.get_network_summary():
                raise Exception(f"Network summary doesn't show CA tppm settings - {dynamic_constants.TPPM_CONFIG}")
        self.log.info("TPPM configuration validated successfully")

    def monitor_offline_entity_extraction(self, subclient_ids, extracting_times, timeout=60):
        """ Monitors the entity extraction job progress for offline cie'd docs in search engine

                Args:

                    subclient_ids        (list)         --  list of subclient ids

                    extracting_times     (Nested list)  -- Extractingat times for subclient from solr

                    Example : [[{'apid': 5999, 'extractingat': '2020-02-18T10:13:54.035Z'}]]

                    timeout              (int)          -- Maximum timeout value for this function in Mins
                                                                default : 60Mins

                Return:
                    None

                Exception:

                         if unable to find job stats

                         if timeout exceeds
        """
        self.log.info("Going to monitor the Entity Extraction job for offline CI'ed documents")
        job_time = 0
        finished_subclient = 0
        total_subclient = len(extracting_times)
        while job_time <= timeout:
            finished_subclient = 0
            forward_times = self.get_latest_forward_time_db(
                subclient_ids=subclient_ids)
            self.log.info("Response json from CS DB : %s", forward_times)
            solr_date_time_format = '%Y-%m-%dT%H:%M:%SZ'
            cs_date_time_format = '%Y-%m-%dT%H:%M:%SZ'
            for subclient in extracting_times:
                solr_subclient = subclient[0]
                mod_solr_subclient = str(solr_subclient['extractingat']).split('.', 1)[0] + 'Z'
                solr_time = datetime.datetime.strptime(mod_solr_subclient, solr_date_time_format)
                for row in forward_times:
                    cs_subclient = row[0]
                    if cs_subclient['apid'] == solr_subclient['apid']:
                        self.log.info("Checking job stats for subclient id :%s", cs_subclient['apid'])
                        cs_time = datetime.datetime.strptime(str(cs_subclient['forwardreftime']), cs_date_time_format)
                        if cs_time == solr_time:
                            self.log.info("Entity extraction completed for subclient : %s", cs_subclient['apid'])
                            self.log.info("Forward reference time set in DB is : %s", cs_time)
                            finished_subclient = finished_subclient + 1
                        else:
                            self.log.info("Entity Extraction not completed for subclient : %s", cs_subclient['apid'])
                            self.log.info("Solr extracting time : %s", solr_time)
                            self.log.info("CS forward reference time : %s", cs_time)
            if finished_subclient == total_subclient:
                self.log.info("Entity extraction completed for all subclients in [%s] mins", job_time)
                break
            time.sleep(60)
            job_time = job_time + 1
        if finished_subclient != total_subclient:
            raise Exception("Operation Timed-out with entity extraction job. Please check")

    def get_latest_extractingat_solr(self, subclient_ids, solr_url):
        """ gets the latest extracting at value for given subclient list from solr

                Args:
                    subclient_ids        (list)   --  list of subclient ids

                    solr_url             (str)    -- Solr url
                        Example : "http://<searchengine_machinename>:<port no>/solr"

                Return:
                    dics : containing subclient and it's corresponding extractingat value from solr

                Exception:

                    if unable to find subclient docs in solr

                    if response is not success
        """
        engine_helper = SearchEngineHelper(tc_object=self.tc_object)
        response = []
        for subclient in subclient_ids:
            self.log.info("Going to get latest extractingat from solr for subclient : %s", subclient)
            new_solr_url = solr_url + "/collection1/select?q=apid:{0}&sort=extractingat desc&rows=1" \
                "&fl=extractingat,apid&wt=json".format(subclient)
            solr_response = engine_helper.execute_search_engine_query(query=new_solr_url)
            if not solr_response:
                raise Exception("No response from solr")
            response.append(solr_response['docs'])
        return response

    def get_latest_forward_time_db(self, subclient_ids):
        """ gets the latest extracting at value for given subclient list from CS db

                Args:
                    subclient_ids        (list)   --  list of subclient ids

                Return:
                    dics : containing subclient and it's corresponding forwardreftime value from db

                Exception:

                    if unable to find subclient docs in db

                    if response is not success
        """
        response = []
        for subclient in subclient_ids:
            self.log.info("Going to get latest extractingat from db for subclient : %s", subclient)
            _query = "select dbo.GetSolrDateString (min( forwardreftime )) as forwardreftime from EntityProcessor " \
                     "where EntityRulerId in ( select EntityRulerId from EntitySelection " \
                     "where SubclientID in ({0}) and enabled=1)".format(subclient)
            self.log.info("Querying CS DB : " + _query)
            self.csdb.execute(_query)
            fwd_time = self.csdb.fetch_one_row()
            if fwd_time is None:
                raise Exception("Unable to get forward ref time for subclient")
            fwd_times = [{'apid': int(subclient), 'forwardreftime': fwd_time[0]}]
            response.append(fwd_times)
        return response

    def check_extracted_entity_with_src(self, solr_response, entity_keys, source_data, expected_entity=None):
        """ Checks whether extracted entities are part of source data

                       Args:
                           solr_response        (dict)   --  Solr query response

                           entity_keys          (list)   -- list of entity keys to validate

                           source_data          (str)    -- Source data content

                           expected_entity      (dict)   -- dict of expected entities

                       Return:
                           None:

                       Exception:

                           if unable to find entity key in document

                           if extracted entity data doesn't match with source data
        """
        expected_count = 0
        actual_count = 0
        if expected_entity is not None:
            for value in expected_entity:
                if isinstance(expected_entity[value], list):
                    expected_count += len(expected_entity[value])
                else:
                    expected_count += 1
        for doc in solr_response['docs']:
            for entity_key in entity_keys:
                entity_name = ""
                if not entity_key.startswith("entity_"):
                    entity_name = "entity_" + entity_key
                else:
                    entity_name = entity_key
                if entity_name in doc:
                    self.log.info("Found the entity in the document: %s", entity_name)
                    if doc[entity_name] is not None and doc[entity_name] != "":
                        entity_extracted = doc[entity_name]
                        for entity_value in entity_extracted:
                            if source_data.find(entity_value) != -1:
                                if expected_entity is None:
                                    self.log.info("Source contains Entity value : %s", doc[entity_name])
                                else:
                                    self.log.info("Expected Entity check for key : %s", entity_name)
                                    self.log.info("Expected result : %s", expected_entity[entity_name])
                                    if entity_name in expected_entity and entity_value in expected_entity[entity_name]:
                                        self.log.info("Expected entity matched : %s", entity_value)
                                        actual_count += 1
                                    else:
                                        raise Exception("Expected entity Mismatched : " + entity_value)
                            else:
                                self.log.info("Source doesn't contain Entity value : %s", entity_value)
                                raise Exception("Source doesn't contain Entity value : " + entity_value)
                    else:
                        raise Exception("Entities extracted contains NoneType or Empty. Please check")
                else:
                    raise Exception("Expected entity is not found in Document : " + entity_name)
        if actual_count != expected_count:
            response = f"Actual {actual_count} vs Expected {expected_count} entity count not matched. Please check"
            raise Exception(response)
        self.log.info("Entity validation with source data succeeded")

    def generate_entity_config(self, entity_fields, rer=None, ner=None, derived=None):
        """ Generates the entity extraction caconfig value for the given input of regex entity list
                Args:

                    entity_fields (list) -- field name to extract entity from

                    rer  (list)          -- entity id's of RER

                    ner  (list)          -- entity id's of NER

                    derived  (list)      -- entity id's of DE

                Return:
                    str  -- caconfig attribute value

                Exception:
                    if unable to form request

                    if input is not list
        """
        if not (
                isinstance(rer, list) or isinstance(ner, list) or isinstance(derived, list) or
                isinstance(entity_fields, list)):
            raise Exception("Invalid input. specify input params as list")
        if rer is None:
            rer = []
        if ner is None:
            ner = []
        if derived is None:
            derived = []
        entity_extraction_json_value = [rer, ner, derived, entity_fields]
        caconfig = [{"task": dynamic_constants.ENTITY_EXTRACTION_JSON_PROP[x],
                     "arguments": entity_extraction_json_value[x]} for x in range
                    (0, len(dynamic_constants.ENTITY_EXTRACTION_JSON_PROP))]
        caconfig = json.dumps(caconfig)
        self.log.info("Generated Entity config Json : %s", caconfig)
        return caconfig

    def validate_autoshutdown(self, ca_client_name, shutdown_time=5):
        """setups auto shutdown on content analyzer machine

                    Args:

                        ca_client_name      (str)       --  CA client name

                        shutdown_time       (int)       --  Auto shutdown interval in mins (default:5Mins)

                    Returns:

                        bool    --  specifies whether auto-shutdown happened or not

        """
        client_obj = self.commcell.clients.get(ca_client_name)
        # make sure python process are up
        self.check_all_python_process(client_obj=client_obj)
        self.log.info("Waiting for auto shutdown to happen")
        time.sleep((shutdown_time + 2) * 60)
        try:
            self.check_all_python_process(client_obj=client_obj)
        except Exception as ep:
            if dynamic_constants.AUTO_SHUTDOWN_NO_PYTHON_RUNNING_ERROR in str(ep):
                self.log.info(dynamic_constants.AUTO_SHUTDOWN_WORKING)
                return True
            else:
                self.log.info(dynamic_constants.AUTO_SHUTDOWN_NOT_WORKING)
        return False

    def setup_autoshutdown(self, ca_client_name, shutdown_time=5):
        """setups auto shutdown on content analyzer machine

            Args:

                ca_client_name      (str)       --  CA client name

                shutdown_time       (int)       --  Auto shutdown interval in mins (default:5Mins)

            Returns:

                None

        """
        client_obj = self.commcell.clients.get(ca_client_name)
        machine_obj = Machine(machine_name=client_obj,
                              commcell_object=self.commcell)

        # add inactivity timer registry
        self.log.info(
            f"Setting up auto shutdown timer registry keys : {dynamic_constants.AUTO_SHUTDOWN_TIMER_REGISTRY} value : {shutdown_time} mins")
        machine_obj.remove_registry(key=dynamic_constants.CA_REGISTRY,
                                    value=dynamic_constants.AUTO_SHUTDOWN_TIMER_REGISTRY)
        machine_obj.remove_registry(key=dynamic_constants.CA_REGISTRY,
                                    value=dynamic_constants.EXTRACTOR_THREAD_TIME_OUT)
        machine_obj.create_registry(key=dynamic_constants.CA_REGISTRY,
                                    value=dynamic_constants.AUTO_SHUTDOWN_TIMER_REGISTRY,
                                    data=shutdown_time,
                                    reg_type=dynamic_constants.REG_DWORD)
        self.log.info(f"Going to restart Content Extractor service")
        if dynamic_constants.WINDOWS in client_obj.os_info.lower():
            client_obj.restart_service(service_name=dynamic_constants.CE_SERVICE_NAME)
        else:
            client_obj.restart_service(service_name=dynamic_constants.CE_SERVICE_NAME_UNIX)
        self.log.info("Service Restart finished")
        time.sleep(240)

    def check_all_python_process(self, client_obj, process_count=None):
        """ Checks whether all default python process is up and running on CA client
                Args:
                    client_obj  (obj)    --  Object of client

                    process_count (int)  --  count of python process to cross check

                Return:
                    None:

                Exception:
                    if unable to find python process

                    if total python process running is not greater than 16 for windows & 17 for unix
        """
        if not process_count:
            process_count = self._python_process_count
        self.log.info(f"CA client id - {client_obj.client_id}")
        cmd = ("(Get-Process | where-object{$_.ProcessName -eq \"%s\"}).Count"
               % self.ca_process_name)
        machine_obj = Machine(client_obj, self.commcell)
        if machine_obj.os_info == "UNIX":
            self.log.info("This is the unix machine")
            if process_count == self._python_process_count:  # default value
                process_count = process_count + 1
            cmd = ("ps -ef | grep -w \"%s\" | grep -v grep | wc -l" % self.ca_process_name)
        self.log.info("Command Formed : %s", cmd)
        total_process_running = machine_obj.execute_command(cmd)
        self.log.info("Python Process Expected count :  Actual count -- %s",
                      str(process_count) + " : " + str(total_process_running.output))
        if len(total_process_running.exception) != 0 or int(total_process_running.output) == 0:
            self.log.info("Python process is not up on CA client.")
            raise Exception(dynamic_constants.AUTO_SHUTDOWN_NO_PYTHON_RUNNING_ERROR)
        # 1-Handler + 7-Generic client + 1 Email + 1 Doc + 1 NER
        if int(total_process_running.output) >= process_count:  # due to dynamic calculation changed to >= check
            self.log.info("All python process is up and running fine.")
            return
        raise Exception("Few python process didn't come up on CA client. Please check")

    def install_content_analyzer(
            self,
            machine_name,
            user_name,
            password,
            platform=WINDOWS,
            pkg=CONTENT_ANALYZER,
            **kwargs):
        """ installs the content analyzer package or the provided package on given machine name
                Args:
                    machine_name (str/list)    --  Name of the machine(s)

                    user_name    (str)    --  Username to access machine

                    password     (str)    --  Password to access machine

                    platform     (str)    --  platform type for machine (Default:Windows)

                    pkg          (str)    --  package which user want to install

                kwargs:

                    sw_cache_client     (str)   --  Remote cache client to be used

                Return:
                    None:

                Exception:
                    if failed to install package

                    if failed to download package on CS
        """
        if pkg not in [INDEX_STORE, CONTENT_ANALYZER]:
            raise Exception("Provided package is not supported by this function")
        is_unix_platform = False
        if platform.lower() == WINDOWS:
            self.log.info("Setting platform type as Windows")
            os_list = pkg_constants.WINDOWS_64.value
            if pkg == INDEX_STORE:
                feature_list = [install_constants.WindowsDownloadFeatures.INDEX_STORE.value,
                                install_constants.WindowsDownloadFeatures.INDEX_GATEWAY.value,
                                install_constants.WindowsDownloadFeatures.CONTENT_EXTRACTOR.value]
            else:
                feature_list = [install_constants.WindowsDownloadFeatures.CONTENT_ANALYZER.value]
        elif platform.lower() == UNIX:
            self.log.info("Setting platform type as Unix")
            is_unix_platform = True
            os_list = pkg_constants.UNIX_LINUX64.value
            feature_list = [install_constants.UnixDownloadFeatures.CONTENT_ANALYZER.value]
        else:
            raise Exception("Unsupported platform type provided")
        self.log.info("Download the latest updates for the current service pack level on commcell : %s",
                      self.commcell.commserv_version)
        download_obj = Download(self.commcell)
        job_obj = download_obj.download_software(
            options=download_constants.SERVICEPACK_AND_HOTFIXES.value,
            os_list=[os_list],
            service_pack=self.commcell.commserv_version)
        self.log.info("Invoked the download software job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this download job for completion")
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Downloading s/w package on CS failed. Please check logs")
            raise Exception("Download s/w on CS failed")
        self.log.info("Download job finished")
        self.log.info(f"Going to do install software ({pkg}) on VM clients : {machine_name}")
        install_obj = Install(self.commcell)
        password = password.encode()
        password = base64.b64encode(password)
        password = password.decode()
        self.log.info("Decoded password for input json : %s", password)
        if is_unix_platform:
            job_obj = install_obj.install_software(
                client_computers=[machine_name] if isinstance(machine_name, str) else machine_name,
                unix_features=feature_list,
                username=user_name,
                password=password,
                sw_cache_client=kwargs.get('sw_cache_client', None))
        else:
            job_obj = install_obj.install_software(
                client_computers=[machine_name] if isinstance(machine_name, str) else machine_name,
                windows_features=feature_list,
                username=user_name,
                password=password,
                sw_cache_client=kwargs.get('sw_cache_client', None))
        self.log.info("Invoked the install software job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this install job for completion")
        # Monitor job for 3hrs
        if not job_obj.wait_for_completion(timeout=180):
            self.log.info(f"Installing {pkg} package on vm failed. Please check logs")
            raise Exception(f"Push installation of {pkg} package failed")
        self.log.info(f"{pkg} package installed successfully on VM client")
        if pkg == CONTENT_ANALYZER:
            self.log.info('Sleeping for 3 minutes for the python process to be up')
            time.sleep(180)
            self.log.info("Refreshing the Content Analyzer")
            self.commcell.content_analyzers.refresh()
