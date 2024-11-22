# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file has the necessary functions to validate 
the current screen which console is showing

This file consists of a class named: ScreenMatcher, which 
determines the current screen shown by the VM

ScreenMatcher
=======

    __init__()              --  Initializes instance of the ScreenMatcher class

    _validate_screen()      --  Matches the screen with OCR output

    get_image_and_text()    --  Returns screenshot along with its text

    is_screen()             --  Checks if the VM is showing a particular screen

    wait_till_screen()      --  Waits for the VM to show a particular screen

Attributes:
----------

    **vm_io**               --  The VmIo instance

    **_SCREEN_CONTENT**     --  The screen key to predefined content dictionary
                                {
                                    "SCREEN_KEY": [
                                        'Content 1',
                                        'Content 2',
                                        ...
                                    ],
                                    ...
                                }

"""
from HyperScale.HyperScaleUtils.vm_io import VmIo
from HyperScale.HyperScaleUtils.screenshot_analyzer import ScreenshotAnalyzer
import time
from AutomationUtils import logger

class ScreenMatcher:
    """
    Given the text from the OCR output, this class
    has the necessary functions to validate the 
    current screen which console is showing
    """

    BOOT_SCREEN_PRESS_ENTER = 'boot_screen_press_enter'

    REIMAGE_SCREEN_INITIAL = "reimage_screen_initial"
    REIMAGE_SCREEN_PRESERVE = "reimage_screen_preserve"
    
    INSTALL_SCREEN_INITIAL = "install_screen_initial"
    INSTALL_SCREEN_INITIAL_HSX = "install_screen_initial_hsx"
    INSTALL_SCREEN_SYSTEM_DRIVE = "install_screen_system_drive"
    INSTALL_SCREEN_METADATA_DRIVE = "install_screen_metadata_drive"
    INSTALL_SCREEN_METADATA_DRIVE_HSX = "install_screen_metadata_drive_hsx"
    INSTALL_SCREEN_DATA_DRIVE = "install_screen_data_drive"
    INSTALL_SCREEN_SUMMARY = "install_screen_summary"
    INSTALL_SCREEN_SUMMARY_HSX = "install_screen_summary_hsx"
    INSTALL_SCREEN_FINISHED = "install_screen_finished"

    OS_LOGIN_SCREEN_HSX3 = "os_login_screen_hsx3"
    OS_LOGIN_SCREEN = "os_login_screen"
    LOGIN_SCREEN = "login_screen"

    SETUP_SCREEN_INITIAL = 'setup_screen_initial'
    SETUP_SCREEN_NETWORK = 'setup_screen_network'
    SETUP_SCREEN_CS_INFO = 'setup_screen_cs_info'
    SETUP_SCREEN_SUCCESS = 'setup_screen_success'

    DHCLIENT_SCREEN_SUCCESS = 'dhclient_screen_success'

    HSX_INSTALLER_SCREEN_VERSION_2212 = 'hsx_installer_screen_version_2212'
    HSX_INSTALLER_SCREEN_VERSION_3_2312 = 'hsx_installer_screen_version_3_2312'
    HSX_INSTALLER_SCREEN_VERSION_3_2408 = 'hsx_installer_screen_version_3_2408'
    HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION = 'hsx_installer_screen_network_configuration'
    HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION_SUMMARY = 'hsx_installer_screen_network_configuration_summary'
    
    SETUP_SCREEN_ROOT_PASSWORD = 'setup_screen_root_password'
    SETUP_SCREEN_COMMSERVE_FQDN = 'setup_screen_commserve_fqdn'
    SETUP_SCREEN_COMMSERVE_INFO = 'setup_screen_commserve_info'
    SETUP_SCREEN_REGISTRATION_SUCCESS = 'setup_screen_registration_success'

    _SCREEN_CONTENT = {
        INSTALL_SCREEN_INITIAL: [
            'A control node contains SSD drives to be configured for hosting partitioned DDB store and index cache. A data node contains SSD drives to be configured for hosting index cache.',
            'Multi node installation will setup hyperscale configuration on all the given cluster nodes.',
        ],
        INSTALL_SCREEN_INITIAL_HSX: [
            'Configure this node for setting up Storage Pool drives and hosting partitioned DDB store and Index Cache.'
            # 'Multi node installation will setup hyperscale configuration on all the given cluster nodes.',
            # Removed to accomodate hsx3
        ],
        INSTALL_SCREEN_SYSTEM_DRIVE: [
            'System drives are used for Operating System installation. Please select which of the following drives should be used as System drives.'
        ],
        INSTALL_SCREEN_METADATA_DRIVE: [
            'Metadata drives are used for storing Deduplication Database and Index Cache. Please select which of the following drives should be used as Metadata drives.'
        ],
        INSTALL_SCREEN_METADATA_DRIVE_HSX: [
            'Metadata drives are used for storing Deduplication Database, Index Cache and Hedvig Metadata.',
            'Please select which of the follwing drives should be used as Metadata drives.'
        ],
        INSTALL_SCREEN_DATA_DRIVE: [
            'Data drives are used for configuring StoragePool disk library. Please select which of the following drives should be used as Data drives.'
        ],
        INSTALL_SCREEN_SUMMARY: [
            'Control node [with 4 drives]',
            '4 drives'
        ],
        INSTALL_SCREEN_SUMMARY_HSX: [
            'Control node [with 9 drives]',
            '9 drives' # added since this screen hsx may have conflict with hs
        ],
        INSTALL_SCREEN_FINISHED: [
            'localhost: Installation completed successfully.'
        ],
        BOOT_SCREEN_PRESS_ENTER: [
            'Commvault HyperScale Install will start in 30 seconds.'
        ],
        REIMAGE_SCREEN_INITIAL: [
            "Hyperscale Configuration Detected",
            "Hyperscale configuration detected on this machine. Existing Hyperscale setup details are as follows"
        ],
        REIMAGE_SCREEN_PRESERVE: [
            # "Preserve Data",
            "Please select whether the drives containing valid Commvault data needs to be reinitialized."
        ],
        OS_LOGIN_SCREEN_HSX3:[
            ": Rocky Linux 8.9 (Green Obsidian)"
        ],
        OS_LOGIN_SCREEN:[
            "Red Hat Enterprise Linux"
        ],
        LOGIN_SCREEN: [
            "This server is configured with optimal settings to function as a Commvault HyperScale node.",
            "Please do not modify any settings on this server."
        ],
        SETUP_SCREEN_INITIAL: [
            "Please set the hostname and root user password of the server"
        ],
        SETUP_SCREEN_NETWORK: [
            "Please select setup button to get to network configuration menu"
        ],
        SETUP_SCREEN_CS_INFO: [
            "The appliance will be registered with the CommServe",
            "Please provide the following information"
        ],
        SETUP_SCREEN_SUCCESS: [
            "Commvault HyperScale has been configured successfully!"
        ],
        DHCLIENT_SCREEN_SUCCESS: [
            "is already running - exiting."
        ],
        HSX_INSTALLER_SCREEN_VERSION_2212: [
            "COMMVAULT @) Version: 2.2212 HyperScale X Version 2.2212"
        ],
        HSX_INSTALLER_SCREEN_VERSION_3_2312: [
            "COMMVAULT @) Version: 3.2312 HyperScale X Version: 3.2312"
        ],
        HSX_INSTALLER_SCREEN_VERSION_3_2408: [
            "COMMVAULT @) Version: 3.2408 HyperScale X Version: 3.2408"
        ],
        HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION: [
            "Network Configuration",
            "Please configure one CommServe Registration network and one Storage Pool network",
            "Configure interface Create bond"
        ],
        HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION_SUMMARY: [
            "Network Configuration Summary",
            "Review network configuration summary",
            "To see details of an interface, hover on its name",
        ],
        SETUP_SCREEN_ROOT_PASSWORD: [
            "Please provide password for root user (password should be same as other nodes in cluster) :"
        ],
        SETUP_SCREEN_COMMSERVE_FQDN:  [
            "Please provide Commserve FQDN :"
        ],
        SETUP_SCREEN_COMMSERVE_INFO: [
            "Please provide Commserve user name for registration :"
            "Enter Commserve password :"
        ],
        SETUP_SCREEN_REGISTRATION_SUCCESS: [
            "Successfully registered MediaAgent"
        ]
    }
    
    def __init__(self, vm_io: VmIo):
        """
        Creates the class instance

        Args:
            vm_io (object)            --  The instance of VmIo class

        """
        self.vm_io = vm_io
        self.__log = logger.get_log()

    def _validate_screen(self, content, screen_key):
        """
        Matches the screen with OCR output

        Args:
            content     (str)   --  The OCR output

            screen_key  (str)   -- The screen key

        Returns:
            okay        (bool)  -- Whether the content matched the screen

        """
        okay = ScreenshotAnalyzer.match_text(content, ScreenMatcher._SCREEN_CONTENT[screen_key])
        return okay

    def get_image_and_text(self, prefix='screen', save_dir='screen'):
        """
        Returns screenshot along with its text

        Args:
            prefix      (str)   --  The prefix for the image file name
                                    (Optional, default: 'screen')
            
            save_dir    (str)   --  The directory to save the image file
                                    (Optional, default: 'screen')

        Returns:
            image,text  (tuple) --  The screenshot and its text

        """
        image_file_path = self.vm_io.take_screenshot(prefix, save_dir)
        text = ScreenshotAnalyzer.get_text(image_file_path)

        return image_file_path, text

    def is_screen(self, screen_key):
        """
        Checks if the VM is showing a particular screen

        Args:
            screen_key  (str)   -- The screen key

        Returns:
            result      (bool)  -- Whether the VM is showing a particular screen

        Note:
            Use wait_till_screen if need to wait for screen to change
        """
        image_file, content = self.get_image_and_text(prefix=screen_key)
        return self._validate_screen(content, screen_key)

    def wait_till_screen(self, screen_key, attempts=10, interval=2):
        """
        Waits for the VM to show a particular screen

        Args:
            screen_key  (str)   --  The screen key

            attempts    (int)   --  The number of screen validations to perform
                                    (Optional, None - infinite attempts, Default: 10)

            interval    (int)   --  The time in seconds to wait between attempts
                                    (Optional, default: 2 seconds)

        Returns:
            result      (bool)  -- Whether the VM showed the screen within the given attempts

        """
        tries = 0
        while True:
            tries += 1
            self.__log.info(f"Waiting for {screen_key}")
            image_file, content = self.get_image_and_text(prefix=screen_key)
            if self._validate_screen(content, screen_key):
                self.__log.info(f"{screen_key} validated by {image_file}")
                return True
            if attempts is not None and tries >= attempts:
                self.__log.info(f"{screen_key} failed to validate after {tries} attempts")
                return False
            self.__log.info(f"{screen_key} waiting for validation at {image_file}. Attempts: {tries}")
            time.sleep(interval)
    
    def wait_till_either_screen(self, screen_keys, attempts=10, interval=2):
        """
        Waits for the VM to show any screen from a list

        Args:
            screen_keys  (list)   --  The screen keys

            attempts    (int)   --  The number of screen validations to perform
                                    (Optional, None - infinite attempts, Default: 10)

            interval    (int)   --  The time in seconds to wait between attempts
                                    (Optional, default: 2 seconds)

        Returns:
            result      (bool)  -- Whether the VM showed the screen within the given attempts

        """
        tries = 0
        prefix = "__".join(screen_keys)
        while True:
            tries += 1
            image_file, content = self.get_image_and_text(prefix=prefix)
            for screen_key in screen_keys:
                self.__log.info(f"Checking {screen_key}")
                if self._validate_screen(content, screen_key):
                    self.__log.info(f"{screen_key} validated by {image_file}")
                    return screen_key
            if attempts is not None and tries >= attempts:
                self.__log.info(f"{prefix} failed to validate after {tries} attempts")
                return False
            self.__log.info(f"{prefix} waiting for validation at {image_file}. Attempts: {tries}")
            time.sleep(interval)
        
