# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2021 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""File for performing Virtual Machine Input Output (VM IO)

This file consists of a base class named: VmIo, which can be used for
getting the screenshot of the VM or sending keys to it

All methods are abstract, the child class needs to implement those

VmIo
=======

    __new__()           --  Creates appropriate VmIo object depending on the type of VM server

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

    **SERVER_TYPE_ESX**     --  string identifying ESX VMs

    **SERVER_TYPE_HYPERV**  --  string identifying HyperV VMs

    **vm_name**             --  name of the VM

    **server_type**         --  server type

    **server_host_name**    --  server host name

    **username**            --  server username

    **password**            --  server password
"""

class VmIo:
    """Class for performing Virtual Machine Input Output (VM IO)"""

    SERVER_TYPE_ESX = "vCenter"
    SERVER_TYPE_HYPERV = "HyperV"

    def __new__(cls, vm_name, server_type, server_host_name, username, password, vm_manager, *args, **kwargs):
        """Returns the instance of one of the Subclasses EsxVmIo / HypervVmIo,
            based on the server_type
        
        Args:
            vm_name             (str)   --  name of the VM

            server_type         (str)   --  server type

            server_host_name    (str)   --  server host name

            username            (str)   --  server username

            password            (str)   --  server password
            
        """
        if server_type == VmIo.SERVER_TYPE_ESX:
            from .esx_vm_io import EsxVmIo
            return object.__new__(EsxVmIo)
        else:
            raise NotImplementedError(f"server_type {server_type} not yet implemented")
    
    def __init__(self, vm_name, server_type, server_host_name, username, password, vm_manager):
        """Initializes instance of the VmIo class.
        
        Args:
            vm_name             (str)   --  name of the VM

            server_type         (str)   --  server type

            server_host_name    (str)   --  server host name

            username            (str)   --  server username

            password            (str)   --  server password

        """
        self.vm_name = vm_name
        self.server_type = server_type
        self.server_host_name = server_host_name
        self.username = username
        self.password = password
        self.vm_manager = vm_manager

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
        raise NotImplementedError('Method not implemented by the child class')
    
    def send_text(self, text):
        """
        Sends a text to the console

        Args:
            text (str) -- A string to send
        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_command(self, command):
        """
        Sends a command to the console

        Args:
            command (str) -- A command to send
        """
        raise NotImplementedError('Method not implemented by the child class')
    
    def send_keys(self, keys):
        """
        Sends a list of keys to the console

        Args:
            keys (list)  -- A list of keys to send like LEFT, RIGHT, UP, DOWN
                            for supported keys refer the dictionary:
                            EsxConsole._KEY_CODE

        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_key(self, key):
        """
        Sends a key to the console

        Args:
            key (str) -- A key to send like LEFT, RIGHT, UP, DOWN
                         for supported keys refer the dictionary:
                         EsxConsole._KEY_CODE

        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_left_arrow(self):
        """
        Sends a left arrow key to the console

        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_right_arrow(self):
        """
        Sends a right arrow key to the console

        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_up_arrow(self):
        """
        Sends a up arrow key to the console
        
        """
        raise NotImplementedError('Method not implemented by the child class')

    def send_down_arrow(self):
        """
        Sends a down arrow key to the console
        
        """
        raise NotImplementedError('Method not implemented by the child class')
