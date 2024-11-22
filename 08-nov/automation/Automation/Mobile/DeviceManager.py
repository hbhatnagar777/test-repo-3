"""
Module is used for Device operations, such as Starting the emulator,
Starting and stoping appium client, executing adb commands.
"""
import time
import os
import subprocess
from AutomationUtils import logger
LOG = logger.get_log()


class AppiumClient:
    """
    Appium client can be started and stopped using this class.
    """
    def __init__(self):
        pass

    @staticmethod
    def _start_appium():
        """
        Executes the command to start the appium.
        """
        os.system("start appium")

    @staticmethod
    def _is_appium_running():
        """
        Checks if appium server is running or not.
        :return True(if appium is running), False(if appium is not running)
        """
        output = str(subprocess.check_output('netstat -an'))
        return bool("0.0.0.0:4723" in output)

    def start_appium(self):
        """
        Starts appium server.
        """
        if not self._is_appium_running():
            LOG.info("Starting appium server..")
            self._start_appium()
            LOG.info("Wait for 2 minutes to start appium server. ")
            time.sleep(2 * 60)  # wait for 2 minutes
        else:
            LOG.info("Appium is already running.")

    @staticmethod
    def _get_process_id():
        """
        Executes netstat command and returns process id of appium
        :return<string>:process id.
        """
        output = str(subprocess.check_output('netstat -aon'))
        start = output.find('0.0.0.0:4723')  # in output string starting
        # from specified string,
        end = output.find(r'\r\n', start)  # till new line character
        #  output = ["b'.0:0", 'LISTENING', '14444\\r\\n', 'TCP', "0.0.0.0:5'"]
        # as above output line will be as shown.
        process_id = (output[start:end].split()[3]).replace('\\r\\n', '')
        return process_id

    def _kill_appium_process(self):
        """
        Using process id the appium process will be killed.
        """
        process_id = self._get_process_id()
        os.system("taskkill /F /pid " + process_id)

    def stop_appium(self):
        """
        Stops appium server if its running.
        """
        if self._is_appium_running():
            self._kill_appium_process()
            time.sleep(2)
            if self._is_appium_running():
                raise Exception("Failure to terminate the appium process.")


class Emulator:
    """
    Class is used to communicate with the Emulator.
    """
    def __init__(self):
        pass

    @staticmethod
    def get_list_of_available_emulators():
        """
        Gets list of devices running.
        :return:<list>List of devices
        """
        ret = os.popen("android list avd").read()
        return ret

    @staticmethod
    def start_emulator(emulator):
        """
        Start the specified emulator.
        :param emulator: Specify the emulator name
        """
        LOG.info("starting emulator..")
        os.system("start emulator -avd " + emulator)
        LOG.info("Wait for 3 minutes to start the emulator.")
        time.sleep(3 * 60)  # wait for 3 minutes

    def is_emulator_running(self, emulator):
        """
        Checks if specified emulator is running or not.
        :param emulator:<string> specify emulator name.
        :return:True if emulator is found else returns False
        """
        return bool(emulator in self.get_list_of_available_emulators())

    @staticmethod
    def stop_emulator():
        """
        Stops emulator if its running.
        """
        os.system("taskkill /F /IM emulator.exe")
        os.system("taskkill /F /IM qemu-system-x86_64.exe")


class ADB:
    """
    Class is used to execute the ADB commands on emulator or android devices.
    """
    def __init__(self):
        pass

    @staticmethod
    def get_list_of_connected_devices():
        """
        Returns the list of connected android devices.
        :return<List>: list of devices
        """
        ret = subprocess.check_output("adb devices")
        return ret

    @staticmethod
    def push_file_to_device(file, path):
        """
        Copies 'file' to specified 'path'
        Args:
            file: (String) specify the name of file from local test case folder/Provide full path
            with file name
            path: (String) The in device where it should be saved.
        """
        #  eg:("adb push testfile.txt /sdcard/automation/testfile.txt")
        # the file will be placed in internal storage
        os.system('"adb push "' + file + '" "' + path)
        time.sleep(3)
