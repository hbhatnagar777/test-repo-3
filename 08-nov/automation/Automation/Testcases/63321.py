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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

"""
"63321":{
        "AgentName":"",
        "ClientName":"",
        "BackupsetName":"",
        "PlanName":"",
        "StoragePolicyName":"",
        "isDatasetPresent" : "True", -> if dataset is already present 
        "TestPath": ""
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsAgent, FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from FileSystem.FSUtils.fshelper import FSHelper
from Web.Common.page_object import handle_testcase_exception, TestStep
from time import sleep

#TODO
# Add support for metallic if metallic test case is run dont query 
#Check if logs are printed for it
#Add support for different scans

class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.fshelper = None
        self.subclient_name = None
        self.num_of_dirs = None
        self.num_of_files = None
        self.file_size = None
        self.mssql = None
        self.tcinputs = {
            "TestPath": None,
            "ClientName": None,
            "BackupsetName": None,
            "PlanName": None
        }

    @test_step
    def login_to_commandcenter(self):
        """Login to the commandcenter"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                    password=self.inputJSONnode['commcell']['commcellPassword'])
        self.fsAgent = FsAgent(self.admin_console)
        self.fsSubclient = FsSubclient(self.admin_console)
        self.fsSubclientDetails = FsSubclientDetails(self.admin_console)
        self.fileServers = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.jobDetails = JobDetails(self.admin_console)
        self.jobs = Jobs(self.admin_console)


    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """
        
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.subclient_name = "Test_" + str(self.id)
        self.num_of_files = int(self.tcinputs.get("num_of_files",1500000))
        self.num_of_dirs = int(self.tcinputs.get("num_of_dirs", 30000))
        self.file_size = int(self.tcinputs.get("file_size",0))
        self.login_to_commandcenter()

    # This method is not executed as we need to get creds to login to csdb
    # Leaving the method here incase we find a better way to login to csdb 
    # At present to get creds we have to pass passowrd from answer file   
    def set_job_update_time(self,update_time:int):
        '''Sets the job update time on cs by updating the table App_iDAType
            Args 
                update_time(int) : Update time in second. Should be multiple of 60
        '''
        #Query to update value in DB
        query = f"Update APP_iDAType\
                SET updateIntervalSec = {update_time}\
                where name = '{self.client_machine.os_info} File System'"
        self.mssql.execute(query)

    
    def navigate_to_job_details_for_jobid(self,job_id):
        """Navigates to jon details page for the particular job id"""
        self.navigator.navigate_to_jobs()
        self.jobs.view_job_details(job_id=job_id, details=False)

    @test_step
    def is_value_updated_in_ui(self, job_id:int,prev_files_count:int,prev_folder_count:int):
        '''Gets the value of files and folder shown in job details page
            Args 
                job_id(int) : Job id for which to read the files and folder from job details
                prev_files_count(int) : Count of previous files seen prior to executing the job
                prev_folder_count(int) : Count of previous folders seen prior to executing the job
            Returns
                boolean : If value is updated or not
                msg : msg depeding on if value is updated or not
                current_files_count : files count seen on UI
                current_folders_count : folders count seen on UI

        '''
        self.admin_console.refresh_page()
        current_folders_count = 0
        current_files_count = 0
        item_status = self.jobDetails.get_item_status()
        self.log.info(item_status)

        if len(item_status)>1:
            scanned_objects = item_status['Scanned objects']
            get_files_folders = scanned_objects.split(" ")
            current_files_count, current_folders_count = map(int, [get_files_folders[2], get_files_folders[0]])
            return self.compare_value(prev_files_count,prev_folder_count,current_files_count,current_folders_count,"DB")
        else :
            # Value is not updated in UI. This may occur when the scan has started but hasn't met the threshold for time update query #TODO
            # Don't need to fail the testcase here as this is e
            msg = "VALUE NOT LOGGED IN UI. PLEASE CHECK THE JOB UPDATE TIME"
            self.log.info(msg)
            return [False,msg,current_files_count,current_folders_count]

    @test_step
    def compare_value(self,prev_files_count,prev_folder_count,current_files_count,current_folders_count,location):
        '''Helper function to compare values'''
        if current_files_count == prev_files_count and current_folders_count == prev_folder_count :
            #files and folder values has not been updated 
            msg = f"FILES AND FOLDER VALUE HAS NOT BEEN UPDATED IN {location}"
            self.log.info(msg)
            self.log.info("PREVIOUS FILES, FOLDER COUNT : %s,%s",prev_files_count,prev_folder_count)
            self.log.info("CURRENT FILES, FOLDER COUNT : %s,%s",current_files_count,current_folders_count)
            return [False,msg,current_files_count,current_folders_count]
        else :
            msg = f"FILES AND FOLDER IS UPDATED IN {location}"
            self.log.info(msg)
            self.log.info("PREVIOUS FILES, FOLDER COUNT : %s,%s",prev_files_count,prev_folder_count)
            self.log.info("CURRENT FILES, FOLDER COUNT : %s,%s",current_files_count,current_folders_count)
            return [True,"",current_files_count,current_folders_count]

    @test_step
    def is_value_updated_in_db(self, job_id,prev_files_count = 0,prev_folder_count = 0):
        '''Gets the value of files and folder in DB
            Args 
                job_id(int) : Job id for which to read the files and folder from job details
                prev_files_count(int) : Count of previous files seen prior to executing the job
                prev_folder_count(int) : Count of previous folders seen prior to executing the job
             Returns
                boolean : If value is updated or not
                msg : msg depeding on if value is updated or not
                current_files_count : files count seen on DB
                current_folders_count : folders count seen on DB

        '''
        current_folders_count = 0
        current_files_count = 0
        query = f"select * from JMMisc WITH (NOLOCK) where itemType = 93 and jobId={job_id}"
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row()
        if len(query_result)>1:
            # query_result headers : id	jobId	selfRefId	itemType	attribute	intData	data	commcellId
            # query_result format : ['19563', '7135', '0', '93', '0', '0', '17,18', '2']
            # 18 folders 17 files
            # We require only data hence query_result[6]
            current_files_count, current_folders_count = map(int, query_result[6].split(','))
            return self.compare_value(prev_files_count,prev_folder_count,current_files_count,current_folders_count,"DB")
        else : 
            # Value is not updated in DB. This may occur when the scan has started but hasn't met the threshold for time update query #TODO
            # Don't need to fail the testcase here as this is e
            msg = "VALUE NOT LOGGED IN DB. PLEASE CHECK THE JOB UPDATE TIME"
            self.log.info(msg)
            return [False,msg,current_files_count,current_folders_count]  

    def run(self):
        """Run function for test case execution"""
        try :
            if self.tcinputs.get("isDatasetPresent") is None:
                #As dataset required for the test is huge its better to have one already confiugred
                self.log.info("Creating data under %s", self.tcinputs["TestPath"])
                self.client_machine.generate_test_data(file_path=self.tcinputs["TestPath"], dirs=self.num_of_dirs,
                                                    files=self.num_of_files, file_size=self.file_size)
            else :
                self.log.info("Not creating dataset as isDatasetPresent is passed from TC INPUTS")
            
            #after creation get the count from api - powersheel, get count  - TODO
            self.log.info("Getting count from machine")
            machine_folder_count = self.client_machine.number_of_items_in_folder(self.tcinputs["TestPath"], include_only="folders",recursive=True)
            machine_files_count = self.client_machine.number_of_items_in_folder(self.tcinputs["TestPath"],include_only="files",recursive=True)

            # Creating subclient from backend as its faster    
            self.fshelper.create_subclient(name=self.subclient_name,
                                        storage_policy=self.tcinputs["StoragePolicyName"],
                                        content=[self.tcinputs["TestPath"]],
                                        allow_multiple_readers=True)
            job = self.fshelper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            job_id = job.job_id
            self.navigate_to_job_details_for_jobid(job_id)
            previous_files_count_db = previous_folders_count_db = 0
            previous_files_count_ui = previous_folders_count_ui = 0

            while (job.phase).upper() == "SCAN":
                #Sleeping for 300 sec as the status is update every 5 mins by default
                self.log.info("Going to sleep...")
                sleep(300)
                self.log.info("Waking up from sleep...")
                result_db, msg_db,previous_files_count_db,previous_folders_count_db  = self.is_value_updated_in_db(job_id,previous_files_count_db,previous_folders_count_db)
                result_ui, msg_ui,previous_files_count_ui,previous_folders_count_ui  = self.is_value_updated_in_ui(job_id,previous_files_count_ui,previous_folders_count_ui)

                # result_log = self.is_log_line_present() # reg key
                if result_db == False:
                    raise Exception(msg_db)
                if result_ui == False:
                    raise Exception(msg_ui)
            
            #ignoring first two parameters as we just need the count
            _, _,current_files_count_ui,current_folders_count_ui  = self.is_value_updated_in_ui(job_id,previous_files_count_ui,previous_folders_count_ui)
            _, _,current_files_count_db,current_folders_count_db  = self.is_value_updated_in_ui(job_id,previous_files_count_ui,previous_folders_count_ui)
            
            if current_files_count_ui != current_files_count_db or current_folders_count_db != current_folders_count_ui:
                msg = "Post Scan count in DB dont match with count in UI"
                raise Exception(msg)
            if current_folders_count_db != machine_folder_count or current_files_count_db != machine_files_count:
                msg = "Folder count returned from machine does not match count returned from UI"
                raise Exception(msg)
            self.log.info("Values returned from system match with UI and DB")

        except Exception as exception_msg:
            handle_testcase_exception(self,exception_msg)  

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

