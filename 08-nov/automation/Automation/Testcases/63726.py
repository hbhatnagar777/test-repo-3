# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from AutomationUtils.database_helper import CommServDatabase
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install import installer_constants, installer_utils
import requests, urllib, xmltodict


class TestCase(CVTestCase):
    """Testcase : Validating DB for GA/CR CU Packs"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Validating DB for GA/CR CU Packs"
        self.tcinputs = {}
        self.default_log_directory = None
        self.commcell = None
        self.config_json = None
        self.csdb = None

    def get_cu_from_xml(self, sp_transaction_recut, xml_url=installer_constants.DEFAULT_MAINTENANCE_RELEASE_XML):
        """
            Returns integer value of latest CU pack for given SP

            Returns:
                int:   latest cu_pack released for that SP
        """
        try:
            if int(sp_transaction_recut.split('_R')[-1]) <= 952:
                xml_url = installer_constants.DEFAULT_CU_CONFIGURATION_XML
                file_request = requests.get(xml_url.format(sp_transaction_recut.split('_')[0]))
            else:
                file_request = requests.get(xml_url.format(sp_transaction_recut))
        except urllib.error.HTTPError as e:
            return None

        available_cu_packs = []
        cu_configuration_dict = xmltodict.parse(file_request.content)
        if not isinstance(cu_configuration_dict[
                              'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries'], list):
            cu_pack_entries = cu_configuration_dict[
                'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries']
            available_cu_packs.append([int(cu_pack_entries['@Number']), int(cu_pack_entries['@GA'])])
        else:
            for each_cu_pack in \
                    cu_configuration_dict['UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs'][
                        'CUPackEntries']:
                available_cu_packs.append([int(each_cu_pack['@Number']), int(each_cu_pack['@GA'])])
        if not available_cu_packs:
            raise Exception("Unable to find latest CU pack")
        return available_cu_packs

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.csdb = CommServDatabase(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(f"SP version of CS installed is {str(self.commcell.commserv_version)}")
            query = f"select distinct u.* from PatchUPVersion u join simInstalledPackages s on u. UPNumber=s.UPNumber " \
                    f"join PatchSPVersion p on p.id=s.SPVersionID and p.id=u.SPVersionID where s.ClientId=2; " \

            self.log.info(query)
            self.csdb.execute(query)
            record = self.csdb.fetch_one_row(named_columns=True)
            self.log.info(record)

            # Mapping the CU's present in the DB
            DB_CU_Mapping = [int(record['UPNumber']),int(record['nGA'])]

            # Mapping the CU's present in the BinaryInfo.xml
            self.log.info(f"SP{self.commcell.commserv_version}")
            trans_recut = installer_utils.get_latest_recut_from_xml(str(self.commcell.commserv_version))
            self.log.info(trans_recut)
            records = self.get_cu_from_xml(trans_recut)

            self.log.info("Available CU Pack's in Maintenance Release XML")
            self.log.info(records)

            if DB_CU_Mapping in records:
                self.log.info("XML and DB are in sync")

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        pass