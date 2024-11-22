# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for activate cvpysdk related operations

ActivateSDKHelper:

     __init__()                         --  Initialize the ActivateSDKHelper object

     get_latest_job_id()                --  returns the latest crawl job id invoked for data source

     validate_sensitive_count()         --  Validates total sensitive document count in data source with source file count

     do_sdg_cleanup()                   --  deletes project/plan/inventory from commcell

     wait_for_playback_for_cijob()      --  Waits for playback to complete before kicking in CI job again

     set_client_wrkload_region()        --  Sets region for given client name

     download_validate_compliance_export()  --  Method to download and validate the compliance search export

"""
import os
import time
import zipfile
import xmltodict

from cvpysdk.activateapps.constants import ComplianceConstants
from cvpysdk.activateapps.sensitive_data_governance import Project
from cvpysdk.activateapps.file_storage_optimization import FsoServer
from AutomationUtils import logger, database_helper
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.constants import DOWNLOAD_FOLDER_PATH


class ActivateSDKHelper:
    """ contains helper class for activate cvpysdk related operations"""

    def __init__(self, commcell_object, app_entity=None, data_source=None):
        """Initialize ActivateSDKHelper class

                Args:

                    commcell_object     (obj)   --  Object of class Commcell

                    app_entity          (obj)   --  object of class Project(SensitiveDataGovernance)/
                                                    object of class FSOServer(FileStorageOptimization)

                    data_source         (name)  --  Name of the data source
        """
        self.commcell = commcell_object
        self.log = logger.get_log()
        self.app_entity = None
        self.activate_obj = commcell_object.activate
        self.all_ds_obj = None
        self.ds_obj = None
        self.is_app_ds_initialized = False
        self.log.info(f"SDK Helper Init started")
        if app_entity:
            self.log.info(f"SDK Helper Initialized with app")
            if isinstance(app_entity, Project):
                self.app_entity = app_entity
            if isinstance(app_entity, FsoServer):
                self.app_entity = app_entity
            self.all_ds_obj = app_entity.data_sources
            if data_source:
                self.ds_obj = self.all_ds_obj.get(data_source)
                self.is_app_ds_initialized = True
                self.log.info(f"SDK Helper initialized with data source")

    def wait_for_playback_for_cijob(self, job_id, analyze_client_id, timeout=240, check_interval=5):
        """Waits for playback to complete before kicking in CI job again

            Args:

                job_id          (str)       --  job id of content indexing job

                analyze_client_id   (str)   --  Analysing client id in SDG or FSO

                timeout             (int)   --  timeout in mins
                                                    (Default:4hrs/240Mins)

                check_interval      (int)   --  Interval between playback success check in Mins
                                                    (Default : 5mins)


            Returns:

                None

            Raises:

                Exception:

                    if failed to find index server db details or ci job

        """
        job_obj = self.commcell.job_controller.get(job_id)
        self.log.info(f"Going to suspend CI job - {job_id}")
        job_obj.pause(wait_for_job_to_pause=True)
        self.log.info(f"Successfully suspended CI job. Wait for playback to finish")
        # playback validation
        options_selector_object = OptionsSelector(self.commcell)
        database_helper.set_csdb(CommServDatabase(self.commcell))
        _query = f"select appid,max(servstartdate) as bkstarttime from jmbkpstats(nolock) where status in (1,3,14) and appid in (select id from app_application(nolock) where clientid={analyze_client_id} and guid in (select dbname from app_indexdbinfo where isprimary=0)) group by appid"
        column_list, resultset = options_selector_object.exec_commserv_query(query=_query)
        time_limit = time.time() + timeout * 60
        while True:
            all_done = True
            if time.time() >= time_limit:
                self.log.info(f"Time limit reached. Exiting....")
                raise Exception("Timeout happened while waiting for playback to happen")
            for row in resultset:
                self.log.info(f"Subclient id : {row[0]} with MAX BkpStart time : {row[1]} found for comparison")
                _query = f"select top 1 dbid,dbuptodate,properties from idxdbstate(nolock) where dbid in (select id from app_indexdbinfo(nolock) where isprimary=0 and dbname in (select guid from app_application(nolock) where clientid={analyze_client_id} and id={row[0]}))"
                column_list, dbresultset = options_selector_object.exec_commserv_query(query=_query)
                if len(dbresultset[0]) == 1:  # empty single quote column
                    self.log.info(f"DBState table entry missing for subclient - {row[0]}")
                    all_done = False
                    continue
                prop_xml = dbresultset[0][2]  # get properties xml from row 1 as it is always uses top 1 in query
                prop_dict = xmltodict.parse(prop_xml)
                db_last_played_time = int(prop_dict['Indexing_DbStats']['@lastPlayedBkpTime'])
                db_last_bkp_time = int(row[1])
                if db_last_played_time < db_last_bkp_time:
                    all_done = False
                    self.log.info(
                        f"Subclient with ID : [{row[0]}] is not yet played back fully. Last Backup time - [{db_last_bkp_time}] "
                        f"Last Playback Time - [{db_last_played_time}]]")
                else:
                    self.log.info(
                        f"Subclient with ID : [{row[0]}] is played back fully. Last Backup time - [{db_last_bkp_time}] "
                        f"Last Playback Time - [{db_last_played_time}]]")
                    resultset.remove(row)  # remove this subclient from monitoring
                    self.log.info(f"Removing this subclient id({row[0]}) from monitoring as it got completed playback")
            if all_done:
                self.log.info(f"Playback completed successfully as per CS DB.")
                break
            self.log.info(f"Going to sleep for {check_interval} mins")
            time.sleep(check_interval * 60)
        self.log.info(f"Going to resume CI job - {job_id}")
        job_obj.resume(wait_for_job_to_resume=True)
        self.log.info("Successfully resumed CI job after playback")

    def get_latest_job_id(self):
        """Returns the latest crawl job id for data source

                Args:
                    None

                Returns:

                    Str --  Job id

                Raises:

                    Exception:

                        if failed to get job id

                        if data source object is not initialized in class

        """
        if not self.is_app_ds_initialized:
            raise Exception("DataSource not initialized. Please check")
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for SDG server added")
        job_id = list(jobs.keys())[0]
        self.log.info(f"Online crawl job submitted : {job_id}")
        return job_id

    def validate_sensitive_count(self, client_name, path):
        """Validates total sensitive count files found with total files in source local path

                Args:

                    client_name     (str)       --  Name of commcell client

                    path            (list)      --  list of local folder path

                Returns:
                    None

                Raises:

                    Exception:

                        if validation fails for total sensitive document count

                        if data source object is not initialized in class

        """
        if not self.is_app_ds_initialized:
            raise Exception("DataSource not initialized. Please check")
        total_doc_in_src = 0
        machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell)
        for src_path in path:
            files = len(machine_obj.get_files_in_path(folder_path=src_path))
            self.log.info(f"File count for path ({src_path}) is {files}")
            total_doc_in_src = total_doc_in_src + files
        self.log.info(f"Total Sensitive document at source client  - {total_doc_in_src}")
        doc_in_dst = self.ds_obj.sensitive_files_count
        if total_doc_in_src != doc_in_dst:
            raise Exception(
                f"Sensitive Document count mismatched. Expected - {total_doc_in_src} but Actual : {doc_in_dst}")
        self.log.info("Sensitive Document count validation - Success")

    def do_sdg_cleanup(self, plan_name, inventory_name, project_name):
        """Deletes the Plan/Inventory/Project from commcell

            Args:

                plan_name       (str)       --  name of plan

                inventory_name  (str)       --  name of inventory

                project_name    (str)       --  name of SDG project

            Returns:

                 None

            Raises:

                Exception:

                    if failed to delete plan/inventory/project
        """
        self.log.info("Cleaning up all SDG entities in environment for this test case")
        plans_obj = self.commcell.plans
        invs_obj = self.commcell.activate.inventory_manager()
        sdg_obj = self.commcell.activate.sensitive_data_governance()
        project_exists = sdg_obj.has_project(project_name)
        if project_exists:
            sdg_obj.delete(project_name)
            self.log.info(f"Deleted the SDG Project - {project_name}")
        if plans_obj.has_plan(plan_name):
            self.log.info(f"Deleting plan as it exists already - {plan_name}")
            plans_obj.delete(plan_name)
        if invs_obj.has_inventory(inventory_name):
            self.log.info(f"Deleting inventory as it exists already - {inventory_name}")
            invs_obj.delete(inventory_name)

    def set_client_wrkload_region(self, client_name, region_name):
        """Sets client region on the commcell

            Args:

                client_name     (str)       --  Name of the client

                region_name     (str)       --  Region name to be set

            Returns:

                None

            Raises:

                Exception:

                    if failed to find region or client in commcell

                    if failed to associate client to region
        """
        if not self.commcell.clients.has_client(
                client_name) or not self.commcell.regions.has_region(region_name):
            raise Exception(
                "Either client name or region name is invalid. Please check")
        region_id = self.commcell.regions.all_regions[region_name]
        client_id = self.commcell.clients.all_clients[client_name]['id']
        self.log.info(
            f"Setting work load region with id [{region_id}] to client with id [{client_id}]")
        self.commcell.regions.set_region(
            entity_type=dynamic_constants.CLIENT_ENTITY_TYPE,
            entity_id=client_id,
            entity_region_type=dynamic_constants.WORKLOAD_ENTITY_TYPE,
            region_id=region_id)

    def download_validate_compliance_export(self, export_set_name, export_name,
                                            exported_files, export_type=ComplianceConstants.ExportTypes.CAB,
                                            app_type=ComplianceConstants.AppTypes.FILE_SYSTEM):
        """Method to download and validate the compliance search export

            Args:
                export_set_name (str)   -   Export Set Name
                export_name     (str)   -   Export Name
                exported_files  (list)  -   List of the search result items
                                            Example :
                                                [ {
                                                    "FileName": <name>,
                                                    "SizeKB": <size>...,
                                                    <name>: <key>
                                                },
                                                {
                                                    "FileName": <name>,
                                                    "SizeKB": <size>...,
                                                    <name>: <key>
                                                }... ]
                export_type     (str)   -   ComplianceConstants.ExportTypes Enum values
                                            Default: CAB

            Returns:
                None

        """
        self.log.info("Downloading and verifying the exported files now")
        export_set = self.commcell.export_sets.get(export_set_name)
        export = export_set.get(export_name)
        download_path = DOWNLOAD_FOLDER_PATH % export_name
        if not os.path.exists(download_path):
            self.log.info(f"Creating new Download folder")
            os.makedirs(download_path)
            self.log.info(f"{download_path} created successfully")
        downloaded_path = export.download_export(
            download_folder=download_path)
        extract_path = downloaded_path.split(".")[0]
        self.log.info(f"Export file downloaded successfully to {download_path}")
        if export_type == ComplianceConstants.ExportTypes.CAB:
            with zipfile.ZipFile(downloaded_path, 'r') as zip_ref:
                if not os.path.exists(extract_path):
                    self.log.info(f"Creating new Extract folder")
                    os.makedirs(extract_path)
                    self.log.info(f"{extract_path} created successfully")
                zip_ref.extractall(extract_path)
            self.log.info(f"ZIP data extracted to {extract_path} successfully")
            self.log.info("Now validating the files")
            for file in exported_files:

                if app_type == ComplianceConstants.AppTypes.TEAMS:
                    file_name = file['appSpecific']['teamsItem']['teamsItemName']
                else:
                    file_name = file[ComplianceConstants.SOLR_FIELD_FILE_NAME]

                if app_type == ComplianceConstants.AppTypes.SHAREPOINT:
                    keyIndex = file_name.rfind('.')
                    file_name = file_name[:keyIndex] + "_1.0" + file_name[keyIndex:]

                file_path = os.path.join(extract_path, file_name)
                if not os.path.exists(file_path):
                    self.log.error(f"File {file_name} does not exist in the download")
                    raise Exception(f"File not found in download : {file_name}")
                file_size = os.path.getsize(file_path)
                expected_file_size = int(file[ComplianceConstants.SOLR_FIELD_SIZE])
                self.log.info(f"File size obtained from FS is {file_size} Bytes")
                self.log.info(f"Expected File size from metadata provided : {expected_file_size}")
                if not app_type == ComplianceConstants.AppTypes.SHAREPOINT:
                    if file_size != expected_file_size:
                        self.log.info(f"File {file_name} size does not match with expected size")
                        raise Exception(f"Invalid file size found for {file_name}")
                    self.log.info(f"File size matched successfully for {file_name}")
        elif export_type == ComplianceConstants.ExportTypes.PST:
            from Application.Exchange.Parsers import pst_parser
            pst_file = pst_parser.parsepst(downloaded_path)
            if len(exported_files) != pst_file:
                self.log.info("Exported PST items count is not matching with the expected count")
                raise Exception(f"Invalid item count found Expected : {len(exported_files)}\n"
                                f" Actual : {pst_file}")
            self.log.info("Exported PST items count matches with the expected count")
            self.log.info(f"Expected items count : {len(exported_files)}")
            self.log.info(f"Actual items count : {pst_file}")

