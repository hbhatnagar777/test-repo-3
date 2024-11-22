# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2021 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""File for performing ESX Virtual Machine Input Output (VM IO)

This file consists of a child class named: EsxVmIo, which can be used for
getting the screenshot of the ESX VM or sending keys to it

All methods are implemented from the base class VmIo

EsxVmIo
=======

    __init__()          --  Initializes instance of the EsxVmIo class

    take_screenshot()   --  Takes the screenshot of the VM

    send_text()         --  Sends a text to the console

    send_command()      --  Sends a command to the console

    send_keys()         --  Sends a list of keys to the console

    send_key()          --  Sends a key to the console

    send_left_arrow()   --  Sends a left arrow key to the console

    send_right_arrow()  --  Sends a right arrow key to the console

    send_up_arrow()     --  Sends a up arrow key to the console

    send_down_arrow()   --  Sends a down arrow key to the console


Attributes:
----------

    **_vm_obj**         --  The VM object

    **_console**        --  EsxConsole object to send keys

    **_screenshot**     --  EsxScreenshot object to capture screenshot

"""

from HyperScale.HyperScaleUtils.esx_screenshot import EsxScreenshot
from HyperScale.HyperScaleUtils.esx_console import EsxConsole
import atexit
import time
from pyVmomi import vim
from pyVim import connect
from HyperScale.HyperScaleUtils.vm_io import VmIo
from AutomationUtils.vmoperations import VmOperations


class EsxVmIo(VmIo):
    """Class for performing ESX Virtual Machine Input Output (VM IO)"""

    def __init__(self, vm_name, server_type, server_host_name, username, password, vm_manager):
        """Initializes instance of the EsxVmIo class.
        
        Args:
            vm_name             (str)   --  name of the VM

            server_type         (str)   --  server type

            server_host_name    (str)   --  server host name

            username            (str)   --  server username

            password            (str)   --  server password

        """
        super().__init__(vm_name, server_type, server_host_name, username, password, vm_manager)
        self.esx_management = vm_manager
        self._vm_obj = self.esx_management.get_vm_object(vm_name)
        if not self._vm_obj:
            raise Exception(f"{self.vm_name} is not defined")
        self._console = EsxConsole(self._vm_obj)
        self._screenshot = EsxScreenshot(server_host_name, username, password, self._vm_obj, self.esx_management)
    
    def take_screenshot(self, prefix=None, save_dir=None):
        """
        Takes the screenshot of the VM, saves it in save_dir
        with file name starting with prefix

        Args:
            prefix    (str) -- The prefix for image file name

            save_dir  (str) -- The directory to save image in

        Returns:
            file_path (str) -- The path of created image file

        """
        return self._screenshot.take_screenshot_via_task(prefix, save_dir)
    
    def send_text(self, text):
        """
        Sends a text to the console

        Args:
            text (str) -- A string to send
        """
        self._console.send_text(text)

    def send_command(self, command):
        """
        Sends a command to the console

        Args:
            command (str) -- A command to send
        """
        self._console.send_command(command)
    
    def send_keys(self, keys):
        """
        Sends a list of keys to the console

        Args:
            keys (list)  -- A list of keys to send like LEFT, RIGHT, UP, DOWN
                            for supported keys refer the dictionary:
                            EsxConsole._KEY_CODE

        """
        self._console.send_keys(keys)

    def send_key(self, key):
        """
        Sends a key to the console

        Args:
            key (str) -- A key to send like LEFT, RIGHT, UP, DOWN
                         for supported keys refer the dictionary:
                         EsxConsole._KEY_CODE

        """
        self._console.send_key(key)

    def send_left_arrow(self):
        """
        Sends a left arrow key to the console

        """
        self._console.send_left_arrow()

    def send_right_arrow(self):
        """
        Sends a right arrow key to the console

        """
        self._console.send_right_arrow()

    def send_up_arrow(self):
        """
        Sends a up arrow key to the console
        
        """
        self._console.send_up_arrow()

    def send_down_arrow(self):
        """
        Sends a down arrow key to the console
        
        """
        self._console.send_down_arrow()
