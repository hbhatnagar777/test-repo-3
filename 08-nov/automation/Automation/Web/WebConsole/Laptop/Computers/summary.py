# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the Summary page on the WebConsole

Summary is the only class defined in this file

"""
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.Laptop.navigator import Navigator


class Summary:
    """
    Handles the operations on Summary page of My data application
    """
    def __init__(self, webconsole):
        """Initializes Summary class object"""
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._navigator = Navigator(self._webconsole)

    @WebAction()
    def _get_clients_list(self):
        """get all clients list"""
        _objects = self._driver.find_elements(By.XPATH, "//*[@class='vw-comp-name']/a")
        return [
            clients_object.text for clients_object in _objects
        ]

    @WebAction()
    def _get_clients_restore_links(self):
        """get all clients restore links"""
        xpath = "//*[@id='computerList']//a[@class='vw-btn vw-btn-primary']"
        restore_objects = self._driver.find_elements(By.XPATH, xpath)
        restore_links = []
        for each_object in restore_objects:
            restore_links.append(each_object.get_attribute("href"))
        return restore_links

    @WebAction()
    def _get_clients_backup_time_size(self):
        """get all clients backup and size info"""
        xpath = "//*[@id='computerList']//*[@class='col-md-4']"
        timesize_objects = self._driver.find_elements(By.XPATH, xpath)
        object_list = []
        for each_object in timesize_objects:
            object_list.append(each_object)
        return object_list

    @WebAction()
    def _get_clients_prop(self):
        """get all clients properis link"""
        xpath = "//*[@id='computerList']//a[@class='vw-spacing vw-btn vw-btn-default']"
        prop_objects = self._driver.find_elements(By.XPATH, xpath)
        client_prop = []
        for each_object in prop_objects:
            client_prop.append(each_object.get_attribute("href"))
        return client_prop

    @WebAction()
    def _goto_detailed_summary_page(self, link):
        """go to client details summary page"""
        self._driver.get(link)

    @WebAction()
    def _goto_browse_and_restore_page(self, link):
        """go to client browse and restore page"""
        self._driver.get(link)

    @PageService()
    def _get_clients_info_list(self):
        """Get all clients info present on My data page"""
        last_backup = []
        next_backup = []
        backup_size = []
        final_res = []
        time_size = self._get_clients_backup_time_size()
        client_list = self._get_clients_list()
        client_prop = self._get_clients_prop()
        restore_link = self._get_clients_restore_links()
        for j in time_size:
            if "Size" in str(j.text):
                backup_size.append(str(j.text).split("Size\n")[1])
            elif "Next Backup" in str(j.text):
                next_backup.append(str(j.text).split("Next Backup\n")[1])
            elif "Last Backup" in str(j.text):
                last_backup.append(str(j.text).split("Last Backup\n")[1])
        file_cat = zip(client_list, restore_link, last_backup, next_backup, backup_size, client_prop)
        for _x in file_cat:
            _dict = {'clientName': '', 'restoreLink': '', 'lastBackup': '', 'nextBackup': '', 'backupSize': '',
                     'clientProp': ''}
            _dict['clientName'] = _x[0]
            _dict['restoreLink'] = _x[1]
            _dict['lastBackup'] = _x[2]
            _dict['nextBackup'] = _x[3]
            _dict['backupSize'] = _x[4]
            _dict['clientProp'] = _x[5]

            final_res.append(_dict)
        return final_res

    @PageService()
    def get_clients_list(self):
        """Get all clients names present on My data page"""
        client_info_list = self._get_clients_info_list()
        client_list = []
        for i in client_info_list:
            client_list.append(i['clientName'])
        return client_list

    @PageService()
    def get_client_last_backup(self, client_name):
        """Get the client last backup info on My data page"""
        client_info_list = self._get_clients_info_list()
        for i in client_info_list:
            if client_name.lower() == i['clientName'].lower():
                return i['lastBackup']

    @PageService()
    def get_client_next_backup(self, client_name):
        """Get the client next backup info on My data page"""
        client_info_list = self._get_clients_info_list()
        for i in client_info_list:
            if client_name.lower() == i['clientName'].lower():
                return i['nextBackup']

    @PageService()
    def get_client_backup_size(self, client_name):
        """Get the client backup size info on My data page"""
        client_info_list = self._get_clients_info_list()
        for i in client_info_list:
            if client_name.lower() == i['clientName'].lower():
                return i['backupSize']

    @PageService()
    def get_client_prop(self, client_name, goto_link=False):
        """Get the client properties and link on My data page"""
        self._navigator.go_to_computers()
        client_info_list = self._get_clients_info_list()
        for i in client_info_list:
            if client_name.lower() == i['clientName'].lower():
                if goto_link is True:
                    link = i['clientProp']
                    self._goto_detailed_summary_page(link)
                else:
                    return i['clientProp']

    @PageService()
    def get_client_restore_link(self, client_name, goto_link=False):
        """Get the client restore link and info on My data page"""
        self._navigator.go_to_computers()
        client_info_list = self._get_clients_info_list()
        for i in client_info_list:
            if client_name.lower() == i['clientName'].lower():
                if goto_link is True:
                    link = i['restoreLink']
                    self._goto_browse_and_restore_page(link)
                else:
                    return i['restoreLink']
