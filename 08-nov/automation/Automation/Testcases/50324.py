"""
Test case to verify Edge App- Share files/Folder.
"""
import sys

from selenium.common.exceptions import NoSuchElementException

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Mobile import EdgeManager
from Mobile import AndroidEdge


class TestCase(CVTestCase):
    """
    Initiates test case.
    """
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Edge APP - Share files/Folder"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.MOBILECONSOLE
        self.show_to_user = False
        self.drive_window = None
        self.edge = None
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
        if self.drive_window.is_folder_exists(folder):
            # If already folder exists, then delete
            # it so that all the permissions should be re created.
            self.drive_window.delete(folder)
        self.drive_window.create_folder(folder)

    def share_folder(self, folder):
        """
        Specified folder will be shared with 2 users, 1 user with edit permission, 1 more user
        with view permission
        Args:
            folder: (String) Specify the folder name to be shared.
        """
        self.log.info("Folder will be shared with 2 users, 1 user with edit permission, "
                      "1 more user with view permission")
        share_window = self.edge.tap_more_options_of_element(folder,
                                                             AndroidEdge.MoreOptionsConstants.SHARE)
        user_id = 'email1@commvault.com'  # 1st user with view permission.
        share_window.set_user_id(user_id)
        share_window.tap_add_user()

        user_id = 'email2@commvault.com'  # 2nd user with edit permission.
        share_window.set_user_id(user_id)
        share_window.set_permission(2)
        share_window.tap_add_user()
        share_window.tap_share()
        self.edge.wait_for_page_load()
        share_window.tap_close()

    def verify_folder_shared(self, folder):
        """
        verify folder is present in shared by me section
        Args:
            folder: (String) Specify the folder name to be searched in share by me section.
        """
        self.log.info("verify folder %s is present in shared by me section", folder)
        menu = self.edge.access_menu()
        menu.access_shared_by_me()
        if self.edge.get_element_by_text(folder) is not None:
            self.log.info("Folder is shared successfully.")
        else:
            raise Exception("Failure to share the folder")

    def unshare_folder(self, folder_name):
        """
        Unshare the folder
        Args:
            folder_name(string):folder name
        """
        while True: # If previous case tc is shared folder, but its not cleaned up,
                    # then this will do cleanup of all folders.
            try:
                element = self.edge.get_element_by_text(folder_name)
                self.edge.tap_more_options_of_element(folder_name, "Unshare")
            except NoSuchElementException:
                return

    def run(self):
        try:
            self.initial_configuration()
            folder = 'Automation_permission'
            self.log.info("Creting a folder, share the folder with multiple users, and verify "
                          "folder exists in Shared by me section")
            self.create_folder(folder)
            self.share_folder(folder)
            self.verify_folder_shared(folder)
            self.unshare_folder(folder)
        except Exception as exp:
            self.log.exception('Test Case failed with\n ' + str(exp))
            self.result_string = str(exp) + str(sys.exc_info())
            self.status = constants.FAILED

    def tear_down(self):
        """Quit Driver"""
        self.edge.quit_driver()
        self.log.info("Test case status:%s", str(self.status))
