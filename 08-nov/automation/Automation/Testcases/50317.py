"""
Test case to verify Edge app - Share files/folders.
"""
from selenium.common.exceptions import NoSuchElementException

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from Mobile import EdgeManager
from Mobile import AndroidEdge


class TestCase(CVTestCase):
    """
    Initiates test case.
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Edge App - favorites"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.MOBILECONSOLE
        self.show_to_user = False
        self.log = logger.get_log()

    def setup(self):
        self.edge = EdgeManager.EdgeFactory.create_app_object()

    def initial_configuration(self):
        """
        Login to app, skip auto upload if screen is displayed, accesses drive.
        """
        self.edge.skip_welcome_screen()
        login_window = self.edge.access_login()
        login_window.login(server=self.inputJSONnode['commcell']["webconsoleHostname"])
        if self.edge.is_auto_upload_shown():
            self.edge.enable_auto_upload()  # Auto upload will be turned off.
        self.drive_window = self.edge.access_drive()

    def create_folder(self, folder):
        """
        Creates specified folder in Drive.
        Args:
            folder: (String) Specify the folder name to be created.
        """
        if not self.drive_window.is_folder_exists(folder):
            self.drive_window.create_folder(folder)

    def add_to_favorites(self, folder):
        """
        Adds specified folder to favorites.
        Args:
            folder: (String) Specify the folder name
        """
        self.log.info("Adding folder to favorites:%s", folder)
        self.edge.tap_more_options_of_element(folder, AndroidEdge.MoreOptionsConstants.ADD_TO_FAVORITES)

    def verify_folder_in_favorites(self, folder):
        """
        Verify in favorites section the specified folder/file exists.
        Args:
            folder: folder: (String) Specify the folder name
        """
        self.log.info("Verifying folder '%s' exists in favorites section", folder)
        menu = self.edge.access_menu()
        menu.access_favorites()
        self.edge.access_favorites()
        if self.edge.get_element_by_text(folder) is not None:
            self.log.info("Verified. Folder '%s' exists in favorites section", folder)
        else:
            raise Exception("The folder which is added to favorites, does not exists. Folder:%s" % folder)

    def remove_from_favorites(self, folder):
        """
        Removes specified file/folder from favorites section.
        Args:
            folder: folder: (String) Specify the folder name
        """
        self.log.info("Removing folder '%s' from favorites section", folder)
        fav_window = self.edge.access_favorites()
        fav_window.remove_from_favorites(folder)
        try:
            self.edge.get_element_by_text(folder)
        except NoSuchElementException:
            self.log.info("Removed folder '%s' from favorites section", folder)
            return
        raise Exception("Failure to delete folder/file from favorites section")

    def run(self):
        try:
            self.initial_configuration()
            folder_name = 'Automation_fav'
            self.log.info("Create a folder, and add it to favorites. And verify folder exists in favorites section.")
            self.create_folder(folder_name)
            self.add_to_favorites(folder_name)
            self.verify_folder_in_favorites(folder_name)
            self.log.info("Removing folder from favorites, and verify its removed.")
            self.remove_from_favorites(folder_name)
            self.status = constants.PASSED
        except Exception as exp:
            self.log.exception('Test Case failed with\n ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.edge.quit_driver()
        self.log.info("Test case status:%s", str(self.status))