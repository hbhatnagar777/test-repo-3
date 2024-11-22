# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm_client``
module provides classes to manage Trusted Platform Modules (TPMs).

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

class HashAlgorithm(Enum):
    """
    The ``HashAlgorithm`` class defines the possible hash algorithms. This
    enumeration was added in vSphere API 8.0.0.1.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    SHA256 = None
    """
    The SHA 256 hash algorithm. This class attribute was added in vSphere API
    8.0.0.1.

    """
    SHA384 = None
    """
    The SHA 384 hash algorithm. This class attribute was added in vSphere API
    8.0.0.1.

    """
    SHA512 = None
    """
    The SHA 512 hash algorithm. This class attribute was added in vSphere API
    8.0.0.1.

    """
    SM3_256 = None
    """
    The SM3 hash algorithm. This class attribute was added in vSphere API
    8.0.0.1.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`HashAlgorithm` instance.
        """
        Enum.__init__(string)

HashAlgorithm._set_values({
    'SHA256': HashAlgorithm('SHA256'),
    'SHA384': HashAlgorithm('SHA384'),
    'SHA512': HashAlgorithm('SHA512'),
    'SM3_256': HashAlgorithm('SM3_256'),
})
HashAlgorithm._set_binding_type(type.EnumType(
    'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.hash_algorithm',
    HashAlgorithm))




class PcrBank(VapiStruct):
    """
    The ``PcrBank`` class contains information that describes digest
    information of a PCR bank. This class was added in vSphere API 8.0.0.1.

    .. tip::
        The arguments are used to initialize data attributes with the same
        names.
    """




    def __init__(self,
                 algorithm=None,
                 pcrs=None,
                ):
        """
        :type  algorithm: :class:`HashAlgorithm`
        :param algorithm: The hash algorithm that is used by TPM to calculate the PCR values.
            This attribute was added in vSphere API 8.0.0.1.
        :type  pcrs: :class:`dict` of :class:`long` and :class:`str`
        :param pcrs: The index of PCR and corresponding TPM digest value. This attribute
            was added in vSphere API 8.0.0.1.
        """
        self.algorithm = algorithm
        self.pcrs = pcrs
        VapiStruct.__init__(self)


PcrBank._set_binding_type(type.StructType(
    'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.pcr_bank', {
        'algorithm': type.ReferenceType(__name__, 'HashAlgorithm'),
        'pcrs': type.MapType(type.IntegerType(), type.BlobType()),
    },
    PcrBank,
    False,
    None))



class EndorsementKeys(VapiInterface):
    """
    The ``EndorsementKeys`` interface provides methods to get the Trusted
    Platform Module (TPM) Endorsement Key (EK) on a host. This class was added
    in vSphere API 8.0.0.1.
    """
    RESOURCE_TYPE = "com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey"
    """
    Resource type for TPM endorsement Key. This class attribute was added in
    vSphere API 8.0.0.1.

    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EndorsementKeysStub)
        self._VAPI_OPERATION_IDS = {}

    class Type(Enum):
        """
        The ``EndorsementKeys.Type`` class defines the endorsement key type based
        on key algorithms. This enumeration was added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        RSA_2048 = None
        """
        The RSA 2048 bit key. This class attribute was added in vSphere API
        8.0.0.1.

        """
        ECC_NIST_P_256 = None
        """
        The ECC NISTP-256 bit key. This class attribute was added in vSphere API
        8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Type` instance.
            """
            Enum.__init__(string)

    Type._set_values({
        'RSA_2048': Type('RSA_2048'),
        'ECC_NIST_P_256': Type('ECC_NIST_P_256'),
    })
    Type._set_binding_type(type.EnumType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.type',
        Type))


    class Summary(VapiStruct):
        """
        The ``EndorsementKeys.Summary`` class contains information that describes a
        TPM endorsement key. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     key=None,
                     type=None,
                    ):
            """
            :type  key: :class:`str`
            :param key: A unique identifier for the TPM endorsement key. This attribute was
                added in vSphere API 8.0.0.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey``.
                When methods return a value of this class as a return value, the
                attribute will be an identifier for the resource type:
                ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey``.
            :type  type: :class:`EndorsementKeys.Type`
            :param type: The TPM endorsement key type. This attribute was added in vSphere
                API 8.0.0.1.
            """
            self.key = key
            self.type = type
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.summary', {
            'key': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey'),
            'type': type.ReferenceType(__name__, 'EndorsementKeys.Type'),
        },
        Summary,
        False,
        None))


    class Info(VapiStruct):
        """
        The ``EndorsementKeys.Info`` class contains information that describes a
        TPM endorsement key. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     type=None,
                     public_area=None,
                     name=None,
                     qualified_name=None,
                     public_key=None,
                     certificate=None,
                     manufacturer_certificate_uri=None,
                     manufacturer_certificates=None,
                    ):
            """
            :type  type: :class:`EndorsementKeys.Type`
            :param type: The TPM endorsement key type. This attribute was added in vSphere
                API 8.0.0.1.
            :type  public_area: :class:`str`
            :param public_area: The TPM endorsement key public area. 
                
                The public area is a TPM2B_PUBLIC structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 12.2.5
                TPM2B_PUBLIC. This attribute was added in vSphere API 8.0.0.1.
            :type  name: :class:`str`
            :param name: The TPM endorsement key name. 
                
                The name is a TPM2B_NAME structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 10.5.3
                TPM2B_NAME. This attribute was added in vSphere API 8.0.0.1.
            :type  qualified_name: :class:`str`
            :param qualified_name: The TPM endorsement key qualified name. 
                
                The qualified name is a TPM2B_NAME structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 10.5.3
                TPM2B_NAME. This attribute was added in vSphere API 8.0.0.1.
            :type  public_key: :class:`str` or ``None``
            :param public_key: The TPM public endorsement key in PEM format. This attribute was
                added in vSphere API 8.0.0.1.
                if None, the PEM format public key could not be determined.
            :type  certificate: :class:`str` or ``None``
            :param certificate: The TPM endorsement key certificate in PEM format. This attribute
                was added in vSphere API 8.0.0.1.
                if None, the certificate cannot be retrieved from the TPM.
            :type  manufacturer_certificate_uri: :class:`str` or ``None``
            :param manufacturer_certificate_uri: The TPM endorsement key issuer URL extracted from the TPM
                endorsement key certificate. This attribute was added in vSphere
                API 8.0.0.1.
                if None, the URI cannot be retrieved from the endorsement key
                certificate.
            :type  manufacturer_certificates: :class:`com.vmware.vcenter.trusted_infrastructure_client.X509CertChain` or ``None``
            :param manufacturer_certificates: The TPM manufacturer's endorsement key certificate chain. 
                
                Endorsement key certificates are signed by the TPM manufacturer.
                When available, the ``manufacturerCertificates`` attribute will
                contain the TPM manufacturer's endorsement key certificate chain..
                This attribute was added in vSphere API 8.0.0.1.
                if None, the certificate chain is not available.
            """
            self.type = type
            self.public_area = public_area
            self.name = name
            self.qualified_name = qualified_name
            self.public_key = public_key
            self.certificate = certificate
            self.manufacturer_certificate_uri = manufacturer_certificate_uri
            self.manufacturer_certificates = manufacturer_certificates
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.info', {
            'type': type.ReferenceType(__name__, 'EndorsementKeys.Type'),
            'public_area': type.BlobType(),
            'name': type.BlobType(),
            'qualified_name': type.BlobType(),
            'public_key': type.OptionalType(type.StringType()),
            'certificate': type.OptionalType(type.StringType()),
            'manufacturer_certificate_uri': type.OptionalType(type.StringType()),
            'manufacturer_certificates': type.OptionalType(type.ReferenceType('com.vmware.vcenter.trusted_infrastructure_client', 'X509CertChain')),
        },
        Info,
        False,
        None))


    class PolicyPcrSpec(VapiStruct):
        """
        The ``EndorsementKeys.PolicyPcrSpec`` class contains information that can
        be used to construct a PCR policy session for unsealing a secret using the
        :func:`EndorsementKeys.unseal` operation. This class was added in vSphere
        API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     pcrs=None,
                     pcr_digest=None,
                    ):
            """
            :type  pcrs: :class:`str`
            :param pcrs: The PCRs to which the data is sealed. 
                
                The PCR selection is a TPML_PCR_SELECTION structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 10.9.7
                TPML_PCR_SELECTION. This attribute was added in vSphere API
                8.0.0.1.
            :type  pcr_digest: :class:`str` or ``None``
            :param pcr_digest: The digest of the PCRs selected in
                :attr:`EndorsementKeys.PolicyPcrSpec.pcrs`. 
                
                The digest is a TPM2B_DIGEST structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 10.4.2
                TPM2B_DIGEST. This attribute was added in vSphere API 8.0.0.1.
                If None, then the PCR digest is calculated by the service based on
                the current PCR state.
            """
            self.pcrs = pcrs
            self.pcr_digest = pcr_digest
            VapiStruct.__init__(self)


    PolicyPcrSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.policy_pcr_spec', {
            'pcrs': type.BlobType(),
            'pcr_digest': type.OptionalType(type.BlobType()),
        },
        PolicyPcrSpec,
        False,
        None))


    class UnsealSpec(VapiStruct):
        """
        The ``EndorsementKeys.UnsealSpec`` class contains information that
        describes the structures required to unseal a secret. This class was added
        in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     public_area=None,
                     private_area=None,
                     seed=None,
                     policy_pcr=None,
                    ):
            """
            :type  public_area: :class:`str`
            :param public_area: The public area which corresponding to the
                :attr:`EndorsementKeys.UnsealSpec.private_area` secret that is
                being unsealed. 
                
                The public area is a TPM2B_PUBLIC structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 12.2.5
                TPM2B_PUBLIC 
                
                This public area is used as the "objectPublic" input to the
                TPM2_Import command. 
                
                Trusted Platform Module Library Part 3: Commands, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 13.3
                TPM2_Import. This attribute was added in vSphere API 8.0.0.1.
            :type  private_area: :class:`str`
            :param private_area: A private area that contains a secret to be unsealed. 
                
                The private area is symmetrically encrypted with the seed value
                derived from :attr:`EndorsementKeys.UnsealSpec.seed`. 
                
                The private area is a TPM2B_PRIVATE structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 12.3.7
                TPM2B_PRIVATE 
                
                This private area is used as the "duplicate" input to the
                TPM2_Import command. 
                
                Trusted Platform Module Library Part 3: Commands, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 13.3
                TPM2_Import. This attribute was added in vSphere API 8.0.0.1.
            :type  seed: :class:`str`
            :param seed: A seed value that is encrypted by the TPM endorsement key. 
                
                The seed will be decrypted with the endorsement key and then will
                be used as a symmetric key to decrypt
                :attr:`EndorsementKeys.UnsealSpec.private_area`. This ensures that
                only a TPM with the expected endorsement key can unseal the secret.
                
                The seed value is a TPM2B_ENCRYPTED_SECRET structure. 
                
                Trusted Platform Module Library Part 2: Structures, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 11.4.3
                TPM2B_ENCRYPTED_SECRET 
                
                This seed is used as the "inSymSeed" input to the TPM2_Import
                command. 
                
                Trusted Platform Module Library Part 3: Commands, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 13.3
                TPM2_Import. This attribute was added in vSphere API 8.0.0.1.
            :type  policy_pcr: :class:`EndorsementKeys.PolicyPcrSpec` or ``None``
            :param policy_pcr: PCR policy required to unseal the secret. 
                
                Used as input to the TPM2_PolicyPCR command on a session that is
                created for issuing the TPM2_Unseal command. 
                
                Trusted Platform Module Library Part 3: Commands, Family "2.0",
                Level 00 Revision 01.59, November 8, 2019, Section 23.7
                TPM2_PolicyPCR. This attribute was added in vSphere API 8.0.0.1.
                If None, then a zeroed authorization policy is used for the
                TPM2_Unseal session.
            """
            self.public_area = public_area
            self.private_area = private_area
            self.seed = seed
            self.policy_pcr = policy_pcr
            VapiStruct.__init__(self)


    UnsealSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.unseal_spec', {
            'public_area': type.BlobType(),
            'private_area': type.BlobType(),
            'seed': type.BlobType(),
            'policy_pcr': type.OptionalType(type.ReferenceType(__name__, 'EndorsementKeys.PolicyPcrSpec')),
        },
        UnsealSpec,
        False,
        None))


    class FilterSpec(VapiStruct):
        """
        The ``EndorsementKeys.FilterSpec`` class contains attributes used to filter
        the results when listing the endorsement key. This class was added in
        vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     types=None,
                    ):
            """
            :type  types: :class:`set` of :class:`EndorsementKeys.Type` or ``None``
            :param types: Type of the endorsement key. This attribute was added in vSphere
                API 8.0.0.1.
                if None or empty, the result will not be filtered by ``types``.
            """
            self.types = types
            VapiStruct.__init__(self)


    FilterSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys.filter_spec', {
            'types': type.OptionalType(type.SetType(type.ReferenceType(__name__, 'EndorsementKeys.Type'))),
        },
        FilterSpec,
        False,
        None))



    def list(self,
             host,
             tpm,
             filter=None,
             ):
        """
        Return a list of configured endorsement keys on a host. This method was
        added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  tpm: :class:`str`
        :param tpm: the TPM identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
        :type  filter: :class:`EndorsementKeys.FilterSpec` or ``None``
        :param filter: a filter for the returned list.
            if None, the behavior is equivalent to a
            :class:`EndorsementKeys.FilterSpec` with attributes None.
        :rtype: :class:`list` of :class:`EndorsementKeys.Summary`
        :return: A list of configured endorsement keys.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the arguments are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the TPM device, or the host is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Read``.
        """
        return self._invoke('list',
                            {
                            'host': host,
                            'tpm': tpm,
                            'filter': filter,
                            })

    def get(self,
            host,
            tpm,
            key,
            ):
        """
        Get the TPM endorsement key details on a host. 
        
        The information returned is derived from executing the TPM2_ReadPublic
        command on the endorsement key object handle. 
        
        Trusted Platform Module Library Part 3: Commands, Family "2.0", Level
        00 Revision 01.59, November 8, 2019, Section 12.4 TPM2_ReadPublic. This
        method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  tpm: :class:`str`
        :param tpm: the TPM identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
        :type  key: :class:`str`
        :param key: the endorsement key identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey``.
        :rtype: :class:`EndorsementKeys.Info`
        :return: The endorsement key info.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the arguments are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the endorsement key, or the TPM device, or the host is not
            found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            'tpm': tpm,
                            'key': key,
                            })

    def unseal(self,
               host,
               tpm,
               key,
               spec,
               ):
        """
        Unseal a secret that is bound to an endorsement key. 
        
        Provided with duplicate key data, load the key as a child of the
        specified endorsement key using the TPM2_Import command and then unseal
        the secret data using the TPM2_Unseal command. 
        
        The duplicate key must include only outer wrapping; inner wrapping is
        not supported. The duplicate key cannot have a complex authorization
        policy (e.g. including command selection, locality, etc). Only PCR
        policy authorization is supported at this time. 
        
        Trusted Platform Module Library Part 1: Architecture, Family "2.0",
        Level 00 Revision 01.59, November 8, 2019, Section 23.3 Duplication 
        
        Trusted Platform Module Library Part 3: Commands, Family "2.0", Level
        00 Revision 01.59, November 8, 2019, Section 13.3 TPM2_Import 
        
        Trusted Platform Module Library Part 3: Commands, Family "2.0", Level
        00 Revision 01.59, November 8, 2019, Section 12.7 TPM2_Unseal. This
        method was added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  tpm: :class:`str`
        :param tpm: the TPM identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
        :type  key: :class:`str`
        :param key: the endorsement key identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey``.
        :type  spec: :class:`EndorsementKeys.UnsealSpec`
        :param spec: the unseal spec.
        :rtype: :class:`str`
        :return: The unsealed secret.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the arguments are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the endorsement key or TPM is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Unseal``.
        """
        return self._invoke('unseal',
                            {
                            'host': host,
                            'tpm': tpm,
                            'key': key,
                            'spec': spec,
                            })
class EventLog(VapiInterface):
    """
    The ``EventLog`` interface provides methods to get the Trusted Platform
    Module (TPM) event log on a host. This class was added in vSphere API
    8.0.0.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.event_log'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _EventLogStub)
        self._VAPI_OPERATION_IDS = {}

    class Type(Enum):
        """
        The ``EventLog.Type`` class lists the event log types. This enumeration was
        added in vSphere API 8.0.0.1.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        EFI_TCG2_EVENT_LOG_FORMAT_TCG_2 = None
        """
        TCG EFI Protocol Specification, Family "2.0", Level 00 Revision 00.13,
        March 30, 2016, Section 5.2 Crypto Agile Log Entry Format. This class
        attribute was added in vSphere API 8.0.0.1.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Type` instance.
            """
            Enum.__init__(string)

    Type._set_values({
        'EFI_TCG2_EVENT_LOG_FORMAT_TCG_2': Type('EFI_TCG2_EVENT_LOG_FORMAT_TCG_2'),
    })
    Type._set_binding_type(type.EnumType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.event_log.type',
        Type))


    class Info(VapiStruct):
        """
        The ``EventLog.Info`` class contains information that describes an event
        log. This class was added in vSphere API 8.0.0.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     type=None,
                     data=None,
                     truncated=None,
                     banks=None,
                    ):
            """
            :type  type: :class:`EventLog.Type`
            :param type: Type of the event log. This attribute was added in vSphere API
                8.0.0.1.
            :type  data: :class:`str` or ``None``
            :param data: Event log data in the format described by
                :attr:`EventLog.Info.type`. This attribute was added in vSphere API
                8.0.0.1.
                This attribute is currently required. It may be optional in a
                future version.
            :type  truncated: :class:`bool`
            :param truncated: Indicates if the event log is truncated. 
                
                An event log is truncated when there was insufficient memory to
                store one or more event entries.. This attribute was added in
                vSphere API 8.0.0.1.
            :type  banks: :class:`list` of :class:`PcrBank`
            :param banks: The resulting PCR banks from event log replay. This attribute was
                added in vSphere API 8.0.0.1.
            """
            self.type = type
            self.data = data
            self.truncated = truncated
            self.banks = banks
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.event_log.info', {
            'type': type.ReferenceType(__name__, 'EventLog.Type'),
            'data': type.OptionalType(type.BlobType()),
            'truncated': type.BooleanType(),
            'banks': type.ListType(type.ReferenceType(__name__, 'PcrBank')),
        },
        Info,
        False,
        None))



    def get(self,
            host,
            tpm,
            ):
        """
        Retrieves the event log associated with the TPM device. This method was
        added in vSphere API 8.0.0.1.

        :type  host: :class:`str`
        :param host: Identifier of the host.
            The parameter must be an identifier for the resource type:
            ``HostSystem``.
        :type  tpm: :class:`str`
        :param tpm: the TPM identifier.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm``.
        :rtype: :class:`EventLog.Info`
        :return: The event information.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if there is a generic error.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the argument is invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if event log is not found, or tpm is not found or host is not
            found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if too many requests are in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the caller is not authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the caller is not authorized.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``HostSystem`` referenced by the parameter ``host``
              requires ``Host.Tpm.Read``.
        """
        return self._invoke('get',
                            {
                            'host': host,
                            'tpm': tpm,
                            })
class _EndorsementKeysStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for list operation
        list_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
            'filter': type.OptionalType(type.ReferenceType(__name__, 'EndorsementKeys.FilterSpec')),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm/{tpm}/endorsement-keys',
            path_variables={
                'host': 'host',
                'tpm': 'tpm',
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

        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
            'key': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm/{tpm}/endorsement-keys/{key}',
            path_variables={
                'host': 'host',
                'tpm': 'tpm',
                'key': 'key',
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

        # properties for unseal operation
        unseal_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
            'key': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.EndorsementKey'),
            'spec': type.ReferenceType(__name__, 'EndorsementKeys.UnsealSpec'),
        })
        unseal_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        unseal_input_value_validator_list = [
        ]
        unseal_output_validator_list = [
        ]
        unseal_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm/{tpm}/endorsement-keys/{key}',
            request_body_parameter='spec',
            path_variables={
                'host': 'host',
                'tpm': 'tpm',
                'key': 'key',
            },
            query_parameters={
            },
            dispatch_parameters={
                'action': 'unseal',
            },
            header_parameters={
            },
            dispatch_header_parameters={
            }
        )

        operations = {
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'EndorsementKeys.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'EndorsementKeys.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'unseal': {
                'input_type': unseal_input_type,
                'output_type': type.BlobType(),
                'errors': unseal_error_dict,
                'input_value_validator_list': unseal_input_value_validator_list,
                'output_validator_list': unseal_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'list': list_rest_metadata,
            'get': get_rest_metadata,
            'unseal': unseal_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.endorsement_keys',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _EventLogStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'host': type.IdType(resource_types='HostSystem'),
            'tpm': type.IdType(resource_types='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.Tpm'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/vcenter/trusted-infrastructure/hosts/{host}/hardware/tpm/{tpm}/event-log',
            path_variables={
                'host': 'host',
                'tpm': 'tpm',
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
                'output_type': type.ReferenceType(__name__, 'EventLog.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.trusted_infrastructure.hosts.hardware.tpm.event_log',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'EndorsementKeys': EndorsementKeys,
        'EventLog': EventLog,
    }

