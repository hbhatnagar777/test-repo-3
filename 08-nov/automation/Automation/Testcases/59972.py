# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Document generation report datasets validation TestCase"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Reports import reportsutils
from Web.Common.page_object import TestStep
from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Validate Document generation report datasets are working fine"
        self.utils = None
        self.cre_api = None
        self.reports = ["Quarterly Business Review PPT Datasets for Private Metrics", "RMS monthly report"]

    def init_tc(self):
        """ Initialize the testcase"""
        self.utils = CustomReportUtils(
            self, self.commcell.webconsole_hostname, username=self.inputJSONnode['commcell']["commcellUsername"]
            , password=self.inputJSONnode['commcell']["commcellPassword"]
        )

    @test_step
    def validate_datasets(self):
        """ validate QBR datasets"""
        commcell_ids = '(1008F2%20OR%20F9E72)'
        created_on = '%5B2020-03-01T00%3A00%3A00Z%20TO%202021-02-28T23%3A59%3A59Z%5D'
        group_name = REPORTS_CONFIG.REPORTS.METRICS.COMPANY_NAME
        group_id = self.commcell.user_groups.get(group_name).user_group_id
        for report in self.reports:
            self.log.info(f"Validate dataset for the report {report}")
            report_id = self.utils.get_report_id(report)
            datasets = self.utils.get_dataset_GUIDS(report_id)
            for dataset in datasets:
                if dataset in '7fc7f5d8-1717-4044-b333-6b948e390fb7':
                    result = self.utils.cre_api.get_data(dataset, {'ccGroupId': f'{group_id}'})
                    if result['failures']:
                        raise CVTestStepFailure(f"Dataset {dataset} "
                                                f"execution is failing with {result['failures']}")

                elif dataset in 'a2f11ff2-1880-4df8-a87b-b70e87d66e2d' or \
                        dataset in 'c14622b2-06ad-440b-f1a8-ff1e4033e838':
                    result = self.utils.cre_api.get_data(dataset, {'ccGroupId': f'{group_id}', 'commUniId': '0'})
                    if result['failures']:
                        raise CVTestStepFailure(f"Dataset {dataset} "
                                            f"execution is failing with {result['failures']}")
                elif dataset in 'a611a303-a7a5-4d62-8752-278818752260' \
                        or dataset in '14101162-3c03-4b66-8cc4-72f5d4f18530' \
                        or dataset in 'f7a8eaa0-682c-4ce2-b66e-9cf8836ce219'\
                        or dataset in 'e25f94cb-7eda-43c3-b8ff-b98c5712c99f'\
                        or dataset in 'a6c990ea-7a2d-4af0-a816-9071584cedac'\
                        or dataset in '1f3d3ee5-6cee-4edb-9132-c3f73cc77fac'\
                        or dataset in 'b1f1d153-4f4a-47cb-88d3-cc9cd6f10cd5'\
                        or dataset in 'fcb84440-00f8-423c-b30d-3b56dad1cd46'\
                        or dataset in 'd52ec686-995b-47fc-8fa9-a3db72715daf'\
                        or dataset in 'c29f15a6-4e6b-4846-b146-9558c8bc9be6'\
                        or dataset in '05e06861-6395-44ed-8ada-7a40d313c1c5'\
                        or dataset in 'a3d28451-937d-4bcf-991a-42e2dfe73af5'\
                        or dataset in '9ac0b320-836c-4788-ab33-6a1bc27b895b':
                    result = self.utils.cre_api.get_data(dataset, {'createdOn': f'{created_on}',
                                                                   'commCellId': f'{commcell_ids}'})
                    if result['failures']:
                        raise CVTestStepFailure(f"The report {report} dataset {dataset} "
                                                f"execution is failing with {result['failures']}")
                elif dataset in 'a4ad397e-ed0f-4672-9bb3-7ff2c6144ff8' or\
                        dataset in 'f88c5708-b213-4a8d-a183-6dce336f7523':
                    result = self.utils.cre_api.get_data(dataset, {'createdOn': f'{created_on}',
                                                                   'commCellId': f'{commcell_ids}', 'fromMonth': '12',
                                                                   'toMonth': '1'
                                                                   })
                    if result['failures']:
                        raise CVTestStepFailure(f"The report {report} dataset {dataset} "
                                                f"execution is failing with {result['failures']}")
                elif dataset in '5ead60de-2928-4b96-8aad-2b3224e382c9' or \
                        dataset in 'cd3d3405-1420-4eeb-ecf5-2e1727386673' or \
                        dataset in '7f914597-0c8e-4f70-ec48-9d0002dfd738' or \
                        dataset in 'a95c3175-0c5b-4335-83d9-de780f3186b7' or \
                        dataset in '8224601f-0e74-473d-bbff-3d3278720039' or \
                        dataset in 'a856a8bf-a300-431f-83b0-a7cadb179c32' or \
                        dataset in '46d024ad-70d4-4d4c-be6a-8e8ae62275e4':
                    result = self.utils.cre_api.get_data(dataset, {'commCellId': f'{commcell_ids}',
                                                                   'createdOn': f'{created_on}',
                                                                   'ccGroupId': '547', 'fromMonth': '12',
                                                                   'toMonth': '1'
                                                                   })
                    if result['failures']:
                        raise CVTestStepFailure(f"The report {report} dataset {dataset} "
                                                f"execution is failing with {result['failures']}")
                else:
                    result = self.utils.cre_api.get_data(dataset)
                    if result['failures']:
                        raise CVTestStepFailure(f"The report {report} dataset {dataset} "
                                                f"execution is failing with {result['failures']}")

    def run(self):
        try:
            self.init_tc()
            self.validate_datasets()
        except Exception as err:
            handle_testcase_exception(self, err)




