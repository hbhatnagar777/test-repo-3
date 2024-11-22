# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2021 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""File for performing ESX Virtual Machine screenshot capture

This file consists of a class named: EsxScreenshot, which 
handles taking the screenshot from an ESX VM

EsxScreenshot
=======

    __init__()              --  Initializes instance of the EsxScreenshot class

    take_screenshot()       --  Takes the screenshot of the VM

Attributes:
----------

    **server_host_name**    --  server host name

    **server_username**     --  server username

    **server_password**     --  server password

    **vm**                  --  The VM object

    **log**                 --  The logger object
    
    **save_dir**            --  The directory to save the screenshots in

"""
from datetime import datetime
import shutil
import requests
from requests.auth import HTTPBasicAuth
from AutomationUtils import logger
from pathlib import Path
import re
from pyVim.task import WaitForTask
from pyVmomi import vim

class EsxScreenshot:
    """
    This class handles taking the screenshot
    from an ESX VM

    Usage:
        vm_config = {
            'server_type': 'vCenter',
            'server_host_name': hostname,
            'username': username,
            'password': password
        }
        esx_management = VmOperations.create_vmoperations_object(
            vm_config)
        vm = esx_management.get_vm_object(vm_name)
        screenshot = EsxScreenshot(
            hostname, username, password, vm)

        image_path = screenshot.take_screenshot("install")
        
    """
    def __init__(self, hostname, username, password, vm, esx_management, save_dir="screen"):
        """
        Creates the class instance

        Args:
            hostname (str)            --  The hostname of the ESX server

            username (str)            --  The username for ESX login

            password (str)            --  The password for ESX login

            vm       (VirtualMachine) --  The managed object for a VM

            save_dir (str)            --  The path used to save the screenshots
                                          (Optional)

        """
        self.server_hostname = hostname
        self.server_username = username
        self.server_password = password
        self.vm = vm
        self.esx_management = esx_management
        self.log = logger.get_log()
        self.save_dir = save_dir
    
    def _get_valid_image_path(self, prefix, save_dir):
        if save_dir is None:
            save_dir = self.save_dir
        file_name = f'{self.vm.name}_{prefix}_{str(datetime.now()).replace(":",".")}.png'
        save_dir_path = Path(save_dir)
        save_dir_path.mkdir(parents=True, exist_ok=True)
        file_path = str(save_dir_path / file_name)
        return file_path
    
    def take_screenshot(self, prefix='img', save_dir=None):
        """
        Takes the screenshot of the VM, saves it in save_dir
        with file name starting with prefix

        Args:
            prefix    (str) - The prefix for image file name
            save_dir  (str) - The directory to save image in

        Returns:
            file_path (str) - The path of created image file
        """
        if save_dir is None:
            save_dir = self.save_dir

        vm_id = self.vm._moId
        hostname = self.server_hostname
        username = self.server_username
        password = self.server_password

        # The reason we are using 1920 x 1152 is because the aspect ratio is 5:3
        url = f"https://{hostname}/screen?id={vm_id}&w=1920&h=1152"
        auth = HTTPBasicAuth(username, password)
        response = requests.get(url, auth=auth, verify=False, stream=True)
        
        file_path = self._get_valid_image_path(prefix, save_dir)
        with open(file_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

        self.log.info(f"Captured screenshot for {vm_id} at {file_path}")

        return file_path


    def _find_datastore(self, content, datastore_name):
        datacenters_object_view = content.viewManager.CreateContainerView(
            content.rootFolder,
            [vim.Datacenter],
            True)

        # Find the datastore and datacenter we are using
        datacenter = None
        datastore = None
        for dc in datacenters_object_view.view:
            datastores_object_view = content.viewManager.CreateContainerView(
                dc,
                [vim.Datastore],
                True)
            for ds in datastores_object_view.view:
                if ds.info.name == datastore_name:
                    datacenter = dc
                    datastore = ds
                    break
        if not datacenter or not datastore:
            self.log.error("Could not find the datastore specified")
            raise SystemExit(-1)
        # Clean up the views now that we have what we need
        datastores_object_view.Destroy()
        datacenters_object_view.Destroy()
        return datacenter, datastore

    def _parse_datastore_path(self, datastorepath):
        m = re.match("\[(.*?)\] (.*)", datastorepath)
        if m is None:
            raise Exception(f"Path |{datastorepath}| does not contain datastore or filename")
        dsname = m.group(1)
        filename = m.group(2)
        return dsname, filename

    def _delete_file_from_datastore(self, datastore_path):
        # datastore_path = [HYDMMESX02-VMs] hsx-rw/hsx-rw-5.png
        datastore_name, filename = self._parse_datastore_path(datastore_path)
        service_instance = self.esx_management.si
        content = service_instance.RetrieveContent()
        dc, ds = self._find_datastore(content, datastore_name)
        try:
            task = content.fileManager.DeleteFile(datastore_path, dc)
            status = WaitForTask(task)
        except Exception as e:
            self.log.error(f"Exception while deleting file {e}")
            status = str(e)
        return True

    def take_screenshot_via_task(self, prefix='img', save_dir=None):
        task = self.vm.CreateScreenshot_Task()
        task_state = WaitForTask(task)
        # [HYDMMESX02-VMs] hsx-rw/hsx-rw-5.png
        screenshot_path = task.info.result
        self.log.info(f"screenshot saved at {screenshot_path}")
        datastore_name, file_name = self._parse_datastore_path(screenshot_path)

        service_instance = self.esx_management.si
        content = service_instance.RetrieveContent()
        session_manager = content.sessionManager
        dc, ds = self._find_datastore(content, datastore_name)

        if not file_name.startswith("/"):
            remote_file = "/" + file_name
        else:
            remote_file = file_name
        resource = f"/folder{remote_file}"
        params = {"dsName": ds.info.name,
                  "dcPath": dc.name}

        hostname = self.esx_management.esx_host
        http_url = "https://" + hostname + ":443" + resource
        client_cookie = service_instance._stub.cookie
        cookie_name = client_cookie.split("=", 1)[0]
        cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
        cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(
            ";", 1)[0].lstrip()
        cookie_text = " " + cookie_value + "; $" + cookie_path
        # Make a cookie
        cookie = dict()
        cookie[cookie_name] = cookie_text

        # https://hydmmesx02.gp.cv.commvault.com/folder/hsx-rw/hsx-rw-5.png?dcPath=ha-datacenter&dsName=HYDMMESX02-VMs&enc=std

        # Get the request headers set up
        headers = {'Content-Type': 'application/octet-stream'}
        file_path = self._get_valid_image_path(prefix, save_dir)
        with open(file_path, "wb") as f:
            self.log.info(f"Retrieving {screenshot_path} from {http_url}")
            response = requests.get(http_url,
                                   params=params,
                                   headers=headers,
                                   cookies=cookie,
                                   verify=False)
            f.write(response.content)
            # self.log.info(f"image has {len(response.content)//1024}KB")

        self._delete_file_from_datastore(screenshot_path)
        return file_path

  
