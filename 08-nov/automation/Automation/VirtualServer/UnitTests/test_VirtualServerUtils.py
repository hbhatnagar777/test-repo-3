import unittest
from VirtualServer.VSAUtils.VirtualServerUtils import bytesto, get_os_flavor


class VirtualServerHelperTest(unittest.TestCase):

    def test_bytesto(self):
        result_kb = bytesto(1024, 'KB')
        self.assertEqual(1, result_kb)

        result_mb = bytesto(123456, 'MB')
        self.assertEqual(0.11773681640625, result_mb)

        result_gb = bytesto(999999999, 'GB')
        self.assertEqual(0.9313225736841559, result_gb)

        result_tb = bytesto(9999999999999, 'TB')
        self.assertEqual(9.094947017728373, result_tb)

    def test_get_os_flavor(self):
        os_to_tests = [
            {"Microsoft Windows server 2012": "Windows"},
            {"CentOS": "Unix"}
        ]

        for os_type in os_to_tests:
            os = list(os_type)[0]
            result = get_os_flavor(os)
            self.assertEqual(result, os_type[os])


if __name__ == "__main__":
    import unittest
    unittest.main()
