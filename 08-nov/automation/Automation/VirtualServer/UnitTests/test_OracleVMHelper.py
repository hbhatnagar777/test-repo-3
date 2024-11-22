import unittest
import responses
from collections import OrderedDict
from unittest.mock import MagicMock, patch
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor, OracleVMHelper


class OracleVMHelperTest(unittest.TestCase):

    ClassIsSetup = False

    def mock_get_servers(self, server):
        return [{"name": "test_server_name_0",
                 "vmIds": [{"name": "vm1", "uri": "https://vm1"},
                           {"name": "vm2", "uri": "https://vm1"}]},
                {"name": "test_server_name", "vmIds": []}]

    def mock_repository_priority_list(self):
        return {"dataStore1": 50, "dataStore2": 30}

    def mock_get_datastore_dict(self):
        return {"dataStore1": 40, "dataStore2": 300}

    def mock_repository_priority_list_positive(self):
        return {"dataStore1": 500, "dataStore2": 300}

    def mock_get_required_resource_for_restore(self, vmlist):
        return 12, 200

    def setUp(self):
        if not self.ClassIsSetup:
            print("Creating OracleVM class object")
            self.setupClass()
            self.__class__.ClassIsSetup = True

    @responses.activate
    @patch.object(OracleVMHelper, 'get_servers', mock_get_servers)
    def setupClass(self):
        responses.add(responses.GET,
                      'https://v:7002/ovm/core/wsapi/rest/Manager',
                      json=[{"managerRunState": "RUNNING"}], status=200)
        unittest.TestCase.setUp(self)

        commcell_mock = MagicMock();
        self.__class__.oracleVM_hypervisor = Hypervisor(
            "oracle center",
            "hostname",
            "username",
            "password",
            "oraclevm", commcell_mock)

    def test_init_values(self):
        self.assertNotEqual(self.oracleVM_hypervisor.vm_dict, {})
        self.assertEqual(len(list(self.oracleVM_hypervisor.vm_dict)), 2)

    @responses.activate
    def test_get_servers(self):
        responses.add(responses.GET,
                      'https://v:7002/ovm/core/wsapi/rest/Server',
                      json=self.mock_get_servers(""), status=200)
        ret_value_default = self.oracleVM_hypervisor.get_servers()[0]
        self.assertEqual(len(ret_value_default["vmIds"]), 2)
        self.assertEqual(ret_value_default["vmIds"][0]["name"], "vm1")
        self.assertEqual(ret_value_default["vmIds"][1]["name"], "vm2")

        ret_value_param = self.oracleVM_hypervisor.get_servers("test_server_name")[0]
        self.assertEqual(ret_value_param["name"], "test_server_name")
        self.assertEqual(len(ret_value_param["vmIds"]), 0)

    # test compute_free_resources
    @patch.object(OracleVMHelper, '_get_repository_priority_list', mock_repository_priority_list)
    @patch.object(OracleVMHelper, '_get_required_resource_for_restore',
                  mock_get_required_resource_for_restore)
    def test_should_return_none_when_no_datastore_is_available(self):
        host_name, repository = self.oracleVM_hypervisor.compute_free_resources(['testvm1'])
        self.assertEqual(host_name, self.oracleVM_hypervisor._server)
        self.assertIsNone(repository)

    @patch.object(OracleVMHelper, '_get_repository_priority_list',
                  mock_repository_priority_list_positive)
    @patch.object(OracleVMHelper, '_get_required_resource_for_restore',
                  mock_get_required_resource_for_restore)
    def test_should_return_correct_data_store(self):
        host_name, repository = self.oracleVM_hypervisor.compute_free_resources(['testvm1'])
        self.assertEqual(host_name, self.oracleVM_hypervisor._server)
        self.assertEqual(repository, "dataStore1")

    # test _get_repository_priority_list
    @patch.object(OracleVMHelper, '_get_datastore_dict', mock_get_datastore_dict)
    def test_get_repository_priority_list(self):
        sorted_data_store_dict = self.oracleVM_hypervisor._get_repository_priority_list()
        self.assertIsInstance(sorted_data_store_dict, OrderedDict)
        self.assertEqual(list(sorted_data_store_dict)[0], 'dataStore2')


if __name__ == "__main__":
    import unittest
    unittest.main()
