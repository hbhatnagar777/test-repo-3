from selenium.webdriver.common.by import By
"""
Edge android app related modules can be accessed here.

"""
import time
from Mobile.EdgeManager import EdgeManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

from AutomationUtils import config
from AutomationUtils import logger

CONSTANTS = config.get_config()


class Constants:
    """
    Constants used in different classes of this file.
    """
    AUTO_UPLOAD_NOT_NOW = "NOT NOW"
    AUTO_UPLOAD_TURN_ON = "TURN ON"
    LOGOUT = "Logout"


class MoreOptionsConstants:
    """
    Constants are used when more options of files are clicked.
    """
    SHARE = "Share"
    GET_LINK = "Get Link"
    ADD_TO_FAVORITES = "Add to Favorites"
    RENAME = "Rename"
    MOVE = "Move"
    DOWNLOAD = "Download"
    EXPORT = "Export"
    DELETE = "Delete"
    UNSHARE = "Unshare"


class EdgeApp(EdgeManager):
    """
    This class creates object of edge app and communicated with app.
    """
    def __init__(self, no_reset, full_reset):
        super().__init__()
        self._full_reset = full_reset
        self._no_reset = no_reset

    def access_login(self):
        """
        Accesses login.
        :return:<object>Login class object
        """
        self.log.info("Accessing login")
        return Login(self)

    def _configure_desired_capabilities(self):
        """
        Sets desired capabilities of edge app.
        """
        self.log.info("Configuring desired capabilities")
        self._desired_capabilities['platformName'] = "Android"
        self._desired_capabilities['platformVersion'] = CONSTANTS.EdgeApp.ANDROID_VERSION
        self._desired_capabilities['deviceName'] = "Android Emulator"
        self._desired_capabilities['app'] = CONSTANTS.EdgeApp.FILE_PATH_ANDROID
        self._desired_capabilities['appPackage'] = "com.commvault.mobile.edge"
        self._desired_capabilities['appActivity'] = "com.commvault.mobile.edge.LoginActivity"
        self._desired_capabilities['newCommandTimeout'] = 10000
        self._desired_capabilities['full-reset'] = self._full_reset
        self._desired_capabilities['noReset'] = self._no_reset
        self._desired_capabilities['avd'] = CONSTANTS.EdgeApp.AVD_NAME
        self._desired_capabilities['avdLaunchTimeout'] = 300000

    def skip_welcome_screen(self):
        """
        Skips welcome screen.
        """
        try:
            self.log.info("Skipping welcome screen")
            self.disable_implicit_wait_time()
            status = self.driver.find_element(By.ID, 'com.commvault.mobile.edge:id/skip_button')
            if status is not False:
                status.click()
                time.sleep(5)
        except NoSuchElementException:
            self.log.info("Welcome screen did not appear")
        finally:
            self.set_implicit_wait_time()

    def is_auto_upload_shown(self):
        """
        Verifies auto upload screen is displayed or not.
        Returns:(Boolean)True if auto upload is displayed, or else returns False
        """
        try:
            time.sleep(5)
            self.log.info("Checking if auto upload screen is displayed")
            self.disable_implicit_wait_time()
            self.driver.find_element(By.ID, "com.commvault.mobile.edge:id/newFeatureImage")
            self.log.info("Auto upload screen is displayed")
            return True
        except NoSuchElementException:
            self.log.info("Auto upload screen is not displayed")
            return False
        finally:
            self.set_implicit_wait_time()

    def enable_auto_upload(self, enable=False):
        """
        Auto upload will be Enabled/skipped.
        :param enable:<Boolean>True/False
            Default : False(Upload will be skipped.)
        """
        if enable is not True:
            self.log.info("Auto upload status:%s", Constants.AUTO_UPLOAD_NOT_NOW)
            auto_upload_status_element = self.get_element_by_text(Constants.AUTO_UPLOAD_NOT_NOW,
                                                                  scroll=False)
        else:
            self.log.info("Auto upload status:%s", Constants.AUTO_UPLOAD_TURN_ON)
            auto_upload_status_element = self.get_element_by_text(Constants.AUTO_UPLOAD_TURN_ON,
                                                                  scroll=False)
        auto_upload_status_element.click()
        self.driver.press_keycode(187)  # 187 is key code for switching between apps.
        time.sleep(5)
        self.driver.press_keycode(187)
        #  press_code(187): Auto upload screen as it pops out, elements which are displaced
        #  couldn't be found with the
        #  driver. So with press_code method app will be sent to background, and
        #  switched back again.
        time.sleep(4)

    def access_drive(self):
        """
        Accesses drive and creates object of Drive class
        :return:<object>Drive class object
        """
        self.log.info("Accessing drive")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.DRIVE).click()
        time.sleep(2)
        return Drive(self)

    def access_shared_with_me(self):
        """
        Accesses shared with me.
        """
        self.log.info("Accessing shared with me section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.SHARED_WITH_ME).click()
        time.sleep(2)

    def access_shared_by_me(self):
        """
        Accesses shared by me.
        """
        self.log.info("Accessing shared by me section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.SHARED_BY_ME).click()
        time.sleep(2)

    def access_downloads(self):
        """
        Accesses shared by me.
        """
        self.log.info("Accessing downloads section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.DOWNLOADS).click()
        time.sleep(2)
        return Downloads(self)

    def access_favorites(self):
        """
        Accesses shared by me and Creates Favorites class object
        :return:<object>returns object of favorites.
        """
        self.log.info("Accessing favorites section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.FAVORITES).click()
        time.sleep(2)
        return Favorites(self)

    def access_trash(self):
        """
        Accesses thrash
        """
        self.log.info("Accessing thrash section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.THRASH).click()
        time.sleep(2)

    def access_devices(self):
        """
        Accesses devices
        """
        self.log.info("Accessing devices section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.THRASH).click()
        time.sleep(2)

    def access_photos_and_videos(self):
        """
        Accesses photos and videos.
        """
        self.log.info("Accessing photos and videos section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.PHOTOS_AND_VIDEOS).click()
        time.sleep(2)

    def access_recent_files(self):
        """
        Accesses recent files.
        """
        self.log.info("Accessing recent files section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.RECENT_FILES).click()
        time.sleep(2)

    def access_uploads(self):
        """
        Accesses uploads.
        """
        self.log.info("Accessing uploads section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.UPLOADS).click()
        time.sleep(2)

    def access_settings(self):
        """
        Accesses Settings.
        """
        self.log.info("Accessing settings section")
        self.get_element_by_text(EdgeManager.EdgeAppConstants.SETTINGS).click()
        time.sleep(2)

    def logout(self):
        """
        Logout from app.
        """
        self.log.info("Logging out")
        self.access_settings()
        time.sleep(2)
        self.get_element_by_text(Constants.LOGOUT).click()
        time.sleep(10)

    def wait_for_page_load(self, time_out_period=200):
        """
        Wait till load mask exists on screen.
        :param time_out_period: Max wait time to wait till load mask to disappear.
            default: 200 seconds
        """
        self.log.info("Wait for page load")
        try:
            time.sleep(3)
            self.disable_implicit_wait_time()
            start_time = time.time()
            while True:
                elapsed = (time.time() - start_time)
                if (self.driver.find_element(By.ID, 'android:id/progress') != []) \
                        and elapsed < time_out_period:
                    continue
                else:
                    raise TimeoutException(msg="Failure to load the page within given "
                                               "time period:" + str(time_out_period))
        except NoSuchElementException:
            pass
        finally:
            self.set_implicit_wait_time()

    def _tap_more_options_of_element(self, file_name):
        """
        taps on more options of specified file.
        :param file_name:<string>Specify the file name
        """
        time.sleep(3)
        self.driver.find_element(By.XPATH, "//*[@text = '" + file_name + "']"
                                          "/../..//android.widget.ImageView"
                                          "[@resource-id='com.commvault.mobile."
                                          "edge:id/menu']").click()
        time.sleep(3)

    def tap_more_options_of_element(self, file_name, option):
        """
        Taps on required option of specified file.
        :param file_name:<String>file name
        :param option:<String>Specify the option to tap.
        """
        self.log.info("Tapping more options of file:%s, and searching for the option:%s",
                      file_name, option)
        self._tap_more_options_of_element(file_name)
        self.hide_keyboard()
        if option == MoreOptionsConstants.SHARE:
            self.get_element_by_text(MoreOptionsConstants.SHARE).click()
            return Share(self)
        elif option == MoreOptionsConstants.GET_LINK:
            self.get_element_by_text(MoreOptionsConstants.GET_LINK).click()
            self.scroll_down()
        elif option == MoreOptionsConstants.ADD_TO_FAVORITES:
            self.get_element_by_text(MoreOptionsConstants.ADD_TO_FAVORITES).click()
        elif option == MoreOptionsConstants.RENAME:
            self.get_element_by_text(MoreOptionsConstants.RENAME).click()
        elif option == MoreOptionsConstants.MOVE:
            self.get_element_by_text(MoreOptionsConstants.MOVE).click()
        elif option == MoreOptionsConstants.DELETE:
            self.scroll_down()
            self.get_element_by_text(MoreOptionsConstants.DELETE).click()
        elif option == MoreOptionsConstants.DOWNLOAD:
            self.get_element_by_text(MoreOptionsConstants.DOWNLOAD).click()
        elif option == MoreOptionsConstants.UNSHARE:
            self.get_element_by_text(MoreOptionsConstants.UNSHARE, scroll=False).click()
            self.get_element_by_text("YES", scroll=False).click()
        else:
            raise ValueError("Incorrect argument passed, option:%s", option)
        time.sleep(3)

    def access_menu(self):
        """
        Accesses menu option from top left if its available. Eg:Drive.
        :return:<object>Menu object will be returned
        """
        self.log.info("Accessing menu")
        self.driver.find_element(By.CLASS_NAME, 'android.widget.ImageButton').click()
        return MenuItems(self)

    def get_devices(self):
        """
        Lists the all the devices present
        :return:<List>list of devices
        """
        self.log.info("Looking for the devices in edge app")
        list_of_devices = []
        found_devices_list = False
        while found_devices_list is not True:
            elements = self.get_list_of_elements()
            for element_text in elements:
                if element_text == "COMMVAULT":
                    continue
                elif element_text == "MY SHARES" or element_text == 'MY DRIVE':
                    self.log.info("Available devices in app:%s", list_of_devices)
                    return list_of_devices
                elif element_text not in list_of_devices:
                    list_of_devices.append(str(element_text))
            self.scroll_down()


class Downloads:
    """
    Operations made on downloads section.
    """
    def __init__(self, app_object: EdgeApp):
        self.app = app_object
        self.log = logger.get_log()

    def _tap_delete(self):
        self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/menu_delete").click()
        time.sleep(4)
        self.app.get_element_by_text("YES", scroll=False).click()
        time.sleep(4)

    def delete_file(self, file):
        """
        Deletes the specified file from downloads section.
        Args:
            file:(String) Specify the file name to delete
        """
        self.log.info("Deleting file '%s' from Downloads section", file)
        self.app.long_press_element(self.app.get_element_by_text(file))
        self._tap_delete()


class Favorites:
    """
    Options/modules which will communicates in favorites.
    """
    def __init__(self, app_object: EdgeApp):
        self.app = app_object
        self.log = logger.get_log()

    def _tap_remove_from_favorites(self):
        """
        Taps on option -> remove from favorites present in favorites section.
        """
        self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/menu_unfavorite").click()

    def remove_from_favorites(self, file_name):
        """
        Removes long pressed element from favorites.
        """
        self.log.info("Removing file %s from favorites section", file_name)
        file_element = self.app.get_element_by_text(file_name)
        self.app.long_press_element(file_element)
        self._tap_remove_from_favorites()
        self.app.get_element_by_text("YES", scroll=False).click()


class Login:
    """
    Login to server using this class.
    """
    def __init__(self, edge: EdgeApp):
        self.edge = edge
        self.log = logger.get_log()

    def _set_user_name(self, username):
        """
        Sets user name
        :param username:<String>Specify the user name
        """
        self.edge.driver.find_element(By.ID, "com.commvault."
                                            "mobile.edge:id/email").send_keys(username)

    def _set_password(self, password):
        """
        Sets password.
        :param password:<String>Specify the password.
        """
        self.edge.driver.find_element(By.ID, "com.commvault."
                                            "mobile.edge:id/password").send_keys(password)

    def _set_server_name(self, server):
        """
        Sets server name.
        :param server:<String>Specify the server name
        """
        self.edge.driver.find_element(By.ID, "com.commvault."
                                            "mobile.edge:id/serverURL").send_keys(server)

    def _tap_login_btn(self):
        """
        Taps on login button
        """
        self.edge.hide_keyboard()
        self.edge.driver.find_element(By.ID, "com.commvault."
                                            "mobile.edge:id/sign_in_button").click()
        time.sleep(3)

    def is_logged_in(self):
        """
        Verifies logged in or not based on login button/welcome screen if its displayed on the
        screen.
        :return:True/False
        """
        self.edge.wait_for_page_load()
        self.edge.disable_implicit_wait_time()
        #  welcome screen or login button should not be displayed in screen to verify its loggedin.
        if self.edge.driver.find_elements(By.ID, "com.commvault.mobile.edge:id/sign_in_button") != \
                [] or \
                self.edge.driver.find_elements(By.ID, 'com.commvault.mobile.edge:id/skip_button') \
                != []:
            self.log.info("App is not logged in")
            self.edge.set_implicit_wait_time()
            return False
        else:
            self.log.info("App is logged in")
            self.edge.set_implicit_wait_time()
            return True

    def _enable_secure_connection(self):
        """
        Enables secure connection.
        """
        self.edge.driver.find_element(By.ID, 'com.commvault.mobile.edge:id/secureSwitch').click()

    def login(self, server, username=CONSTANTS.ADMIN_USERNAME, password=CONSTANTS.ADMIN_PASSWORD,
              secure_connection=False):
        """
        Logs in specified server takes user name and passwords from config file by default.
        :param username:<string>specify the user name
        :param password:<string>Specify the password
        :param server:<string>specify the server name
        :param secure_connection<Boolean>True/False
        """
        self.log.info("Logging in to edge app, with the "
                      "user %s, to the server %s", username, server)
        if not self.is_logged_in():
            self._set_user_name(username)
            self._set_password(password)
            self._set_server_name(server)
            if secure_connection is True:
                self._enable_secure_connection()
            self._tap_login_btn()
            time.sleep(5)
            self.edge.wait_for_page_load()
            if not self.is_logged_in():
                raise Exception("Failed to login!")
            self.log.info("Logged in successfully to server %s", server)


class Drive:
    """
    It has modules which will communicates through drive.
    """
    def __init__(self, app_object: EdgeApp):
        self.app = app_object
        self._remove_preview_screen()
        self.log = logger.get_log()

    def _remove_preview_screen(self):
        """
        Removes the hand screen if its displayed.
        """
        try:
            self.app.disable_implicit_wait_time()
            self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/hand_both").click()
        except NoSuchElementException:
            pass
        finally:
            self.app.set_implicit_wait_time()

    def _tap_add_icon(self):
        """
        clicks on add icon
        """
        self.log.info("Tapping add icon")
        element = self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/fab")
        element.click()
        time.sleep(3)

    def _tap_files_icon(self):
        """
        Taps files icon after clicking on add icon.
        """
        self.log.info("Tapping files icon.")
        self.app.get_element_by_text("Files", scroll=False).click()
        time.sleep(3)

    def _tap_images_icon(self):
        """
        Taps on images icon present in drive -> add -> images
        """
        self.log.info("Tapping images icon")
        self.app.get_element_by_text("Images", scroll=False).click()

    def _tap_folder_icon(self):
        """
        Taps folder icon present in drive while creating a new folder.
        """
        self.log.info("Tapping folder icon")
        self.app.get_element_by_text("Folder", scroll=False).click()

    def _tap_delete_icon(self):
        """
         Clicks on delete icon, when
        """
        time.sleep(3)
        self.log.info("Tapping delete icon.")
        self.app.driver.find_element(By.ID, "com.commvault."
                                           "mobile.edge:id/menu_browse_delete").click()

    def _set_folder_name(self, folder_name):
        """
        While creating a folder, provide the new folder name to be created.
        :param folder_name:<String>Specify the folder name
        """
        time.sleep(2)
        self.app.driver.find_element(By.ID, 'com.commvault'
                                           '.mobile.edge:id/folderEditText').send_keys(folder_name)

    def _tap_create(self):
        """
        While creating new folder, taps on 'Create' button.
        """
        self.app.get_element_by_text("CREATE", scroll=False).click()

    def _tap_upload(self):
        """
        Use this function to upload a file or image.
        """
        self.app.get_element_by_text("UPLOAD", scroll=False).click()

    def tap_folder(self, folder_name):
        """
        Taps on any folder present in drive.
        :param folder_name:<String>Specify the folder name.
        """
        self.app.get_element_by_text(folder_name).click()
        time.sleep(3)

    def is_folder_exists(self, folder_name):
        """
        Verifies if folder exists on not in drive.
        :param folder_name: <String> Specify the folder name
        :return: True/False depending on folder exists on not.
        """
        self.log.info("Checking if folder exists, folder name:%s", folder_name)
        try:
            self.app.get_element_by_text(folder_name)
            self.log.info("Folder already exists:%s", folder_name)
            return True
        except NoSuchElementException:
            self.app.drag_to_top()
            return False

    def delete(self, entity_name):
        """
        Deletes any folder/File in drive.
        :param entity_name:<String>Folder/File name
        """
        self.log.info("Deleting Folder/File, name:%s", entity_name)
        element = self.app.get_element_by_text(entity_name)
        self.app.long_press_element(element)
        self._tap_delete_icon()
        time.sleep(5)
        self.app.get_element_by_text("YES", scroll=False).click()

    def create_folder(self, folder_name):
        """
        Creates new folder in drive.
        :param folder_name:<String>Specify the folder name
        """
        self.log.info("Creating folder, name:%s", folder_name)
        self._tap_add_icon()
        self._tap_folder_icon()
        self._set_folder_name(folder_name)
        self._tap_create()
        time.sleep(4)

    def _redirect_to_upload_directory(self, path):
        """
        Redirects to required folder loaction.
        Args:
            path: Specify the path where it needs to be redirected in device storage.
        """
        self.app.get_element_by_text(path).click()

    def upload_file(self, file_name, folder):
        """
        Uploads file in drive.
        Args:
            file_name:(String)file name to be uploaded.
            folder:(String) Specify the folder name in which file to be uploaded.
        """
        self.log.info("Uploading a file '%s' in drive from folder '%s'", file_name, folder)
        self._tap_add_icon()
        self._tap_files_icon()
        time.sleep(3)
        self.tap_folder(folder)
        self.app.get_element_by_text(file_name, scroll=False).click()
        self._tap_upload()
        time.sleep(15)

    def _tap_download(self):
        self.log.info("Tapping download")
        self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/menu_browse_download").click()
        time.sleep(15)

    def download_file(self, file_name):
        """
        Downloads specified file from Drive section.
        Args:
            file_name: (String) Specify the file name.
        """
        self.log.info("Downloading the file:" + file_name)
        self.app.long_press_element(self.app.get_element_by_text(file_name, scroll=False))
        time.sleep(5)
        self._tap_download()


class MenuItems:
    """
    Menu operation can be done through this. This can be used when driver is in 'Drive'.
    """
    def __init__(self, edge: EdgeApp):
        self.app = edge
        self.log = logger.get_log()

    def access_drive(self):
        """
        Taps on Drive and return class object
        :return:<Object>Driver object
        """
        self.log.info("Accessing drive")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.DRIVE).click()
        return Drive(self.app)

    def access_recent_files(self):
        """
        Accesses Recent files section
        """
        self.log.info("Accessing recent")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.RECENT_FILES).click()

    def access_shared_with_me(self):
        """
        Accesses shared with me section.
        """
        self.log.info("Accessing shared with me")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.SHARED_WITH_ME).click()

    def access_shared_by_me(self):
        """
        Accesses shared by me section.
        """
        self.log.info("Accessing shared by me section")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.SHARED_BY_ME).click()

    def access_downloads(self):
        """
        Accesses downloads section.
        """
        self.log.info("Accessing downloads section")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.DOWNLOADS).click()
        return Downloads(self.app)

    def access_favorites(self):
        """
        Accesses favorites section.
        """
        self.log.info("Accessing favorites section")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.FAVORITES).click()

    def access_uploads(self):
        """
        Accesses uploads section.
        """
        self.log.info("Accessing uploads section")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.UPLOADS).click()

    def access_settings(self):
        """
        Accesses settings section.
        """
        self.log.info("Accessing settings section")
        self.app.get_element_by_text(EdgeManager.EdgeAppConstants.SETTINGS).click()


class Share:
    """
    These are Share modules, can be used to communicate with share .
    """
    def __init__(self, edge: EdgeApp):
        self.app = edge
        self.log = logger.get_log()

    def set_user_id(self, user_id):
        """
        Sets user name
        :param user_id:<String>Specify username
        """
        self.log.info("Setting user id %s", user_id)
        self.app.driver.find_element(By.ID, 'com.commvault'
                                           '.mobile.edge:id/shareTextView').send_keys(user_id)

    def tap_add_user(self):
        """
        Taps on (+) icon, Adds mentioned user.
        """
        self.log.info("Tapping add user")
        self.app.driver.find_element(By.ID, 'com.commvault.mobile.edge:id/addUser').click()

    def _set_view_permission(self):
        """
        Sets view permission.
        """
        self.log.info("Setting view permission")
        self.app.driver.find_element(By.ID, "com.commvault.mobile.edge:id/toolbar").click()
        self.app.get_element_by_text('Can view', scroll=False).click()
        time.sleep(4)

    def _set_edit_permission(self):
        """
        Sets edit permission.
        """
        self.log.info("Setting edit permission")
        self._set_view_permission()
        self.app.get_element_by_text('Can edit', scroll=False).click()

    def set_permission(self, permission):
        """
        1: Can View
        2: Can Edit
        """
        self.log.info("Setting permission")
        if permission == 1:
            pass  # by default it will be can view permission
        elif permission == 2:
            time.sleep(5)
            self._set_edit_permission()
        else:
            raise ValueError("Invalid argument passed for permission arg:%s", permission)

    def add_message(self, message):
        """
        Specify the message/Comments to be added.
        :param message:<String> Specify the message
        """
        self.app.driver.find_element(By.ID, 'com.commvault.'
                                           'mobile.edge:id/writeMessageText').send_keys(message)

    def tap_cancel(self):
        """
        Tap on cancel to cancel adding user.
        """
        self.app.hide_keyboard()
        self.app.driver.find_element(By.ID, 'com.commvault.mobile.edge:id/cancelShare')

    def tap_share(self):
        """
        Taps on share button once user is specified.
        """
        self.log.info("Tapping share button")
        self.app.hide_keyboard()
        self.app.get_element_by_text('SHARE').click()
        time.sleep(3)

    def tap_update(self):
        """
        Taps on update, if any changes are updated in share.
        """
        self.app.get_element_by_text('UPDATE').click()
        time.sleep(3)

    def tap_close(self):
        """
        Taps of close button in share.
        :return:
        """
        self.app.get_element_by_text('CLOSE').click()
        time.sleep(3)

    def share_data(self, user_id, permission=1, message=None):
        """
        Share folder with only 1 specific user.
        :param user_id:specify the user id.
        :param permission: specify the permission.
                permission = 1 to set view permission.
                permission = 2 to set edit permission.
        :param message: Specify the message to be added.
        """
        self.log.info("Sharing file/folder with user id:%s", user_id)
        self.set_user_id(user_id)
        if permission is not 1:
            self.set_permission(permission)
        #  by default can view permission will be set.
        self.app.hide_keyboard()
        if message is not None:
            self.add_message(message)
        try:
            self.tap_share()
        except NoSuchElementException:
            self.tap_update()
