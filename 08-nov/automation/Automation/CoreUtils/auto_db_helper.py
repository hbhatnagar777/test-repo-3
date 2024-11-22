# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file to update the Automation Database with the list of test cases,
and their inputs and other attributes before every run.

AutoDBHelper is the only class defined in this file.

AutoDBHelper: Helper class to populate the Automation Database with the test case attributes.

AutoDBHelper:

    __init__()                  --  initializes the instance of the AutoDBHelper class

    _get_directories_list()     --  returns the list of sub directories under specified directory

    _get_test_cases()           --  returns the list of test cases present under the given path

    _read_testcase_details()    --  reads test case details, and updates the test case details dict

    _generate_xml_string()      --  generates the XML string using the test case details dictionary

    _write_xml_to_file()        --  write the XML to the file TestCaseDB.xml under CoreUtils path

    _parse_testcase_directory() --  parses the test case directory and read the list of test cases
                                        present, and their inputs

    _parse_package()            --  parses automation package and returns list of test cases

    execute()                   --  executes automation db helper function

    xml()                       --  returns the xml string

"""

import os
import imp
import sys
import threading
import xml.etree.cElementTree as ET


class AutoDBHelper(object):
    """Helper class to update the Automation Database with the test cases, and their attributes."""

    def __init__(self):
        """Initializes the instance of AutoDBHelper class."""
        self._test_case_details = {}
        self._automation_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._lock = threading.Lock()
        self._xml = ''

    @staticmethod
    def _get_directories_list(input_directory):
        """Returns the list of directories present under the specified input directory.

            Args:
                input_directory     (str)   --  path of the directory to get the sub directories of

            Returns:
                list    -   list consisting of the sub directories inside the input directory
        """
        for _ in os.walk(input_directory):
            yield _[0]

    def _get_test_cases(self, path):
        """Returns the list of test cases present inside the given path.

            Args:
                path    (str)   --  full path of the test cases directory

            Returns:
                list    -   list consisting of the test cases present under the given path
        """
        test_cases = []

        for item in os.listdir(path):
            if item.endswith(".py"):
                test_cases.append(item)

        return test_cases

    def _read_testcase_details(self, test_case_id, directory_path):
        """Reads the test case details, and updates the test case details dictionary."""
        self._lock.acquire()

        test_case_id = test_case_id.replace(".py", "")

        try:
            path = imp.find_module(test_case_id, [directory_path])
            module = imp.load_module(test_case_id, *path)

            test_case_class = getattr(module, 'TestCase')
            test_case = test_case_class()

            if (not test_case.show_to_user
                or test_case.product is None
                or test_case.feature is None):
                return

            temp_dict = {}
            temp_dict[test_case_id] = {
                "TestCaseName": test_case.name,
                "TestCaseInputs": test_case.tcinputs,
                "Product": test_case.product,
                "Feature": test_case.feature,
                "OS": str(test_case.applicable_os),
                "ShowToUser": '1' if test_case.show_to_user else '0'
            }

            self._test_case_details.update(temp_dict)
        except Exception:
            pass
        finally:
            try:
                self._lock.release()
            except RuntimeError:
                pass

    def _generate_xml_string(self):
        """Generates the xml string input to be passed to db script"""
        if self._test_case_details:
            root = ET.Element("TestCases")

            for test_case_id in self._test_case_details:
                test_case = ET.SubElement(root, "TestCase")
                ET.SubElement(test_case, "TestCaseID").text = test_case_id
                ET.SubElement(
                    test_case,
                    "TestCaseName").text = self._test_case_details[test_case_id]['TestCaseName']
                ET.SubElement(
                    test_case,
                    "Product").text = self._test_case_details[test_case_id]['Product']
                ET.SubElement(
                    test_case,
                    "Feature").text = self._test_case_details[test_case_id]['Feature']
                ET.SubElement(
                    test_case,
                    "OS").text = self._test_case_details[test_case_id]['OS']
                ET.SubElement(
                    test_case,
                    "ShowToUser").text = self._test_case_details[test_case_id]['ShowToUser']

                test_case_inputs = ET.SubElement(test_case, "TestCaseInputs")

                for key, value in self._test_case_details[test_case_id]['TestCaseInputs'].items():
                    input_element = ET.SubElement(test_case_inputs, "Input")
                    input_element.set('name', key)
                    input_element.text = None

            self._xml = ET.tostring(root)

    def _write_xml_to_file(self):
        """Writes the XML to a file with the name: `TestCaseDB.xml` inside the CoreUtils folder."""
        try:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TestCaseDB.xml')

            if self.xml:
                with open(file_path, 'w') as output_file:
                    output_file.write(self.xml)
        except Exception:
            raise Exception("Failed to generate test case db file")

    def _parse_testcase_directory(self, testcase_directory, recursively=False):
        """Parses the test case directory and reads the list of test cases
            present in the folder, and their inputs and other attributes.

            Args:
                testcase_directory     (str)   --  path of the test case directory

                recursively            (bool)   -- is set parse the test case
                directory recursively
                            default: False
        """
        sys.path.append(testcase_directory)

        test_cases_list = self._get_test_cases(testcase_directory)

        for test_case in test_cases_list:
            self._read_testcase_details(test_case, testcase_directory)

        if recursively:
            sub_directories = self._get_directories_list(testcase_directory)
            if sub_directories:
                [self._parse_testcase_directory(path) for path in sub_directories]

        sys.path.remove(testcase_directory)

    def _parse_package(self):
        """Parses the Automation Package to get the list of Test Cases, and their attributes."""
        try:
            sys.path.append(self._automation_directory)

            # read sub directories in current directory
            testcases_directory = os.path.join(self._automation_directory, 'Testcases')
            custom_directory = os.path.join(self._automation_directory, 'Custom')

            self._parse_testcase_directory(testcases_directory)
            self._parse_testcase_directory(custom_directory, recursively=True)

            self._generate_xml_string()
        except Exception as excp:
            raise Exception("Failed to parse package with error: {0}".format(excp))
        finally:
            sys.path.remove(self._automation_directory)

    @property
    def xml(self):
        """Returns the value of the xml attribute."""
        if self._xml:
            return self._xml.decode()

        return self._xml

    def execute(self, write_to_file=False):
        """Parses through the Automation Package and generates the XML.

            Args:
                write_to_file   (bool)  --  boolean flag to specify whether to write the XML
                                                generated to a file, or to return the XML string

                True    -   method will write the XML to a file

                False   -   method will return the XML string

                    default: False

            Returns:
                None    -   if the flag write_to_file was set to True

                str     -   XML string, if the flag write_to_file was set to False
        """
        self._parse_package()

        if write_to_file is True:
            self._write_xml_to_file()
            return None

        return self.xml


def main(write_to_file=False):
    """Main method for initializing instance of the AutoDBHelper class, and parsing the Automation
        Package, and generating the XML.

        Args:
            write_to_file   (bool)  --  boolean flag to specify whether to write the XML generated
                                            to a file, or to return the XML string

                True    -   method will write the XML to a file

                False   -   method will return the XML string

                    default: False
    """
    auto_db_helper = AutoDBHelper()
    return auto_db_helper.execute(write_to_file)


if __name__ == "__main__":
    FLAG = False

    if len(sys.argv) > 1:
        FLAG = bool(sys.argv[1])

    print(main(FLAG))
