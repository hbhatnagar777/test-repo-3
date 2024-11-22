# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing deployment operations

DeploymentHelper is the only class defined in this file

DeploymentHelper: Helper class to perform deployment operations

DeploymentHelper:

    deploy_vmware_ova()             --  Deploys the OVA into the given VMware vCenter Server

    validate_vm()                   --  Validates the newly deployed VM is up or not

    validate_services()             --  Validates the Commvault services on the new VM

"""

import time
import socket
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from pyVmomi import vim, vmodl
import tarfile
import os
from threading import Timer
from six.moves.urllib.request import Request, urlopen
import ssl


class DeploymentHelper:
    """Helper class to deploy OVA and do setup"""

    def __init__(self, testcase, **kwargs):
        """
        constructor for install related files
        """

        self.log = testcase.log
        self.testcase = testcase
        self.tcinputs = testcase.tcinputs
        self.kwargs = kwargs
        self.hvobj, self.machine, self.auth_code, self.vm_name, self.dc_obj, self.r_pool_obj, self.ds_obj, self.network_name, \
            self.network_obj, self.ip_assignment, self.diskProvisioning, self.use_dhcp, \
            self.ova_path, self.host, self.vm_pass, self.domain, self.cs_password, self.cs_user_name, self.cs_host_name_or_ip, \
            self.cs_client_name, self.net_mask, self.ip_address, self.default_gateway, self.primary_dns, self.secondary_dns = (
                                                                                                                                  None,) * 25
        self.server_host_name = self.tcinputs.get('vCenter', self.tcinputs.get('hyp_host_name'))
        self.user_name = self.tcinputs.get('vCenterUsername', self.tcinputs.get('hyp_user_name'))
        self.password = self.tcinputs.get('vCenterPassword', self.tcinputs.get('hyp_pwd'))
        self.create_connection()
        self.initialize_data()

    def create_connection(self):
        """
        Create a connection to the vcenter

        """
        try:
            self.hvobj = Hypervisor([self.server_host_name], self.user_name, self.password, 'vmware',
                                    self.testcase.commcell, socket.gethostbyname_ex(socket.gethostname())[2][0])
        except Exception as exp:
            self.log.exception("Exception when creating connection to vcenter for deploying OVA: {}".format(exp))
            raise exp

    def initialize_data(self):
        """
        Initialize all basic inputs for deploying OVA

        """
        try:
            dc_name = self.tcinputs['DataCenter']
            self.host = self.tcinputs['Host']
            self.dc_obj = self.get_dc_object(dc_name)
            r_pool = self.tcinputs.get('ResourcePool', 'Resources')
            self.r_pool_obj = self.get_rp(r_pool)
            ds_name = self.tcinputs['Datastore']
            self.ds_obj = self.get_ds(ds_name)
            self.network_name = self.tcinputs['NetworkName']
            self.network_obj = self.get_network(self.network_name)
            self.vm_name = self.tcinputs.get('lin_backup_gatewayname', self.tcinputs.get('FREL_Client'))
            self.ip_assignment = self.tcinputs.get('DHCPPolicy', 'dhcpPolicy')
            self.diskProvisioning = self.tcinputs.get('DiskProvisioning', 'thin')
            self.use_dhcp = self.tcinputs.get('Use_DHCP', 'True')
            self.ova_path = self.kwargs.get('ova_path', self.tcinputs.get('OVAPath', ''))
            self.auth_code = self.kwargs.get('auth_code', )
            self.vm_pass = self.tcinputs.get('lin_remote_userpassword', self.tcinputs.get('VMPassword', None))
            self.domain = self.tcinputs.get('Domain', '')
            self.cs_host_name_or_ip = self.tcinputs.get('cs_hostname_or_ip')
            self.cs_user_name = self.tcinputs.get('cs_username')
            self.cs_password = self.tcinputs.get('cs_password')
            self.cs_client_name = self.tcinputs.get('cs_clientname')
            self.ip_address = self.tcinputs.get('ip_address')
            self.default_gateway = self.tcinputs.get('default_gateway')
            self.primary_dns = self.tcinputs.get('primary_dns')
            self.secondary_dns = self.tcinputs.get('secondary_dns')
            self.net_mask = self.tcinputs.get('net_mask')


        except Exception as exp:
            self.log.exception("Exception when initializing inputs {}".format(exp))
            raise exp

    def get_dc_object(self, dc_name):
        """
        Get Datacenter by its name
        Args:
                dc_name                (string):   Name of the resource pool
        Returns:
                dc      (object):   object for Datacenter
        """
        for dc in self.hvobj.connection.content.rootFolder.childEntity:
            if dc.name == dc_name:
                return dc
        raise Exception('Failed to find datacenter named {}'.format(dc_name))

    def get_rp(self, rp_name):
        """
        Get a resource pool in the datacenter by its names.
        Args:
                rp_name                (string):   Name of the resource pool
        Returns:
                resource_pool      (object):   object for resource pool
        """
        view_manager = self.hvobj.connection.content.viewManager
        container_view = view_manager.CreateContainerView(self.dc_obj, [vim.ResourcePool], True)
        try:
            for resource_pool in container_view.view:
                if resource_pool.name == rp_name:
                    return resource_pool
        finally:
            container_view.Destroy()
        raise Exception("Failed to find resource pool {} in datacenter {}".format(rp_name, self.dc_obj.name))

    def get_ds(self, ds_name):
        """
        Pick a datastore by its name.
        Args:
                ds_name                (string):   Name of the datastore
        Returns:
                datastore      (object):   object for the datastore
        """
        for datastore in self.dc_obj.datastore:
            try:
                if datastore.name == ds_name:
                    return datastore
            except Exception:  # Ignore datastores that have issues
                pass
        raise Exception("Failed to find {} on datacenter {}".format(ds_name, self.dc_obj.name))

    def get_network(self, network_name):
        """
        Get network by its name.
        Args:
                network_name                (string):   Name of the network
            Returns:
                network      (object):   object for the network
        """
        for network in self.dc_obj.network:
            try:
                if network.name == network_name:
                    return network
            except Exception:  # Ignore network that have issues
                pass
        raise Exception("Failed to find {} on datacenter {}".format(network_name, self.dc_obj.name.name))

    def deploy_ova(self):
        """
        Deploy OVA
        Returns:
                True       if successful
                False      if failure

        """

        ovf_handle = OvfHandler(self.log, self.ova_path)
        ovf_manager = self.hvobj.connection.content.ovfManager
        ovf_properties = [
            vim.KeyValue(key='name', value=self.vm_name),
            vim.KeyValue(key='network', value=self.network_name),
            vim.KeyValue(key='IPAllocationPolicy', value=self.ip_assignment),
            vim.KeyValue(key='bbClientHostname', value=self.vm_name),
            vim.KeyValue(key='baClientName', value=self.vm_name),
            vim.KeyValue(key='bcRootPassword', value=self.vm_pass),
            vim.KeyValue(key='aeDNSSearch', value=self.domain),
            vim.KeyValue(key='aaUseDHCP', value=self.use_dhcp)]

        if self.kwargs.get('is_metallic', False):

            ovf_properties.append(
                vim.KeyValue(key='paramAuthCode', value=self.auth_code))
        else:
            # need to add support for non metallic commvault deployment
            ovf_properties = [
                vim.KeyValue(key='paramNetworkGateway', value=self.cs_host_name_or_ip),
                vim.KeyValue(key='abIP', value=self.ip_address),
                vim.KeyValue(key='acNetmask', value=self.net_mask),
                vim.KeyValue(key='adGateway', value=self.default_gateway),
                vim.KeyValue(key='afdns1', value=self.primary_dns),
                vim.KeyValue(key='agdns2', value=self.secondary_dns)]

            if self.auth_code:
                # Auth code provided
                ovf_properties.append(
                    vim.KeyValue(key='paramAuthCode', value=self.auth_code))
            else:
                # No auth code, use CS credentials
                ovf_properties.append(vim.KeyValue(key='ccCSUsername', value=self.cs_user_name))
                ovf_properties.append(vim.KeyValue(key='cdCSPassword', value=self.cs_password))
        cisp = vim.OvfManager.CreateImportSpecParams(
            diskProvisioning=self.diskProvisioning,
            entityName=self.vm_name,
            networkMapping=[vim.OvfManager.NetworkMapping(name=self.network_name, network=self.network_obj)],
            ipAllocationPolicy=self.ip_assignment,
            ipProtocol='IPv4',
            propertyMapping=ovf_properties
        )

        cisr = ovf_manager.CreateImportSpec(
            ovf_handle.get_descriptor(), self.r_pool_obj, self.ds_obj, cisp)

        # These errors might be handleable by supporting the parameters in
        # CreateImportSpecParams
        if cisr.error:
            self.log.error("The following errors will prevent import of this OVA:")
            for error in cisr.error:
                self.log.error("{}".format(error))
            return False

        ovf_handle.set_spec(cisr)

        lease = self.r_pool_obj.ImportVApp(cisr.importSpec, self.dc_obj.vmFolder)
        while lease.state == vim.HttpNfcLease.State.initializing:
            self.log.info("Waiting for lease to be ready...")
            time.sleep(1)

        if lease.state == vim.HttpNfcLease.State.error:
            self.log.error("Lease error: {}".format(lease.error))
            return False
        if lease.state == vim.HttpNfcLease.State.done:
            return True

        self.log.info("Starting deploy...")
        return ovf_handle.upload_disks(lease, self.host)

    def validate_vm(self):
        """
        Validates the deployed VM

        Raises:
            Exception:
                if the newly deployed VM could not be validated

        """
        try:
            self.hvobj.VMs = self.vm_name
            self.hvobj.VMs[self.vm_name].update_vm_info("All", True, True)
            self.machine = self.hvobj.VMs[self.vm_name].machine
            attempt = 5
            while attempt >= 0:
                if self.validate_services(self.kwargs.get('services'), attempt):
                    break
                else:
                    attempt -= 1
        except Exception as exp:
            self.log.exception("Exception occurred while validating the deployed VM."
                               " Please check the logs")
            raise exp

    def validate_services(self, services=None, attempt=0):
        """
        Validates all the services in the deployed OVA
        Args:
                services        (list): services to check if they are up
                attempt         (int):  number of attempts left

        Raises:
            Exception:
                if atleast one of the service is not up

        """
        if not services:
            services = ['cvd', 'tomcat', 'AppMgrSvc', 'BlrSvc', 'ClMgrs', 'cvfwd', 'EvMgrs', 'JobMgr',
                        'MediaManager', 'QSDK', 'sqlservr']

        self.log.info("Attempt number {}. Waiting for 2 minutes for services to come up".format(5 - attempt))
        time.sleep(120)
        for service in services:
            if not self.machine.is_process_running(service):
                if attempt > 0:
                    return False
                else:
                    raise Exception("One of the expected process {} is not running".format(service))
        return True

    def deploy(self):
        try:
            if self.deploy_ova():
                if self.kwargs.get('validate', True):
                    self.validate_vm()
            else:
                self.log.exception("Not able to deploy OVA")
        except Exception as exp:
            self.log.exception("Exception occurred while deploying and/or validating the client")
            raise exp


class FileHandle(object):
    def __init__(self, filename):
        self.filename = filename
        self.fh = open(filename, 'rb')

        self.st_size = os.stat(filename).st_size
        self.offset = 0

    def __del__(self):
        self.fh.close()

    def tell(self):
        return self.fh.tell()

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset

        return self.fh.seek(offset, whence)

    def seekable(self):
        return True

    def read(self, amount):
        self.offset += amount
        result = self.fh.read(amount)
        return result

    # A slightly more accurate percentage
    def progress(self):
        return int(100.0 * self.offset / self.st_size)


class WebHandle(object):
    def __init__(self, url):
        self.url = url
        r = urlopen(url)
        if r.code != 200:
            raise FileNotFoundError(url)
        self.headers = self._headers_to_dict(r)
        if 'accept-ranges' not in self.headers:
            raise Exception("Site does not accept ranges")
        self.st_size = int(self.headers['content-length'])
        self.offset = 0

    def _headers_to_dict(self, r):
        result = {}
        if hasattr(r, 'getheaders'):
            for n, v in r.getheaders():
                result[n.lower()] = v.strip()
        else:
            for line in r.info().headers:
                if line.find(':') != -1:
                    n, v = line.split(': ', 1)
                    result[n.lower()] = v.strip()
        return result

    def tell(self):
        return self.offset

    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset
        return self.offset

    def seekable(self):
        return True

    def read(self, amount):
        start = self.offset
        end = self.offset + amount - 1
        req = Request(self.url,
                      headers={'Range': 'bytes=%d-%d' % (start, end)})
        r = urlopen(req)
        self.offset += amount
        result = r.read(amount)
        r.close()
        return result

    # A slightly more accurate percentage
    def progress(self):
        return int(100.0 * self.offset / self.st_size)


class OvfHandler(object):
    """
    OvfHandler handles most of the OVA operations.
    It processes the tarfile, matches disk keys to files and
    uploads the disks, while keeping the progress up to date for the lease.
    """

    def __init__(self, log, ovafile):
        """
        Performs necessary initialization, opening the OVA file,
        processing the files and reading the embedded ovf file.
        """
        self.log = log
        self.handle = self._create_file_handle(ovafile)
        self.tarfile = tarfile.open(fileobj=self.handle)
        ovffilename = list(filter(lambda x: x.endswith(".ovf"),
                                  self.tarfile.getnames()))[0]
        ovffile = self.tarfile.extractfile(ovffilename)
        self.descriptor = ovffile.read().decode()

    def _create_file_handle(self, entry):
        """
        A simple mechanism to pick whether the file is local or not.
        This is not very robust.
        """
        if os.path.exists(entry):
            return FileHandle(entry)
        return WebHandle(entry)

    def get_descriptor(self):
        return self.descriptor

    def set_spec(self, spec):
        """
        The import spec is needed for later matching disks keys with
        file names.
        """
        self.spec = spec

    def get_disk(self, file_item):
        """
        Does translation for disk key to file name, returning a file handle.
        """
        ovffilename = list(filter(lambda x: x == file_item.path,
                                  self.tarfile.getnames()))[0]
        return self.tarfile.extractfile(ovffilename)

    def get_device_url(self, file_item, lease):
        for device_url in lease.info.deviceUrl:
            if device_url.importKey == file_item.deviceId:
                return device_url
        raise Exception("Failed to find deviceUrl for file {}".format(file_item.path))

    def upload_disks(self, lease, host):
        """
        Uploads all the disks, with a progress keep-alive.
        """
        self.lease = lease
        try:
            self.start_timer()
            for fileItem in self.spec.fileItem:
                self.upload_disk(fileItem, lease, host)
            lease.Complete()
            self.log.info("OVA successfully deployed")
            return True
        except vmodl.MethodFault as ex:
            self.log.error("Hit an error in upload: {}".format(ex))
            lease.Abort(ex)
        except Exception as ex:
            self.log.exeception("Lease: {}".format(lease.info))
            self.log.exeception("Hit an error in upload: {}".format(ex))
            lease.Abort(vmodl.fault.SystemError(reason=str(ex)))
        return False

    def upload_disk(self, file_item, lease, host):
        """
        Upload an individual disk. Passes the file handle of the
        disk directly to the urlopen request.
        """
        ovffile = self.get_disk(file_item)
        if ovffile is None:
            return
        device_url = self.get_device_url(file_item, lease)
        url = device_url.url.replace('*', host)
        headers = {'Content-length': self.get_tarfile_size(ovffile)}
        if hasattr(ssl, '_create_unverified_context'):
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = None
        req = Request(url, ovffile, headers)
        urlopen(req, context=ssl_context)

    def start_timer(self):
        """
        A simple way to keep updating progress while the disks are transferred.
        """
        Timer(30, self.timer).start()

    def timer(self):
        """
        Update the progress and reschedule the timer if not complete.
        """
        try:
            prog = self.handle.progress()
            self.lease.Progress(prog)
            if self.lease.state not in [vim.HttpNfcLease.State.done,
                                        vim.HttpNfcLease.State.error]:
                self.start_timer()
            if prog < 95:
                self.log.info("Progress: {}%".format(prog))
        except Exception:  # Any exception means we should stop updating progress.
            pass

    def get_tarfile_size(self, tarfile):
        """
        Determine the size of a file inside the tarball.
        If the object has a size attribute, use that. Otherwise, seek to the end
        and report that.
        """
        if hasattr(tarfile, 'size'):
            return tarfile.size
        size = tarfile.seek(0, 2)
        tarfile.seek(0, 0)
        return size
