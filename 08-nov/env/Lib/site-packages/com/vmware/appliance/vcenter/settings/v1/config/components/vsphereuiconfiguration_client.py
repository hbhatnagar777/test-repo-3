# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.vsphereuiconfiguration.
#---------------------------------------------------------------------------

"""


"""

__author__ = 'VMware, Inc.'
__docformat__ = 'restructuredtext en'

import sys
from warnings import warn

from vmware.vapi.bindings import type
from vmware.vapi.bindings.converter import TypeConverter
from vmware.vapi.bindings.enum import Enum
from vmware.vapi.bindings.error import VapiError
from vmware.vapi.bindings.struct import VapiStruct
from vmware.vapi.bindings.stub import (
    ApiInterfaceStub, StubFactoryBase, VapiInterface)
from vmware.vapi.bindings.common import raise_core_exception
from vmware.vapi.data.validator import (UnionValidator, HasFieldsOfValidator)
from vmware.vapi.exception import CoreException
from vmware.vapi.lib.constants import TaskType
from vmware.vapi.lib.rest import OperationRestMetadata


class VsphereUIConfiguration(VapiStruct):
    """
    ``VsphereUIConfiguration`` class This spec is used to configure the
    behavior of the vsphere-ui service.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """



    _canonical_to_pep_names = {
                            'enable_IDP_configuration': 'enable_idp_configuration',
                            }

    def __init__(self,
                 enable_idp_configuration=None,
                 enable_cloud_admin_role_protection=None,
                 enable_deprecated_vc_alert=None,
                 enable_intercom_chat=None,
                 enable_file_browser_download_upload_from_vc=None,
                 enable_hybrid_management=None,
                 enable_ceip=None,
                 help_url_pointing_to_aws=None,
                 enable_ad_iwa_ids=None,
                 enable_csp_oidc_federation=None,
                ):
        """
        :type  enable_idp_configuration: :class:`bool` or ``None``
        :param enable_idp_configuration: Property to configure the IDPConfiguration view, with this enabled,
            user will be able to view and configure IDP
        :type  enable_cloud_admin_role_protection: :class:`bool` or ``None``
        :param enable_cloud_admin_role_protection: Property to enable CloudAdminRoleProtection in the UI
        :type  enable_deprecated_vc_alert: :class:`bool` or ``None``
        :param enable_deprecated_vc_alert: Property to enable DeprecatedVcAlert in the UI
        :type  enable_intercom_chat: :class:`bool` or ``None``
        :param enable_intercom_chat: Property to enable Intercom Chat in the UI
        :type  enable_file_browser_download_upload_from_vc: :class:`bool` or ``None``
        :param enable_file_browser_download_upload_from_vc: Property to enable file browser download and upload from VC
        :type  enable_hybrid_management: :class:`bool` or ``None``
        :param enable_hybrid_management: Property to enable hybrid management view.
        :type  enable_ceip: :class:`bool` or ``None``
        :param enable_ceip: Property to enable CEIP view from Administration -> Deployment.
        :type  help_url_pointing_to_aws: :class:`bool` or ``None``
        :param help_url_pointing_to_aws: Property that indicates that Help url should point to url for AWS.
        :type  enable_ad_iwa_ids: :class:`bool` or ``None``
        :param enable_ad_iwa_ids: Property that indicates Identity Source of type IWA should be
            enabled.
        :type  enable_csp_oidc_federation: :class:`bool` or ``None``
        :param enable_csp_oidc_federation: Property that indicates CSP OIDC identity provider configured in
            vCenter.
        """
        self.enable_idp_configuration = enable_idp_configuration
        self.enable_cloud_admin_role_protection = enable_cloud_admin_role_protection
        self.enable_deprecated_vc_alert = enable_deprecated_vc_alert
        self.enable_intercom_chat = enable_intercom_chat
        self.enable_file_browser_download_upload_from_vc = enable_file_browser_download_upload_from_vc
        self.enable_hybrid_management = enable_hybrid_management
        self.enable_ceip = enable_ceip
        self.help_url_pointing_to_aws = help_url_pointing_to_aws
        self.enable_ad_iwa_ids = enable_ad_iwa_ids
        self.enable_csp_oidc_federation = enable_csp_oidc_federation
        VapiStruct.__init__(self)


VsphereUIConfiguration._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.vsphereuiconfiguration.vsphere_UI_configuration', {
        'enable_IDP_configuration': type.OptionalType(type.BooleanType()),
        'enable_cloud_admin_role_protection': type.OptionalType(type.BooleanType()),
        'enable_deprecated_vc_alert': type.OptionalType(type.BooleanType()),
        'enable_intercom_chat': type.OptionalType(type.BooleanType()),
        'enable_file_browser_download_upload_from_vc': type.OptionalType(type.BooleanType()),
        'enable_hybrid_management': type.OptionalType(type.BooleanType()),
        'enable_ceip': type.OptionalType(type.BooleanType()),
        'help_url_pointing_to_aws': type.OptionalType(type.BooleanType()),
        'enable_ad_iwa_ids': type.OptionalType(type.BooleanType()),
        'enable_csp_oidc_federation': type.OptionalType(type.BooleanType()),
    },
    VsphereUIConfiguration,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

