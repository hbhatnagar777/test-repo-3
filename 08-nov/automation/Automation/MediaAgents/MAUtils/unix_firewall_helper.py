# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
File for Linux firewall helper, File for performing operations on a machine /
computer with UNIX Operating System

UnixFirewallHelper
====================

    __init__()                          --  Initialize object of the class

    _get_logger()                       --  Returns the custom logger for this module
    
    verify_firewall_is_running          --  Verifies whether firewall is running or not

    verify_enable_firewall_registry     --  Verifies if sHSEnableFirewall is set as Y

    verify_firewall_default_zone        --  Verifies that default firewall zone is set to block

    verify_firewall_active_zones        --  Verifies that default firewall zone is set to block

    validate_services_for_zone          --  Validates that services are allowed for the given firewall zone

    hsx_firewall_validation_suite       --  Complete validation suite for HSX firewall protection

"""

from AutomationUtils import database_helper, logger
from AutomationUtils.unix_machine import UnixMachine
from Install import install_helper

class UnixFirewallHelper:
    """
        Helper class for linux firewall
    """

    def __init__(self, machine_obj: UnixMachine = None, commcell_obj=None, log_obj=None):
        """
        Initialise instance for UnixFirewallHelper
        Args:
            machine_obj     (object)    --  instance for machine
            commcell_obj    (object)    --  instance for commcell
            log_obj         (object)    --  instance for log
        """
        self.machine = machine_obj
        self.commcell = commcell_obj
        self.csdb = database_helper.get_csdb()
        self.client_obj = None
        self.media_agent_name = self.machine.machine_name
        self.short_name = self.media_agent_name.split('.', 1)[0]
        self.log = self._get_logger(log_obj)
        self.install_helper_obj = install_helper.InstallHelper(self.commcell, self.machine)
        if self.commcell is None or self.machine is None:
            raise Exception(f"No machine or client object passed, machine_obj : "
                            f"{self.machine}\tcommcell_obj"
                            f" : {self.commcell}")
        if self.log is None:
            raise Exception(f"Log object not initialised, log_obj : {self.log}")
        if self.machine and self.machine.client_object:
            self.client_obj = self.machine.client_object
        else:
            self.client_obj = self.commcell.clients.get(self.media_agent_name)
        self.dir_install = self.client_obj.install_directory

    def _get_logger(self, log_obj):
        """Returns the custom logger for this module

            Args:

                log_obj (obj)   --  The logger from CVTestCase

            Returns:

                logger  (obj)   --  The custom logger object
        """
        log_file = log_obj.handlers[0].baseFilename
        log_name = f"UnixFirewallHelper_{self.short_name}"
        msg_prefix = f"[{self.short_name}] "
        logger_obj = logger.get_custom_logger(log_name, log_file, msg_prefix)
        return logger_obj
    
    def verify_firewall_is_running(self, ma_machine):
        """ Verifies whether firewall is running or not
        
            Args:

                ma_machine     (obj)          --  Machine class object of MA
        
            Returns:

                result          (bool)          --  Returns True if firewall is running
        
        """

        check1, check2 = False, False

        command = f"firewall-cmd --state"
        self.log.info(f"Command : {command}")
        output = ma_machine.execute_command(command)
        output = output.output.rstrip()
        if output == "running":
            self.log.info(f"Firewall status -> running")
            check1 = True
        else:
            self.log.error(f"Firewall status -> not running")

        command = f"systemctl status firewalld | grep 'Active: active (running)'"
        self.log.info(f"Command : {command}")
        output = ma_machine.execute_command(command)
        output = output.output.rstrip()
        if output:
            self.log.info(f"Firewall status -> running")
            check2 = True
        else:
            self.log.error(f"Firewall status -> not running")
        
        return all((check1, check2))
    
    def verify_enable_firewall_registry(self, ma_machine):
        """Verifies if sHSEnableFirewall is set as Y

            Args:

                ma_machine      (obj)           --  Machine class object of MA

            Returns:

                result          (bool)          --  Returns True if sHSEnableFirewall is set as Y

        """

        reg_key = "sHSEnableFirewall"
        reg_value = ma_machine.get_registry_value(
            "MediaAgent", reg_key, commvault_key='')
        if not reg_value:
            raise Exception(
                f"Couldn't find {reg_key} reg key for {ma_machine.machine_name}")
        
        if reg_value == "Y":
            self.log.info(f"{reg_key} reg key set to Y")
            return True
        self.log.error(f"{reg_key} reg key not set to Y. Current value -> {reg_value}")
        return False
    
    def verify_firewall_default_zone(self, ma_machine):
        """ Verifies that default firewall zone is set to block
        
            Args:

                ma_machine     (obj)          --  Machine class object of MA
        
            Returns:

                result          (bool)          --  Returns True if default zone is set to block
        """

        command = f"firewall-cmd --get-default-zone"
        self.log.info(f"Command : {command}")
        output = ma_machine.execute_command(command)
        output = output.output.rstrip()
        if output != "block":
            self.log.error(f"Default zone is not set to block zone. Current default zone -> {output}")
            return False
        self.log.info(f"Default zone set to block zone")
        return True

    def verify_firewall_active_zones(self, ma_machine):
        """ Verifies that default firewall zone is set to block
        
            Args:

                ma_machine     (obj)          --  Machine class object of MA
        
            Returns:

                result          (bool)          --  Returns True if active zones are associated
                                                    with right interfaces
        """

        # Output looks like
        # block
        #   interfaces: bond1
        # cv_storage_zone
        #   interfaces: bond2

        command = f"firewall-cmd --get-active-zones"
        self.log.info(f"Command : {command}")
        output = ma_machine.execute_command(command)
        output_lines = output.output.strip().split("\n")

        expected_interfaces = {
            "cv_storage_zone": "bond2",
            "block": "bond1"
        }

        for i, line in enumerate(output_lines):
            if line in expected_interfaces:
                zone = line
                interfaces = output_lines[i + 1].split(": ", 1)[-1]
                if expected_interfaces[zone] in interfaces:
                    self.log.info(f"The zone '{zone}' has the expected interface '{expected_interfaces[zone]}'.")
                else:
                    self.log.error(f"The zone '{zone}' does not have the expected interface '{expected_interfaces[zone]}'. {zone} zone has wrong interface {interfaces}")
                    return False
        return True

    def validate_services_for_zone(self,ma_machine,zone="block"):
        """ Validates that services are allowed for the given firewall zone
        
            Args:

                ma_machine     (obj)            --  Machine class object of MA

                zone           (str)            --  String representing the zone whose services are to be validated          
        
            Returns:

                result          (bool)          --  Returns True if all required services are allowed on the given zone

        """


        # Output looks like
        # commvault nfs nfs3 ntp rpc-bind ssh
        command = f"firewall-cmd --list-services --zone={zone}"
        self.log.info(f"Command : {command}")
        output = ma_machine.execute_command(command)

        services = output.output.split()
        self.log.info(f"Services allowed on {zone} zone: {services}")
        for service in services:
            command = f"firewall-cmd --zone={zone} --query-service={service}"
            self.log.info(f"Command : {command}")
            output = ma_machine.execute_command(command)
            
            if output.output.rsplit()[0] != "yes":
                self.log.error(f"{service} not running")
                return False
            self.log.info(f"{service} is running")
        self.log.info(f"All required services running on {zone} zone")
        return True

    @staticmethod
    def hsx_firewall_validation_suite(ma_names, ma_machines, hyperscale_helper, fw_helpers):
        """The complete validation suite for HSX firewall protection

            Args:

                ma_names            (list)  --  The MA names

                ma_machines         (dict)  --  Dictionary, MA name -> machine object

                hyperscale_helper   (obj)   --  The HyperScaleHelper obj

            Returns:

                result, reason      (bool)  --  True if all checks are passed
                                                False if any check fails and reason of failure

        """
        log = hyperscale_helper.log

        step_name = 'HSX Firewall Protection Validation Suite'
        log.info(step_name)
        step_errors = []
        suite_result = []

        def do_step_start():
            nonlocal step_errors
            step_count = len(suite_result) + 1
            log.info(f"STEP {step_count}: {step_name} - START")
            step_errors = []
        
        def do_step_error(msg):
            log.error(msg)
            step_errors.append(msg)

        def do_step_end():
            step_count = len(suite_result) + 1
            log.info(f"STEP {step_count}: {step_name} - END. {len(step_errors)} Errors")
            step_details = {"step_name":step_name, "step_errors":step_errors}
            suite_result.append(step_details)
        
        def show_summary():
            success = True
            reason_string =f""
            for idx, details in enumerate(suite_result):
                step_count = idx+1
                step_name = details['step_name']
                step_errors = details['step_errors']
                if step_errors:
                    log.error(f"STEP {step_count}: {step_name} FAILED")
                    success = False
                    for error in step_errors:
                        reason_string += (error + ' | ')
                        log.error(error)
                else:
                    log.info(f"STEP {step_count}: {step_name} SUCCESSFUL")
            return success, reason_string
        
        # 1. Verifying if firewall is running or not
        step_name = "Verifying whether firewall is running or not"
        do_step_start()
        
        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].verify_firewall_is_running(ma_machine)
            if not result:
                msg = f"Firewall status on {ma_name} -> not running"
                do_step_error(msg)
            else:
                log.info(f"Firewall status on {ma_name} -> running")
        
        do_step_end()

        # 2. Verify sHSEnableFirewall reg key is set to Y across MAs
        step_name = "sHSEnableFirewall reg key validation"
        do_step_start()
        
        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].verify_enable_firewall_registry(ma_machine)
            if not result:
                msg = f"Failed to verify sHSEnableFirewall set to Y on {ma_name}"
                do_step_error(msg)
            else:
                log.info(f"Verified sHSEnableFirewall set to Y on {ma_name}")
        
        do_step_end()

        # 3. Verify firewall default zone is set to block across all MAs
        step_name = "Verifying firewall default zone"
        do_step_start()
        
        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].verify_firewall_default_zone(ma_machine)
            if not result:
                msg = f"Failed to verify firewall default zone on {ma_name}"
                do_step_error(msg)
            else:
                log.info(f"Verified firewall default zone on {ma_name}")
        
        do_step_end()

        # 4. Verify firewall active zone interfaces 
        step_name = "Verify firewall active zone interfaces "
        do_step_start()
        
        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].verify_firewall_active_zones(ma_machine)
            if not result:
                msg = f"Failed to verify active zone on interfaces on {ma_name}"
                do_step_error(msg)
            else:
                log.info(f"Verified active zone on interfaces on {ma_name}")
        
        do_step_end()

        # 5. Check if commmvault services are running
        step_name = "Checking if commvault services and processes are up"
        do_step_start()

        result = hyperscale_helper.verify_commvault_service_and_processes_are_up(ma_names, ma_machines)
        if not result:
            msg = f"Failed to verify if commvault services or processes are up"
            do_step_error(msg)
        else:
            log.info("Commvault services and processes are up on all nodes")
            
        do_step_end()

        # 6. Check if hedvig services are running
        step_name = "Checking if hedvig services are up"
        do_step_start()

        result = hyperscale_helper.verify_hedvig_services_are_up(ma_names, ma_machines)
        if not result:
            msg = f"Failed to verify if hedvig services are up"
            do_step_error(msg)
        else:
            log.info("Hedvig services are up on all nodes")

        do_step_end()

        # 7. Check if all required services are running on block zone
        step_name = "Check if all required services are running on block zone"
        do_step_start()

        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].validate_services_for_zone(ma_machine,"block")
            if not result:
                msg = f"Failed to verify all required services are running on {ma_name} in block zone"
                do_step_error(msg)
            else:
                log.info(f"Verified all required services are running on {ma_name} in block zone")

        do_step_end()

        # 8. Check if all required services are running on cv_storage_zone zone
        step_name = "Check if all required services are running on cv_storage_zone zone"
        do_step_start()

        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result = fw_helpers[ma_name].validate_services_for_zone(ma_machine,"cv_storage_zone")
            if not result:
                msg = f"Failed to verify all required services are running on {ma_name} in cv_storage_zone zone"
                do_step_error(msg)
            else:
                log.info(f"Verified all required services are running on {ma_name} in cv_storage_zone zone")

        do_step_end()

        return show_summary()