# -**- coding: utf-8 -**-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by Server test cases"""

MAPACKAGEID = '51'
"""str: Simpackage id to get client ids from siminstalled packages."""

APPGROUPXML = """<?xml version='1.0' encoding='UTF-8'?>
               <TMMsg_AppGroupSelection>
                <appGroups appGroupId=\"22\" />
              </TMMsg_AppGroupSelection>"""
""" APPGROUP value to create client group with FS IDA installed clients."""

APPADVANCEPKG = """<?xml version='1.0' encoding='UTF-8'?>
              <App_AdvanceKeyInfo>
                <packages val='51' />
              </App_AdvanceKeyInfo>"""
""" Package Installed value to create client group with Installed agent as Media agent."""

PASSWORD = '######'
"""str: Password to create Non-Admin user."""
QUERY_DICT = {
        "client_level_prop_query": "select c.id EntityId, 3 EntityType, cp.attrName AttrName, "
                                   "'client level props' Descriptions, c.id from app_client c "
                                   "join app_clientProp cp on c.id = cp.componentnameid "
                                   "join app_credprops cred on cred.attrUserName = cp.attrName"
                                   " or cred.attrPwdName = cp.attrName where cred.tableId = 21 ",

        "apptype_prop_query": " select i.clientId ClientId, i.appTypeId EntityId, 4 EntityType, "
                              "ip.attrName AttrName, 'ida level props' Descriptions "
                              "from APP_IDAName i join app_idaprop ip " 
                              "on i.id = ip.componentnameid join app_credprops cred " 
                              "on cred.attrUserName = ip.attrName or " 
                              "cred.attrPwdName = ip.attrName " 
                              "where cred.tableId = 31 ",

        "backupset_prop_query": "select distinct bs.id EntityId, "
                                "6 EntityType, bsp.attrName AttrName,  " 
                                "'backupset level props' Descriptions, app.clientId from " 
                                "APP_BackupsetName bs join app_backupsetprop bsp on " 
                                "bs.id = bsp.componentnameid join app_credprops cred on " 
                                "cred.attrUserName = bsp.attrName or " 
                                "cred.attrPwdName = bsp.attrName join app_application app on " 
                                "app.backupSet = bs.id  where cred.tableId = 51",

        "instance_prop_query": "select distinct i.id EntityId, 5 EntityType, ip.attrName AttrName,  "
                                "'instance level props' Descriptions, app.clientId "
                                "from APP_InstanceName i join app_Instanceprop ip on "
                                "i.id = ip.componentnameid join app_credprops cred "
                                "on cred.attrUserName = ip.attrName or "
                                "cred.attrPwdName = ip.attrName join app_application app on "
                                "app.instance = i.id where cred.tableId = 41",

        "subclient_prop_query": "select a.id EntityId, 7 EntityType, sp.attrName AttrName, "
                                "'subclient level props' Descriptions, a.clientId from "
                                "APP_application a join app_subclientprop sp on "
                                "a.id = sp.componentnameid join app_credprops cred on "
                                "cred.attrUserName = sp.attrName or "
                                "cred.attrPwdName = sp.attrName where cred.tableId = 61 "
                                "order by EntityId"
    }


def statics_constant():
    """
    retruns statistics dictonary constant.
    """
    return {
            "ClientSessionWrapper::send()": {
                "cvd.exe": 0,
                "ifind.exe": 0,
                "clBackup.exe": 0,
                "CvPostOps.exe":0,
                "unknown": 0},
            "ClientSessionWrapper::receive()": {
                "cvd.exe": 0,
                "ifind.exe": 0,
                "clBackup.exe": 0,
                "CvPostOps.exe":0,
                "unknown": 0},
            }
