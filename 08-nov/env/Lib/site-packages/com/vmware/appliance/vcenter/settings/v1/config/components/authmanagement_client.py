# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.
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

class IdentitySourceType(Enum):
    """
    The ``IdentitySourceType`` class contains the possible Identity Source
    Types. **Warning:** This enumeration is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    AD_OVER_IWA = None
    """
    Active Directory (Integrated Windows Authentication). **Warning:** This
    class attribute is available as Technology Preview. These are early access
    APIs provided to test, automate and provide feedback on the feature. Since
    this can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    """
    AD_OVER_LDAP = None
    """
    Active Directory over LDAP. **Warning:** This class attribute is available
    as Technology Preview. These are early access APIs provided to test,
    automate and provide feedback on the feature. Since this can change based
    on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    """
    OPEN_LDAP = None
    """
    Open LDAP. **Warning:** This class attribute is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    """
    IDP_ADFS = None
    """
    Active Directory Federation Services (Microsoft ADFS). **Warning:** This
    class attribute is available as Technology Preview. These are early access
    APIs provided to test, automate and provide feedback on the feature. Since
    this can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    """
    IDP_CSP = None
    """
    VMware Cloud Services Platform. **Warning:** This class attribute is
    available as Technology Preview. These are early access APIs provided to
    test, automate and provide feedback on the feature. Since this can change
    based on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    """
    IDP_WS1B = None
    """
    VMware Workspace ONE Broker. **Warning:** This class attribute is available
    as Technology Preview. These are early access APIs provided to test,
    automate and provide feedback on the feature. Since this can change based
    on feedback, VMware does not guarantee backwards compatibility and
    recommends against using them in production environments. Some Technology
    Preview APIs might only be applicable to specific environments.

    """
    IDP_VMWAREID = None
    """
    Oauth2 for MyVMwareId. **Warning:** This class attribute is available as
    Technology Preview. These are early access APIs provided to test, automate
    and provide feedback on the feature. Since this can change based on
    feedback, VMware does not guarantee backwards compatibility and recommends
    against using them in production environments. Some Technology Preview APIs
    might only be applicable to specific environments.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`IdentitySourceType` instance.
        """
        Enum.__init__(string)

IdentitySourceType._set_values({
    'AD_OVER_IWA': IdentitySourceType('AD_OVER_IWA'),
    'AD_OVER_LDAP': IdentitySourceType('AD_OVER_LDAP'),
    'OPEN_LDAP': IdentitySourceType('OPEN_LDAP'),
    'IDP_ADFS': IdentitySourceType('IDP_ADFS'),
    'IDP_CSP': IdentitySourceType('IDP_CSP'),
    'IDP_WS1B': IdentitySourceType('IDP_WS1B'),
    'IDP_VMWAREID': IdentitySourceType('IDP_VMWAREID'),
})
IdentitySourceType._set_binding_type(type.EnumType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.identity_source_type',
    IdentitySourceType))




class AuthenticationManagement(VapiStruct):
    """
    ``AuthenticationManagement`` class This structure contains the Spec
    required for Authentication Management configurations. **Warning:** This
    class is available as Technology Preview. These are early access APIs
    provided to test, automate and provide feedback on the feature. Since this
    can change based on feedback, VMware does not guarantee backwards
    compatibility and recommends against using them in production environments.
    Some Technology Preview APIs might only be applicable to specific
    environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 version=None,
                 privileges=None,
                 global_permissions=None,
                 roles=None,
                 vc_groups=None,
                 identity_sources=None,
                 password_policy=None,
                 token_policy=None,
                 lockout_policy=None,
                ):
        """
        :type  version: :class:`str`
        :param version: The version of authorization management this configuration is
            applicable to. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  privileges: :class:`list` of :class:`Privileges` or ``None``
        :param privileges: List of Privileges. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  global_permissions: :class:`list` of :class:`GlobalPermission`
        :param global_permissions: List of Global Permission. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  roles: :class:`list` of :class:`Roles`
        :param roles: List of Roles. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  vc_groups: :class:`list` of :class:`VCGroups`
        :param vc_groups: List of VCGroups. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  identity_sources: :class:`list` of :class:`IdentitySource` or ``None``
        :param identity_sources: List of Identity Sources added to VC. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  password_policy: :class:`PasswordPolicy` or ``None``
        :param password_policy: Password Policy. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  token_policy: :class:`TokenPolicy` or ``None``
        :param token_policy: Token Policy. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  lockout_policy: :class:`LockoutPolicy` or ``None``
        :param lockout_policy: Lockout Policy. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        """
        self.version = version
        self.privileges = privileges
        self.global_permissions = global_permissions
        self.roles = roles
        self.vc_groups = vc_groups
        self.identity_sources = identity_sources
        self.password_policy = password_policy
        self.token_policy = token_policy
        self.lockout_policy = lockout_policy
        VapiStruct.__init__(self)


AuthenticationManagement._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.authentication_management', {
        'version': type.StringType(),
        'privileges': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'Privileges'))),
        'global_permissions': type.ListType(type.ReferenceType(__name__, 'GlobalPermission')),
        'roles': type.ListType(type.ReferenceType(__name__, 'Roles')),
        'vc_groups': type.ListType(type.ReferenceType(__name__, 'VCGroups')),
        'identity_sources': type.OptionalType(type.ListType(type.ReferenceType(__name__, 'IdentitySource'))),
        'password_policy': type.OptionalType(type.ReferenceType(__name__, 'PasswordPolicy')),
        'token_policy': type.OptionalType(type.ReferenceType(__name__, 'TokenPolicy')),
        'lockout_policy': type.OptionalType(type.ReferenceType(__name__, 'LockoutPolicy')),
    },
    AuthenticationManagement,
    False,
    None))



class LockoutPolicy(VapiStruct):
    """
    ``LockoutPolicy`` class This structure represents the configuration in
    Lockout Policy. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 failed_login_attempts=None,
                 failure_interval=None,
                 unlock_time=None,
                ):
        """
        :type  failed_login_attempts: :class:`long`
        :param failed_login_attempts: Maximum number of failed login attempts. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  failure_interval: :class:`long`
        :param failure_interval: Time interval between failures. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  unlock_time: :class:`long`
        :param unlock_time: Unlock time. **Warning:** This attribute is available as Technology
            Preview. These are early access APIs provided to test, automate and
            provide feedback on the feature. Since this can change based on
            feedback, VMware does not guarantee backwards compatibility and
            recommends against using them in production environments. Some
            Technology Preview APIs might only be applicable to specific
            environments.
        """
        self.failed_login_attempts = failed_login_attempts
        self.failure_interval = failure_interval
        self.unlock_time = unlock_time
        VapiStruct.__init__(self)


LockoutPolicy._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.lockout_policy', {
        'failed_login_attempts': type.IntegerType(),
        'failure_interval': type.IntegerType(),
        'unlock_time': type.IntegerType(),
    },
    LockoutPolicy,
    False,
    None))



class PasswordPolicy(VapiStruct):
    """
    ``PasswordPolicy`` class This structure represents the configuration in
    Password Policy. **Warning:** This class is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 special_chars=None,
                 alpha_chars=None,
                 uppercase_chars=None,
                 lowercase_chars=None,
                 numeric_chars=None,
                 adj_identical_chars=None,
                 password_reuse=None,
                 max_life=None,
                 max_length=None,
                 min_length=None,
                ):
        """
        :type  special_chars: :class:`long`
        :param special_chars: Minimum special characters. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  alpha_chars: :class:`long`
        :param alpha_chars: Minimum alphabetic characters. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  uppercase_chars: :class:`long`
        :param uppercase_chars: Minimum uppercase characters. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  lowercase_chars: :class:`long`
        :param lowercase_chars: Minimum lowercase characters. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  numeric_chars: :class:`long`
        :param numeric_chars: Minimum numeric characters. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  adj_identical_chars: :class:`long`
        :param adj_identical_chars: Maximum adjacent identical characters. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  password_reuse: :class:`long`
        :param password_reuse: Previous password reuse restriction. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  max_life: :class:`long`
        :param max_life: Maximum lifetime. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  max_length: :class:`long`
        :param max_length: Maximum length. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  min_length: :class:`long`
        :param min_length: Minimum length. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        """
        self.special_chars = special_chars
        self.alpha_chars = alpha_chars
        self.uppercase_chars = uppercase_chars
        self.lowercase_chars = lowercase_chars
        self.numeric_chars = numeric_chars
        self.adj_identical_chars = adj_identical_chars
        self.password_reuse = password_reuse
        self.max_life = max_life
        self.max_length = max_length
        self.min_length = min_length
        VapiStruct.__init__(self)


PasswordPolicy._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.password_policy', {
        'special_chars': type.IntegerType(),
        'alpha_chars': type.IntegerType(),
        'uppercase_chars': type.IntegerType(),
        'lowercase_chars': type.IntegerType(),
        'numeric_chars': type.IntegerType(),
        'adj_identical_chars': type.IntegerType(),
        'password_reuse': type.IntegerType(),
        'max_life': type.IntegerType(),
        'max_length': type.IntegerType(),
        'min_length': type.IntegerType(),
    },
    PasswordPolicy,
    False,
    None))



class TokenPolicy(VapiStruct):
    """
    ``TokenPolicy`` class This structure represents the configuration in Token
    Policy. **Warning:** This class is available as Technology Preview. These
    are early access APIs provided to test, automate and provide feedback on
    the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 clock_tolerance=None,
                 token_renewal=None,
                 token_delegation=None,
                 bearer_refresh=None,
                 hok_refresh=None,
                ):
        """
        :type  clock_tolerance: :class:`long`
        :param clock_tolerance: Clock tolerance ms. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  token_renewal: :class:`long`
        :param token_renewal: Maximum token renewal count. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  token_delegation: :class:`long`
        :param token_delegation: Maximum token delegation count. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  bearer_refresh: :class:`long`
        :param bearer_refresh: Maximum Bearer RefreshToken lifetime. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  hok_refresh: :class:`long`
        :param hok_refresh: Maximum HoK RefreshToken lifetime. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.clock_tolerance = clock_tolerance
        self.token_renewal = token_renewal
        self.token_delegation = token_delegation
        self.bearer_refresh = bearer_refresh
        self.hok_refresh = hok_refresh
        VapiStruct.__init__(self)


TokenPolicy._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.token_policy', {
        'clock_tolerance': type.IntegerType(),
        'token_renewal': type.IntegerType(),
        'token_delegation': type.IntegerType(),
        'bearer_refresh': type.IntegerType(),
        'hok_refresh': type.IntegerType(),
    },
    TokenPolicy,
    False,
    None))



class Privileges(VapiStruct):
    """
    ``Privileges`` class This structure represents the configuration for
    Privileges. **Warning:** This class is available as Technology Preview.
    These are early access APIs provided to test, automate and provide feedback
    on the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 id=None,
                 description=None,
                 group=None,
                 is_on_parent=None,
                ):
        """
        :type  id: :class:`str`
        :param id: Privilege identifier. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  description: :class:`str` or ``None``
        :param description: Privilege description. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  group: :class:`str`
        :param group: Group to which the privilege belongs to. **Warning:** This
            attribute is available as Technology Preview. These are early
            access APIs provided to test, automate and provide feedback on the
            feature. Since this can change based on feedback, VMware does not
            guarantee backwards compatibility and recommends against using them
            in production environments. Some Technology Preview APIs might only
            be applicable to specific environments.
        :type  is_on_parent: :class:`bool`
        :param is_on_parent: does this apply to the parent entity?. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.id = id
        self.description = description
        self.group = group
        self.is_on_parent = is_on_parent
        VapiStruct.__init__(self)


Privileges._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.privileges', {
        'id': type.StringType(),
        'description': type.OptionalType(type.StringType()),
        'group': type.StringType(),
        'is_on_parent': type.BooleanType(),
    },
    Privileges,
    False,
    None))



class Roles(VapiStruct):
    """
    ``Roles`` class This structure represents the configuration for Roles.
    **Warning:** This class is available as Technology Preview. These are early
    access APIs provided to test, automate and provide feedback on the feature.
    Since this can change based on feedback, VMware does not guarantee
    backwards compatibility and recommends against using them in production
    environments. Some Technology Preview APIs might only be applicable to
    specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 id=None,
                 name=None,
                 description=None,
                 privilege_ids=None,
                ):
        """
        :type  id: :class:`long` or ``None``
        :param id: Role identifier. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  name: :class:`str`
        :param name: Role name which is unique across roles. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  description: :class:`str` or ``None``
        :param description: Role description. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  privilege_ids: :class:`list` of :class:`str` or ``None``
        :param privilege_ids: List of Privileges present in the Role. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.id = id
        self.name = name
        self.description = description
        self.privilege_ids = privilege_ids
        VapiStruct.__init__(self)


Roles._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.roles', {
        'id': type.OptionalType(type.IntegerType()),
        'name': type.StringType(),
        'description': type.OptionalType(type.StringType()),
        'privilege_ids': type.OptionalType(type.ListType(type.StringType())),
    },
    Roles,
    False,
    None))



class VCGroups(VapiStruct):
    """
    ``VCGroups`` class This structure represents the configuration for
    VCGroups. **Warning:** This class is available as Technology Preview. These
    are early access APIs provided to test, automate and provide feedback on
    the feature. Since this can change based on feedback, VMware does not
    guarantee backwards compatibility and recommends against using them in
    production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 principal=None,
                 description=None,
                 members=None,
                ):
        """
        :type  principal: :class:`str`
        :param principal: Unique name of the VC group. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  description: :class:`str` or ``None``
        :param description: VCGroup description. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  members: :class:`list` of :class:`com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client.Principal` or ``None``
        :param members: List of members present in the vcGroup. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.principal = principal
        self.description = description
        self.members = members
        VapiStruct.__init__(self)


VCGroups._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.VC_groups', {
        'principal': type.StringType(),
        'description': type.OptionalType(type.StringType()),
        'members': type.OptionalType(type.ListType(type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client', 'Principal'))),
    },
    VCGroups,
    False,
    None))



class GlobalPermission(VapiStruct):
    """
    ``GlobalPermissions`` class This structure represents the configuration for
    Global Permissions. **Warning:** This class is available as Technology
    Preview. These are early access APIs provided to test, automate and provide
    feedback on the feature. Since this can change based on feedback, VMware
    does not guarantee backwards compatibility and recommends against using
    them in production environments. Some Technology Preview APIs might only be
    applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 principal=None,
                 role_ids=None,
                 role_names=None,
                 propagate=None,
                ):
        """
        :type  principal: :class:`com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client.Principal`
        :param principal: Principal with roles. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  role_ids: :class:`list` of :class:`long` or ``None``
        :param role_ids: Role Ids assigned to this Principal. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  role_names: :class:`list` of :class:`str`
        :param role_names: Role Names assigned to this Principal. **Warning:** This attribute
            is available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        :type  propagate: :class:`bool`
        :param propagate: Propagating to child objects. **Warning:** This attribute is
            available as Technology Preview. These are early access APIs
            provided to test, automate and provide feedback on the feature.
            Since this can change based on feedback, VMware does not guarantee
            backwards compatibility and recommends against using them in
            production environments. Some Technology Preview APIs might only be
            applicable to specific environments.
        """
        self.principal = principal
        self.role_ids = role_ids
        self.role_names = role_names
        self.propagate = propagate
        VapiStruct.__init__(self)


GlobalPermission._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.global_permission', {
        'principal': type.ReferenceType('com.vmware.appliance.vcenter.settings.v1.config.components.authcommon_client', 'Principal'),
        'role_ids': type.OptionalType(type.ListType(type.IntegerType())),
        'role_names': type.ListType(type.StringType()),
        'propagate': type.BooleanType(),
    },
    GlobalPermission,
    False,
    None))



class IdentitySource(VapiStruct):
    """
    ``IdentitySource`` class This structure represents the configuration for
    Identity Source present in vCenter. **Warning:** This class is available as
    Technology Preview. These are early access APIs provided to test, automate
    and provide feedback on the feature. Since this can change based on
    feedback, VMware does not guarantee backwards compatibility and recommends
    against using them in production environments. Some Technology Preview APIs
    might only be applicable to specific environments.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 identity_source_type=None,
                 names=None,
                 alias=None,
                ):
        """
        :type  identity_source_type: :class:`IdentitySourceType`
        :param identity_source_type: Identity Source Type. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  names: :class:`list` of :class:`str`
        :param names: Identity Source name. **Warning:** This attribute is available as
            Technology Preview. These are early access APIs provided to test,
            automate and provide feedback on the feature. Since this can change
            based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        :type  alias: :class:`str` or ``None``
        :param alias: Alias for Identity Source. **Warning:** This attribute is available
            as Technology Preview. These are early access APIs provided to
            test, automate and provide feedback on the feature. Since this can
            change based on feedback, VMware does not guarantee backwards
            compatibility and recommends against using them in production
            environments. Some Technology Preview APIs might only be applicable
            to specific environments.
        """
        self.identity_source_type = identity_source_type
        self.names = names
        self.alias = alias
        VapiStruct.__init__(self)


IdentitySource._set_binding_type(type.StructType(
    'com.vmware.appliance.vcenter.settings.v1.config.components.authmanagement.identity_source', {
        'identity_source_type': type.ReferenceType(__name__, 'IdentitySourceType'),
        'names': type.ListType(type.StringType()),
        'alias': type.OptionalType(type.StringType()),
    },
    IdentitySource,
    False,
    None))




class StubFactory(StubFactoryBase):
    _attrs = {
    }

