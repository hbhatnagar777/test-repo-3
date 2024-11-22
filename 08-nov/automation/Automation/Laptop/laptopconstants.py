# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by laptop related testcases."""

CG_CUSTOM_PACKAGE = "Auto_CustomPackageClientGroup"
''' Client group input to the custom package creation.'''

CG_AUTH_REGISTER = "Auto_RegisterWithAuthCode"
''' Servers registered with commcell auth code will be associated to this client group '''

REINSTALL_NAME = "_reinstall"
''' This string will be appended for reinstalled client '''

REINSTALLED_CLIENT_STR = "___1"
'''This string gets appended when clients are reinstalled with a different owner '''

REPURPOSED_CLIENT = "_repurposed"
'''When repurposed additional key is set the deconfigured client is appended with this string '''

UNIX_INSTALL_DIR = r"/opt/commvault/Log_Files"
''' Commvault default install"ation location for Mac machines '''

DOCUMENTS_PATH = "C:\\Users\\admin\\Documents\\Inc1"
'''This is the defaut documents path used for douments moniker'''

LIBRARY_PATH = "C:\\Users\\admin\\Appdata\\Roaming\\Inc1"
'''This is the defaut Library path used for <WKF,Library> moniker'''

TEST_DATA_PATH = "C:\\selftest"
'''This is the defaut testpath to create testdata for FS backup cases'''

ONEDRIVE_PATH = "C:\\Users\\admin\\OneDrive"
'''This is the path for onedrive on client'''

DROPBOX_PATH = "C:\\Users\\admin\\Dropbox"
'''This is the path for dropbox on client'''

GOOGLEDRIVE_PATH = "C:\\Users\\admin\\Google Drive"
'''This is the path for googledrive on client'''

PST_FILE_PATH = ""
'''This is the path for PST files'''

HOME_PATH = ""
''' This is the path for home on client for home moniker'''

EMAIL_ID = ""
'''This is the emailid used for pst file evalaution'''

WINDOWS_PATH = "C:\\Users\\Administrator\\Documents\\"
'''This is the default documents path used to create new data on winodws'''

MAC_PATH = "/Users/cvadmin/Documents/"
'''This is the default documents path used to create new data on mac'''

MAC_DOCUMENTS_PATH = "/Users/cvadmin/Documents/Inc1"
'''This is the default documents path used to create new data on mac'''

MAC_TEST_DATA_PATH = "/Users/cvadmin/selftest"
'''This is the defaut testpath to create testdata for FS backup cases'''

MAC_LIBRARY_PATH = "/Users/cvadmin/Library/Inc1"
'''This is the defaut Library path used for <WKF,Library> moniker'''

MAC_ONEDRIVE_PATH = "/Users/cvadmin/OneDrive"
'''This is the path for onedrive on client'''

MAC_DROPBOX_PATH = "/Users/cvadmin/Dropbox/automation"
'''This is the path for dropbox on client'''

MAC_HOME_PATH = "/Users/cvadmin"
''' This is the path for home on client for home moniker'''


'''This is the defaut Library path used for <WKF,Library> moniker'''