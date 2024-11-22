# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

"""Main helper file for performing Sharepoint Server operations.

SharepointAutomation, SharepointHelper, SharepointInit, SharepointValidate are the only classes defined in this file.

SharepointAutomation: Helper class to initialize objects for SharepointHelper.

SharepointHelper: Helper class to perform Sharepoint server operations.

SharepointInit: Helper class to perform Sharepoint Server initialization operations.

SharepointValidate: Helper class to perform Sharepoint Server validation operations.


SharepointHelper:

    __init__()                  --  initializes Sharepoint Server helper object.

    sharepoint_setup()          --  This function creates the sharepoint setup environment by creating
    testcase directory, web application, site collections and subclient.

    create_subclient()          --  This function creates a Sharepoint subclient and assign necessary properties.

    sharepoint_backup()         --  This function initiates a backup job, waits for completion and validates backed up
    items.

    sharepoint_restore()        --  This function initiates a restore job, waits for completion and validates restored
    items.

SharepointInit:

    __init__()                  --  initializes Sharepoint Server helper object.

    create_web_application()    --  This function creates the Sharepoint server web application.

    delete_web_application()    --  This function deletes the Sharepoint server web application.

    create_sites()              --  This function creates a number of Sharepoint server site collections.

    create_list()               --  This function will create a list/library on a Sharepoint site.

    upload_file()               --  This function will upload a file to a document library on a given Sharepoint site.

SharepointValidate:

    __init__()                  --  initializes Sharepoint Server helper object.

    create_meta_data()          --  This function will create a validation file with meta data of the web application.

    check_file()                --  This function will verify a file exists within a library.

"""
import os
import time
import random
import threading
from datetime import datetime
from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from . import sharepointconstants
from .sharepointconstants import SharepointListTemplate

GLOBAL_LOCK = threading.Lock()


class SharepointAutomation:
    """Helper class to initialize Sharepoint Helper objects"""

    global GLOBAL_LOCK

    def __init__(self, _tcobject, _spclient, _sqlclient, _sqlinstance, _spfarmuser, _spfarmpass):
        """Initializes SharepointAutomation class objects

        Args:
            _spclient (str): Name of the client
            _sqlclient (str): Name of the SQL backend client
            _sqlinstance (str): Name of the Sharepoint Farm's SQL instance
            _spfarmuser (str): Sharepoint Farm admin user name
            _spfarmpass (str): Sharepoint Farm admin password
            _tcobject (:obj:'CVTestCase'): test case object

        """

        self.log = _tcobject.log
        self.spclient = _spclient
        self.sqlclient = _sqlclient
        self.sqlinstance = _sqlinstance
        self.spfarmuser = _spfarmuser
        self.spfarmpass = _spfarmpass
        self.tcobject = _tcobject
        self.csdb = database_helper.get_csdb()


class SharepointHelper:
    """Helper class to perform Sharepoint Server operations"""

    global GLOBAL_LOCK

    def __init__(self, _tcobject, _spclient, _sqlclient, _sqlinstance, _spfarmuser, _spfarmpass):
        """Initializes SharepointHelper object

            Args:
                _spclient (str): Name of the client
                _sqlclient (str): Name of the SQL backend client
                _sqlinstance (str): Name of the Sharepoint Farm's SQL instance
                _spfarmuser (str): Sharepoint Farm admin user name
                _spfarmpass (str): Sharepoint Farm admin password
                _tcobject (:obj:'CVTestCase'): test case object

        """
        self.spautomation = SharepointAutomation(_tcobject, _spclient, _sqlclient, _sqlinstance,
                                                 _spfarmuser, _spfarmpass)
        self.spinit = SharepointInit(self)
        self.spvalidate = SharepointValidate(self)

        self.log = self.spautomation.log
        self.csdb = self.spautomation.csdb
        self.tcobject = self.spautomation.tcobject

        self.port = None
        self.webapp = None
        self.app_pool_name = None
        self.site_title = None
        self.library_name = None
        self.dbname = None
        self.subclient = None
        self.subcontent = None
        self.storagepolicy = None
        self.tcdir = None
        self.tctime = None
        self.spsetup_list = None
        self.upload_file_list = None
        self.sharepoint_client_members = []
        self.sharepoint_client_primary_member = None

    def sharepoint_setup(self, storagepolicy, noof_apps=1, noof_sites=1):
        """This function creates the sharepoint setup environment by creating the web application,
        site collections and subclient.

        Args:
            storagepolicy (str): Name of storage policy to assign to subclient.

            noof_apps (int): Number of Web Applications to create.

            noof_sites (int): Number of Web Applications to create.

        """

        log = self.log
        spmachine = Machine(self.spautomation.spclient)

        try:
            tc_id = self.tcobject.id
            time1 = (datetime.now()).strftime("%H:%M:%S")
            logdir = self.spautomation.tcobject.log_dir
            subclientname = sharepointconstants.SUBCLIENT_NAME.format(tc_id, time1)
            site_title = None
            library_name = None

            # build temporary testcase logging directory and create it
            tcdir = os.path.normpath(os.path.join(logdir, tc_id + '-' + time1.replace(":", "")))
            spmachine.create_directory(tcdir)
            self.tcdir = tcdir

            # retrieve client host name from CSDB
            self.csdb.execute("SELECT net_hostname FROM APP_CLIENT where name = '{0}'"
                              .format(self.spautomation.spclient))
            cur = self.csdb.fetch_all_rows()
            client_hostname = cur[0][0]

            spsetup_list = []
            subcontent = []
            for i in range(1, noof_apps + 1):
                # generate a random port number for web application
                # TODO add extra code here to verify port isn't in use
                port = str(random.randint(1000, 65535))

                webapp = sharepointconstants.WEBAPP_URL.format(client_hostname, port)

                dbname = sharepointconstants.DB_NAME.format(port)
                app_pool_name = sharepointconstants.APP_POOL.format(port)

                # create web app
                self.spinit.create_web_application(
                    webapp,
                    app_pool_name,
                    self.spautomation.spfarmuser,
                    self.spautomation.spfarmpass,
                    dbname,
                    self.spautomation.sqlinstance
                )

                setup_dict = {
                    "application_pool": app_pool_name,
                    "port": port,
                    "web_application": webapp,
                    "content_database": dbname,
                    "database_server": self.spautomation.sqlinstance,
                    "credentials": {
                        "username": self.spautomation.spfarmuser,
                        "password": self.spautomation.spfarmpass
                    }
                }
                spsetup_list.append(setup_dict)
                self.spsetup_list = spsetup_list

                site_title = 'TC_' + str(tc_id) + '_' + time1.replace(":", "")
                site_url = "/".join([webapp[:-1], 'sites', site_title])
                library_name = 'DocLib' + str(tc_id) + '_' + time1

                # create site collection
                self.spinit.create_sites(site_url, self.spautomation.spfarmuser, "STS#0", site_title, noof_sites)

                # create document library
                self.spinit.create_list(site_url, library_name)

                # generate test data
                self.spautomation.tcobject.spmachine.generate_test_data(tcdir, files=10)

                # upload some files to the sharepoint site
                self.spinit.upload_file(site_url, library_name, tcdir)

                # subclient content
                subcontent.append(sharepointconstants.CONTENT_WEBAPP.format(app_pool_name)[4:])

            # create subclient
            log.info("*" * 10 + " Creating subclient [{0}] ".format(subclientname) + "*" * 10)
            try:
                self.create_subclient(subclientname, subcontent, storagepolicy)
            except Exception as excp:
                raise Exception("Failed to create subclient.\nError: '{0}'".format(excp))
            finally:
                self.subclient = self.tcobject.backupset.subclients.get(subclientname)

            self.subcontent = subcontent
            self.storagepolicy = storagepolicy
            self.tctime = time1
            self.site_title = site_title
            self.library_name = library_name

        except Exception as excp:
            raise Exception("Exception raised in sharepoint_setup()\nError: '{0}'".format(excp))

    def create_subclient(self, subclientname, subcontent, storagepolicy):
        """This function makes the necessary calls and assignments to create a Sharepoint
        subclient.

        Args:
            subclientname (str): Name of subclient to be created.

            subcontent (list): Content to add to subclient.

            storagepolicy (str): Storage policy to assign to subclient.

        """

        try:

            self.tcobject.backupset.subclients.add(subclientname, storagepolicy)
            subclient = self.tcobject.backupset.subclients.get(subclientname)
            subclient.content = subcontent

            request_json = sharepointconstants.SP_SUBCLIENT_PROP_DICT
            sqlclient_dict = {
                "ContentDatabaseSqlClient": {
                    "clientName": self.spautomation.sqlclient
                }
            }
            request_json.update(sqlclient_dict)

            subclient_prop = ["_sharepoint_subclient_prop", request_json]
            subclient.sharepoint_subclient_prop = subclient_prop

            request_json = sharepointconstants.SP_SUBCLIENT_STORAGE_DICT

            subclient.sharepoint_subclient_prop = ["_commonProperties['storageDevice']",
                                                   request_json]

        except Exception as excp:
            raise Exception("Exception raised in create_subclient()\nError: '{0}'".format(excp))

    def sharepoint_backup(self, backup_type):
        """This function initiates a backup job, waits for completion, and validates backed up
        items.

        Args:
            backup_type (str): Type of backup to run: Full, Differential.

        """

        log = self.log

        try:
            log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
            job = self.tcobject.subclient.backup(backup_type)
            log.info("Started {0} backup with Job ID: {1}".format(backup_type, str(job.job_id)))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        backup_type, job.delay_reason
                    )
                )
            if job.status == 'Completed':
                log.info("Successfully finished {0} backup job".format(backup_type))
            else:
                raise Exception("Backup job {0} did not complete successfully".format(job.job_id))

            # TODO Verify how to calculate number of objects for successful backup
            j_details = job.details
            # if int(j_details['jobDetail']['detailInfo']['numOfObjects']) != \
            #         len(self.tcobject.subclient.content) * 4:
            #     raise Exception("Failed to backup all content in subclient")
            log.info("Backup job Details: {0}".format(int(j_details['jobDetail']['detailInfo']['numOfObjects'])))
            log.info(
                "Content number of objects to expect restored: {0}".format(len(self.tcobject.subclient.content) * 4)
            )

        except Exception as excp:
            raise Exception("Exception raised in sharepoint_backup()\nError: '{0}'".format(excp))

    def sharepoint_restore(self, content):
        """This function initiates a restore job, waits for completion, and validates restored
        items.

        Args:
            content (list): Content to restore.

        """

        log = self.log

        try:
            job = self.tcobject.subclient.restore(content, self.spautomation.sqlclient, self.spsetup_list)

            log.info("*" * 10 + " Started Restore with Job ID: {0} ".format(job.job_id) + "*" * 10)
            if not job.wait_for_completion():
                raise Exception("Restore job failed for unexpected reasons. Check log files.")

            # getting exception when checking job details without a sleep
            time.sleep(10)
            j_details = job.details
            log.info("Restore job Details: {0}".format(int(j_details['jobDetail']['detailInfo']['numOfObjects'])))
            log.info("Content number of objects to expect restored: {0}".format(len(content) * 4))

            # TODO Verify how to calculate number of objects for successful
            # if not int(j_details['jobDetail']['detailInfo']['numOfObjects']) == len(content) * 4:
            #     raise Exception("Failed to restore all Sharepoint content.")

        except Exception as excp:
            raise Exception("Exception raised in sharepoint_restore()\nError: '{0}'".format(excp))


class SharepointInit:
    """Helper class to perform Sharepoint Server initialization operations"""

    global GLOBAL_LOCK

    def __init__(self, _sphelper):
        """Initializes SQLHelper object

        Args:
            _sphelper (:obj: 'SharepointHelper'): Instance of SharepointHelper

        """

        self.sphelper = _sphelper

    def create_web_application(self, webapp_url, webapp_name, spfarmuser, spfarmpass, database_name, database_server):
        """This function creates the Sharepoint server web application.

        Args:

            webapp_url (list): URL of the web application.

            webapp_name (str): Name of web application.

            spfarmuser (str): Sharepoint farm user to create web application.

            spfarmpass (str): Sharepoint farm user's password.

            database_name (str): Content database name to be associated to web application.

            database_server (str): SQL backend server to Sharepoint farm.


        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            webapp_dict = {
                "WebappURL": webapp_url,
                "WebappName": webapp_name,
                "AppPoolName": webapp_name,
                "AppPoolAcct": spfarmuser,
                "AppPoolPass": spfarmpass,
                "DatabaseName": database_name,
                "DatabaseServer": database_server
            }

            log.info("Creating Webapp [{0}] on [{1}]".format(
                webapp_url, self.sphelper.spautomation.spclient))

            output = spmachine.execute_script(sharepointconstants.CREATE_WEBAPP, webapp_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create web application")

        except Exception as excp:
            raise Exception("Exception raised in create_web_application()\nError: '{0}'".format(excp))

    def delete_web_application(self, webapp_url=None):
        """This function deletes the Sharepoint server web application.

        Args:

            webapp_url (str): URL of the web application.

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            if webapp_url is None:
                for sp_dict in self.sphelper.spsetup_list:
                    webapp_url = sp_dict["web_application"]
                    webapp_dict = {
                        "WebappURL": webapp_url,
                    }
                    log.info("Deleting Webapp [{0}] on [{1}]".format(
                        webapp_url, self.sphelper.spautomation.spclient))

                    output = spmachine.execute_script(
                        sharepointconstants.DELETE_WEBAPP, webapp_dict
                    )
                    if output.exit_code != 0:
                        log.error("Failed to delete web application [{0}]".format(webapp_url))
            else:
                webapp_dict = {
                    "WebappURL": webapp_url,
                }

                log.info("Deleting Webapp [{0}] on [{1}]".format(webapp_url, self.sphelper.spautomation.spclient))

                output = spmachine.execute_script(sharepointconstants.DELETE_WEBAPP, webapp_dict)
                if output.exit_code != 0:
                    raise Exception("Failed to delete web application")

        except Exception as excp:
            log.exception(
                "Exception raised in delete_web_application()\nError: '{0}'".format(excp)
            )
            raise

    def create_sites(self, site_url, spfarmuser, site_template, site_title, site_count):
        """This function creates a number of Sharepoint server site collections.

        Args:

            site_url (str): URL of web application.

            spfarmuser (str): Sharepoint farm user to be associated to site.

            site_template (str): Sharepoint site template to use for creating site.

            site_title (str): Title for Sharepoint site.

            site_count (int): Number of sites to create.

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            site_dict = {
                "SiteURL": site_url,
                "SiteOwner": spfarmuser,
                "SiteTemplate": site_template,
                "SiteTitle": site_title,
                "SiteCount": site_count
            }

            log.info("Creating Site Collection [{0}] on [{1}]"
                     .format(site_url, self.sphelper.spautomation.spclient))

            output = spmachine.execute_script(sharepointconstants.CREATE_SITES, site_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create site collection. {0}".format(output.formatted_output))

        except Exception as excp:
            raise Exception("Exception raised in create_sites()\nError: '{0}'".format(excp))

    def create_list(self, site_url, library_name, list_template=SharepointListTemplate.DOCLIBRARY):
        """This function will create a list/library on a Sharepoint site

        Args:
            site_url (str): URL of the site where to create list/library

            library_name (str): name of list/library to create

            list_template (sharepointconstants.SharepointListTemplate.value): type of list/library to create

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            list_dict = {
                "SiteURL": site_url,
                "LibraryName": library_name,
                "ListTemplate": list_template.value
            }

            log.info(r"Creating Library\List on Site [{0}] on [{1}]"
                     .format(site_url, self.sphelper.spautomation.spclient))

            output = spmachine.execute_script(sharepointconstants.CREATE_LIST, list_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create list or library. '{0}'".format(output.formatted_output))

        except Exception as excp:
            raise Exception("Exception raised in create_list()\nError: '{0}'".format(excp))

    def upload_file(self, site_url, library_name, file_dir, noof_files=None):
        """This function will upload a file to a document library on a given Sharepoint site

        Args:
            site_url (str): URL of the site where to upload the file.

            library_name (str): Name of library where to upload the file.

            file_dir (str): Path of file to upload to Sharepoint library.

            noof_files (int): Number of files to upload. Random number between 1-10 will be picked if not given.

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            file_list = []
            all_files = []
            self.sphelper.upload_file_list = []

            if noof_files is None:
                noof_files = random.randint(1, 11)

            for root, dirs, files in os.walk(file_dir):
                for file in files:
                    all_files.append(os.path.join(root, file))
            for i in range(1, noof_files + 1):
                while True:
                    file_path = random.choice(all_files)
                    if file_path in file_list:
                        continue
                    else:
                        file_list.append(file_path)
                        break

                file_dict = {
                    "SiteURL": site_url,
                    "LibraryName": library_name,
                    "FilePath": file_path
                }

                log.info("Uploading file [{0}] to library [{1}] on Site [{2}] on [{3}]"
                         .format(file_path, library_name, site_url, self.sphelper.spautomation.spclient))

                output = spmachine.execute_script(sharepointconstants.UPLOAD_FILE, file_dict)
                if output.exit_code != 0:
                    raise Exception("Failed to upload file to library. {0}".format(output.formatted_output))

                self.sphelper.upload_file_list.append(file_path)

        except Exception as excp:
            raise Exception("Exception raised in upload_file()\nError: '{0}'".format(excp))


class SharepointValidate:
    """Helper class to perform Sharepoint Server validation operations"""

    global GLOBAL_LOCK

    def __init__(self, _sphelper):
        """Initializes SQLHelper object

        Args:
            _sphelper (:obj: 'SharepointHelper'): Instance of SharepointHelper

        """

        self.sphelper = _sphelper
        self.csdb = self.sphelper.spautomation.csdb
        self.tcobject = self.sphelper.spautomation.tcobject

    def create_meta_data(self, file_name, webapp_url):
        """
        This function will create a validation file with meta data of the web application.

        Args:

            file_name (str): Name of file.

            webapp_url (str): URL of web application.

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            # TODO check backupset and use appropriate scripts for metadata. Should have 1 method to handle all cases.
            # TODO check if we can create 1 meta data for all web apps or libraries passed in here.

            if webapp_url is None:
                for sp_dict in self.sphelper.spsetup_list:
                    webapp_url = sp_dict["web_application"]
                    meta_dict = {
                        "MetaFile": file_name,
                        "WebappURL": webapp_url
                    }

                    log.info("Creating Meta Information for Webapp [{0}] on [{1}] in file [{2}]"
                             .format(webapp_url, self.sphelper.spautomation.spclient, file_name))

                    output = spmachine.execute_script(sharepointconstants.CREATE_META_DB, meta_dict)
                    if output.exit_code != 0:
                        raise Exception("Failed to create meta data file.")
            else:
                meta_dict = {
                    "MetaFile": file_name,
                    "WebappURL": webapp_url
                }

                log.info("Creating Meta Information for Webapp [{0}] on [{1}] in file [{2}]"
                         .format(webapp_url, self.sphelper.spautomation.spclient, file_name))

                output = spmachine.execute_script(sharepointconstants.CREATE_META_DB, meta_dict)
                if output.exit_code != 0:
                    raise Exception("Failed to create meta data file.")

        except Exception as excp:
            raise Exception("Exception raised in create_meta_data()\nError: '{0}'".format(excp))

    def check_file(self, webapp_url, library_name, site_title, file_name):
        """
        This function will verify a file exists within a library.

        Args:

            webapp_url (str): URL of web application.

            library_name (str): Name of library.

            site_title (str): Name of library.

            file_name (str): Name of file.

        Returns:

            bool: True for Success else False

        """

        log = self.sphelper.log
        spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            site_url = "/".join([webapp_url[:-1], 'sites', site_title])
            file_dict = {
                "SiteURL": site_url,
                "LibraryName": library_name,
                "FileName": file_name
            }

            log.info("Checking file [{0}] on Site [{1}] and Library [{2}] on [{3}]"
                     .format(file_name, site_url, library_name, self.sphelper.spautomation.spclient))

            output = spmachine.execute_script(sharepointconstants.CHECK_FILE, file_dict)
            if output.exit_code == 0:
                return True if "exists" in output.formatted_output else False

            raise Exception("Failed to validate file in library. {0}".format(output.formatted_output))

        except Exception as excp:
            raise Exception("Exception raised in check_file()\nError: '{0}'".format(excp))
    def get_sharepoint_members(self, sql_client, job_id):
        """This function gets all clients that were detected in the workflow
        Args:
            sql_client (str): Name of the SQL server client
            job_id (str): Job id of the workflow
        """
        import xml.etree.ElementTree as ET
        try:
            wfdb = database_helper.WFEngineDatabase(self.tcobject.commcell)
            wfdb.execute("SELECT execution from WF_Process where jobId = {0}".format(job_id))
            cur = wfdb.fetch_all_rows()
            xml_data = cur[0][0]
            tree = ET.fromstring(xml_data)
            client_host_names = tree.find('.//sharePointClientHostNamesStr')
            self.sphelper.sharepoint_client_members = client_host_names.text.split(', ')
            # append sql server and sharepoint pseudo client to the member server list
            self.sphelper.sharepoint_client_members.append(self.sphelper.spautomation.spclient)
            self.sphelper.sharepoint_client_members.append(sql_client)
            self.sphelper.sharepoint_client_members = [
                x.lower() for x in self.sphelper.sharepoint_client_members
            ]
            # get primary sharepoint server from pseudo client properties
            pm_server_query = """SELECT c.name
                FROM APP_Client c
                WHERE c.id = (
                    SELECT attrVal
                        FROM APP_ClientProp cp
                        WHERE cp.componentNameId = (SELECT id FROM APP_CLIENT WHERE name = '{0}')
                        AND cp.attrName = 'SharePoint Primary Member Server'
                    )""".format(self.sphelper.spautomation.spclient)
            self.csdb.execute(pm_server_query)
            cur = self.csdb.fetch_all_rows()
            self.sphelper.sharepoint_client_primary_member = cur[0][0]
        except Exception as excp:
            raise Exception("Exception raised in get_sharepoint_members()\nError: '{0}'".format(excp))
