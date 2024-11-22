# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: This test case verifies that the vmware replication ip customization works properly for both linux and
windows vms by verifying in the backend with (Linux proxy + No FREL)

TestCase: Class for executing this test case
Sample JSON: {
        "ClientName": "idc",
        "source_vms": ["vm1", "vm2"],
        "recovery_target": "target",
        "storage_name" : "storage",
        "dns_1": "<destination machine dns primary>",
        "dns_2": "<destination machine dns secondary>",
}
"""
from Web.Common.exceptions import CVTestCaseInitFailure

tc_56283 = __import__('56283')


class TestCase(tc_56283.TestCase):
    def __init__(self):
        super().__init__(self)
        self.name = ("VMWare: IP customization verification (FREL capable proxy in Target "
                     "but no FREL on destination hypervisor)")

    def verify_proxy_configuration(self, auto_instance):
        """Verifies that the proxy configuration is Windows + FREL"""
        hypervisor_name = auto_instance.auto_vsaclient.vsa_client.name
        for proxy_name in auto_instance.proxy_list:
            proxy_client = self.commcell.clients.get(proxy_name)
            if 'windows' in proxy_client.os_info.lower():
                raise CVTestCaseInitFailure("Windows Proxy not configured on source hypervisor")
            try:
                if self.dr_helper.source_auto_instance.fbr_ma:
                    raise CVTestCaseInitFailure(f"FREL configured for {hypervisor_name}, but it shouldn't")
            except Exception:
                pass
