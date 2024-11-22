# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that handles discovery phase

classes defined:
    VsaDiscovery        - Handles discovery phase

"""

import re
from . import VirtualServerConstants


class VsaDiscovery(object):
    """
    Class to do the handle all the discovery and filters

    Methods:
            fetch_subclient_content()   - Gets the subclient content

            merge_rules()               - Merge two lists

            collect_vm_list()           - Get lists of vms as per rule

            match_pattern()             - Matches the regression list

            is_content_modifier()       - Checks for content modifiers in rule

            py_equivalent_regex()       - Converts regex to python equivalent

            map_filter_by_instance()    - Maps filter type by instance type

    """

    def __init__(self, hvobj):
        """
        Initialize the VM initialization properties
        """
        self.hvobj = hvobj
        self.all_vm_list = None

    def fetch_subclient_content(self, content):
        """

        Args:
            content                             (list):  List of rules for the vm content/filters

        Returns:
            vm_collect_list                     (list):  List of selected vms

        Raises:
            Exception:
                if it fails to to Fetch all subclient content
        """
        try:
            if self.all_vm_list is None:
                self.all_vm_list = self.hvobj.get_all_vms_in_hypervisor()
            vm_collect_list = []
            for each_content in content:
                total_vm_list = []
                if 'content' in each_content:
                    for each_rule in each_content['content']:
                        vm_list_per_rule = self.collect_vm_list(each_rule)
                        if each_content['allOrAnyChildren']:
                            total_vm_list = self.merge_rules(total_vm_list, vm_list_per_rule, 'and')
                        else:
                            total_vm_list = self.merge_rules(total_vm_list, vm_list_per_rule)
                else:
                    total_vm_list = self.collect_vm_list(each_content)
                vm_collect_list = self.merge_rules(vm_collect_list, total_vm_list)
            return vm_collect_list

        except Exception as err:
            self.hvobj.log.exception(
                "Failed to Fetch all subclient content {0}".format(err))
            raise err

    def merge_rules(self, final_list, new_list, operator='or'):
        """
        Merges two list

        Args:
            final_list                 (list):  List one

            new_list                    (list):  List two

            operator                    (str):  Operator for merging two list

        Returns:
            list                        List of merged lists

        Raises:
            Exception:
                if it fails to merge two list

        """
        try:
            if operator in ('or', 'and'):
                if not final_list:
                    return new_list
                if not new_list:
                    return final_list
                if operator == 'or':
                    return list(set(final_list) | set(new_list))
                return list(set(final_list) & set(new_list))
            if operator == 'not':
                return list(set(final_list) - set(new_list))
        except Exception as err:
            self.hvobj.log.exception(
                "Failed to Merge list {0}".format(err))
            raise err

    def map_filter_by_instance(self, pattern):
        """
        Change filter type based on the instance

        Args:
             pattern            (str): Pattern to find and replace filter type

        Returns:
             Changed pattern based on instance type
        """
        filter_type_mapping = VirtualServerConstants.filter_type_mapping
        filter_type = pattern.split("type:")[1]
        instance_type = self.hvobj.instance_type
        mapped_filter_type = filter_type_mapping.get(instance_type, {}).get(filter_type.lower(), filter_type)
        mapped_pattern = pattern.replace(f"type:{filter_type}", f"type:{mapped_filter_type}")
        return mapped_pattern

    def collect_vm_list(self, vm_rule):
        """
        Collect all vm vm list based on rule

        Args:
            vm_rule                         (list):  content rule for discovery

        Returns:
            list_of_vms                     (list):  List of VMs

        Raises:
            Exception:
                if it fails to get vm list
        """

        def absolute_vm_name():
            list_of_vms = [vm_rule['display_name']]
            return list_of_vms

        def tag():
            pattern = self.map_filter_by_instance("tag:" + vm_rule['display_name'] + "\ntype:" + (vm_rule['type'].lower()))
            list_of_vms = self.hvobj.get_all_vms_in_hypervisor(pattern=pattern,
                                                               c_type='listvms')
            return list_of_vms

        def vm_power_state_excp():
            pattern = self.map_filter_by_instance("id:" + vm_rule['id'] + "\ntype:" + (vm_rule['type'].lower()))
            list_of_vms = self.hvobj.get_all_vms_in_hypervisor(pattern=pattern,
                                                               c_type='listvms')
            return list_of_vms

        def expr_vm_name():
            expr_rule = self.gui_to_python_regex(vm_rule['display_name'])
            list_of_vms = self.match_pattern(vm_rule, expr_rule)
            return list_of_vms

        def expr_other():
            if vm_rule['type'].lower() in ('vmpowerstate'):
                expr_rule = vm_rule['display_name']
            else:
                expr_rule = self.gui_to_python_regex(vm_rule['display_name'])
            pattern = self.map_filter_by_instance(
                "display_name:" + expr_rule + "\ntype:" + (vm_rule['type'].lower()))
            list_of_vms = self.hvobj.get_all_vms_in_hypervisor(pattern=pattern, c_type='listvms')
            return list_of_vms

        check_rules = {
            absolute_vm_name: vm_rule['type'].lower()
                                in ('vmname', 'vm', 'virtual machine') and vm_rule['id'] != '',
            tag: vm_rule['type'].lower() in ('tag', 'tagcategory') and 'urn:vmomi' not in vm_rule['id'],
            vm_power_state_excp: vm_rule['type'].lower() not in ('server', 'vmpowerstate') and vm_rule['id'] != '',
            expr_vm_name: vm_rule['type'].lower() in ('vmname', 'vm'),
            expr_other: True
        }

        for val in check_rules:
            if check_rules[val]:
                return val()

    def match_pattern(self, vm_rule, expr_rule):
        """
        Does all the regex match for the rule

        Args:
            vm_rule                         (list):  content rule for discovery

        Returns:
            _temp_list                      (list):  List of VMs after pattern match

        Raises:
            Exception:
                if it fails to get vm list after pattern match
        """
        try:
            #_vms = self.py_equivalent_regex(vm_rule['display_name'])
            reg = re.compile(expr_rule, re.I)
            _temp_list = list(filter(reg.match, self.all_vm_list))
            if not vm_rule['equal_value']:
                _temp_list = self.merge_rules(self.all_vm_list, _temp_list, 'not')
            return _temp_list
        except Exception as err:
            self.hvobj.log.exception(
                "Failed to get vm list after pattern match {0}".format(err))
            raise err

    def is_content_modifier(self):
        """
        Will add details for this later
        """
        # if pattern in powerstate, notes, tag
        # return True
        # for now testing with just vms, returning false
        return False

    def gui_to_python_regex(self, expr_rule):
        """

        Args:
            expr_rule                           (str):  regular expression equivalent in subclient

        Returns:
            expr_rule                           (str):  regular expression equivalent in python
        Raises:
            Exception:
                if it fails to convert to python equivalent regex
        """

        try:
            rep = {'?': '\w{1}', '!': '^', '*': '.*'}
            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            expr_rule = pattern.sub(lambda m: rep[re.escape(m.group(0))], expr_rule)
            if expr_rule.isalnum():
                expr_rule = '^' + expr_rule + '$'
            elif expr_rule[-1].isalnum():
                expr_rule = expr_rule + '$'
            return expr_rule
        except Exception as err:
            self.hvobj.log.exception(
                "Failed to convert into python equivalent regex {0}".format(err))
            raise err