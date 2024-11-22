# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This file contains classes named DedupeHelper, CloudLibrary and MMHelper which consists of
 methods required for MM testacse assistance like DB queries, log parsing, etc.

Class KVMAdmin:

    _set_credentials(): set the credentials for hyperscale by reading the config INI file

    getvm_domstate():  Function to Lookup the Domain State of the VM

    getvm_list():   Function to Get the list of domains at the virtual environment

    create_vm():   Function to Create a virtual client

    delete_vm():  Function to Delete a virtual domain from KVM server

    restart_vm(): Function to Restart a Virtual Domain

    clone_vm(): Function to create Clone of a virtual domain

    find_vm_ip_addr():  Function to obtain the IP of a virtual machine

    guest_mount(): Function to perform guest mount operation for HyperScale VM.

    guest_unmount(): Function to perform guest unmount of an HyperScale VM.

    ifcfgfileedit():  Function to update network scripts to obtain DHCP IP.

    editrcscript():   Function to edit init rc scripts

    stopvm():  Function to stop the Virtual Domain

    startvm(): Function to Start the Virtual Domain

    addhostentry(): Function to add host entries across the HyperScale VM's

    addhostentrycs(): Function to add host entries on the CommServer

    copyreg_to_csscript(): Function to copy register to CS script on all the HyperScale MA's

    executereg_tocs(): Function to execute register to CS script on HyperScale MA's

    commvault_restart(): Function to restart commvault services on HyperScale MA

"""
import time
from AutomationUtils import config
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine


class KvmAdmin():
    """
    Base class for KVM Linux Virtualization helper functions
    to create HyperScale Reference Architecture end to end configurations
    """

    def __init__(self, kvmserver_machine=None, log=None):
        """
        Creates KvmAdmin class object

        kvmserver_machine (object) : machine class object of kvmserver machine

        log (object)  : log file object

        """
        self.log = log
        self.kvmserver_machine = kvmserver_machine
        self.config = config.get_config()
        self.diskpath = "/var/lib/libvirt/images/"
        self.tail = " --network bridge=br0 --os-type=linux --os-variant=generic"
        self.numdisks = 3
        self._set_credentials()

    def _set_credentials(self):
        """
        set the credentials for hyperscale by reading the config INI file

        Returns:
            None

        Raises:
            Exception if Credentials are not found.
        """

        keys = eval('self.config.HyperScale.Credentials')
        self.vmuser = keys[0]
        self.vmpassword = keys[1]

    def getvm_domstate(self, kvmname):
        """
        Function to Lookup the Domain State of the VM

        Args:
            kvmname  (string)    -- kvmserver name

        Returns:
            return kvmstate

        Raises:
            Exception if failed to get kvmserver state
        """

        try:
            cmd = 'virsh domstate ' + kvmname
            retcode, output = self.kvmserver_machine.execute_command(cmd)
            self.log.info("return code is %s" % str(retcode))
            return output[0]
        except Exception:
            self.log.exception("exception in GetVMState")
            raise Exception("exception in GetVMState")

    def getvm_list(self, kvmname):
        """
        Function to Get the list of domains at the virtual environment

        Args:
            kvmname  (string)    -- kvm client name

        Returns:
            return boolean : True if client exists else False.

        Raises:
            Exception if failed to get kvm clients list.
        """

        try:
            cmd = 'virsh list'
            output = self.kvmserver_machine.execute_command(cmd)
            output = output.output.split('\n')
            for row in output:
                if str(kvmname) in row:
                    self.log.info("VM exists")
                    return True
            return False
        except Exception:
            self.log.exception("exception in GetVMList")
            raise Exception("exception in GetVMList")

    def create_vm(self, kvmname, cdrompath):
        """
        Function to Create a virtual client

        Args:
            kvmname  (string)    -- kvm client name

            cdrompath (string)   -- dvd path on the server

        Returns:
            return None

        Raises:
            Exception if failed to create kvm client.
        """

        try:
            cmdseq = []
            for i in range(1, self.numdisks + 1):
                cmd = " --disk path=" + self.diskpath + kvmname + \
                      "-" + str(i) + ".img,size=100,sparse=no"
                cmdseq.append(cmd)
            cmdseq = "".join(cmdseq)
            self.log.info("virt-install --name=" + kvmname + str(
                cmdseq) + " --graphics spice --vcpu=2 --ram=4098 --cdrom=" + cdrompath + self.tail)
            cmd = ("virt-install --name=" + kvmname + str(
                cmdseq) + " --graphics spice --vcpu=2 --ram=4098 --cdrom=" + cdrompath + self.tail)
            self.kvmserver_machine.execute_command(cmd)
            self.log.info("####VM Sucessfully created")
        except Exception:
            self.log.exception("Exception in KVM CreateVM")
            raise Exception("Exception in KVM CreateVM")

    def delete_vm(self, kvmname):
        """
        Function to Delete a virtual domain from KVM server

        Args:
            kvmname  (string)    -- kvm client name

        Returns:
            return None

        Raises:
            Exception if failed to delete kvm client.
        """

        try:
            cmdrm = []
            cmd = ("virsh shutdown " + kvmname)
            self.kvmserver_machine.execute_command(cmd)
            time.sleep(6)
            cmd = ("virsh destroy " + kvmname)
            self.kvmserver_machine.execute_command(cmd)
            cmd = ("virsh undefine " + kvmname)
            self.kvmserver_machine.execute_command(cmd)
            for i in range(1, self.numdisks + 1):
                cmd2 = self.diskpath + kvmname + "-" + str(i) + ".img"
                cmdrm.append(cmd2)
            cmdrm = " ".join(cmdrm)
            cmd = ("rm -rf " + cmdrm)
            self.log.info(cmd)
            self.kvmserver_machine.execute_command(cmd)
            self.log.info("#########VM sucessfully shutdown and Deleted along with disks#########")

        except Exception:
            self.log.exception("Exception in KVM DeleteVM")
            raise Exception("Exception in KVM DeleteVM")

    def restart_vm(self, kvmname):
        """
        Function to Restart a Virtual Domain

        Args:
            kvmname  (string)    -- kvm client name

        Returns:
            return boolean : True if client restart successfully else False.

        Raises:
            Exception if failed to restart kvm client.
        """

        try:
            cmd = "virsh reboot " + kvmname
            self.log.info(cmd)
            self.kvmserver_machine.execute_command(cmd)
            time.sleep(60)
            return True
        except Exception:
            self.log.exception("Exception in KVM RestartVM")
            raise Exception("Exception in KVM RestartVM")

    def clone_vm(self, kvmsrc, kvmclone):
        """
        Function to create Clone of a virtual domain

        Args:
            kvmsrc  (string)    -- kvm client name

            kvmclone  (string)    -- kvm cloned client name

        Returns:
            return None.

        Raises:
            Exception if failed to clone kvm client.
        """

        try:
            self.log.info("virsh suspend " + kvmsrc)
            cmd = "virsh suspend " + kvmsrc
            self.kvmserver_machine.execute_command(cmd)
            cmdseq = []
            cmdrm = []
            for i in range(1, self.numdisks + 1):
                query = " --file=" + self.diskpath + kvmclone + "-" + str(i) + ".img"
                cmdseq.append(query)
                diskcmd = self.diskpath + kvmclone + "-" + str(i) + ".img"
                cmdrm.append(diskcmd)
            cmdseq = "".join(cmdseq)
            cmdrm = " ".join(cmdrm)
            cmd = "rm -rf " + cmdrm
            output = self.kvmserver_machine.execute_command(cmd)
            self.log.info(output.output)
            cmd = "virt-clone --original " + kvmsrc + " --name " + kvmclone + str(cmdseq)
            self.log.info(cmd)
            self.kvmserver_machine.execute_command(cmd)
            time.sleep(30)
            self.log.info("##############cloned VM###########")
            cmd = "virsh resume " + kvmsrc
            self.log.info(cmd)
            self.kvmserver_machine.execute_command(cmd)
            cmd = "virsh start " + kvmclone
            self.kvmserver_machine.execute_command(cmd)
            time.sleep(60)
        except Exception:
            self.log.exception("Exception in CloneVM")
            raise Exception("Exception in CloneVM")

    def find_vm_ip_addr(self, kvmname):
        """
        Function to obtain the IP of a virtual machine

        Args:
            kvmname  (string)    -- kvm client name

        Returns:
            return kvmclient IP address.

        Raises:
            Exception if failed to get kvm client IP address.

        """

        try:
            cmd = ("""arp -an | grep \"`virsh dumpxml %s | grep \"mac address\" |
             sed \"s/.*'\\(.*\\)'.*/\\1/g\"`\" | awk '{
             gsub(/[\\(\\)]/,\"\",$2); print $2 }'""" % kvmname)
            self.log.info(cmd)
            output = self.kvmserver_machine.execute_command(cmd)
            self.log.info(output.output.strip())
            return output.output.strip()
        except Exception:
            self.log.exception("Exception in findVMIPAddr")
            raise Exception("Exception in findVMIPAddr")

    def guest_mount(self, kvmname):
        """
        Function to perform guest mount operation for HyperScale VM.

        Args:
            kvmname  (string)    -- kvm client name

        Returns:
            return None

        Raises:
            Exception if failed to mount guest kvm client.
        """

        try:
            query = self.diskpath + kvmname + "-1.img -m /dev/systemvg/root --rw /mnt3"
            cmd = "guestmount -a " + query
            self.log.info(cmd)
            output = self.kvmserver_machine.execute_command(cmd)
            self.log.info(output.output)
            time.sleep(5)
        except Exception:
            self.log.exception("Exception in guestMount")
            raise Exception("Exception in guest Mount")

    def guest_unmount(self):
        """
        Function to perform guest unmount of an HyperScale VM.

        Args:
            None
        Returns:
            return None

        Raises:
            Exception if failed to unmount guest kvm client.
        """

        try:
            cmd = "guestunmount /mnt3 "
            output = self.kvmserver_machine.execute_command(cmd)
            self.log.info(output)
            time.sleep(5)
        except Exception:
            self.log.exception("Exception in guestUnMount")
            raise Exception("Exception in guestUnMount")

    def ifcfgfileedit(self):
        """
        Function to update network scripts to obtain DHCP IP.

        Args:
            None

        Returns:
            return None

        Raises:
            Exception if failed to update network scripts.
        """

        try:

            machine_obj = self.kvmserver_machine
            machine_obj.delete_file('/mnt3/etc/sysconfig/network-scripts/ifcfg-hca1')
            line = "ONBOOT=yes" + "\n" + "BOOTPROTO=dhcp" + "\n" + "DEVICE=ens3" + "\n" + "IPV6INIT=no"
            machine_obj.create_file('/mnt3/etc/sysconfig/network-scripts/ifcfg-ens3', line)
            time.sleep(30)

        except Exception as err:
            self.log.exception("Exception in ifcfgFile %s" % err)
            raise Exception("Exception in ifcfgFile")

    def editrcscript(self):
        """
        Function to edit init rc scripts

        Args:
            None

        Returns:
            return None

        Raises:
            Exception if failed to edit rc scripts
        """

        try:
            machine_obj = self.kvmserver_machine
            machine_obj.delete_file('/mnt3/etc/rc.d/rc.local')
            line = ("#!/bin/bash" + "\n" + "touch /var/lock/subsys/local" +
                    "\n" + "ping -c 3 " + machine_obj.machine_name)
            machine_obj.create_file('/mnt3/etc/rc.d/rc.local', line)
            cmd = "chmod 777 /mnt3/etc/rc.d/rc.local"
            output = self.kvmserver_machine.execute_command(cmd)
            self.log.info(output)
            time.sleep(30)

        except Exception:
            self.log.exception("Exception in editrcscript")
            raise Exception("Exception in editrcscript")

    def stopvm(self, kvmsrc):
        """
        Function to stop the Virtual Domain

        Args:
            kvmsrc  (string)    -- kvm client name

        Returns:
            return None

        Raises:
            Exception if failed to shutdown kvm client
        """
        try:
            self.log.info("virsh shutdown " + kvmsrc)
            cmd = "virsh shutdown " + kvmsrc
            self.kvmserver_machine.execute_command(cmd)
            time.sleep(30)
        except Exception:
            self.log.exception("Exception in StopVM")
            raise Exception("Exception in StopVM")

    def startvm(self, kvmsrc):
        """
        Function to Start the Virtual Domain

        Args:
            kvmsrc  (string)    -- kvm client name

        Returns:
            return None

        Raises:
            Exception if failed to start kvm client
        """
        try:
            self.log.info("virsh start " + kvmsrc)
            cmd = "virsh start " + kvmsrc
            self.kvmserver_machine.execute_command(cmd)
        except Exception:
            self.log.exception("Exception in StartVM")
            raise Exception("Exception in StartVM")

    def addhostentry(self, entry):
        """
        Function to add host entries across the HyperScale VM's

        Args:
            entry  (list)    -- kvm client details

        Returns:
            return None

        Raises:
            Exception if failed to add host entry

        """
        try:

            machine_obj = UnixMachine(entry[0], None,
                                      self.vmuser, self.vmpassword)
            output = machine_obj.execute_command('cat /etc/hosts')
            filecontent = output.output
            newln1 = (str(entry[0]) + "       " + entry[3])
            newln1sds = (str(entry[0]) + "       " + entry[3] + "sds")
            newln2 = (str(entry[1]) + "       " + entry[4])
            newln2sds = (str(entry[1]) + "       " + entry[4] + "sds")
            newln3 = (str(entry[2]) + "       " + entry[5])
            newln3sds = (str(entry[2]) + "       " + entry[5] + "sds")
            lines = filecontent.split("\n")
            lines = [line for line in lines if entry[3] not in line]
            lines = [line for line in lines if entry[4] not in line]
            lines = [line for line in lines if entry[5] not in line]
            lines = [line for line in lines if line]
            lines = [line for line in lines if line.strip()]
            lines.append(newln1)
            lines.append(newln1sds)
            lines.append(newln2)
            lines.append(newln2sds)
            lines.append(newln3)
            lines.append(newln3sds)
            content = ""
            for line in lines:
                content = content + '\n' + line
            machine_obj.create_file('/etc/hosts', content)
            cmd = ("sshpass -p 'cvadmin' scp -o StrictHostKeyChecking=no -r /etc/hosts root@%s:/etc/" % entry[4])
            self.log.info(cmd)
            machine_obj.execute_command(cmd)
            cmd = ("sshpass -p 'cvadmin' scp -o StrictHostKeyChecking=no -r /etc/hosts root@%s:/etc/" % entry[5])
            self.log.info(cmd)
            machine_obj.execute_command(cmd)

        except Exception as err:
            self.log.exception("Exception in Add Host Entry %s" % err)
            raise Exception("Exception in Add Host Entry")

    def addhostentrycs(self, kvmnode, ipaddr, csmachine, user, password):
        """
        Function to add host entries on the CommServer

        Args:
            kvmnode  (string)    -- kvm client

            ipaddr       (string)    -- kvm client ip address

            csmachine (string)   -- commserver name

            user       (string)  -- Commserver user name

            password   (string)  -- Commserver password

        Returns:
            return None

        Raises:
            Exception if failed to add host entry on commserver
        """
        try:

            remotefile = r'c:\Windows\System32\drivers\etc\hosts'
            machine_obj = Machine(csmachine, None, user, password)
            lines = machine_obj.read_file(remotefile)
            lines = lines.split(r'\n')
            newln = (ipaddr + "       " + kvmnode)
            lines = [line for line in lines if kvmnode not in line]
            lines = [line for line in lines if line]
            lines = [line for line in lines if line.strip()]
            lines.append(newln)
            content = ""
            for line in lines:
                content = content + '\n' + line
            machine_obj.create_file(remotefile, content)
        except Exception as err:
            self.log.exception("Exception in Add Host Entry %s" % err)
            raise Exception("Exception in Add Host Entry")

    def copyreg_to_csscript(self, vmip):
        """
        Function to copy register to CS script on all the HyperScale MA's

        Args:
            kvmclient  (string)    -- kvm client name

            vmip       (string)    -- kvm client ip address

        Returns:
            return None

        Raises:
            Exception if failed to copy script to kvm client
        """
        try:
            machine_obj = self.kvmserver_machine

            for ipvalue in vmip:
                cmd = ("sshpass -p '%s' scp -o StrictHostKeyChecking=no -r /root/autoRegisterToCS.py %s:/opt/commvault/MediaAgent/" % (self.vmpassword, ipvalue))
                self.log.info(cmd)
                machine_obj.execute_command(cmd)
            self.log.info("copy script completed")
        except Exception:
            self.log.exception("Exception in RegisterToCS")
            raise Exception("Exception in RegisterToCS")

    def executereg_tocs(self, ipaddr, kvmnode, csname, user, password):
        """
        Function to execute register to CS script on HyperScale MA's

        Args:
            kvmnode  (string)    -- kvm client

            ip addr      (string) -- kvm client ip address

            csmachine (string)   -- commserver name

            user (string)        -- commcell user

            password (string)    -- commcell password

        Returns:
            return None

        Raises:
            Exception if failed execute register to CS script on HyperScale MA's
        """
        try:

            machine_obj = UnixMachine(ipaddr, None, self.vmuser, self.vmpassword)
            cmd = ('/opt/commvault/MediaAgent/autoRegisterToCS.py -uname \'' +
                   user + '\' -passwd \'' + password + '\' -client ' +
                   kvmnode + ' -commserve ' + csname)
            self.log.info("command used for registration %s" % cmd)
            output = machine_obj.execute_command(cmd)
            self.log.info(output)

        except Exception:
            self.log.exception("Exception in RegisterToCS")
            raise Exception("Exception in RegisterToCS")

    def commvault_restart(self, ipvalue):
        """
        Function to restart commvault services on HyperScale MA

        Args:
            ipvalue  (string)    -- ipvalue of client

        Returns:
            return None

        Raises:
            Exception if failed to restart commvault services on client
        """
        try:
            machine_obj = Machine(ipvalue, None, self.vmuser, self.vmpassword)
            cmd = 'commvault restart'
            output = machine_obj.execute_command(cmd)
            self.log.info(output)

        except Exception:
            self.log.exception("Exception in Commvault Restart ")
            raise Exception("Exception in Commvault Restart ")
