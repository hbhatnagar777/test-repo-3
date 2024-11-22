"""
Test case to verify Mobile APP - Commvault Edge - Upload and Download.
"""
import os

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Mobile import EdgeManager
from selenium.common.exceptions import NoSuchElementException
from Mobile.DeviceManager import ADB


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Edge App - Upload and Download"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.MOBILECONSOLE
        self.log = logger.get_log()
        self.edge = None

    def setup(self):
        self.edge = EdgeManager.EdgeFactory.create_app_object()

    def _initial_configuration(self):
        """
        Login to app, skip auto upload if screen is displayed, accesses drive.
        """
        self.edge.skip_welcome_screen()
        login_window = self.edge.access_login()
        login_window.login(server=self.inputJSONnode['commcell']["webconsoleHostname"])
        if self.edge.is_auto_upload_shown():
            self.edge.enable_auto_upload()  # Auto upload will be turned off.
        self.drive_window = self.edge.access_drive()

    def _get_temp_dir_path(self):
        """
        If temp directory exists in automation folder, returns the path, or else creates temp
        directory and returns the path.
        Returns:(String):Temp directory path.
        """
        self.log.info("Creating temp directory if it does not exists")
        temp_directory_path = os.path.join(constants.AUTOMATION_DIRECTORY, constants.TEMP_DIR,
                                           self._id)
        if not os.path.exists(temp_directory_path):
            os.mkdir(temp_directory_path)
        return temp_directory_path

    def _create_local_file(self, temp_dir_path, file_name):
        """
        Creates a local file in temp directory.
        Args:
            temp_dir_path :(String) temp dir path
            file_name: (String) file path
        """
        self.log.info("Creating a file")
        if not os.path.exists(temp_dir_path):
            os.makedirs(temp_dir_path)
        file = open(os.path.join(temp_dir_path, file_name), 'w')
        file.write('Hi. This is test file to check upload functionality.')
        file.close()
        return True

    def _push_file_to_device(self, file_path, path):
        # the file will be placed into sdcard/automation folder.
        # The folder will be created automatically.
        self.log.info("File will be copied in device storage")
        ADB.push_file_to_device(file_path, path)

    def _create_folder(self, folder):
        """
        Creates specified folder in Drive.
        Args:
            folder: (String) Specify the folder name to be created.
        """
        self.log.info("Creating folder '%s'in drive section", folder)
        if self.drive_window.is_folder_exists(folder):
            # If already folder exists, then delete
            self.drive_window.delete(folder)
        self.drive_window.create_folder(folder)

    def _verify_upload_file(self, file):
        """
        Push file to device storage, upload same file from storage to drive. Verify its uploaded
        """
        self.log.info("Push file to device storage, upload same file from storage to drive. "
                      "Verify its uploaded")
        folder = "Download"
        # All local files will be created in temp directory.
        temp_directory_path = self._get_temp_dir_path()
        file_path = os.path.join(temp_directory_path, file)
        self._create_local_file(temp_directory_path, file)
        device_storage_path = '/storage/emulated/0/' + folder
        self._push_file_to_device(file_path, device_storage_path)
        self._create_folder(folder)  # Create a folder in drive
        self.drive_window.tap_folder(folder)  # Enter into newly created folder.
        self.drive_window.upload_file(file, folder)  # upload a file.
        try:
            self.edge.get_element_by_text(file)  # Verify file is uploaded.
            self.log.info("File %s uploaded successfully into drive", file)
        except NoSuchElementException:
            raise Exception("Failure to upload file:%s", file)

    def _verify_download_file(self, file):
        """
        Download the file and verify its downloaded successfully. And delete the file from
        downloads section.
        Args:
            file: (String): Specify the file name to be downloaded.
        """
        self.log.info("Download the file and verify its downloaded successfully. And delete the "
                      "file from downloads section.")
        self.drive_window.download_file(file)
        menu = self.edge.access_menu()
        downloads_window = menu.access_downloads()
        try:
            self.edge.get_element_by_text(file)
            self.log.info("File '%s' downloaded successfully", file)
        except NoSuchElementException:
            raise Exception("Failure to download the file '%s'", file)
        self.log.info("Deleting file")
        downloads_window.delete_file(file)

    def run(self):
        try:
            file = "edge_app_upload_50277.txt"
            self._initial_configuration()
            self._verify_upload_file(file)
            self._verify_download_file(file)
            self.status = constants.PASSED
        except Exception as exp:
            self.log.exception('Test Case failed with\n ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Quit driver"""
        self.edge.quit_driver()
        self.log.info("Test case status:%s", str(self.status))
