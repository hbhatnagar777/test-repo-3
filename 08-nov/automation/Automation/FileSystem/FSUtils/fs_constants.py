# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""File for All the constants related to FileSystem"""

import os

MAC_MA_PATHS = ["/Library/Preferences/SystemConfiguration/com.apple.PowerManagement.plist",
                "/Library/Safari/Bookmarks.plist",
                "/Library/Safari/TopSites.plist",
                "/Library/Application Support/Google/Chrome/Default",
                "/Library/Preferences/com.google.Chrome.plist",
                "/Library/Keychains",
                "/Library/Preferences/com.apple.keychainaccess.plist",
                "/Library/Application Support/AddressBook",
                "/Library/Preferences/com.apple.AddressBook.plist",
                "/Library/Calendars",
                "/Library/Preferences/com.apple.iCal.plist",
                "/Library/Accounts",
                "/Library/Preferences/com.apple.accountsd.plist"]

WIN_MA_PATHS = ["%Desktop%",
                "%Documents%",
                "%Music%",
                "%Pictures%",
                "%NTUSER%",
                "%WALLPAPER%",
                "%SCRSAVER%",
                "%SYSTEM%",
                "%LOCALAPPDATA%\\Microsoft\\Media Player",
                "%FAVORITES%",
                "%LOCALAPPDATA%\\Microsoft\\Internet Explorer\\Quick Launch",
                "%LOCALAPPDATA%\\Microsoft\\Internet Explorer",
                "%APPDATA%\\Microsoft\\SystemCertificates",
                "%APPDATA%\\Microsoft\\Outlook",
                "%LOCALAPPDATA%\\Microsoft\\Outlook",
                "%APPDATA%\\Microsoft\\Office",
                "%APPDATA%\\Microsoft\\PowerPoint",
                "%APPDATA%\\Microsoft\\Stationery",
                "%APPDATA%\\Microsoft\\Signatures",
                "%APPDATA%\\Microsoft\\UProof",
                "%LOCALAPPDATA%\\Microsoft\\Feeds",
                "%LOCALAPPDATA%\\Microsoft\\Feeds Cache",
                "%LOCALAPPDATA%\\Microsoft\\Windows\\History",
                "%APPDATA%\\Microsoft\\Windows\\Cookies",
                "%APPDATA%\\Microsoft\\Network",
                "%Videos%"
                ]

WIN_DATA_CLASSIFIER_CONFIG_REGKEY = "Data Classification\\Configuration\\"
WIN_DATA_CLASSIFIER_STATUS_REGKEY = "Data Classification\\Status\\"
WIN_DATA_CLASSIFIER_BASE_PATH = "System Volume Information\\Commvault\\Data Classification\\"
