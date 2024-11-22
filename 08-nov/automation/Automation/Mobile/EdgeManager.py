"""
Module is used to perform actions on Edge specific app only.
"""
from abc import ABCMeta, abstractmethod
from Mobile.AppManager import AppManager
from Mobile.DeviceManager import AppiumClient
from Mobile import utils
from AutomationUtils import config

CONSTANTS = config.get_config()
EDGE_CONSTANTS = CONSTANTS.EdgeApp


class EdgeManager(AppManager, metaclass=ABCMeta):
    """
    Edge specific actions like:login, logout, drive, operations to be performed on devices list,
    uploading files/folders etc.
    """
    class EdgeAppConstants:
        """
        These are the constants used tap on specific feature. Any feature is updated in text then it
        should be updated here.
        """
        DRIVE = "Drive"
        RECENT_FILES = "Recent Files"
        THRASH = "Trash"
        PHOTOS_AND_VIDEOS = "Photos and Videos"
        SHARED_WITH_ME = "Shared with me"
        SHARED_BY_ME = "Shared by me"
        DOWNLOADS = "Downloads"
        FAVORITES = "Favorites"
        UPLOADS = "Uploads"
        SETTINGS = "Settings"

    def __init__(self):
        super().__init__()

    @abstractmethod
    def access_login(self):
        """
        Gets login class object to operate on login page.
        :return: login class object
        """
        raise NotImplementedError

    @abstractmethod
    def logout(self):
        """
        This should tap on settings page object and then it should redirect to logout.
        """
        raise NotImplementedError

    @abstractmethod
    def access_devices(self):
        """
        Actions to be done on My Devices window can be handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_drive(self):
        """
        Returns Drive class object to operate on drive window.
        """
        raise NotImplementedError

    @abstractmethod
    def access_recent_files(self):
        """
        Actions to be done on Recent Files window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_trash(self):
        """
        Actions to be done on Thrash window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_photos_and_videos(self):
        """
        Actions to be done on Photos and Videos window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_shared_with_me(self):
        """
        Actions to be done on Shared with me window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_shared_by_me(self):
        """
        Actions to be done on Shared By me window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_downloads(self):
        """
        Actions to be done on Downloads window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_favorites(self):
        """
        Actions to be done on Favorites window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_uploads(self):
        """
        Actions to be done on Uploads window are handled here.
        """
        raise NotImplementedError

    @abstractmethod
    def access_settings(self):
        """
        Actions to be done on Settings window are handled here.
        """
        raise NotImplementedError


class EdgeFactory(object):
    """
    This class is used to control and manage the creation of the
    app drivers by the TC.
    """
    TYPE_ANDROID = "Android"
    TYPE_iOS = "iOS"

    @staticmethod
    def create_app_object(app_type=CONSTANTS.EdgeApp.DEFAULT_APP_TYPE,
                          no_reset=True,
                          full_reset=False):
        """
        Creates the app edge object based on Android or IOS depending on config file.
        :param app_type:Android/IOS
        :param no_reset:<True/False>Do not stop app,do not clear app data, and do not uninstall
        apk.
        :param full_reset:<True/False>Stop app, clear app data and uninstall apk after test.
        :return:Edge type object
        """
        appium_client = AppiumClient()
        appium_client.start_appium()
        if app_type == EdgeFactory.TYPE_ANDROID:
            from Mobile.AndroidEdge import EdgeApp as Android_App
            if utils.is_apk_file_updated(EDGE_CONSTANTS.FILE_PATH_ANDROID):
                full_reset = True
                no_reset = False
            edge = Android_App(no_reset, full_reset)
        else:
            raise Exception("Unsupported OS type:%s" % app_type)
        edge.open_app()
        return edge
