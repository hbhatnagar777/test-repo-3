# Copyright (c) 2023 VMware, Inc. All rights reserved.
# VMware Confidential
# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Copyright (c) 2024 Broadcom.  All rights reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.

# AUTO GENERATED FILE -- DO NOT MODIFY!
#
# vAPI stub file for package com.vmware.vcenter.vm.
#---------------------------------------------------------------------------

"""
The ``com.vmware.vcenter.vm_client`` module provides classes for managing
virtual machines.

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

class GuestOS(Enum):
    """
    The ``GuestOS`` class defines the valid guest operating system types used
    for configuring a virtual machine.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    DOS = None
    """
    MS-DOS.

    """
    WIN_31 = None
    """
    Windows 3.1

    """
    WIN_95 = None
    """
    Windows 95

    """
    WIN_98 = None
    """
    Windows 98

    """
    WIN_ME = None
    """
    Windows Millennium Edition

    """
    WIN_NT = None
    """
    Windows NT 4

    """
    WIN_2000_PRO = None
    """
    Windows 2000 Professional

    """
    WIN_2000_SERV = None
    """
    Windows 2000 Server

    """
    WIN_2000_ADV_SERV = None
    """
    Windows 2000 Advanced Server

    """
    WIN_XP_HOME = None
    """
    Windows XP Home Edition

    """
    WIN_XP_PRO = None
    """
    Windows XP Professional

    """
    WIN_XP_PRO_64 = None
    """
    Windows XP Professional Edition (64 bit)

    """
    WIN_NET_WEB = None
    """
    Windows Server 2003, Web Edition

    """
    WIN_NET_STANDARD = None
    """
    Windows Server 2003, Standard Edition

    """
    WIN_NET_ENTERPRISE = None
    """
    Windows Server 2003, Enterprise Edition

    """
    WIN_NET_DATACENTER = None
    """
    Windows Server 2003, Datacenter Edition

    """
    WIN_NET_BUSINESS = None
    """
    Windows Small Business Server 2003

    """
    WIN_NET_STANDARD_64 = None
    """
    Windows Server 2003, Standard Edition (64 bit)

    """
    WIN_NET_ENTERPRISE_64 = None
    """
    Windows Server 2003, Enterprise Edition (64 bit)

    """
    WIN_LONGHORN = None
    """
    Windows Longhorn

    """
    WIN_LONGHORN_64 = None
    """
    Windows Longhorn (64 bit)

    """
    WIN_NET_DATACENTER_64 = None
    """
    Windows Server 2003, Datacenter Edition (64 bit)

    """
    WIN_VISTA = None
    """
    Windows Vista

    """
    WIN_VISTA_64 = None
    """
    Windows Vista (64 bit)

    """
    WINDOWS_7 = None
    """
    Windows 7

    """
    WINDOWS_7_64 = None
    """
    Windows 7 (64 bit)

    """
    WINDOWS_7_SERVER_64 = None
    """
    Windows Server 2008 R2 (64 bit)

    """
    WINDOWS_8 = None
    """
    Windows 8

    """
    WINDOWS_8_64 = None
    """
    Windows 8 (64 bit)

    """
    WINDOWS_8_SERVER_64 = None
    """
    Windows 8 Server (64 bit)

    """
    WINDOWS_9 = None
    """
    Windows 10

    """
    WINDOWS_9_64 = None
    """
    Windows 10 (64 bit)

    """
    WINDOWS_9_SERVER_64 = None
    """
    Windows 10 Server (64 bit)

    """
    WINDOWS_11_64 = None
    """
    Windows 11 (64 bit). This class attribute was added in vSphere API 8.0.0.1.

    """
    WINDOWS_12_64 = None
    """
    Windows 12 (64 bit). This class attribute was added in vSphere API 8.0.0.1.

    """
    WINDOWS_HYPERV = None
    """
    Windows Hyper-V

    """
    WINDOWS_SERVER_2019 = None
    """
    Windows Server 2019. This class attribute was added in vSphere API 7.0.0.0.

    """
    WINDOWS_SERVER_2021 = None
    """
    Windows Server 2022. This class attribute was added in vSphere API 7.0.1.0.

    """
    WINDOWS_SERVER_2025 = None
    """
    Windows Server 2025. This class attribute was added in vSphere API 8.0.0.1.

    """
    FREEBSD = None
    """
    FreeBSD 10 or earlier

    """
    FREEBSD_64 = None
    """
    FreeBSD 10 x64 or earlier

    """
    FREEBSD_11 = None
    """
    FreeBSD 11. This class attribute was added in vSphere API 6.7.

    """
    FREEBSD_12 = None
    """
    FreeBSD 12. This class attribute was added in vSphere API 6.7.

    """
    FREEBSD_13 = None
    """
    FreeBSD 13. This class attribute was added in vSphere API 7.0.1.0.

    """
    FREEBSD_14 = None
    """
    FreeBSD 14. This class attribute was added in vSphere API 8.0.0.1.

    """
    FREEBSD_11_64 = None
    """
    FreeBSD 11 x64. This class attribute was added in vSphere API 6.7.

    """
    FREEBSD_12_64 = None
    """
    FreeBSD 12 x64. This class attribute was added in vSphere API 6.7.

    """
    FREEBSD_13_64 = None
    """
    FreeBSD 13 x64. This class attribute was added in vSphere API 7.0.1.0.

    """
    FREEBSD_14_64 = None
    """
    FreeBSD 14 x64. This class attribute was added in vSphere API 8.0.0.1.

    """
    REDHAT = None
    """
    Red Hat Linux 2.1

    """
    RHEL_2 = None
    """
    Red Hat Enterprise Linux 2

    """
    RHEL_3 = None
    """
    Red Hat Enterprise Linux 3

    """
    RHEL_3_64 = None
    """
    Red Hat Enterprise Linux 3 (64 bit)

    """
    RHEL_4 = None
    """
    Red Hat Enterprise Linux 4

    """
    RHEL_4_64 = None
    """
    Red Hat Enterprise Linux 4 (64 bit)

    """
    RHEL_5 = None
    """
    Red Hat Enterprise Linux 5

    """
    RHEL_5_64 = None
    """
    Red Hat Enterprise Linux 5 (64 bit)

    """
    RHEL_6 = None
    """
    Red Hat Enterprise Linux 6

    """
    RHEL_6_64 = None
    """
    Red Hat Enterprise Linux 6 (64 bit)

    """
    RHEL_7 = None
    """
    Red Hat Enterprise Linux 7

    """
    RHEL_7_64 = None
    """
    Red Hat Enterprise Linux 7 (64 bit)

    """
    RHEL_8_64 = None
    """
    Red Hat Enterprise Linux 8 (64 bit). This class attribute was added in
    vSphere API 6.7.

    """
    RHEL_9_64 = None
    """
    Red Hat Enterprise Linux 9 (64 bit). This class attribute was added in
    vSphere API 7.0.1.0.

    """
    CENTOS = None
    """
    CentOS 4/5

    """
    CENTOS_64 = None
    """
    CentOS 4/5 (64-bit)

    """
    CENTOS_6 = None
    """
    CentOS 6

    """
    CENTOS_6_64 = None
    """
    CentOS 6 (64-bit)

    """
    CENTOS_7 = None
    """
    CentOS 7

    """
    CENTOS_7_64 = None
    """
    CentOS 7 (64-bit)

    """
    CENTOS_8_64 = None
    """
    CentOS 8 (64-bit). This class attribute was added in vSphere API 6.7.

    """
    CENTOS_9_64 = None
    """
    CentOS 9 (64-bit). This class attribute was added in vSphere API 7.0.1.0.

    """
    ORACLE_LINUX = None
    """
    Oracle Linux 4/5

    """
    ORACLE_LINUX_64 = None
    """
    Oracle Linux 4/5 (64-bit)

    """
    ORACLE_LINUX_6 = None
    """
    Oracle Linux 6

    """
    ORACLE_LINUX_6_64 = None
    """
    Oracle Linux 6 (64-bit)

    """
    ORACLE_LINUX_7 = None
    """
    Oracle Linux 7

    """
    ORACLE_LINUX_7_64 = None
    """
    Oracle Linux 7 (64-bit)

    """
    ORACLE_LINUX_8_64 = None
    """
    Oracle Linux 8 (64-bit). This class attribute was added in vSphere API 6.7.

    """
    ORACLE_LINUX_9_64 = None
    """
    Oracle Linux 9 (64-bit). This class attribute was added in vSphere API
    7.0.1.0.

    """
    SUSE = None
    """
    Suse Linux

    """
    SUSE_64 = None
    """
    Suse Linux (64 bit)

    """
    SLES = None
    """
    Suse Linux Enterprise Server 9

    """
    SLES_64 = None
    """
    Suse Linux Enterprise Server 9 (64 bit)

    """
    SLES_10 = None
    """
    Suse linux Enterprise Server 10

    """
    SLES_10_64 = None
    """
    Suse Linux Enterprise Server 10 (64 bit)

    """
    SLES_11 = None
    """
    Suse linux Enterprise Server 11

    """
    SLES_11_64 = None
    """
    Suse Linux Enterprise Server 11 (64 bit)

    """
    SLES_12 = None
    """
    Suse linux Enterprise Server 12

    """
    SLES_12_64 = None
    """
    Suse Linux Enterprise Server 12 (64 bit)

    """
    SLES_15_64 = None
    """
    Suse Linux Enterprise Server 15 (64 bit). This class attribute was added in
    vSphere API 6.7.

    """
    SLES_16_64 = None
    """
    Suse Linux Enterprise Server 16 (64 bit). This class attribute was added in
    vSphere API 7.0.1.0.

    """
    NLD_9 = None
    """
    Novell Linux Desktop 9

    """
    OES = None
    """
    Open Enterprise Server

    """
    SJDS = None
    """
    Sun Java Desktop System

    """
    MANDRAKE = None
    """
    Mandrake Linux

    """
    MANDRIVA = None
    """
    Mandriva Linux

    """
    MANDRIVA_64 = None
    """
    Mandriva Linux (64 bit)

    """
    TURBO_LINUX = None
    """
    Turbolinux

    """
    TURBO_LINUX_64 = None
    """
    Turbolinux (64 bit)

    """
    UBUNTU = None
    """
    Ubuntu Linux

    """
    UBUNTU_64 = None
    """
    Ubuntu Linux (64 bit)

    """
    DEBIAN_4 = None
    """
    Debian GNU/Linux 4

    """
    DEBIAN_4_64 = None
    """
    Debian GNU/Linux 4 (64 bit)

    """
    DEBIAN_5 = None
    """
    Debian GNU/Linux 5

    """
    DEBIAN_5_64 = None
    """
    Debian GNU/Linux 5 (64 bit)

    """
    DEBIAN_6 = None
    """
    Debian GNU/Linux 6

    """
    DEBIAN_6_64 = None
    """
    Debian GNU/Linux 6 (64 bit)

    """
    DEBIAN_7 = None
    """
    Debian GNU/Linux 7

    """
    DEBIAN_7_64 = None
    """
    Debian GNU/Linux 7 (64 bit)

    """
    DEBIAN_8 = None
    """
    Debian GNU/Linux 8

    """
    DEBIAN_8_64 = None
    """
    Debian GNU/Linux 8 (64 bit)

    """
    DEBIAN_9 = None
    """
    Debian GNU/Linux 9

    """
    DEBIAN_9_64 = None
    """
    Debian GNU/Linux 9 (64 bit)

    """
    DEBIAN_10 = None
    """
    Debian GNU/Linux 10

    """
    DEBIAN_10_64 = None
    """
    Debian GNU/Linux 10 (64 bit)

    """
    DEBIAN_11 = None
    """
    Debian GNU/Linux 11. This class attribute was added in vSphere API 7.0.0.0.

    """
    DEBIAN_11_64 = None
    """
    Debian GNU/Linux 11 (64 bit). This class attribute was added in vSphere API
    7.0.0.0.

    """
    DEBIAN_12 = None
    """
    Debian GNU/Linux 12. This class attribute was added in vSphere API 8.0.0.1.

    """
    DEBIAN_12_64 = None
    """
    Debian GNU/Linux 12 (64 bit). This class attribute was added in vSphere API
    8.0.0.1.

    """
    ASIANUX_3 = None
    """
    Asianux Server 3

    """
    ASIANUX_3_64 = None
    """
    Asianux Server 3 (64 bit)

    """
    ASIANUX_4 = None
    """
    Asianux Server 4

    """
    ASIANUX_4_64 = None
    """
    Asianux Server 4 (64 bit)

    """
    ASIANUX_5_64 = None
    """
    Asianux Server 5 (64 bit)

    """
    ASIANUX_7_64 = None
    """
    Asianux Server 7 (64 bit)

    """
    ASIANUX_8_64 = None
    """
    Asianux Server 8 (64 bit). This class attribute was added in vSphere API
    6.7.

    """
    ASIANUX_9_64 = None
    """
    Asianux Server 9 (64 bit). This class attribute was added in vSphere API
    7.0.1.0.

    """
    OPENSUSE = None
    """
    OpenSUSE Linux

    """
    OPENSUSE_64 = None
    """
    OpenSUSE Linux (64 bit)

    """
    FEDORA = None
    """
    Fedora Linux

    """
    FEDORA_64 = None
    """
    Fedora Linux (64 bit)

    """
    COREOS_64 = None
    """
    CoreOS Linux (64 bit)

    """
    VMWARE_PHOTON_64 = None
    """
    VMware Photon (64 bit)

    """
    OTHER_24X_LINUX = None
    """
    Linux 2.4x Kernel

    """
    OTHER_24X_LINUX_64 = None
    """
    Linux 2.4x Kernel (64 bit)

    """
    OTHER_26X_LINUX = None
    """
    Linux 2.6x Kernel

    """
    OTHER_26X_LINUX_64 = None
    """
    Linux 2.6x Kernel (64 bit)

    """
    OTHER_3X_LINUX = None
    """
    Linux 3.x Kernel

    """
    OTHER_3X_LINUX_64 = None
    """
    Linux 3.x Kernel (64 bit)

    """
    OTHER_4X_LINUX = None
    """
    Linux 4.x Kernel. This class attribute was added in vSphere API 6.7.

    """
    OTHER_4X_LINUX_64 = None
    """
    Linux 4.x Kernel (64 bit). This class attribute was added in vSphere API
    6.7.

    """
    OTHER_5X_LINUX = None
    """
    Linux 5.x Kernel. This class attribute was added in vSphere API 7.0.1.0.

    """
    OTHER_5X_LINUX_64 = None
    """
    Linux 5.x Kernel (64 bit). This class attribute was added in vSphere API
    7.0.1.0.

    """
    OTHER_6X_LINUX = None
    """
    Linux 6.x Kernel. This class attribute was added in vSphere API 8.0.0.1.

    """
    OTHER_6X_LINUX_64 = None
    """
    Linux 6.x Kernel (64 bit). This class attribute was added in vSphere API
    8.0.0.1.

    """
    OTHER_LINUX = None
    """
    Linux 2.2x Kernel

    """
    GENERIC_LINUX = None
    """
    Other Linux

    """
    OTHER_LINUX_64 = None
    """
    Linux (64 bit)

    """
    SOLARIS_6 = None
    """
    Solaris 6

    """
    SOLARIS_7 = None
    """
    Solaris 7

    """
    SOLARIS_8 = None
    """
    Solaris 8

    """
    SOLARIS_9 = None
    """
    Solaris 9

    """
    SOLARIS_10 = None
    """
    Solaris 10 (32 bit)

    """
    SOLARIS_10_64 = None
    """
    Solaris 10 (64 bit)

    """
    SOLARIS_11_64 = None
    """
    Solaris 11 (64 bit)

    """
    OS2 = None
    """
    OS/2

    """
    ECOMSTATION = None
    """
    eComStation 1.x

    """
    ECOMSTATION_2 = None
    """
    eComStation 2.0

    """
    NETWARE_4 = None
    """
    Novell NetWare 4

    """
    NETWARE_5 = None
    """
    Novell NetWare 5.1

    """
    NETWARE_6 = None
    """
    Novell NetWare 6.x

    """
    OPENSERVER_5 = None
    """
    SCO OpenServer 5

    """
    OPENSERVER_6 = None
    """
    SCO OpenServer 6

    """
    UNIXWARE_7 = None
    """
    SCO UnixWare 7

    """
    DARWIN = None
    """
    Mac OS 10.5

    """
    DARWIN_64 = None
    """
    Mac OS 10.5 (64 bit)

    """
    DARWIN_10 = None
    """
    Mac OS 10.6

    """
    DARWIN_10_64 = None
    """
    Mac OS 10.6 (64 bit)

    """
    DARWIN_11 = None
    """
    Mac OS 10.7

    """
    DARWIN_11_64 = None
    """
    Mac OS 10.7 (64 bit)

    """
    DARWIN_12_64 = None
    """
    Mac OS 10.8 (64 bit)

    """
    DARWIN_13_64 = None
    """
    Mac OS 10.9 (64 bit)

    """
    DARWIN_14_64 = None
    """
    Mac OS 10.10 (64 bit)

    """
    DARWIN_15_64 = None
    """
    Mac OS 10.11 (64 bit)

    """
    DARWIN_16_64 = None
    """
    Mac OS 10.12 (64 bit)

    """
    DARWIN_17_64 = None
    """
    Mac OS 10.13 (64 bit). This class attribute was added in vSphere API 6.7.

    """
    DARWIN_18_64 = None
    """
    Mac OS 10.14 (64 bit). This class attribute was added in vSphere API 6.7.

    """
    DARWIN_19_64 = None
    """
    Mac OS 10.15 (64 bit). This class attribute was added in vSphere API
    7.0.0.0.

    """
    DARWIN_20_64 = None
    """
    Mac OS 11 (64 bit). This class attribute was added in vSphere API 7.0.1.0.

    """
    DARWIN_21_64 = None
    """
    Mac OS 12 (64 bit). This class attribute was added in vSphere API 7.0.1.0.

    """
    DARWIN_22_64 = None
    """
    Mac OS 13 (64 bit). This class attribute was added in vSphere API 8.0.0.1.

    """
    DARWIN_23_64 = None
    """
    Mac OS 14 (64 bit). This class attribute was added in vSphere API 8.0.0.1.

    """
    VMKERNEL = None
    """
    VMware ESX 4

    """
    VMKERNEL_5 = None
    """
    VMware ESX 5

    """
    VMKERNEL_6 = None
    """
    VMware ESX 6

    """
    VMKERNEL_65 = None
    """
    VMware ESXi 6.5 AND ESXi 6.7.

    """
    VMKERNEL_7 = None
    """
    VMware ESX 7. This class attribute was added in vSphere API 7.0.0.0.

    """
    VMKERNEL_8 = None
    """
    VMware ESX 8. This class attribute was added in vSphere API 8.0.0.1.

    """
    AMAZONLINUX2_64 = None
    """
    Amazon Linux 2 (64 bit). This class attribute was added in vSphere API
    6.7.1.

    """
    AMAZONLINUX3_64 = None
    """
    Amazon Linux 3 (64 bit). This class attribute was added in vSphere API
    7.0.1.0.

    """
    CRXPOD_1 = None
    """
    CRX Pod 1. This class attribute was added in vSphere API 7.0.0.0.

    """
    CRXSYS_1 = None
    """
    CRX Sys 1. This class attribute was added in vSphere API 8.0.3.0.

    """
    ROCKYLINUX_64 = None
    """
    Rocky Linux (64-bit). This class attribute was added in vSphere API
    8.0.0.1.

    """
    ALMALINUX_64 = None
    """
    AlmaLinux (64-bit). This class attribute was added in vSphere API 8.0.0.1.

    """
    OTHER = None
    """
    Other Operating System

    """
    OTHER_64 = None
    """
    Other Operating System (64 bit)

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`GuestOS` instance.
        """
        Enum.__init__(string)

GuestOS._set_values({
    'DOS': GuestOS('DOS'),
    'WIN_31': GuestOS('WIN_31'),
    'WIN_95': GuestOS('WIN_95'),
    'WIN_98': GuestOS('WIN_98'),
    'WIN_ME': GuestOS('WIN_ME'),
    'WIN_NT': GuestOS('WIN_NT'),
    'WIN_2000_PRO': GuestOS('WIN_2000_PRO'),
    'WIN_2000_SERV': GuestOS('WIN_2000_SERV'),
    'WIN_2000_ADV_SERV': GuestOS('WIN_2000_ADV_SERV'),
    'WIN_XP_HOME': GuestOS('WIN_XP_HOME'),
    'WIN_XP_PRO': GuestOS('WIN_XP_PRO'),
    'WIN_XP_PRO_64': GuestOS('WIN_XP_PRO_64'),
    'WIN_NET_WEB': GuestOS('WIN_NET_WEB'),
    'WIN_NET_STANDARD': GuestOS('WIN_NET_STANDARD'),
    'WIN_NET_ENTERPRISE': GuestOS('WIN_NET_ENTERPRISE'),
    'WIN_NET_DATACENTER': GuestOS('WIN_NET_DATACENTER'),
    'WIN_NET_BUSINESS': GuestOS('WIN_NET_BUSINESS'),
    'WIN_NET_STANDARD_64': GuestOS('WIN_NET_STANDARD_64'),
    'WIN_NET_ENTERPRISE_64': GuestOS('WIN_NET_ENTERPRISE_64'),
    'WIN_LONGHORN': GuestOS('WIN_LONGHORN'),
    'WIN_LONGHORN_64': GuestOS('WIN_LONGHORN_64'),
    'WIN_NET_DATACENTER_64': GuestOS('WIN_NET_DATACENTER_64'),
    'WIN_VISTA': GuestOS('WIN_VISTA'),
    'WIN_VISTA_64': GuestOS('WIN_VISTA_64'),
    'WINDOWS_7': GuestOS('WINDOWS_7'),
    'WINDOWS_7_64': GuestOS('WINDOWS_7_64'),
    'WINDOWS_7_SERVER_64': GuestOS('WINDOWS_7_SERVER_64'),
    'WINDOWS_8': GuestOS('WINDOWS_8'),
    'WINDOWS_8_64': GuestOS('WINDOWS_8_64'),
    'WINDOWS_8_SERVER_64': GuestOS('WINDOWS_8_SERVER_64'),
    'WINDOWS_9': GuestOS('WINDOWS_9'),
    'WINDOWS_9_64': GuestOS('WINDOWS_9_64'),
    'WINDOWS_9_SERVER_64': GuestOS('WINDOWS_9_SERVER_64'),
    'WINDOWS_11_64': GuestOS('WINDOWS_11_64'),
    'WINDOWS_12_64': GuestOS('WINDOWS_12_64'),
    'WINDOWS_HYPERV': GuestOS('WINDOWS_HYPERV'),
    'WINDOWS_SERVER_2019': GuestOS('WINDOWS_SERVER_2019'),
    'WINDOWS_SERVER_2021': GuestOS('WINDOWS_SERVER_2021'),
    'WINDOWS_SERVER_2025': GuestOS('WINDOWS_SERVER_2025'),
    'FREEBSD': GuestOS('FREEBSD'),
    'FREEBSD_64': GuestOS('FREEBSD_64'),
    'FREEBSD_11': GuestOS('FREEBSD_11'),
    'FREEBSD_12': GuestOS('FREEBSD_12'),
    'FREEBSD_13': GuestOS('FREEBSD_13'),
    'FREEBSD_14': GuestOS('FREEBSD_14'),
    'FREEBSD_11_64': GuestOS('FREEBSD_11_64'),
    'FREEBSD_12_64': GuestOS('FREEBSD_12_64'),
    'FREEBSD_13_64': GuestOS('FREEBSD_13_64'),
    'FREEBSD_14_64': GuestOS('FREEBSD_14_64'),
    'REDHAT': GuestOS('REDHAT'),
    'RHEL_2': GuestOS('RHEL_2'),
    'RHEL_3': GuestOS('RHEL_3'),
    'RHEL_3_64': GuestOS('RHEL_3_64'),
    'RHEL_4': GuestOS('RHEL_4'),
    'RHEL_4_64': GuestOS('RHEL_4_64'),
    'RHEL_5': GuestOS('RHEL_5'),
    'RHEL_5_64': GuestOS('RHEL_5_64'),
    'RHEL_6': GuestOS('RHEL_6'),
    'RHEL_6_64': GuestOS('RHEL_6_64'),
    'RHEL_7': GuestOS('RHEL_7'),
    'RHEL_7_64': GuestOS('RHEL_7_64'),
    'RHEL_8_64': GuestOS('RHEL_8_64'),
    'RHEL_9_64': GuestOS('RHEL_9_64'),
    'CENTOS': GuestOS('CENTOS'),
    'CENTOS_64': GuestOS('CENTOS_64'),
    'CENTOS_6': GuestOS('CENTOS_6'),
    'CENTOS_6_64': GuestOS('CENTOS_6_64'),
    'CENTOS_7': GuestOS('CENTOS_7'),
    'CENTOS_7_64': GuestOS('CENTOS_7_64'),
    'CENTOS_8_64': GuestOS('CENTOS_8_64'),
    'CENTOS_9_64': GuestOS('CENTOS_9_64'),
    'ORACLE_LINUX': GuestOS('ORACLE_LINUX'),
    'ORACLE_LINUX_64': GuestOS('ORACLE_LINUX_64'),
    'ORACLE_LINUX_6': GuestOS('ORACLE_LINUX_6'),
    'ORACLE_LINUX_6_64': GuestOS('ORACLE_LINUX_6_64'),
    'ORACLE_LINUX_7': GuestOS('ORACLE_LINUX_7'),
    'ORACLE_LINUX_7_64': GuestOS('ORACLE_LINUX_7_64'),
    'ORACLE_LINUX_8_64': GuestOS('ORACLE_LINUX_8_64'),
    'ORACLE_LINUX_9_64': GuestOS('ORACLE_LINUX_9_64'),
    'SUSE': GuestOS('SUSE'),
    'SUSE_64': GuestOS('SUSE_64'),
    'SLES': GuestOS('SLES'),
    'SLES_64': GuestOS('SLES_64'),
    'SLES_10': GuestOS('SLES_10'),
    'SLES_10_64': GuestOS('SLES_10_64'),
    'SLES_11': GuestOS('SLES_11'),
    'SLES_11_64': GuestOS('SLES_11_64'),
    'SLES_12': GuestOS('SLES_12'),
    'SLES_12_64': GuestOS('SLES_12_64'),
    'SLES_15_64': GuestOS('SLES_15_64'),
    'SLES_16_64': GuestOS('SLES_16_64'),
    'NLD_9': GuestOS('NLD_9'),
    'OES': GuestOS('OES'),
    'SJDS': GuestOS('SJDS'),
    'MANDRAKE': GuestOS('MANDRAKE'),
    'MANDRIVA': GuestOS('MANDRIVA'),
    'MANDRIVA_64': GuestOS('MANDRIVA_64'),
    'TURBO_LINUX': GuestOS('TURBO_LINUX'),
    'TURBO_LINUX_64': GuestOS('TURBO_LINUX_64'),
    'UBUNTU': GuestOS('UBUNTU'),
    'UBUNTU_64': GuestOS('UBUNTU_64'),
    'DEBIAN_4': GuestOS('DEBIAN_4'),
    'DEBIAN_4_64': GuestOS('DEBIAN_4_64'),
    'DEBIAN_5': GuestOS('DEBIAN_5'),
    'DEBIAN_5_64': GuestOS('DEBIAN_5_64'),
    'DEBIAN_6': GuestOS('DEBIAN_6'),
    'DEBIAN_6_64': GuestOS('DEBIAN_6_64'),
    'DEBIAN_7': GuestOS('DEBIAN_7'),
    'DEBIAN_7_64': GuestOS('DEBIAN_7_64'),
    'DEBIAN_8': GuestOS('DEBIAN_8'),
    'DEBIAN_8_64': GuestOS('DEBIAN_8_64'),
    'DEBIAN_9': GuestOS('DEBIAN_9'),
    'DEBIAN_9_64': GuestOS('DEBIAN_9_64'),
    'DEBIAN_10': GuestOS('DEBIAN_10'),
    'DEBIAN_10_64': GuestOS('DEBIAN_10_64'),
    'DEBIAN_11': GuestOS('DEBIAN_11'),
    'DEBIAN_11_64': GuestOS('DEBIAN_11_64'),
    'DEBIAN_12': GuestOS('DEBIAN_12'),
    'DEBIAN_12_64': GuestOS('DEBIAN_12_64'),
    'ASIANUX_3': GuestOS('ASIANUX_3'),
    'ASIANUX_3_64': GuestOS('ASIANUX_3_64'),
    'ASIANUX_4': GuestOS('ASIANUX_4'),
    'ASIANUX_4_64': GuestOS('ASIANUX_4_64'),
    'ASIANUX_5_64': GuestOS('ASIANUX_5_64'),
    'ASIANUX_7_64': GuestOS('ASIANUX_7_64'),
    'ASIANUX_8_64': GuestOS('ASIANUX_8_64'),
    'ASIANUX_9_64': GuestOS('ASIANUX_9_64'),
    'OPENSUSE': GuestOS('OPENSUSE'),
    'OPENSUSE_64': GuestOS('OPENSUSE_64'),
    'FEDORA': GuestOS('FEDORA'),
    'FEDORA_64': GuestOS('FEDORA_64'),
    'COREOS_64': GuestOS('COREOS_64'),
    'VMWARE_PHOTON_64': GuestOS('VMWARE_PHOTON_64'),
    'OTHER_24X_LINUX': GuestOS('OTHER_24X_LINUX'),
    'OTHER_24X_LINUX_64': GuestOS('OTHER_24X_LINUX_64'),
    'OTHER_26X_LINUX': GuestOS('OTHER_26X_LINUX'),
    'OTHER_26X_LINUX_64': GuestOS('OTHER_26X_LINUX_64'),
    'OTHER_3X_LINUX': GuestOS('OTHER_3X_LINUX'),
    'OTHER_3X_LINUX_64': GuestOS('OTHER_3X_LINUX_64'),
    'OTHER_4X_LINUX': GuestOS('OTHER_4X_LINUX'),
    'OTHER_4X_LINUX_64': GuestOS('OTHER_4X_LINUX_64'),
    'OTHER_5X_LINUX': GuestOS('OTHER_5X_LINUX'),
    'OTHER_5X_LINUX_64': GuestOS('OTHER_5X_LINUX_64'),
    'OTHER_6X_LINUX': GuestOS('OTHER_6X_LINUX'),
    'OTHER_6X_LINUX_64': GuestOS('OTHER_6X_LINUX_64'),
    'OTHER_LINUX': GuestOS('OTHER_LINUX'),
    'GENERIC_LINUX': GuestOS('GENERIC_LINUX'),
    'OTHER_LINUX_64': GuestOS('OTHER_LINUX_64'),
    'SOLARIS_6': GuestOS('SOLARIS_6'),
    'SOLARIS_7': GuestOS('SOLARIS_7'),
    'SOLARIS_8': GuestOS('SOLARIS_8'),
    'SOLARIS_9': GuestOS('SOLARIS_9'),
    'SOLARIS_10': GuestOS('SOLARIS_10'),
    'SOLARIS_10_64': GuestOS('SOLARIS_10_64'),
    'SOLARIS_11_64': GuestOS('SOLARIS_11_64'),
    'OS2': GuestOS('OS2'),
    'ECOMSTATION': GuestOS('ECOMSTATION'),
    'ECOMSTATION_2': GuestOS('ECOMSTATION_2'),
    'NETWARE_4': GuestOS('NETWARE_4'),
    'NETWARE_5': GuestOS('NETWARE_5'),
    'NETWARE_6': GuestOS('NETWARE_6'),
    'OPENSERVER_5': GuestOS('OPENSERVER_5'),
    'OPENSERVER_6': GuestOS('OPENSERVER_6'),
    'UNIXWARE_7': GuestOS('UNIXWARE_7'),
    'DARWIN': GuestOS('DARWIN'),
    'DARWIN_64': GuestOS('DARWIN_64'),
    'DARWIN_10': GuestOS('DARWIN_10'),
    'DARWIN_10_64': GuestOS('DARWIN_10_64'),
    'DARWIN_11': GuestOS('DARWIN_11'),
    'DARWIN_11_64': GuestOS('DARWIN_11_64'),
    'DARWIN_12_64': GuestOS('DARWIN_12_64'),
    'DARWIN_13_64': GuestOS('DARWIN_13_64'),
    'DARWIN_14_64': GuestOS('DARWIN_14_64'),
    'DARWIN_15_64': GuestOS('DARWIN_15_64'),
    'DARWIN_16_64': GuestOS('DARWIN_16_64'),
    'DARWIN_17_64': GuestOS('DARWIN_17_64'),
    'DARWIN_18_64': GuestOS('DARWIN_18_64'),
    'DARWIN_19_64': GuestOS('DARWIN_19_64'),
    'DARWIN_20_64': GuestOS('DARWIN_20_64'),
    'DARWIN_21_64': GuestOS('DARWIN_21_64'),
    'DARWIN_22_64': GuestOS('DARWIN_22_64'),
    'DARWIN_23_64': GuestOS('DARWIN_23_64'),
    'VMKERNEL': GuestOS('VMKERNEL'),
    'VMKERNEL_5': GuestOS('VMKERNEL_5'),
    'VMKERNEL_6': GuestOS('VMKERNEL_6'),
    'VMKERNEL_65': GuestOS('VMKERNEL_65'),
    'VMKERNEL_7': GuestOS('VMKERNEL_7'),
    'VMKERNEL_8': GuestOS('VMKERNEL_8'),
    'AMAZONLINUX2_64': GuestOS('AMAZONLINUX2_64'),
    'AMAZONLINUX3_64': GuestOS('AMAZONLINUX3_64'),
    'CRXPOD_1': GuestOS('CRXPOD_1'),
    'CRXSYS_1': GuestOS('CRXSYS_1'),
    'ROCKYLINUX_64': GuestOS('ROCKYLINUX_64'),
    'ALMALINUX_64': GuestOS('ALMALINUX_64'),
    'OTHER': GuestOS('OTHER'),
    'OTHER_64': GuestOS('OTHER_64'),
})
GuestOS._set_binding_type(type.EnumType(
    'com.vmware.vcenter.vm.guest_OS',
    GuestOS))



class GuestOSFamily(Enum):
    """
    The ``GuestOSFamily`` class defines the valid guest operating system family
    types reported by a virtual machine. This enumeration was added in vSphere
    API 6.7.

    .. note::
        This class represents an enumerated type in the interface language
        definition. The class contains class attributes which represent the
        values in the current version of the enumerated type. Newer versions of
        the enumerated type may contain new values. To use new values of the
        enumerated type in communication with a server that supports the newer
        version of the API, you instantiate this class. See :ref:`enumerated
        type description page <enumeration_description>`.
    """
    WINDOWS = None
    """
    Windows operating system. This class attribute was added in vSphere API
    6.7.

    """
    LINUX = None
    """
    Linux operating system. This class attribute was added in vSphere API 6.7.

    """
    NETWARE = None
    """
    Novell Netware. This class attribute was added in vSphere API 6.7.

    """
    SOLARIS = None
    """
    Solaris operating system. This class attribute was added in vSphere API
    6.7.

    """
    DARWIN = None
    """
    Mac OS operating system. This class attribute was added in vSphere API 6.7.

    """
    OTHER = None
    """
    Other operating systems. This class attribute was added in vSphere API 6.7.

    """

    def __init__(self, string):
        """
        :type  string: :class:`str`
        :param string: String value for the :class:`GuestOSFamily` instance.
        """
        Enum.__init__(string)

GuestOSFamily._set_values({
    'WINDOWS': GuestOSFamily('WINDOWS'),
    'LINUX': GuestOSFamily('LINUX'),
    'NETWARE': GuestOSFamily('NETWARE'),
    'SOLARIS': GuestOSFamily('SOLARIS'),
    'DARWIN': GuestOSFamily('DARWIN'),
    'OTHER': GuestOSFamily('OTHER'),
})
GuestOSFamily._set_binding_type(type.EnumType(
    'com.vmware.vcenter.vm.guest_OS_family',
    GuestOSFamily))




class DataSets(VapiInterface):
    """
    The ``DataSets`` class provides methods for sharing information between a
    virtual machine and its guest operating system. 
    
    See the VMware Guest SDK Programming Guide for details on using DataSets
    from within a virtual machine. 
    
    Information is grouped into data sets, each of which contains key-value
    entries comprising the data. It's expected that each application using the
    service will have at least one unique data set in which to store its data
    to avoid conflict with other applications. Each data set has attributes
    defining its access control and interoperability configuration. 
    
    It's not recommended that sensitive data (for example, passwords or private
    keys) be stored in plain-text. The data will be visible to other
    applications, running both on the management network and within the guest.
    The data can also be exposed by backups or templates. 
    
    Data set support requires the virtual machine be at virtual hardware
    version :attr:`Hardware.Version.VMX_20` or later. 
    
    Data sets should only be modified by the application that creates them.
    Otherwise the application may stop working.. This class was added in
    vSphere API 8.0.0.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.data_sets'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _DataSetsStub)
        self._VAPI_OPERATION_IDS = {}

    class Access(Enum):
        """
        Possible Entry access modes. This enumeration was added in vSphere API
        8.0.0.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NONE = None
        """
        No access is allowed for data set Entries. This class attribute was added
        in vSphere API 8.0.0.0.

        """
        READ_ONLY = None
        """
        Only read access is allowed for data set Entries. This class attribute was
        added in vSphere API 8.0.0.0.

        """
        READ_WRITE = None
        """
        Full read, write and delete access is allowed on data set Entries. This
        class attribute was added in vSphere API 8.0.0.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Access` instance.
            """
            Enum.__init__(string)

    Access._set_values({
        'NONE': Access('NONE'),
        'READ_ONLY': Access('READ_ONLY'),
        'READ_WRITE': Access('READ_WRITE'),
    })
    Access._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.data_sets.access',
        Access))


    class Info(VapiStruct):
        """
        The ``DataSets.Info`` class describes a data set. This class was added in
        vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     description=None,
                     host=None,
                     guest=None,
                     used=None,
                     omit_from_snapshot_and_clone=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: The name of the data set. This attribute was added in vSphere API
                8.0.0.0.
            :type  description: :class:`str`
            :param description: A description of how the data set is used by its creator. This
                attribute was added in vSphere API 8.0.0.0.
            :type  host: :class:`DataSets.Access`
            :param host: Host access control. 
                
                Controls access to the data set by the
                :class:`com.vmware.vcenter.vm.data_sets_client.Entries` methods..
                This attribute was added in vSphere API 8.0.0.0.
            :type  guest: :class:`DataSets.Access`
            :param guest: Guest access control. 
                
                Controls access to the data set from in-guest APIs.. This attribute
                was added in vSphere API 8.0.0.0.
            :type  used: :class:`long`
            :param used: The total size in bytes of the Entry data in use by this data set.
                This attribute was added in vSphere API 8.0.0.0.
            :type  omit_from_snapshot_and_clone: :class:`bool`
            :param omit_from_snapshot_and_clone: If :class:`set`, the data set is considered a property of the
                virtual machine, and is not included in a snapshot operation or
                when the virtual machine is cloned. When a virtual machine is
                reverted to a snapshot, any data set with {\\\\@link
                #omitFromSnapshotAndClone) {\\\\@term set} will be destroyed. Any
                data set with {\\\\@link #omitFromSnapshotAndClone} {\\\\@term
                unset} will be restored to the state when the snapshot was created.
                This attribute was added in vSphere API 8.0.0.0.
            """
            self.name = name
            self.description = description
            self.host = host
            self.guest = guest
            self.used = used
            self.omit_from_snapshot_and_clone = omit_from_snapshot_and_clone
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.data_sets.info', {
            'name': type.StringType(),
            'description': type.StringType(),
            'host': type.ReferenceType(__name__, 'DataSets.Access'),
            'guest': type.ReferenceType(__name__, 'DataSets.Access'),
            'used': type.IntegerType(),
            'omit_from_snapshot_and_clone': type.BooleanType(),
        },
        Info,
        False,
        None))


    class CreateSpec(VapiStruct):
        """
        The ``DataSets.CreateSpec`` class describes a data set to be created. This
        class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     description=None,
                     host=None,
                     guest=None,
                     omit_from_snapshot_and_clone=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: The name of the data set. **It is recommended that this value take
                the form "com.company.project" to avoid conflict with other
                uses.**. This attribute was added in vSphere API 8.0.0.0.
            :type  description: :class:`str`
            :param description: A description of how the data set is used by its creator. This
                field can contain up to 1024 bytes. This attribute was added in
                vSphere API 8.0.0.0.
            :type  host: :class:`DataSets.Access`
            :param host: Host access control. 
                
                Controls access to the data set by the
                :class:`com.vmware.vcenter.vm.data_sets_client.Entries` methods..
                This attribute was added in vSphere API 8.0.0.0.
            :type  guest: :class:`DataSets.Access`
            :param guest: Guest access control. 
                
                Controls access to the data set from the in-guest APIs.. This
                attribute was added in vSphere API 8.0.0.0.
            :type  omit_from_snapshot_and_clone: :class:`bool` or ``None``
            :param omit_from_snapshot_and_clone: If :class:`set`, the data set is considered a property of the
                virtual machine, and is not included in a snapshot operation or
                when the virtual machine is cloned. When a virtual machine is
                reverted to a snapshot, any data set with {\\\\@link
                #omitFromSnapshotAndClone) {\\\\@term set} will be destroyed. Any
                data set with {\\\\@link #omitFromSnapshotAndClone} {\\\\@term
                unset} will be restored to the state when the snapshot was created.
                This attribute was added in vSphere API 8.0.0.0.
                If None, the data set is copied when a virtual machine is cloned or
                a snapshot is taken.
            """
            self.name = name
            self.description = description
            self.host = host
            self.guest = guest
            self.omit_from_snapshot_and_clone = omit_from_snapshot_and_clone
            VapiStruct.__init__(self)


    CreateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.data_sets.create_spec', {
            'name': type.StringType(),
            'description': type.StringType(),
            'host': type.ReferenceType(__name__, 'DataSets.Access'),
            'guest': type.ReferenceType(__name__, 'DataSets.Access'),
            'omit_from_snapshot_and_clone': type.OptionalType(type.BooleanType()),
        },
        CreateSpec,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``DataSets.UpdateSpec`` class describes attibutes of a data set that
        can be modified. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     description=None,
                     host=None,
                     guest=None,
                     omit_from_snapshot_and_clone=None,
                    ):
            """
            :type  description: :class:`str` or ``None``
            :param description: A description of how the data set is used by its creator. This
                field can contain up to 1024 bytes. This attribute was added in
                vSphere API 8.0.0.0.
                If set, the value is changed.
            :type  host: :class:`DataSets.Access` or ``None``
            :param host: The access control from the host. This attribute was added in
                vSphere API 8.0.0.0.
                If set, the value is changed.
            :type  guest: :class:`DataSets.Access` or ``None``
            :param guest: The access control from the guest. This attribute was added in
                vSphere API 8.0.0.0.
                If set, the value is changed.
            :type  omit_from_snapshot_and_clone: :class:`bool` or ``None``
            :param omit_from_snapshot_and_clone: If :class:`set`, the data set is considered a property of the
                virtual machine, and is not included in a snapshot operation or
                when the virtual machine is cloned. When a virtual machine is
                reverted to a snapshot, any data set with {\\\\@link
                #omitFromSnapshotAndClone) {\\\\@term set} will be destroyed. Any
                data set with {\\\\@link #omitFromSnapshotAndClone} {\\\\@term
                unset} will be restored to the state when the snapshot was created.
                This attribute was added in vSphere API 8.0.0.0.
                If set, the value is changed.
            """
            self.description = description
            self.host = host
            self.guest = guest
            self.omit_from_snapshot_and_clone = omit_from_snapshot_and_clone
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.data_sets.update_spec', {
            'description': type.OptionalType(type.StringType()),
            'host': type.OptionalType(type.ReferenceType(__name__, 'DataSets.Access')),
            'guest': type.OptionalType(type.ReferenceType(__name__, 'DataSets.Access')),
            'omit_from_snapshot_and_clone': type.OptionalType(type.BooleanType()),
        },
        UpdateSpec,
        False,
        None))


    class Summary(VapiStruct):
        """
        Basic data set information. This class was added in vSphere API 8.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     data_set=None,
                     name=None,
                     description=None,
                    ):
            """
            :type  data_set: :class:`str`
            :param data_set: The identifier of the data set. This attribute was added in vSphere
                API 8.0.0.0.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.vcenter.vm.DataSet``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.vcenter.vm.DataSet``.
            :type  name: :class:`str`
            :param name: The name of the data set. This attribute was added in vSphere API
                8.0.0.0.
            :type  description: :class:`str`
            :param description: The description of the data set. This attribute was added in
                vSphere API 8.0.0.0.
            """
            self.data_set = data_set
            self.name = name
            self.description = description
            VapiStruct.__init__(self)


    Summary._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.data_sets.summary', {
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'name': type.StringType(),
            'description': type.StringType(),
        },
        Summary,
        False,
        None))



    def create(self,
               vm,
               spec,
               ):
        """
        Creates a new data set. This method was added in vSphere API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  spec: :class:`DataSets.CreateSpec`
        :param spec: Specification of the data set to be created.
        :rtype: :class:`str`
        :return: The identifier of the new data set.
            The return value will be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyExists` 
            if the data set with the same name already exists.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the specification is incorrect.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is in a state that doesn't allow
            modifications, for example suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the new data set requires more resources than are available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetCreate``.
        """
        return self._invoke('create',
                            {
                            'vm': vm,
                            'spec': spec,
                            })

    def delete(self,
               vm,
               data_set,
               force=None,
               ):
        """
        Delete a data set. This method was added in vSphere API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set to be deleted.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :type  force: :class:`bool` or ``None``
        :param force: If true, delete the data set even if it is not empty.
            If None a :class:`com.vmware.vapi.std.errors_client.ResourceInUse`
            exception will be reported if the data set is not empty. This is
            the equivalent of passing the value false.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is in a state that doesn't allow
            modifications, for example suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            if the data set is not empty and ``force`` is not :class:`set`.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetDelete``.
        """
        return self._invoke('delete',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            'force': force,
                            })

    def get(self,
            vm,
            data_set,
            ):
        """
        Returns information describing a data set. This method was added in
        vSphere API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set to be queried.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :rtype: :class:`DataSets.Info`
        :return: Details about the data set.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetGet``.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            })

    def update(self,
               vm,
               data_set,
               spec,
               ):
        """
        Modifies the attributes of a data set. This method was added in vSphere
        API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  data_set: :class:`str`
        :param data_set: Identifier of the data set to be queried.
            The parameter must be an identifier for the resource type:
            ``com.vmware.vcenter.vm.DataSet``.
        :type  spec: :class:`DataSets.UpdateSpec`
        :param spec: new attributes of the data set. Data sets should only be modified
            by the application that creates them. Otherwise the application may
            stop working.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if any of the new attributes are invalid.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is in a state that doesn't allow
            modification, for example suspendeds.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the data set is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if the new data set attributes requires more resources than are
            available.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetUpdate``.
        """
        return self._invoke('update',
                            {
                            'vm': vm,
                            'data_set': data_set,
                            'spec': spec,
                            })

    def list(self,
             vm,
             ):
        """
        Lists the data sets of a virtual machine. This method was added in
        vSphere API 8.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :rtype: :class:`list` of :class:`DataSets.Summary`
        :return: The list of data sets.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual hardware version of the virtual machine does not
            support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the ESXi host version does not support DataSets
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.DataSets.DataSetList``.
        """
        return self._invoke('list',
                            {
                            'vm': vm,
                            })
class Hardware(VapiInterface):
    """
    The ``Hardware`` class provides methods for configuring the virtual
    hardware of a virtual machine.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.hardware'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _HardwareStub)
        self._VAPI_OPERATION_IDS = {}

    class Version(Enum):
        """
        The ``Hardware.Version`` class defines the valid virtual hardware versions
        for a virtual machine. See https://kb.vmware.com/s/article/1003746 (Virtual
        machine hardware versions (1003746)).

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        VMX_03 = None
        """
        Hardware version 3, first supported in ESXi 2.5.

        """
        VMX_04 = None
        """
        Hardware version 4, first supported in ESXi 3.0.

        """
        VMX_06 = None
        """
        Hardware version 6, first supported in WS 6.0.

        """
        VMX_07 = None
        """
        Hardware version 7, first supported in ESXi 4.0.

        """
        VMX_08 = None
        """
        Hardware version 8, first supported in ESXi 5.0.

        """
        VMX_09 = None
        """
        Hardware version 9, first supported in ESXi 5.1.

        """
        VMX_10 = None
        """
        Hardware version 10, first supported in ESXi 5.5.

        """
        VMX_11 = None
        """
        Hardware version 11, first supported in ESXi 6.0.

        """
        VMX_12 = None
        """
        Hardware version 12, first supported in Workstation 12.0.

        """
        VMX_13 = None
        """
        Hardware version 13, first supported in ESXi 6.5.

        """
        VMX_14 = None
        """
        Hardware version 14, first supported in ESXi 6.7. This class attribute was
        added in vSphere API 6.7.

        """
        VMX_15 = None
        """
        Hardware version 15, first supported in ESXi 6.7 Update 2. This class
        attribute was added in vSphere API 6.7.2.

        """
        VMX_16 = None
        """
        Hardware version 16, first supported in Workstation 15.0. This class
        attribute was added in vSphere API 7.0.0.0.

        """
        VMX_17 = None
        """
        Hardware version 17, first supported in ESXi 7.0.0-0. This class attribute
        was added in vSphere API 7.0.0.0.

        """
        VMX_18 = None
        """
        Hardware version 18, first supported in ESXi 7.0 U1. This class attribute
        was added in vSphere API 7.0.1.0.

        """
        VMX_19 = None
        """
        Hardware version 19, first supported in ESXi 7.0 U2. This class attribute
        was added in vSphere API 7.0.2.0.

        """
        VMX_20 = None
        """
        Hardware version 20, first supported in ESXi 8.0.0.1. This class attribute
        was added in vSphere API 8.0.0.1.

        """
        VMX_21 = None
        """
        Hardware version 21, first supported in ESXi 8.0 U2. This class attribute
        was added in vSphere API 8.0.2.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`Version` instance.
            """
            Enum.__init__(string)

    Version._set_values({
        'VMX_03': Version('VMX_03'),
        'VMX_04': Version('VMX_04'),
        'VMX_06': Version('VMX_06'),
        'VMX_07': Version('VMX_07'),
        'VMX_08': Version('VMX_08'),
        'VMX_09': Version('VMX_09'),
        'VMX_10': Version('VMX_10'),
        'VMX_11': Version('VMX_11'),
        'VMX_12': Version('VMX_12'),
        'VMX_13': Version('VMX_13'),
        'VMX_14': Version('VMX_14'),
        'VMX_15': Version('VMX_15'),
        'VMX_16': Version('VMX_16'),
        'VMX_17': Version('VMX_17'),
        'VMX_18': Version('VMX_18'),
        'VMX_19': Version('VMX_19'),
        'VMX_20': Version('VMX_20'),
        'VMX_21': Version('VMX_21'),
    })
    Version._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.hardware.version',
        Version))


    class UpgradePolicy(Enum):
        """
        The ``Hardware.UpgradePolicy`` class defines the valid virtual hardware
        upgrade policies for a virtual machine.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NEVER = None
        """
        Do not upgrade the virtual machine when it is powered on.

        """
        AFTER_CLEAN_SHUTDOWN = None
        """
        Run scheduled upgrade when the virtual machine is powered on after a clean
        shutdown of the guest operating system.

        """
        ALWAYS = None
        """
        Run scheduled upgrade when the virtual machine is powered on.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`UpgradePolicy` instance.
            """
            Enum.__init__(string)

    UpgradePolicy._set_values({
        'NEVER': UpgradePolicy('NEVER'),
        'AFTER_CLEAN_SHUTDOWN': UpgradePolicy('AFTER_CLEAN_SHUTDOWN'),
        'ALWAYS': UpgradePolicy('ALWAYS'),
    })
    UpgradePolicy._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.hardware.upgrade_policy',
        UpgradePolicy))


    class UpgradeStatus(Enum):
        """
        The ``Hardware.UpgradeStatus`` class defines the valid virtual hardware
        upgrade statuses for a virtual machine.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NONE = None
        """
        No scheduled upgrade has been attempted.

        """
        PENDING = None
        """
        Upgrade is scheduled but has not yet been run.

        """
        SUCCESS = None
        """
        The most recent scheduled upgrade was successful.

        """
        FAILED = None
        """
        The most recent scheduled upgrade was not successful.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`UpgradeStatus` instance.
            """
            Enum.__init__(string)

    UpgradeStatus._set_values({
        'NONE': UpgradeStatus('NONE'),
        'PENDING': UpgradeStatus('PENDING'),
        'SUCCESS': UpgradeStatus('SUCCESS'),
        'FAILED': UpgradeStatus('FAILED'),
    })
    UpgradeStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.hardware.upgrade_status',
        UpgradeStatus))


    class Info(VapiStruct):
        """
        The ``Hardware.Info`` class contains information related to the virtual
        hardware of a virtual machine.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'upgrade_policy',
                {
                    'AFTER_CLEAN_SHUTDOWN' : [('upgrade_version', True)],
                    'ALWAYS' : [('upgrade_version', True)],
                    'NEVER' : [],
                }
            ),
            UnionValidator(
                'upgrade_status',
                {
                    'FAILED' : [('upgrade_error', True)],
                    'NONE' : [],
                    'PENDING' : [],
                    'SUCCESS' : [],
                }
            ),
        ]



        def __init__(self,
                     version=None,
                     upgrade_policy=None,
                     upgrade_version=None,
                     upgrade_status=None,
                     upgrade_error=None,
                    ):
            """
            :type  version: :class:`Hardware.Version`
            :param version: Virtual hardware version.
            :type  upgrade_policy: :class:`Hardware.UpgradePolicy`
            :param upgrade_policy: Scheduled upgrade policy.
            :type  upgrade_version: :class:`Hardware.Version`
            :param upgrade_version: Target hardware version to be used on the next scheduled virtual
                hardware upgrade.
                This attribute is optional and it is only relevant when the value
                of ``upgradePolicy`` is one of
                :attr:`Hardware.UpgradePolicy.AFTER_CLEAN_SHUTDOWN` or
                :attr:`Hardware.UpgradePolicy.ALWAYS`.
            :type  upgrade_status: :class:`Hardware.UpgradeStatus`
            :param upgrade_status: Scheduled upgrade status.
            :type  upgrade_error: :class:`Exception`
            :param upgrade_error: Reason for the scheduled upgrade failure.
                This attribute is optional and it is only relevant when the value
                of ``upgradeStatus`` is :attr:`Hardware.UpgradeStatus.FAILED`.
            """
            self.version = version
            self.upgrade_policy = upgrade_policy
            self.upgrade_version = upgrade_version
            self.upgrade_status = upgrade_status
            self.upgrade_error = upgrade_error
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.hardware.info', {
            'version': type.ReferenceType(__name__, 'Hardware.Version'),
            'upgrade_policy': type.ReferenceType(__name__, 'Hardware.UpgradePolicy'),
            'upgrade_version': type.OptionalType(type.ReferenceType(__name__, 'Hardware.Version')),
            'upgrade_status': type.ReferenceType(__name__, 'Hardware.UpgradeStatus'),
            'upgrade_error': type.OptionalType(type.AnyErrorType()),
        },
        Info,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The ``Hardware.UpdateSpec`` class describes the updates to virtual hardware
        settings of a virtual machine.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'upgrade_policy',
                {
                    'AFTER_CLEAN_SHUTDOWN' : [('upgrade_version', False)],
                    'ALWAYS' : [('upgrade_version', False)],
                    'NEVER' : [],
                }
            ),
        ]



        def __init__(self,
                     upgrade_policy=None,
                     upgrade_version=None,
                    ):
            """
            :type  upgrade_policy: :class:`Hardware.UpgradePolicy` or ``None``
            :param upgrade_policy: Scheduled upgrade policy. 
                
                If set to :attr:`Hardware.UpgradePolicy.NEVER`, the
                :attr:`Hardware.Info.upgrade_version` attribute will be reset to
                None.
                If None, the value is unchanged.
            :type  upgrade_version: :class:`Hardware.Version` or ``None``
            :param upgrade_version: Target hardware version to be used on the next scheduled virtual
                hardware upgrade. 
                
                If specified, this attribute must represent a newer virtual
                hardware version than the current virtual hardware version reported
                in :attr:`Hardware.Info.version`.
                If :attr:`Hardware.UpdateSpec.upgrade_policy` is set to
                :attr:`Hardware.UpgradePolicy.NEVER`, this attribute must be None.
                Otherwise, if this attribute is None, default to the most recent
                virtual hardware version supported by the server.
            """
            self.upgrade_policy = upgrade_policy
            self.upgrade_version = upgrade_version
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.hardware.update_spec', {
            'upgrade_policy': type.OptionalType(type.ReferenceType(__name__, 'Hardware.UpgradePolicy')),
            'upgrade_version': type.OptionalType(type.ReferenceType(__name__, 'Hardware.Version')),
        },
        UpdateSpec,
        False,
        None))



    def get(self,
            vm,
            ):
        """
        Returns the virtual hardware settings of a virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :rtype: :class:`Hardware.Info`
        :return: Virtual hardware settings of the virtual machine.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if the virtual machine's configuration state cannot be accessed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            })

    def update(self,
               vm,
               spec,
               ):
        """
        Updates the virtual hardware settings of a virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  spec: :class:`Hardware.UpdateSpec`
        :param spec: Specification for updating the virtual hardware settings of the
            virtual machine.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the virtual machine is already configured for the desired
            hardware version.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the requested virtual hardware version is not newer than the
            current version.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the requested virtual hardware version is not supported by the
            server.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is busy performing another operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if the virtual machine's configuration state cannot be accessed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('update',
                            {
                            'vm': vm,
                            'spec': spec,
                            })

    def upgrade(self,
                vm,
                version=None,
                ):
        """
        Upgrades the virtual machine to a newer virtual hardware version.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  version: :class:`Hardware.Version` or ``None``
        :param version: New virtual machine version.
            If None, defaults to the most recent virtual hardware version
            supported by the server.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is not powered off.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the virtual machine is already configured for the desired
            hardware version.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if ``version`` is older than the current virtual hardware version.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if ``version`` is not supported by the server.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is busy performing another operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if the virtual machine's configuration state cannot be accessed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        """
        return self._invoke('upgrade',
                            {
                            'vm': vm,
                            'version': version,
                            })
class Identity(VapiInterface):
    """
    The ``Identity`` class provides methods for managing the identity of a
    virtual machine. This class was added in vSphere API 6.7.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.identity'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _IdentityStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``Identity.Info`` class contains information about the identity of a
        virtual machine. This class was added in vSphere API 6.7.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     name=None,
                     bios_uuid=None,
                     instance_uuid=None,
                    ):
            """
            :type  name: :class:`str`
            :param name: Virtual machine name. This attribute was added in vSphere API
                6.7.1.
            :type  bios_uuid: :class:`str`
            :param bios_uuid: 128-bit SMBIOS UUID of a virtual machine represented as a
                hexadecimal string in "12345678-abcd-1234-cdef-123456789abc"
                format. This attribute was added in vSphere API 6.7.1.
            :type  instance_uuid: :class:`str`
            :param instance_uuid: VirtualCenter-specific 128-bit UUID of a virtual machine,
                represented as a hexademical string. This identifier is used by
                VirtualCenter to uniquely identify all virtual machine instances,
                including those that may share the same SMBIOS UUID. This attribute
                was added in vSphere API 6.7.1.
            """
            self.name = name
            self.bios_uuid = bios_uuid
            self.instance_uuid = instance_uuid
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.identity.info', {
            'name': type.StringType(),
            'bios_uuid': type.StringType(),
            'instance_uuid': type.StringType(),
        },
        Info,
        False,
        None))


class LibraryItem(VapiInterface):
    """
    The ``LibraryItem`` class provides methods to identify virtual machines
    managed by Content Library. This class was added in vSphere API 6.9.1.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.library_item'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _LibraryItemStub)
        self._VAPI_OPERATION_IDS = {}

    class Info(VapiStruct):
        """
        The ``LibraryItem.Info`` class contains information about the library item
        associated with a virtual machine. This class was added in vSphere API
        6.9.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     check_out=None,
                    ):
            """
            :type  check_out: :class:`LibraryItem.CheckOutInfo` or ``None``
            :param check_out: Information about the checked out virtual machine. This attribute
                was added in vSphere API 6.9.1.
                If None, the virtual machine is not checked out from a library
                item.
            """
            self.check_out = check_out
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.library_item.info', {
            'check_out': type.OptionalType(type.ReferenceType(__name__, 'LibraryItem.CheckOutInfo')),
        },
        Info,
        False,
        None))


    class CheckOutInfo(VapiStruct):
        """
        The ``LibraryItem.CheckOutInfo`` class contains information about a virtual
        machine checked out of a content library item. This class was added in
        vSphere API 6.9.1.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     library_item=None,
                    ):
            """
            :type  library_item: :class:`str`
            :param library_item: Identifier of the library item that the virtual machine is checked
                out from. This attribute was added in vSphere API 6.9.1.
                When clients pass a value of this class as a parameter, the
                attribute must be an identifier for the resource type:
                ``com.vmware.content.library.Item``. When methods return a value of
                this class as a return value, the attribute will be an identifier
                for the resource type: ``com.vmware.content.library.Item``.
            """
            self.library_item = library_item
            VapiStruct.__init__(self)


    CheckOutInfo._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.library_item.check_out_info', {
            'library_item': type.IdType(resource_types='com.vmware.content.library.Item'),
        },
        CheckOutInfo,
        False,
        None))



    def get(self,
            vm,
            ):
        """
        Returns the information about the library item associated with the
        virtual machine. This method was added in vSphere API 6.9.1.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :rtype: :class:`LibraryItem.Info`
        :return: Information about the library item associated with the virtual
            machine.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user that requested the method cannot be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user that requested the method is not authorized to perform
            the method.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            })
class Power(VapiInterface):
    """
    The ``Power`` class provides methods for managing the power state of a
    virtual machine.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.power'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _PowerStub)
        self._VAPI_OPERATION_IDS = {}

    class State(Enum):
        """
        The ``Power.State`` class defines the valid power states for a virtual
        machine.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        POWERED_OFF = None
        """
        The virtual machine is powered off.

        """
        POWERED_ON = None
        """
        The virtual machine is powered on.

        """
        SUSPENDED = None
        """
        The virtual machine is suspended.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`State` instance.
            """
            Enum.__init__(string)

    State._set_values({
        'POWERED_OFF': State('POWERED_OFF'),
        'POWERED_ON': State('POWERED_ON'),
        'SUSPENDED': State('SUSPENDED'),
    })
    State._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.power.state',
        State))


    class Info(VapiStruct):
        """
        The ``Power.Info`` class contains information about the power state of a
        virtual machine.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """

        _validator_list = [
            UnionValidator(
                'state',
                {
                    'POWERED_OFF' : [('clean_power_off', True)],
                    'POWERED_ON' : [],
                    'SUSPENDED' : [],
                }
            ),
        ]



        def __init__(self,
                     state=None,
                     clean_power_off=None,
                    ):
            """
            :type  state: :class:`Power.State`
            :param state: Power state of the virtual machine.
            :type  clean_power_off: :class:`bool`
            :param clean_power_off: Flag indicating whether the virtual machine was powered off
                cleanly. This attribute may be used to detect that the virtual
                machine crashed unexpectedly and should be restarted.
                This attribute is optional and it is only relevant when the value
                of ``state`` is :attr:`Power.State.POWERED_OFF`.
            """
            self.state = state
            self.clean_power_off = clean_power_off
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.power.info', {
            'state': type.ReferenceType(__name__, 'Power.State'),
            'clean_power_off': type.OptionalType(type.BooleanType()),
        },
        Info,
        False,
        None))



    def get(self,
            vm,
            ):
        """
        Returns the power state information of a virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :rtype: :class:`Power.Info`
        :return: Power state information for the specified virtual machine.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if the virtual machine's configuration or execution state cannot be
            accessed.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``System.Read``.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            })

    def start(self,
              vm,
              ):
        """
        Powers on a powered-off or suspended virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the virtual machine is already powered on.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unsupported` 
            if the virtual machine does not support being powered on (e.g.
            marked as a template, serving as a fault-tolerance secondary
            virtual machine).
        :raise: :class:`com.vmware.vapi.std.errors_client.UnableToAllocateResource` 
            if resources cannot be allocated for the virtual machine (e.g.
            physical resource allocation policy cannot be satisfied,
            insufficient licenses are available to run the virtual machine).
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInaccessible` 
            if resources required by the virtual machine are not accessible
            (e.g. virtual machine configuration files or virtual disks are on
            inaccessible storage, no hosts are available to run the virtual
            machine).
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceInUse` 
            if resources required by the virtual machine are in use (e.g.
            virtual machine configuration files or virtual disks are locked,
            host containing the virtual machine is an HA failover host).
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is performing another operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.Interact.PowerOn``.
        """
        return self._invoke('start',
                            {
                            'vm': vm,
                            })

    def stop(self,
             vm,
             ):
        """
        Powers off a powered-on or suspended virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the virtual machine is already powered off.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is performing another operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.Interact.PowerOff``.
        """
        return self._invoke('stop',
                            {
                            'vm': vm,
                            })

    def suspend(self,
                vm,
                ):
        """
        Suspends a powered-on virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            if the virtual machine is already suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is powered off.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is performing another operation.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.Interact.Suspend``.
        """
        return self._invoke('suspend',
                            {
                            'vm': vm,
                            })

    def reset(self,
              vm,
              ):
        """
        Resets a powered-on virtual machine.

        :type  vm: :class:`str`
        :param vm: Virtual machine identifier.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is powered off or suspended.
        :raise: :class:`com.vmware.vapi.std.errors_client.ResourceBusy` 
            if the virtual machine is performing another operation
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the system is unable to communicate with a service to complete
            the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user can not be authenticated.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized` 
            if the user doesn't have the required privileges.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthorized`
            if you do not have all of the privileges described as follows: 
            
            * The resource ``VirtualMachine`` referenced by the parameter
              ``vm`` requires ``VirtualMachine.Interact.Reset``.
        """
        return self._invoke('reset',
                            {
                            'vm': vm,
                            })
class Tools(VapiInterface):
    """
    The ``Tools`` class provides methods for managing VMware Tools in the guest
    operating system. This class was added in vSphere API 7.0.0.0.
    """

    _VAPI_SERVICE_ID = 'com.vmware.vcenter.vm.tools'
    """
    Identifier of the service in canonical form.
    """
    def __init__(self, config):
        """
        :type  config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param config: Configuration to be used for creating the stub.
        """
        VapiInterface.__init__(self, config, _ToolsStub)
        self._VAPI_OPERATION_IDS = {}

    class RunState(Enum):
        """
        Current run state of VMware Tools in the guest operating system. This
        enumeration was added in vSphere API 7.0.0.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NOT_RUNNING = None
        """
        VMware Tools is not running. This class attribute was added in vSphere API
        7.0.0.0.

        """
        RUNNING = None
        """
        VMware Tools is running. This class attribute was added in vSphere API
        7.0.0.0.

        """
        EXECUTING_SCRIPTS = None
        """
        VMware Tools is running scripts as part of a state transition. This class
        attribute was added in vSphere API 7.0.0.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`RunState` instance.
            """
            Enum.__init__(string)

    RunState._set_values({
        'NOT_RUNNING': RunState('NOT_RUNNING'),
        'RUNNING': RunState('RUNNING'),
        'EXECUTING_SCRIPTS': RunState('EXECUTING_SCRIPTS'),
    })
    RunState._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.tools.run_state',
        RunState))


    class UpgradePolicy(Enum):
        """
        The ``Tools.UpgradePolicy`` class defines when Tools are auto-upgraded for
        a virtual machine. This enumeration was added in vSphere API 7.0.0.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        MANUAL = None
        """
        No auto-upgrades for Tools will be performed for this virtual machine.
        Users must manually invoke the :func:`Tools.upgrade` method to update
        Tools. This class attribute was added in vSphere API 7.0.0.0.

        """
        UPGRADE_AT_POWER_CYCLE = None
        """
        When the virtual machine is power-cycled, the system checks for a newer
        version of Tools when the virtual machine is powered on. If it is
        available, a Tools upgrade is automatically performed on the virtual
        machine and it is rebooted if necessary. This class attribute was added in
        vSphere API 7.0.0.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`UpgradePolicy` instance.
            """
            Enum.__init__(string)

    UpgradePolicy._set_values({
        'MANUAL': UpgradePolicy('MANUAL'),
        'UPGRADE_AT_POWER_CYCLE': UpgradePolicy('UPGRADE_AT_POWER_CYCLE'),
    })
    UpgradePolicy._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.tools.upgrade_policy',
        UpgradePolicy))


    class VersionStatus(Enum):
        """
        The ``Tools.VersionStatus`` class defines the version status types of
        VMware Tools installed in the guest operating system. This enumeration was
        added in vSphere API 7.0.0.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        NOT_INSTALLED = None
        """
        VMware Tools has never been installed. This class attribute was added in
        vSphere API 7.0.0.0.

        """
        CURRENT = None
        """
        VMware Tools is installed, and the version is current. This class attribute
        was added in vSphere API 7.0.0.0.

        """
        UNMANAGED = None
        """
        VMware Tools is installed, but it is not managed by VMware. This includes
        open-vm-tools or OSPs which should be managed by the guest operating
        system. This class attribute was added in vSphere API 7.0.0.0.

        """
        TOO_OLD_UNSUPPORTED = None
        """
        VMware Tools is installed, but the version is too old. This class attribute
        was added in vSphere API 7.0.0.0.

        """
        SUPPORTED_OLD = None
        """
        VMware Tools is installed, supported, but a newer version is available.
        This class attribute was added in vSphere API 7.0.0.0.

        """
        SUPPORTED_NEW = None
        """
        VMware Tools is installed, supported, and newer than the version available
        on the host. This class attribute was added in vSphere API 7.0.0.0.

        """
        TOO_NEW = None
        """
        VMware Tools is installed, and the version is known to be too new to work
        correctly with this virtual machine. This class attribute was added in
        vSphere API 7.0.0.0.

        """
        BLACKLISTED = None
        """
        VMware Tools is installed, but the installed version is known to have a
        grave bug and should be immediately upgraded. This class attribute was
        added in vSphere API 7.0.0.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`VersionStatus` instance.
            """
            Enum.__init__(string)

    VersionStatus._set_values({
        'NOT_INSTALLED': VersionStatus('NOT_INSTALLED'),
        'CURRENT': VersionStatus('CURRENT'),
        'UNMANAGED': VersionStatus('UNMANAGED'),
        'TOO_OLD_UNSUPPORTED': VersionStatus('TOO_OLD_UNSUPPORTED'),
        'SUPPORTED_OLD': VersionStatus('SUPPORTED_OLD'),
        'SUPPORTED_NEW': VersionStatus('SUPPORTED_NEW'),
        'TOO_NEW': VersionStatus('TOO_NEW'),
        'BLACKLISTED': VersionStatus('BLACKLISTED'),
    })
    VersionStatus._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.tools.version_status',
        VersionStatus))


    class ToolsInstallType(Enum):
        """
        The ``Tools.ToolsInstallType`` class defines the installation type of the
        Tools in the guest operating system. This enumeration was added in vSphere
        API 7.0.0.0.

        .. note::
            This class represents an enumerated type in the interface language
            definition. The class contains class attributes which represent the
            values in the current version of the enumerated type. Newer versions of
            the enumerated type may contain new values. To use new values of the
            enumerated type in communication with a server that supports the newer
            version of the API, you instantiate this class. See :ref:`enumerated
            type description page <enumeration_description>`.
        """
        UNKNOWN = None
        """
        Installation type is not known. Most likely tools have been installed by
        OSPs or open-vm-tools, but a version that does not report its install type
        or an install type that we do not recognize. This class attribute was added
        in vSphere API 7.0.0.0.

        """
        MSI = None
        """
        MSI is the installation type used for VMware Tools on Windows. This class
        attribute was added in vSphere API 7.0.0.0.

        """
        TAR = None
        """
        Tools have been installed by the tar installer. This class attribute was
        added in vSphere API 7.0.0.0.

        """
        OSP = None
        """
        OSPs are RPM or Debian packages tailored for the OS in the VM. See
        http://packages.vmware.com. This class attribute was added in vSphere API
        7.0.0.0.

        """
        OPEN_VM_TOOLS = None
        """
        open-vm-tools are the open-source version of VMware Tools, may have been
        packaged by the OS vendor. This class attribute was added in vSphere API
        7.0.0.0.

        """

        def __init__(self, string):
            """
            :type  string: :class:`str`
            :param string: String value for the :class:`ToolsInstallType` instance.
            """
            Enum.__init__(string)

    ToolsInstallType._set_values({
        'UNKNOWN': ToolsInstallType('UNKNOWN'),
        'MSI': ToolsInstallType('MSI'),
        'TAR': ToolsInstallType('TAR'),
        'OSP': ToolsInstallType('OSP'),
        'OPEN_VM_TOOLS': ToolsInstallType('OPEN_VM_TOOLS'),
    })
    ToolsInstallType._set_binding_type(type.EnumType(
        'com.vmware.vcenter.vm.tools.tools_install_type',
        ToolsInstallType))


    class Info(VapiStruct):
        """
        The ``Tools.Info`` class describes the VMWare Tools properties of a virtual
        machine. This class was added in vSphere API 7.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     auto_update_supported=None,
                     install_attempt_count=None,
                     error=None,
                     version_number=None,
                     version=None,
                     upgrade_policy=None,
                     version_status=None,
                     install_type=None,
                     run_state=None,
                    ):
            """
            :type  auto_update_supported: :class:`bool`
            :param auto_update_supported: Set if the virtual machine supports auto-upgrading Tools via
                :class:`Tools.UpgradePolicy`. This attribute was added in vSphere
                API 7.0.0.0.
            :type  install_attempt_count: :class:`long` or ``None``
            :param install_attempt_count: Number of attempts that have been made to install or upgrade the
                version of Tools installed on this virtual machine. This attribute
                was added in vSphere API 7.0.0.0.
                This attribute will be None if there have been no Tools install or
                upgrade attempt.
            :type  error: :class:`Exception` or ``None``
            :param error: Error that happened, if any, during last attempt to upgrade or
                install Tools. This attribute was added in vSphere API 7.0.0.0.
                This attribute will be None if a the last Tools install or upgrade
                attempt succeeded.
            :type  version_number: :class:`long` or ``None``
            :param version_number: Version of VMware Tools installed on the guest operating system.
                This attribute was added in vSphere API 7.0.0.0.
                This attribute wil be None if VMWare Tools is not installed. This
                is an integer constructed as follows: (((MJR) << 10) + ((MNR) << 5)
                + (REV)) Where MJR is tha major verson, MNR is the minor version
                and REV is the revision. Tools version = T Tools Version Major =
                MJR = (T / 1024) Tools Version Minor = MNR = ((T % 1024) / 32)
                Tools Version Revision = BASE = ((T % 1024) % 32) Tools actual
                version = MJR.MNR.REV
            :type  version: :class:`str` or ``None``
            :param version: Version of VMware Tools installed on the guest operating system.
                This is a human-readable value that should not be parsed. This
                attribute was added in vSphere API 7.0.0.0.
                This attribute wil be None if VMWare Tools is not installed.
            :type  upgrade_policy: :class:`Tools.UpgradePolicy`
            :param upgrade_policy: Tools upgrade policy setting for the virtual machine.
                :class:`Tools.UpgradePolicy`. This attribute was added in vSphere
                API 7.0.0.0.
            :type  version_status: :class:`Tools.VersionStatus` or ``None``
            :param version_status: Current version status of VMware Tools in the guest operating
                system, if known. This attribute was added in vSphere API 7.0.0.0.
                This attribute will be None if the version status is not known, for
                example if VMware Tools is too old to report the information.
            :type  install_type: :class:`Tools.ToolsInstallType` or ``None``
            :param install_type: Current installation type of VMware Tools in the guest operating
                system. This attribute was added in vSphere API 7.0.0.0.
                This attribute will be None if the installation type is not known,
                for example if VMware Tools is too old to report the information.
            :type  run_state: :class:`Tools.RunState`
            :param run_state: Current run state of VMware Tools in the guest operating system.
                This attribute was added in vSphere API 7.0.0.0.
            """
            self.auto_update_supported = auto_update_supported
            self.install_attempt_count = install_attempt_count
            self.error = error
            self.version_number = version_number
            self.version = version
            self.upgrade_policy = upgrade_policy
            self.version_status = version_status
            self.install_type = install_type
            self.run_state = run_state
            VapiStruct.__init__(self)


    Info._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.tools.info', {
            'auto_update_supported': type.BooleanType(),
            'install_attempt_count': type.OptionalType(type.IntegerType()),
            'error': type.OptionalType(type.AnyErrorType()),
            'version_number': type.OptionalType(type.IntegerType()),
            'version': type.OptionalType(type.StringType()),
            'upgrade_policy': type.ReferenceType(__name__, 'Tools.UpgradePolicy'),
            'version_status': type.OptionalType(type.ReferenceType(__name__, 'Tools.VersionStatus')),
            'install_type': type.OptionalType(type.ReferenceType(__name__, 'Tools.ToolsInstallType')),
            'run_state': type.ReferenceType(__name__, 'Tools.RunState'),
        },
        Info,
        False,
        None))


    class UpdateSpec(VapiStruct):
        """
        The (\\\\@name UpdateSpec} class describes the VMware Tools properties of a
        virtual machine that can be updated. This class was added in vSphere API
        7.0.0.0.

        .. tip::
            The arguments are used to initialize data attributes with the same
            names.
        """




        def __init__(self,
                     upgrade_policy=None,
                    ):
            """
            :type  upgrade_policy: :class:`Tools.UpgradePolicy` or ``None``
            :param upgrade_policy: Tools upgrade policy setting for the virtual machine.
                :class:`Tools.UpgradePolicy`. This attribute was added in vSphere
                API 7.0.0.0.
                If None the upgrade policy will not be modified.
            """
            self.upgrade_policy = upgrade_policy
            VapiStruct.__init__(self)


    UpdateSpec._set_binding_type(type.StructType(
        'com.vmware.vcenter.vm.tools.update_spec', {
            'upgrade_policy': type.OptionalType(type.ReferenceType(__name__, 'Tools.UpgradePolicy')),
        },
        UpdateSpec,
        False,
        None))



    def get(self,
            vm,
            ):
        """
        Get the properties of VMware Tools. This method was added in vSphere
        API 7.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :rtype: :class:`Tools.Info`
        :return: VMware Tools properties.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        """
        return self._invoke('get',
                            {
                            'vm': vm,
                            })

    def update(self,
               vm,
               spec,
               ):
        """
        Update the properties of VMware Tools. This method was added in vSphere
        API 7.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  spec: :class:`Tools.UpdateSpec`
        :param spec: The new values.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the system reports an error while responding to the request.
        :raise: :class:`com.vmware.vapi.std.errors_client.InvalidArgument` 
            if the :attr:`Tools.UpdateSpec.upgrade_policy` attribute contains a
            value that is not supported by the server.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        """
        return self._invoke('update',
                            {
                            'vm': vm,
                            'spec': spec,
                            })

    def upgrade(self,
                vm,
                command_line_options=None,
                ):
        """
        Begins the Tools upgrade process. To monitor the status of the Tools
        upgrade, clients should check the Tools status by calling
        :func:`Tools.get` and examining ``versionStatus`` and ``runState``.
        This method was added in vSphere API 7.0.0.0.

        :type  vm: :class:`str`
        :param vm: Identifier of the virtual machine.
            The parameter must be an identifier for the resource type:
            ``VirtualMachine``.
        :type  command_line_options: :class:`str` or ``None``
        :param command_line_options: Command line options passed to the installer to modify the
            installation procedure for Tools.
            Set if any additional options are desired.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotFound` 
            if the virtual machine is not found.
        :raise: :class:`com.vmware.vapi.std.errors_client.ServiceUnavailable` 
            if the VMware Tools are not running.
        :raise: :class:`com.vmware.vapi.std.errors_client.NotAllowedInCurrentState` 
            if the virtual machine is not powered on.
        :raise: :class:`com.vmware.vapi.std.errors_client.AlreadyInDesiredState` 
            is an upgrade is already in progress.
        :raise: :class:`com.vmware.vapi.std.errors_client.Error` 
            if the upgrade process fails inside the guest operating system.
        :raise: :class:`com.vmware.vapi.std.errors_client.Unauthenticated` 
            if the user cannot be authenticated.
        """
        return self._invoke('upgrade',
                            {
                            'vm': vm,
                            'command_line_options': command_line_options,
                            })
class _DataSetsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for create operation
        create_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'spec': type.ReferenceType(__name__, 'DataSets.CreateSpec'),
        })
        create_error_dict = {
            'com.vmware.vapi.std.errors.already_exists':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyExists'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        create_input_value_validator_list = [
        ]
        create_output_validator_list = [
        ]
        create_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/data-sets',
            request_body_parameter='spec',
            path_variables={
                'vm': 'vm',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'force': type.OptionalType(type.BooleanType()),
        })
        delete_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        delete_input_value_validator_list = [
        ]
        delete_output_validator_list = [
        ]
        delete_rest_metadata = OperationRestMetadata(
            http_method='DELETE',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
            },
            query_parameters={
                'force': 'force',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
            'data_set': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
            'spec': type.ReferenceType(__name__, 'DataSets.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/vm/{vm}/data-sets/{dataSet}',
            request_body_parameter='spec',
            path_variables={
                'vm': 'vm',
                'data_set': 'dataSet',
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
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        list_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),

        }
        list_input_value_validator_list = [
        ]
        list_output_validator_list = [
        ]
        list_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/vm/{vm}/data-sets',
            path_variables={
                'vm': 'vm',
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
            'create': {
                'input_type': create_input_type,
                'output_type': type.IdType(resource_types='com.vmware.vcenter.vm.DataSet'),
                'errors': create_error_dict,
                'input_value_validator_list': create_input_value_validator_list,
                'output_validator_list': create_output_validator_list,
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
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'DataSets.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'list': {
                'input_type': list_input_type,
                'output_type': type.ListType(type.ReferenceType(__name__, 'DataSets.Summary')),
                'errors': list_error_dict,
                'input_value_validator_list': list_input_value_validator_list,
                'output_validator_list': list_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'create': create_rest_metadata,
            'delete': delete_rest_metadata,
            'get': get_rest_metadata,
            'update': update_rest_metadata,
            'list': list_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.data_sets',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _HardwareStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
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
            url_template='/vcenter/vm/{vm}/hardware',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'spec': type.ReferenceType(__name__, 'Hardware.UpdateSpec'),
        })
        update_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
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
            url_template='/vcenter/vm/{vm}/hardware',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for upgrade operation
        upgrade_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'version': type.OptionalType(type.ReferenceType(__name__, 'Hardware.Version')),
        })
        upgrade_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.invalid_argument':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'InvalidArgument'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        upgrade_input_value_validator_list = [
        ]
        upgrade_output_validator_list = [
        ]
        upgrade_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/hardware/action/upgrade',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Hardware.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'upgrade': {
                'input_type': upgrade_input_type,
                'output_type': type.VoidType(),
                'errors': upgrade_error_dict,
                'input_value_validator_list': upgrade_input_value_validator_list,
                'output_validator_list': upgrade_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'update': update_rest_metadata,
            'upgrade': upgrade_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.hardware',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _IdentityStub(ApiInterfaceStub):
    def __init__(self, config):
        operations = {
        }
        rest_metadata = {
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.identity',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _LibraryItemStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
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
            url_template='/vcenter/vm/{vm}/library-item',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'LibraryItem.Info'),
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
            self, iface_name='com.vmware.vcenter.vm.library_item',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _PowerStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
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
            url_template='/vcenter/vm/{vm}/power',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for start operation
        start_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        start_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.unsupported':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unsupported'),
            'com.vmware.vapi.std.errors.unable_to_allocate_resource':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'UnableToAllocateResource'),
            'com.vmware.vapi.std.errors.resource_inaccessible':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInaccessible'),
            'com.vmware.vapi.std.errors.resource_in_use':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceInUse'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        start_input_value_validator_list = [
        ]
        start_output_validator_list = [
        ]
        start_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/power/start',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for stop operation
        stop_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        stop_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        stop_input_value_validator_list = [
        ]
        stop_output_validator_list = [
        ]
        stop_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/power/stop',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for suspend operation
        suspend_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        suspend_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        suspend_input_value_validator_list = [
        ]
        suspend_output_validator_list = [
        ]
        suspend_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/power/suspend',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for reset operation
        reset_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        reset_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.resource_busy':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ResourceBusy'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),
            'com.vmware.vapi.std.errors.unauthorized':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthorized'),

        }
        reset_input_value_validator_list = [
        ]
        reset_output_validator_list = [
        ]
        reset_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/power/reset',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Power.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'start': {
                'input_type': start_input_type,
                'output_type': type.VoidType(),
                'errors': start_error_dict,
                'input_value_validator_list': start_input_value_validator_list,
                'output_validator_list': start_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'stop': {
                'input_type': stop_input_type,
                'output_type': type.VoidType(),
                'errors': stop_error_dict,
                'input_value_validator_list': stop_input_value_validator_list,
                'output_validator_list': stop_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'suspend': {
                'input_type': suspend_input_type,
                'output_type': type.VoidType(),
                'errors': suspend_error_dict,
                'input_value_validator_list': suspend_input_value_validator_list,
                'output_validator_list': suspend_output_validator_list,
                'task_type': TaskType.NONE,
            },
            'reset': {
                'input_type': reset_input_type,
                'output_type': type.VoidType(),
                'errors': reset_error_dict,
                'input_value_validator_list': reset_input_value_validator_list,
                'output_validator_list': reset_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'start': start_rest_metadata,
            'stop': stop_rest_metadata,
            'suspend': suspend_rest_metadata,
            'reset': reset_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.power',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)

class _ToolsStub(ApiInterfaceStub):
    def __init__(self, config):
        # properties for get operation
        get_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
        })
        get_error_dict = {
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        get_input_value_validator_list = [
        ]
        get_output_validator_list = [
        ]
        get_rest_metadata = OperationRestMetadata(
            http_method='GET',
            url_template='/vcenter/vm/{vm}/tools',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
               },
            query_parameters={
            }
        )

        # properties for update operation
        update_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'spec': type.ReferenceType(__name__, 'Tools.UpdateSpec'),
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

        }
        update_input_value_validator_list = [
        ]
        update_output_validator_list = [
        ]
        update_rest_metadata = OperationRestMetadata(
            http_method='PATCH',
            url_template='/vcenter/vm/{vm}/tools',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        # properties for upgrade operation
        upgrade_input_type = type.StructType('operation-input', {
            'vm': type.IdType(resource_types='VirtualMachine'),
            'command_line_options': type.OptionalType(type.StringType()),
        })
        upgrade_error_dict = {
            'com.vmware.vapi.std.errors.not_found':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotFound'),
            'com.vmware.vapi.std.errors.service_unavailable':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'ServiceUnavailable'),
            'com.vmware.vapi.std.errors.not_allowed_in_current_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'NotAllowedInCurrentState'),
            'com.vmware.vapi.std.errors.already_in_desired_state':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'AlreadyInDesiredState'),
            'com.vmware.vapi.std.errors.error':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Error'),
            'com.vmware.vapi.std.errors.unauthenticated':
                type.ReferenceType('com.vmware.vapi.std.errors_client', 'Unauthenticated'),

        }
        upgrade_input_value_validator_list = [
        ]
        upgrade_output_validator_list = [
        ]
        upgrade_rest_metadata = OperationRestMetadata(
            http_method='POST',
            url_template='/vcenter/vm/{vm}/tools',
            path_variables={
                'vm': 'vm',
            },
             header_parameters={
                 },
            query_parameters={
            }
        )

        operations = {
            'get': {
                'input_type': get_input_type,
                'output_type': type.ReferenceType(__name__, 'Tools.Info'),
                'errors': get_error_dict,
                'input_value_validator_list': get_input_value_validator_list,
                'output_validator_list': get_output_validator_list,
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
            'upgrade': {
                'input_type': upgrade_input_type,
                'output_type': type.VoidType(),
                'errors': upgrade_error_dict,
                'input_value_validator_list': upgrade_input_value_validator_list,
                'output_validator_list': upgrade_output_validator_list,
                'task_type': TaskType.NONE,
            },
        }
        rest_metadata = {
            'get': get_rest_metadata,
            'update': update_rest_metadata,
            'upgrade': upgrade_rest_metadata,
        }
        ApiInterfaceStub.__init__(
            self, iface_name='com.vmware.vcenter.vm.tools',
            config=config, operations=operations, rest_metadata=rest_metadata,
            is_vapi_rest=True)


class StubFactory(StubFactoryBase):
    _attrs = {
        'DataSets': DataSets,
        'Hardware': Hardware,
        'Identity': Identity,
        'LibraryItem': LibraryItem,
        'Power': Power,
        'Tools': Tools,
        'console': 'com.vmware.vcenter.vm.console_client.StubFactory',
        'data_sets': 'com.vmware.vcenter.vm.data_sets_client.StubFactory',
        'guest': 'com.vmware.vcenter.vm.guest_client.StubFactory',
        'hardware': 'com.vmware.vcenter.vm.hardware_client.StubFactory',
        'storage': 'com.vmware.vcenter.vm.storage_client.StubFactory',
        'tools': 'com.vmware.vcenter.vm.tools_client.StubFactory',
    }

