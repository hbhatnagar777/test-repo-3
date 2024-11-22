# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.namespace_management.supervisors.identity.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.namespace_management.supervisors.identity_client``
module provides classes related to identity management for a Supervisor.

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


class Providers(VapiInterface):
    """
    The ``Providers`` class provides methods to configure identity management
    on a Supervisor. This class was added in vSphere API 8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.namespace_management.supervisors.identity.providers'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ProvidersStub)
        self._VAPI_OPERATION_IDS = {}

    class Summary(VapiStruct):
        """
        The ``Providers.Summary`` class provides an overview of an identity
        provider configured for the given Supervisor. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     provider=None,
                     display_name=None,
                    ):
            """
            :type  provider: :class:`str`
            :param provider: The immutable identifier of an identity provider generated when an
                identity provider is registered for a Supervisor. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
            :type  display_name: :class:`str`
            :param display_name: A name to be used for the given identity provider. This name will
                be displayed in the vCenter UI. This attribute was added in vSphere
                API 8.0.0.1.
            """
            self.provider = provider
            self.display_name = display_name
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.identity.providers.summary', {
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
            'display_name': type.StringType(),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``Providers.Info`` class provides details about an identity provider
        configured with a Supervisor. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'issuer_URL': 'issuer_url',
                                'client_ID': 'client_id',
                                }

        def __init__(self,
                     provider=None,
                     display_name=None,
                     issuer_url=None,
                     username_claim=None,
                     groups_claim=None,
                     client_id=None,
                     certificate_authority_data=None,
                     additional_scopes=None,
                     additional_authorize_parameters=None,
                    ):
            """
            :type  provider: :class:`str`
            :param provider: The immutable identifier of an identity provider generated when an
                identity provider is registered for a Supervisor. This attribute
                was added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``. When
                methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.namespace_management.identity.Provider``.
            :type  display_name: :class:`str`
            :param display_name: A name to be used for the given identity provider. This name will
                be displayed in the vCenter UI. This attribute was added in vSphere
                API 8.0.0.1.
            :type  issuer_url: :class:`str`
            :param issuer_url: The URL to the identity provider issuing tokens. The OIDC discovery
                URL will be derived from the issuer URL, according to `RFC8414
                <https://datatracker.ietf.org/doc/html/rfc8414>`_:
                https://issuerURL/.well-known/openid-configuration. This must use
                HTTPS as the scheme. This attribute was added in vSphere API
                8.0.0.1.
            :type  username_claim: :class:`str` or ``None``
            :param username_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the username for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, the upstream issuer URL will be concatenated with the
                'sub' claim to generate the username to be used with Kubernetes.
            :type  groups_claim: :class:`str` or ``None``
            :param groups_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the groups for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, no groups will be used from the upstream identity
                provider.
            :type  client_id: :class:`str`
            :param client_id: The clientID is the OAuth 2.0 client ID registered in the upstream
                identity provider and used by the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
            :type  certificate_authority_data: :class:`str` or ``None``
            :param certificate_authority_data: The certificate authority data holds the trusted roots to be used
                to establish HTTPS connections with the identity provider. This
                attribute was added in vSphere API 8.0.0.1.
                If None, HTTPS connections with the upstream identity provider will
                rely on a default set of system trusted roots.
            :type  additional_scopes: :class:`list` of :class:`str` or ``None``
            :param additional_scopes: Additional scopes to be requested in tokens issued by this identity
                provider. The 'openid' scope will always be requested. This
                attribute was added in vSphere API 8.0.0.1.
                If None, no additional scopes will be requested.
            :type  additional_authorize_parameters: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param additional_authorize_parameters: Any additional parameters to be sent to the upstream identity
                provider during the authorize request in the OAuth2 authorization
                code flow. One use case is to pass in a default tenant ID if you
                have a multi-tenant identity provider. For instance, with VMware's
                Cloud Services Platform, if your organization ID is
                'long-form-org-id', the 'orgLink' parameter can be set to
                "/csp/gateway/am/api/orgs/long-form-org-id" to allow users logging
                in to leverage that organization. This attribute was added in
                vSphere API 8.0.0.1.
                If None, no additional parameters will be sent to the upstream
                identity provider.
            """
            self.provider = provider
            self.display_name = display_name
            self.issuer_url = issuer_url
            self.username_claim = username_claim
            self.groups_claim = groups_claim
            self.client_id = client_id
            self.certificate_authority_data = certificate_authority_data
            self.additional_scopes = additional_scopes
            self.additional_authorize_parameters = additional_authorize_parameters
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.identity.providers.info', {
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
            'display_name': type.StringType(),
            'issuer_URL': type.StringType(),
            'username_claim': type.OptionalType(type.StringType()),
            'groups_claim': type.OptionalType(type.StringType()),
            'client_ID': type.StringType(),
            'certificate_authority_data': type.OptionalType(type.StringType()),
            'additional_scopes': type.OptionalType(type.ListType(type.StringType())),
            'additional_authorize_parameters': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
        },
        Info,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``Providers.CreateSpec`` class is used to register a new upstream
        identity provider for use with a Supervisor. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'issuer_URL': 'issuer_url',
                                'client_ID': 'client_id',
                                }

        def __init__(self,
                     display_name=None,
                     issuer_url=None,
                     username_claim=None,
                     groups_claim=None,
                     client_id=None,
                     client_secret=None,
                     certificate_authority_data=None,
                     additional_scopes=None,
                     additional_authorize_parameters=None,
                    ):
            """
            :type  display_name: :class:`str`
            :param display_name: A name to be used for the given identity provider. This name will
                be displayed in the vCenter UI. This attribute was added in vSphere
                API 8.0.0.1.
            :type  issuer_url: :class:`str`
            :param issuer_url: The URL to the identity provider issuing tokens. The OIDC discovery
                URL will be derived from the issuer URL, according to `RFC8414
                <https://datatracker.ietf.org/doc/html/rfc8414>`_:
                https://issuerURL/.well-known/openid-configuration. This must use
                HTTPS as the scheme. This attribute was added in vSphere API
                8.0.0.1.
            :type  username_claim: :class:`str` or ``None``
            :param username_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the username for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, the upstream issuer URL will be concatenated with the
                'sub' claim to generate the username to be used with Kubernetes.
            :type  groups_claim: :class:`str` or ``None``
            :param groups_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the groups for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, no groups will be used from the upstream identity
                provider.
            :type  client_id: :class:`str`
            :param client_id: The clientID is the OAuth 2.0 client ID registered in the upstream
                identity provider and used by the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
            :type  client_secret: :class:`str`
            :param client_secret: The OAuth 2.0 client secret to be used by the Supervisor when
                authenticating to the upstream identity provider. This attribute
                was added in vSphere API 8.0.0.1.
            :type  certificate_authority_data: :class:`str` or ``None``
            :param certificate_authority_data: Certificate authority data to be used to establish HTTPS
                connections with the identity provider. This must be a PEM-encoded
                value. This attribute was added in vSphere API 8.0.0.1.
                If None, HTTPS connections with the upstream identity provider will
                rely on a default set of system trusted roots.
            :type  additional_scopes: :class:`list` of :class:`str` or ``None``
            :param additional_scopes: Additional scopes to be requested in tokens issued by this identity
                provider. This attribute was added in vSphere API 8.0.0.1.
                If None, no additional scopes will be requested.
            :type  additional_authorize_parameters: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param additional_authorize_parameters: Any additional parameters to be sent to the upstream identity
                provider during the authorize request in the OAuth2 authorization
                code flow. One use case is to pass in a default tenant ID if you
                have a multi-tenant identity provider. For instance, with VMware's
                Cloud Services Platform, if your organization ID is
                'long-form-org-id', the 'orgLink' parameter can be set to
                "/csp/gateway/am/api/orgs/long-form-org-id" to allow users logging
                in to leverage that organization. This attribute was added in
                vSphere API 8.0.0.1.
                If None, no additional parameters will be sent to the upstream
                identity provider.
            """
            self.display_name = display_name
            self.issuer_url = issuer_url
            self.username_claim = username_claim
            self.groups_claim = groups_claim
            self.client_id = client_id
            self.client_secret = client_secret
            self.certificate_authority_data = certificate_authority_data
            self.additional_scopes = additional_scopes
            self.additional_authorize_parameters = additional_authorize_parameters
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.identity.providers.create_spec', {
            'display_name': type.StringType(),
            'issuer_URL': type.StringType(),
            'username_claim': type.OptionalType(type.StringType()),
            'groups_claim': type.OptionalType(type.StringType()),
            'client_ID': type.StringType(),
            'client_secret': type.SecretType(),
            'certificate_authority_data': type.OptionalType(type.StringType()),
            'additional_scopes': type.OptionalType(type.ListType(type.StringType())),
            'additional_authorize_parameters': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
        },
        CreateSpec,
        False,
        None))


    class SetSpec(VapiStruct):
        """
        The ``Providers.SetSpec`` class is used to fully replace the configuration
        of an upstream identity provider for use with a Supervisor. This class was
        added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'issuer_URL': 'issuer_url',
                                'client_ID': 'client_id',
                                }

        def __init__(self,
                     display_name=None,
                     issuer_url=None,
                     username_claim=None,
                     groups_claim=None,
                     client_id=None,
                     client_secret=None,
                     certificate_authority_data=None,
                     additional_scopes=None,
                     additional_authorize_parameters=None,
                    ):
            """
            :type  display_name: :class:`str`
            :param display_name: A name to be used for the given identity provider. This name will
                be displayed in the vCenter UI. This attribute was added in vSphere
                API 8.0.0.1.
            :type  issuer_url: :class:`str`
            :param issuer_url: The URL to the identity provider issuing tokens. The OIDC discovery
                URL will be derived from the issuer URL, according to `RFC8414
                <https://datatracker.ietf.org/doc/html/rfc8414>`_:
                https://issuerURL/.well-known/openid-configuration. This must use
                HTTPS as the scheme. This attribute was added in vSphere API
                8.0.0.1.
            :type  username_claim: :class:`str` or ``None``
            :param username_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the username for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, the upstream issuer URL will be concatenated with the
                'sub' claim to generate the username to be used with Kubernetes.
            :type  groups_claim: :class:`str` or ``None``
            :param groups_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the groups for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, no groups will be used from the upstream identity
                provider.
            :type  client_id: :class:`str`
            :param client_id: The clientID is the OAuth 2.0 client ID registered in the upstream
                identity provider and used by the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
            :type  client_secret: :class:`str`
            :param client_secret: The OAuth 2.0 client secret to be used by the Supervisor when
                authenticating to the upstream identity provider. This attribute
                was added in vSphere API 8.0.0.1.
            :type  certificate_authority_data: :class:`str` or ``None``
            :param certificate_authority_data: Certificate authority data to be used to establish HTTPS
                connections with the identity provider. This must be a PEM-encoded
                value. This attribute was added in vSphere API 8.0.0.1.
                If None, HTTPS connections with the upstream identity provider will
                rely on a default set of system trusted roots.
            :type  additional_scopes: :class:`list` of :class:`str` or ``None``
            :param additional_scopes: Additional scopes to be requested in tokens issued by this identity
                provider. This attribute was added in vSphere API 8.0.0.1.
                If None, no additional scopes will be requested.
            :type  additional_authorize_parameters: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param additional_authorize_parameters: Any additional parameters to be sent to the upstream identity
                provider during the authorize request in the OAuth2 authorization
                code flow. One use case is to pass in a default tenant ID if you
                have a multi-tenant identity provider. For instance, with VMware's
                Cloud Services Platform, if your organization ID is
                'long-form-org-id', the 'orgLink' parameter can be set to
                "/csp/gateway/am/api/orgs/long-form-org-id" to allow users logging
                in to leverage that organization. This attribute was added in
                vSphere API 8.0.0.1.
                If None, no additional parameters will be sent to the upstream
                identity provider.
            """
            self.display_name = display_name
            self.issuer_url = issuer_url
            self.username_claim = username_claim
            self.groups_claim = groups_claim
            self.client_id = client_id
            self.client_secret = client_secret
            self.certificate_authority_data = certificate_authority_data
            self.additional_scopes = additional_scopes
            self.additional_authorize_parameters = additional_authorize_parameters
            VapiStruct.__init__(self)


    SetSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.identity.providers.set_spec', {
            'display_name': type.StringType(),
            'issuer_URL': type.StringType(),
            'username_claim': type.OptionalType(type.StringType()),
            'groups_claim': type.OptionalType(type.StringType()),
            'client_ID': type.StringType(),
            'client_secret': type.SecretType(),
            'certificate_authority_data': type.OptionalType(type.StringType()),
            'additional_scopes': type.OptionalType(type.ListType(type.StringType())),
            'additional_authorize_parameters': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
        },
        SetSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Providers.UpdateSpec`` class contains the specification required to
        update the configuration of an identity provider used with a Supervisor.
        This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """



        _canonical_to_pep_names = {
                                'issuer_URL': 'issuer_url',
                                'client_ID': 'client_id',
                                }

        def __init__(self,
                     display_name=None,
                     issuer_url=None,
                     username_claim=None,
                     unset_username_claim=None,
                     groups_claim=None,
                     unset_groups_claim=None,
                     client_id=None,
                     client_secret=None,
                     certificate_authority_data=None,
                     unset_certificate_authority_data=None,
                     additional_scopes=None,
                     additional_authorize_parameters=None,
                    ):
            """
            :type  display_name: :class:`str` or ``None``
            :param display_name: A name to be used for the given identity provider. This name will
                be displayed in the vCenter UI. This attribute was added in vSphere
                API 8.0.0.1.
                if None, the name will remained unchanged.
            :type  issuer_url: :class:`str` or ``None``
            :param issuer_url: The URL to the identity provider issuing tokens. The OIDC discovery
                URL will be derived from the issuer URL, according to `RFC8414
                <https://datatracker.ietf.org/doc/html/rfc8414>`_:
                https://issuerURL/.well-known/openid-configuration. This must use
                HTTPS as the scheme. This attribute was added in vSphere API
                8.0.0.1.
                If None, the issuer URL will not be updated.
            :type  username_claim: :class:`str` or ``None``
            :param username_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the username for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, the username claim will not be updated.
            :type  unset_username_claim: :class:`bool` or ``None``
            :param unset_username_claim: This represents the intent of the change to
                :attr:`Providers.UpdateSpec.username_claim`. If this field is set
                to ``true``, the existing 'usernameClaim' value will be removed. If
                this field is set to ``false``, the existing username claim will be
                changed to the value specified in
                :attr:`Providers.UpdateSpec.username_claim`, if any. This attribute
                was added in vSphere API 8.0.0.1.
                If None, the existing 'usernameClaim' value will be changed to the
                value specified in :attr:`Providers.UpdateSpec.username_claim`, if
                any.
            :type  groups_claim: :class:`str` or ``None``
            :param groups_claim: The claim from the upstream identity provider ID token or user info
                endpoint to inspect to obtain the groups for the given user. This
                attribute was added in vSphere API 8.0.0.1.
                If None, the groups claim will not be updated.
            :type  unset_groups_claim: :class:`bool` or ``None``
            :param unset_groups_claim: This represents the intent of the change to
                :attr:`Providers.UpdateSpec.groups_claim`. If this field is set to
                ``true``, the existing 'groupsClaim' value will be removed. If this
                field is set to ``false``, the existing groups claim will be
                changed to the value specified in
                :attr:`Providers.UpdateSpec.groups_claim`, if any. This attribute
                was added in vSphere API 8.0.0.1.
                If None, the existing 'groupsClaim' value will be changed to the
                value specified in :attr:`Providers.UpdateSpec.groups_claim`, if
                any.
            :type  client_id: :class:`str` or ``None``
            :param client_id: The clientID is the OAuth 2.0 client ID registered in the upstream
                identity provider and used by the Supervisor. This attribute was
                added in vSphere API 8.0.0.1.
                If None, the client ID will not be updated.
            :type  client_secret: :class:`str` or ``None``
            :param client_secret: The OAuth 2.0 client secret to be used by the Supervisor when
                authenticating to the upstream identity provider. This attribute
                was added in vSphere API 8.0.0.1.
                If None, the client secret will not be updated.
            :type  certificate_authority_data: :class:`str` or ``None``
            :param certificate_authority_data: Certificate authority data to be used to establish HTTPS
                connections with the identity provider. This must be a PEM-encoded
                value. This attribute was added in vSphere API 8.0.0.1.
                If None, the certificate authority data will not be updated.
            :type  unset_certificate_authority_data: :class:`bool` or ``None``
            :param unset_certificate_authority_data: This represents the intent of the change to
                :attr:`Providers.UpdateSpec.certificate_authority_data`. If this
                field is set to ``true``, the existing 'certificateAuthorityData'
                value will be removed. If this field is set to ``false``, the
                existing certificate authority data will be changed to the value
                specified in
                :attr:`Providers.UpdateSpec.certificate_authority_data`, if any.
                This attribute was added in vSphere API 8.0.0.1.
                If None, the existing 'certificateAuthorityData' value will be
                changed to the value specified in
                :attr:`Providers.UpdateSpec.certificate_authority_data`, if any.
            :type  additional_scopes: :class:`list` of :class:`str` or ``None``
            :param additional_scopes: Additional scopes to be requested in tokens issued by this identity
                provider. This attribute was added in vSphere API 8.0.0.1.
                If None, the additional scopes will not be updated.
            :type  additional_authorize_parameters: (:class:`dict` of :class:`str` and :class:`str`) or ``None``
            :param additional_authorize_parameters: Any additional parameters to be sent to the upstream identity
                provider during the authorize request in the OAuth2 authorization
                code flow. One use case is to pass in a default tenant ID if you
                have a multi-tenant identity provider. For instance, with VMware's
                Cloud Services Platform, if your organization ID is
                'long-form-org-id', the 'orgLink' parameter can be set to
                "/csp/gateway/am/api/orgs/long-form-org-id" to allow users logging
                in to leverage that organization. This attribute was added in
                vSphere API 8.0.0.1.
                If None, the additional parameters will not be updated.
            """
            self.display_name = display_name
            self.issuer_url = issuer_url
            self.username_claim = username_claim
            self.unset_username_claim = unset_username_claim
            self.groups_claim = groups_claim
            self.unset_groups_claim = unset_groups_claim
            self.client_id = client_id
            self.client_secret = client_secret
            self.certificate_authority_data = certificate_authority_data
            self.unset_certificate_authority_data = unset_certificate_authority_data
            self.additional_scopes = additional_scopes
            self.additional_authorize_parameters = additional_authorize_parameters
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.namespace_management.supervisors.identity.providers.update_spec', {
            'display_name': type.OptionalType(type.StringType()),
            'issuer_URL': type.OptionalType(type.StringType()),
            'username_claim': type.OptionalType(type.StringType()),
            'unset_username_claim': type.OptionalType(type.BooleanType()),
            'groups_claim': type.OptionalType(type.StringType()),
            'unset_groups_claim': type.OptionalType(type.BooleanType()),
            'client_ID': type.OptionalType(type.StringType()),
            'client_secret': type.OptionalType(type.SecretType()),
            'certificate_authority_data': type.OptionalType(type.StringType()),
            'unset_certificate_authority_data': type.OptionalType(type.BooleanType()),
            'additional_scopes': type.OptionalType(type.ListType(type.StringType())),
            'additional_authorize_parameters': type.OptionalType(type.MapType(type.StringType(), type.StringType())),
        },
        UpdateSpec,
        False,
        None))



    def get(self,
            supervisor,
            provider,
            ):
        """
        Returns information about an identity provider configured for a
        Supervisor. This method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: identifier for the Supervisor for which the identity provider is
            being read.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  provider: :class:`str`
        :param provider: identifier for the identity provider that is being read.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.identity.Provider``.
        :rtype: :class:`Providers.Info`
        :return: An {#link Info} representing the requested identity provider.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given identity provider or Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the System.Read privilege on the Supervisor.
        """
        return self._invoke('get',
                            {
                            'supervisor': supervisor,
                            'provider': provider,
                            })

    def list(self,
             supervisor,
             ):
        """
        List the identity providers configured for a given Supervisor. This
        method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the Supervisor for which identity providers are being listed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :rtype: :class:`list` of :class:`Providers.Summary`
        :return: A list of {#link Summary} with details about the identity providers
            associated with a given Supervisor.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the System.Read privilege on the Supervisor.
        """
        return self._invoke('list',
                            {
                            'supervisor': supervisor,
                            })

    def create(self,
               supervisor,
               spec,
               ):
        """
        Create a new identity provider to be used with a Supervisor. Currently,
        only a single identity provider can be created. This method was added
        in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the Supervisor for which the identity provider is being registered.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  spec: :class:`Providers.CreateSpec`
        :param spec: the {#link CreateSpec} describing the identity provider to be
            registered.
        :rtype: :class:`str`
        :return: a unique identifier for the identity provider that was registered.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.identity.Provider``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the specified Supervisor does not exist, or if an identity
            provider is already configured.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the Namespaces.Manage privilege on the
            Supervisor.
        """
        return self._invoke('create',
                            {
                            'supervisor': supervisor,
                            'spec': spec,
                            })

    def update(self,
               supervisor,
               provider,
               spec,
               ):
        """
        Update an existing identity provider used with a Supervisor. This
        method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the identifier for the Supervisor associated with the identity
            provider to be updated.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  provider: :class:`str`
        :param provider: the identifier for the identity provider that is to be updated.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.identity.Provider``.
        :type  spec: :class:`Providers.UpdateSpec`
        :param spec: the {#UpdateSpec} to be applied to the identity provider
            configuration.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given identity provider or Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the Namespaces.Manage privilege on the
            Supervisor.
        """
        return self._invoke('update',
                            {
                            'supervisor': supervisor,
                            'provider': provider,
                            'spec': spec,
                            })

    def set(self,
            supervisor,
            provider,
            spec,
            ):
        """
        Update the entire configuration for an existing identity provider used
        with a Supervisor. This method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the identifier for the Supervisor associated with the identity
            provider to be updated.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  provider: :class:`str`
        :param provider: the identifier for the identity provider that is to be updated.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.identity.Provider``.
        :type  spec: :class:`Providers.SetSpec`
        :param spec: the {#link SetSpec} to be applied to the identity provider
            configuration.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the ``spec`` contains any errors.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given identity provider or Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the Namespaces.Manage privilege on the
            Supervisor.
        """
        return self._invoke('set',
                            {
                            'supervisor': supervisor,
                            'provider': provider,
                            'spec': spec,
                            })

    def delete(self,
               supervisor,
               provider,
               ):
        """
        Remove an identity provider configured with a given Supervisor. This
        will result in users no longer being able to log in to either the
        Supervisor or any of its workload clusters with that identity provider.
        This method was added in vSphere API 8.0.0.1.

        :type  supervisor: :class:`str`
        :param supervisor: the identifier of the Supervisor which is associated with the
            identity provider being removed.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.supervisor.Supervisor``.
        :type  provider: :class:`str`
        :param provider: the identifier for the identity provider that is to be deleted.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.namespace_management.identity.Provider``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the given identity provider or Supervisor cannot be found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user is missing the Namespaces.Manage privilege on the
            Supervisor.
        """
        return self._invoke('delete',
                            {
                            'supervisor': supervisor,
                            'provider': provider,
                            })
class _ProvidersStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers/{provider}',
            path_variables={
                'supervisor': 'supervisor',
                'provider': 'provider',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers',
            path_variables={
                'supervisor': 'supervisor',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'spec': type.ReferenceType(__name__, 'Providers.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
            'spec': type.ReferenceType(__name__, 'Providers.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers/{provider}',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
                'provider': 'provider',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for set operation
        set_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
            'spec': type.ReferenceType(__name__, 'Providers.SetSpec'),
        })
        set_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        set_input_value_validator_list = [
        ]
        set_output_validator_list = [
        ]
        set_rest_metadata = OperationRestMetadata(
            http_method='PUT',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers/{provider}',
            request_body_parameter='spec',
            path_variables={
                'supervisor': 'supervisor',
                'provider': 'provider',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        # properties for delete operation
        delete_input_type = type.StructType('operation-input', {
            'supervisor': type.IdType(resource_types='com.vmware.vcenter.namespace_management.supervisor.Supervisor'),
            'provider': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/namespace-management/supervisors/{supervisor}/identity/providers/{provider}',
            path_variables={
                'supervisor': 'supervisor',
                'provider': 'provider',
            },
            query_parameters={
            },
            dispatch_parameters={
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Providers.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'Providers.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.namespace_management.identity.Provider'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'update': {
                'input_type': update_input_type,
                'output_type': type.VoidType(),
                'errors': update_error_dict,
                'input_value_validator_list': update_input_value_validator_list,
                'output_validator_list': update_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'set': {
                'input_type': set_input_type,
                'output_type': type.VoidType(),
                'errors': set_error_dict,
                'input_value_validator_list': set_input_value_validator_list,
                'output_validator_list': set_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'delete': {
                'input_type': delete_input_type,
                'output_type': type.VoidType(),
                'errors': delete_error_dict,
                'input_value_validator_list': delete_input_value_validator_list,
                'output_validator_list': delete_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'list': list_rest_metadata,
            'create': create_rest_metadata,
            'update': update_rest_metadata,
            'set': set_rest_metadata,
            'delete': delete_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.namespace_management.supervisors.identity.providers',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'Providers': Providers,
    }

