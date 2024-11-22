# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by Multicommcell related operations."""

USERNAME = 'test1_user'
"""str: Username to create user"""

PASSWORD = '######'
"""str: Password to create Non-Admin user."""


class WebRoutingConfig:
    """All constants for testing web routing feature"""
    DB_USERNAME = ''
    DB_PASSWORD = ''
    RDP_USERNAME = ''
    RDP_PASSWORD = ''
    CS_USERNAME = ''
    CS_PASSWORD = ''
    SERVICE_HOSTNAME = ''

    SERVICE_AD_CREDS = {
        "ad_name": "",
        "ad_hostname": "",
        "ad_username": "",
        "ad_password": "",
        "master_username": "",
        "master_password": "",
        "master_email": ""
    }
    COMMON_AD_CREDS = {
        "ad_name": "",
        "ad_hostname": "",
        "ad_username": "",
        "ad_password": "",
        "master_username": "",
        "master_password": "",
        "master_email": ""
    }
    ROUTER_AD_CREDS = {
        "ad_name": "",
        "ad_hostname": "",
        "ad_username": "",
        "ad_password": "",
        "master_username": "",
        "master_password": "",
        "master_email": ""
    }
    SAML_CREDS = {
        "app_name": "",
        "idpmetadata_xml_path": "",
        "email_suffixes": [""],
        "saml_username": "",
        "saml_password": "",
        "saml_email": ""
    }
    DEFAULT_PASSWORD = ''


class RingRoutingConfig:
    """All constants for testing Ring Routing feature"""
    DB_USERNAME = ''
    DB_PASSWORD = ''
    RDP_USERNAME = ''
    RDP_PASSWORD = ''
    CS_USERNAME = ''
    CS_PASSWORD = ''
    DEFAULT_PASSWORD = ''
    SERVICE_COMMCELLS = []
    PLAN = ''
    RESELLER_IDP = ''
    RESELLER_WORKLOADS = []
    CHILD_IDP = ''
    CHILD_WORKLOADS = []
