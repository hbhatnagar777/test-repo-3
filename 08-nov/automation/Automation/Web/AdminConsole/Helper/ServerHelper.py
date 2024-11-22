# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from random import sample
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)

class ServerHelper:
    
    def __init__(self, admin_console, commcell=None, csdb=None):
        """
            Initializes the server helper module

            Args:

                admin_console   (object) --  AdminConsole class object

                commcell                 --  comcell object

                csdb                     --  csdb object
        """
        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.log = self.__admin_console.log
        self.__csdb = csdb
        self.__servers = Servers(admin_console)
        
    @PageService()
    def validate_listing_type_filter(self):
        """Method to validate server type filter"""
        self.log.info('Validating server type filter...')
        self.__navigator.navigate_to_servers()
        
        infrastructure_servers = "SELECT DISPLAYNAME FROM APP_CLIENT WHERE ID IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME LIKE 'ISINFRASTRUCTUREMACHINE' AND ATTRVAL = '1') AND ID <> 1"
        self.__get_data_for_validation(query= infrastructure_servers, type= 'Infrastructure', company_name= 'All')
        
        all_servers = """
        SELECT DISPLAYNAME FROM APP_CLIENT WHERE ID NOT IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME in ('INDEX SERVER TYPE', 'Exchange Pseudo Client')) AND ID <> 1
        AND 1 = 
        CASE 
            WHEN ID IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME = 'VIRTUAL MACHINE NAME')
                THEN
                CASE
                    WHEN ID IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME = 'LAST BACKUP JOBID') THEN 1
                    ELSE
                        CASE
                        WHEN ID IN (SELECT distinct clientid from simInstalledPackages) THEN 1 ELSE 0
                        END
                END
            ELSE 1
        END
        """
        self.__get_data_for_validation(query= all_servers, type= 'All', company_name= 'All')
        
    @PageService()
    def validate_listing_company_filter(self):
        """Method to validate company filter"""
        self.log.info('Validating company filter...')
        self.__navigator.navigate_to_servers()

        self.__csdb.execute('SELECT ID, HOSTNAME FROM UMDSPROVIDERS WHERE SERVICETYPE=5 AND ENABLED=1 AND FLAGS=0')
        company_details = self.__csdb.fetch_all_rows()
        if len(company_details) > 3: company_details = sample(company_details, 3) # pick any random 3 companies
        temp_dict = {company_name: id for id, company_name in company_details}
        
        for company_name, id in temp_dict.items(): # company filter validation for infrastructure servers
            company_infrastructure_servers = f"""
                SELECT c.displayName 
                FROM APP_Client c WITH (NOLOCK) 
                JOIN APP_ClientProp cp WITH (NOLOCK) ON c.id = cp.componentNameId 
                JOIN App_CompanyEntities ce WITH (NOLOCK) ON c.id = ce.entityId 
                WHERE cp.attrName LIKE 'IsInfrastructureMachine' AND cp.attrVal = '1' 
                AND c.id <> 1 AND ce.entityType = 3 AND ce.companyId = {id}
            """
            self.__get_data_for_validation(query= company_infrastructure_servers, type= 'Infrastructure', company_name= company_name)
        self.log.info('Company filter validation completed for infrastructure servers')

        for company_name, id in temp_dict.items(): # company filter validation for all servers
            company_servers = f"""
            SELECT DISPLAYNAME FROM APP_CLIENT WHERE ID NOT IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME in ('INDEX SERVER TYPE', 'Exchange Pseudo Client')) AND ID <> 1
            AND ID IN (SELECT ENTITYID FROM APP_COMPANYENTITIES WHERE ENTITYTYPE = 3 AND COMPANYID = {id})
            AND 1 = 
            CASE 
            WHEN ID IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME = 'VIRTUAL MACHINE NAME')
                THEN
                CASE
                    WHEN ID IN (SELECT COMPONENTNAMEID FROM APP_CLIENTPROP WHERE ATTRNAME = 'LAST BACKUP JOBID') THEN 1
                    ELSE
                        CASE
                        WHEN ID IN (SELECT distinct clientid from simInstalledPackages) THEN 1 ELSE 0
                        END
                END
            ELSE 1
        END
            """
            self.__get_data_for_validation(query= company_servers, type= 'All', company_name= company_name)
        self.log.info('Company filter validation completed for all servers')
        
    @PageService()
    def __get_data_for_validation(self, query, type= None, company_name=None):
        """Method to retrieve Servers data from UI and DB for validation purpose """
        self.__servers.reset_filters() # clear filters before fetching data
        self.__csdb.execute(query)
        db_data = {temp[0] for temp in self.__csdb.fetch_all_rows() if temp[0] != ''}
        ui_data = set(self.__servers.get_all_servers(server_type= type, company= company_name))
        if db_data != ui_data:
            self.log.info(f'DB Servers : {sorted(db_data)}')
            self.log.info(f'UI Servers : {sorted(ui_data)}')
            data_missing_from_ui = db_data - ui_data
            extra_entities_on_ui = ui_data - db_data
            raise CVWebAutomationException(f'Mismatch found between UI and DB\nData missing from UI : {data_missing_from_ui}\
                                           Extra entities on UI : {extra_entities_on_ui}')
        self.log.info('Validation completed')
    
    def view_logs(self, clientname):
        """ Method to select view logs on specified client

            Args:
                  client_name (str) --- Name of client on which view logs option to check.
            Returns:
                    viewlogspanel (object)  --- Returns viewlogs panel object

            Raises:
                Exception:

                    -- if fails to run view logs operation

        """
        self.__navigator.navigate_to_servers()
        viewlogspanel = self.__servers.view_logs(clientname) 
        return viewlogspanel       
    
    def validate_viewlogs(self,logfiles, viewlogspanel):
        """
        Method to validate logs on Viewlogs window.
        
        @args:
            logfiles   (list)  -- List files to validate on view logs window
            viewlogspanel (object)  -- Viewlogs panel object
            
            Returns:
                      None
            Raises:
                Exception:
                    -- if fails to validate view logs operation

        """
        for logfile in logfiles:
            viewlogspanel.searchlogs(logfile)
            viewlogspanel.view_logs_selectrow([logfile])
        viewlogspanel.click_submit()
        log_windows = self.__admin_console.browser.driver.window_handles
        if len(log_windows) !=len(logfiles)+1:
            raise Exception("Number of tabs opened for view logs are not equal to number of logs to view")         
        viewlogs = ViewLogs(self.__admin_console)
        logdict={} 
        for i in range(len(logfiles)):
            self.__admin_console.browser.driver.switch_to.window(log_windows[i+1])
            currenturl = self.__admin_console.browser.driver.current_url
            for value in logfiles:
                if str(currenturl).find(value)>=0:
                    logdict[value]=1
                    break                      
            logdata = viewlogs.get_log_data()
            if not (logdata):
                raise Exception("No logs found for log {%s}"%str(currenturl))
        if sorted(logdict.keys()) !=sorted(logfiles):
            raise Exception("Url dicts {%s} do not have the logfile names {%s}"%(str(logdict),str(logfiles)))   
        for window in  log_windows[1:]:
            self.__admin_console.browser.driver.switch_to.window(window)
            self.__admin_console.browser.driver.close()
        self.__admin_console.browser.driver.switch_to.window(log_windows[0])
        
    def viewlogs_add_filter_validate(self, columnname, filter_item, criteria, viewlogspanel):
        """
        method to add filter and validate view logs
        Arguments:
                filter_item   (str):      To filter servers of a particular type
                company_name  (str):      To filter servers of a particular company
                criteria      (enum):     enum value of Rfilter value
        Returns:
            None
        Raises:
            Exception:
                -- if fails to validate view logs operation

        """ 
        viewlogspanel.add_filter(columnname, filter_item, criteria)
        rowsdata = viewlogspanel.table_columndata(columnname)
        self.log.info('column data values are %s'%str(rowsdata))
        for row in rowsdata:
            if str(row).lower().find(filter_item.lower()) <0:
                raise Exception("Table data row {%s} contains other than filter specified item {%s}"%(str(row),filter_item))
        viewlogspanel.click_cancel()
