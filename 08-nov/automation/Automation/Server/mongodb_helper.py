# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing MongoDB related operations

MongoDBHelper:

    __init__()                           --  initializing the MongoDB helper class

    _check_if_mongoDB_is_installed       --  check if MongoDB and webserver are installed on the client

    validate_service_status              --  check if MongoDB service is running or not

    validate_installed_mongodb_version   --  get the installed MongoDB version on the client

    validate_cc_login                    --  validate command center login

    validate_check_readiness             --  validate MongoDB check readiness of the mongoDB client

"""
from cvpysdk.commcell import Commcell
from AutomationUtils import logger
from AutomationUtils import machine
from AutomationUtils import database_helper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Database.MongoDBUtils import mongodbhelper
import time, re


class MongoDBHelper:
    """Helper class for performing MongoDB related operations"""

    def __init__(self, commcell: Commcell, machine_name: str, password=None)->None:
        """Method to initialize MongoDB helper object"""
        self.commcell = commcell
        self.log = logger.get_log()
        self.machine = machine.Machine(machine_name=machine_name, commcell_object=self.commcell)
        self.client_os_info = self.commcell.clients.get(machine_name).os_info.lower()
        if password:
            self.mongodb = mongodbhelper.MongoDBHelper(self.commcell, db_user="mongoadmincv",db_password=password,
                                                       masterhostname=machine_name)

    @staticmethod
    def get_default_webserver(csdb: database_helper.CommServDatabase)->tuple:
        """Method to get the default webserver name and hostname"""
        query = "SELECT CL.name, CL.net_hostname FROM GXGlobalParam P WITH(NOLOCK) JOIN APP_Client CL WITH(NOLOCK) ON P.value = CL.id WHERE P.name LIKE 'Web Search Server for Super Search'"
        csdb.execute(query)
        return csdb.fetch_all_rows()[0] # (webserver_name, webserver_hostname)

    @property
    def connection(self):
        """
        returns MongoDB connection
        """
        if self.mongodb:
            return self.mongodb.connection

    def __check_if_mongodb_is_installed(self):
        """Method to check if MongoDB and webserver are installed on the client"""
        try:
            if "windows" in self.client_os_info:
                self.machine.verify_installed_packages(["252", "952"])
                self.log.info("MongoDB and Webserver package are installed")
                return True
            else:
                self.machine.verify_installed_packages(["1174", "1604"])
                self.log.info("MongoDB and Webserver package are installed")
                return True
        except Exception:
            raise Exception("Required packages are not installed on the client")

    def __restart_webservice(self):
        """method to restart webservice"""
        if self.__check_if_mongodb_is_installed():
            if "windows" in self.client_os_info:
                try:
                    self.log.info("Restarting iis on windows machine")
                    self.commcell.commserv_client.execute_command("iisreset")
                    return True
                except Exception as e:
                    raise Exception(f"Failed to restart iis. Error : {e}")
            else:
                try:
                    self.log.info("Restarting WebServerCore on Unix machine")
                    self.commcell.commserv_client.execute_command("commvault restart -s WebServerCore")
                    return True
                except Exception as e:
                    raise Exception(f"Failed to restart WebServerCore. Error : {e}")

    def validate_service_status(self)->bool:
        """Method to check if MongoDB service is running or not"""
        if self.__check_if_mongodb_is_installed():
            self.log.info("checking the OS")
            if "windows" in self.client_os_info:
                self.log.info("MongoDB is installed on a windows client. Checking MongoDB service status")
                running_services = self.machine.execute_command('Get-Service | Where Status -eq "Running" | select Name')
                if "GxMONGO(Instance001)" in [service[0] for service in running_services.formatted_output]:
                    self.log.info("MongoDB service is running")
                    return True
                else:
                    raise Exception("MongoDB service is down")
            else:
                self.log.info("MongoDB is installed on a unix client. Checking MongoDB service status")
                if self.machine.execute_command('ps -A | grep MongoDB').formatted_output:
                    self.log.info("MongoDB service is running")
                    return True
                else:
                    raise Exception("MongoDB service is down")

    def validate_installed_mongodb_version(self) -> bool:
        """Method to get the installed MongoDB version on the client"""
        if self.__check_if_mongodb_is_installed():
            if "windows" in self.client_os_info:
                os_version_match = re.search(r'(\d{4})', self.client_os_info)
                if os_version_match:
                    os_version = int(os_version_match.group())
                    sMongoVersionExpected = "7.0" if os_version >= 2019 else "6.0"
                else:
                    raise Exception("Failed to fetch os version")
            else:
                sMongoVersionExpected = "7.0"

            self.log.info("checking the installed mongoDB version")
            sMongoVersionInstalled = self.machine.get_registry_value("Database","sMongoVersion")
            if sMongoVersionInstalled == sMongoVersionExpected:
                self.log.info(f"MongoDB version installed is {sMongoVersionExpected}")
                return True
            else:
                raise Exception(f"Incorrect MongoDB version. Installed MongoDB version{sMongoVersionInstalled}, "
                                f"Expected Mongo Version is {sMongoVersionExpected}")

    def validate_cc_login(self, username:str, password:str) -> bool:
        """Method to validate command center login"""
        browser = BrowserFactory().create_browser_object()
        try:
            browser.open()
            adminconsole_obj = AdminConsole(browser, self.commcell.commserv_hostname)
            adminconsole_obj.login(username,password)
            return True
        except Exception as e:
            self.log.error(e)
            raise Exception("Login failed")
        finally:
            browser.close()

    def validate_check_readiness(self) -> bool:
        """Method to validate MongoDB check readiness"""
        if self.__check_if_mongodb_is_installed():
            if self.commcell.commserv_client.is_mongodb_ready:
                self.log.info("MongoDB Check readiness Passed")
                return True
            else:
                raise Exception(self.commcell.commserv_client.readiness_details.get_mongodb_failure_reason())

    def validate_entity_cache(self) -> bool:
        """
        method to validate Commcell entity cache by dropping all the collections under CommCellEntityCache DB ,
        and restart iis
        """
        if self.mongodb:
            try:
                self.log.info("deleting all the collections from the DB CommcellEntityCache")
                col_names_1 = self.mongodb.get_collection_list('CommcellEntityCache')
                self.mongodb.drop_collections('CommcellEntityCache',col_names_1)

                self.log.info("restarting Webservice")
                self.__restart_webservice()
                time.sleep(60)

                self.log.info("validating that the collections are populated back")
                col_names_2 = self.mongodb.get_collection_list('CommcellEntityCache')
                missing_col = [col for col in col_names_2 if col not in col_names_1]
                if not missing_col:
                    return True
                else:
                    raise Exception(f'Validation failed.Following collections are not populated: {missing_col}')
            except Exception as e:
                raise Exception(f"Failed to validate Entity cache. Error : {e}")

