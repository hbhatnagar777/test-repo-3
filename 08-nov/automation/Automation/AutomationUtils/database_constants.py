# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Helper file for maintaining DB related constants and queries.
"""

from enum import Enum

CLASS_MAP = {
    'client': 'ClientQueries',
    'mediaagent': 'MediaAgentQueries',
    'gxglobalparam': 'AdditionalSettings'
}

class AdditionalSettings(Enum):
    """ Gxglobalparam related queries """

    VALUE_FROM_NAME = """select value from GxGlobalParam where name = '{0}'"""

class MediaAgentQueries(Enum):
    """Media agent related queries"""

    DISKLESS = """select a.name from simInstalledPackages as S
                    INNER JOIN app_client as A ON A.id = S.ClientId
                    where S.simPackageID=51 and A.id not in
                    (select DISTINCT ClientId from MMDeviceController)
                    """
    '''Media agents with no disk libraries configured'''

    DISK = """select A.name from simInstalledPackages as S
                INNER JOIN app_client as A ON A.id = S.ClientId
                where S.simPackageID=51 and A.id in
                (select DISTINCT ClientId from MMDeviceController)"""
    '''Media agents with at least one disk library configured'''

    DISK_LINUX = """select A.name from simInstalledPackages as S
                INNER JOIN app_client as A ON A.id = S.ClientId
                where S.simPackageID=1301 and A.id in
                (select DISTINCT ClientId from MMDeviceController)"""
    '''Linux Media agents with at least one disk library configured'''

    WINDOWS = """select A.name from app_client as A
                    INNER JOIN simOperatingSystem as S on A.simOperatingSystemId = S.id
                    WHERE A.specialClientFlags = 0 and A.id > 1
                    and S.Type = 'Windows' and S.name like '%Windows%'
                    and S.PlatformType like '%6%'"""
    '''Windows Media agents'''

    ALIASNAME = """select AliasName from MMLibrary where LibraryId = (
                    select LibraryId from MMMountPath where MountPathId = (
                    select MountPathId from MMMountPathToStorageDevice where DeviceId = (
                    select Max(DeviceId) from MMDeviceController where Folder='{0}')))"""
    '''Disk library alias name from mount path'''

    ANY = """select A.name from simInstalledPackages as S
                INNER JOIN app_client as A ON A.id = S.ClientId
                where S.simPackageID in (1301, 51)"""
    '''windows or linux media agents'''

class ClientQueries(Enum):
    """Client related queries"""

    ALL = """select name from app_client where specialClientFlags = 0
                and simOperatingSystemId > 0 ORDER by id ASC"""
    '''All valid cilents with no special flags set'''

    NON_MA = """select name from app_client where specialClientFlags = 0
                and id not in (select ClientId from mmhost) and
                id !=2  and simOperatingSystemId > 0
                ORDER by id ASC"""
    ''' Clients where media agent is not installed '''

    GROUP_ID = """select ClientId from APP_ClientGroupAssoc where clientGroupId = '{0}'"""
    '''ALL Client ID's associated to client group'''

    APP_TYPEID = """ select clientId from APP_Application where appTypeId = '{0}'"""
    '''ALL Client ID's associated to appType'''

    SIM_ID = """select ClientId from simInstalledPackages where simPackageID = '{0}'"""
    '''ALL Client ID's associated to Package ID'''

    NAME_ID = """select id from APP_Client where name like '%{0}%' """
    '''Client ID's associated to Name 172'''

    TIMEZONE_ID = """select app_client.id from APP_ClientProp join app_client on
                    app_client.id = app_clientprop.componentnameid
                    where APP_ClientProp.attrName = 'timezone' and
                    attrVal='1:480:Pacific Standard Time' or
                    attrVal='0:-330:India Standard Time' """
    '''Client ID's associated to Time Zone'''

    OSTYPE_ID = """select app_client.id from APP_Client join simOperatingSystem on
                    simOperatingSystem.Id = APP_Client.simOperatingSystemId
                    where simOperatingSystem.Type = '{0}' """
    '''Client ID's associated OperatingSystem Windows'''

    PACKAGE_ID = """select app_client.id from APP_Client join
                    simOperatingSystem on (simOperatingSystem.Id = APP_Client.simOperatingSystemId
                    and simOperatingSystem.Type ='Windows') join simInstalledPackages on
                   (simInstalledPackages.clientId = APP_Client.Id and
                    simInstalledPackages.simPackageID=51)"""
    '''Client ID's associated OperatingSystem Windows and simPackageID=51'''
