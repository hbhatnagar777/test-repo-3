# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Custom JavaScript and CSS"""
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Custom JavaScript and CSS"
        self.browser = None
        self.webconsole = None
        self.export = None
        self.utils = None
        self.report_builder = None
        self.table = None
        self.page = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode["commcell"]["commcellUsername"],
                                           password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.goto_reports()

            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
            navigator = Navigator(self.webconsole)
            navigator.goto_report_builder()
            query = """
                             DECLARE @i INT = 0
                             DECLARE @tmpTable table(
                                 ID INT IDENTITY(1,1),
                                 colExpr VARCHAR(MAX),
                                 colScrpt VARCHAR(MAX),
                                 colCSS VARCHAR(MAX),
                                 tblScrpt VARCHAR(MAX),
                                 pgScrpt VARCHAR(MAX),
                                 tblCSS VARCHAR(MAX),
                                 pgCSS VARCHAR(MAX))
                             WHILE @i < 3
                                 BEGIN
                                     INSERT INTO @tmpTable (colExpr, colScrpt, colCSS, tblScrpt, pgScrpt, tblCSS, pgCSS)
                                     VALUES('colExpr', 'colScrpt', 'colCSS', 'tblScrpt', 'pgScrpt', 'tblCSS', 'pgCSS')
                                     SET @i = @i + 1
                                 END
                             SELECT *
                             FROM @tmpTable
                            """

            self.report_builder = builder.ReportBuilder(self.webconsole)
            self.report_builder.set_report_name(self.name)
            dataset = builder.Datasets.DatabaseDataset()
            self.report_builder.add_dataset(dataset)
            dataset.set_dataset_name("Automation Dataset 49973")
            dataset.set_sql_query(query)
            dataset.save()
            self.table = builder.DataTable("Automation Table")
            self.report_builder.add_component(self.table, dataset)
            self.table.add_column_from_dataset("ID")
            self.table.add_column_from_dataset("tblScrpt")
            self.table.add_column_from_dataset("tblCSS")
            self.table.add_column_from_dataset("pgCSS")
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def page_level_script(self):
        """Enter Page level script"""
        script = """function pgScript() {return 'Page Level Script';}"""

        self.page = builder.Page("Page0")
        self.report_builder.associate_page(self.page)
        self.page.custom_javascript(script)

        col_pg_script = self.table.Column("pgScrpt")
        self.table.add_column(col_pg_script)
        col_pg_script.format_as_custom("return pgScript();")

    @test_step
    def page_level_css(self):
        """Enter Page level css"""
        script = "#%s {color: green;}" % self.table.id
        self.page.custom_styles(script)

    @test_step
    def table_level_script(self):
        """Enter table level script"""
        script = """if(columnIndex == 1) {return columnIndex + ' ' + rowIndex;}"""
        self.table.set_cell_expression(script)
        self.report_builder.refresh()

    @test_step
    def table_level_css(self):
        """Enter table level css"""
        script = "font-size: 130%;"
        self.table.set_row_style(script)
        self.report_builder.refresh()

    @test_step
    def column_level_expression(self):
        """Enter Column level expression"""
        script = "return cellData + ' textScript';"
        col_colexpr = self.table.Column("colExpr")
        self.table.add_column(col_colexpr)
        col_colexpr.format_as_custom(script)

    @test_step
    def column_level_script(self):
        """Enter column level script"""
        script = "return cellData + ' ' + row['ID'];"
        col_colscrpt = self.table.Column("colScrpt")
        self.table.add_column(col_colscrpt)
        col_colscrpt.format_as_custom(script)

    @test_step
    def column_level_css(self):
        """Enter column level css"""
        script = "background-color:yellow"
        col_colcss = self.table.Column("colCSS")
        self.table.add_column(col_colcss)
        col_colcss.set_custom_styles(script)

    def validate_table(self):
        """validate table on builder and viewer"""
        self.log.info("Inside Builder\n")
        self.report_builder.save(deploy=True)
        self.report_builder.open_report()
        self.validate_table_content()
        report_viewer = viewer.CustomReportViewer(self.webconsole)
        self.table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(self.table)
        self.log.info("Inside Viewer\n")
        self.validate_table_content()

    @test_step
    def export_as_html(self):
        """Export the report as HTML"""
        report_viewer = viewer.CustomReportViewer(self.webconsole)
        export = report_viewer.export_handler()
        self.utils.reset_temp_dir()
        export.to_html()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

        path = self.utils.get_temp_files("html")
        self.browser.driver.execute_script("window.open()")
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
        self.browser.driver.get(path[0])
        report_viewer = viewer.CustomReportViewer(self.webconsole)
        self.table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(self.table)
        self.log.info("Opening saved HTML\n")
        self.validate_table_content()
        self.browser.driver.close()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

    @test_step
    def validate_table_content(self):
        """Validate table column data"""
        data = {'ID': ['1', '2', '3'],
                'tblScrpt': ['1 0', '1 1', '1 2'],
                'tblCSS': ['tblCSS', 'tblCSS', 'tblCSS'],
                'pgCSS': ['pgCSS', 'pgCSS', 'pgCSS'],
                'pgScrpt': ['Page Level Script', 'Page Level Script', 'Page Level Script'],
                'colExpr': ['colExpr textScript', 'colExpr textScript', 'colExpr textScript'],
                'colScrpt': ['colScrpt 1', 'colScrpt 2', 'colScrpt 3'],
                'colCSS': ['colCSS', 'colCSS', 'colCSS']}

        detailed_data = self.table.get_attributed_table_data()
        dict_ = dict()
        for key, values in detailed_data.items():
            list_ = list()
            for value in values:
                if value["font_color"] != "rgba(51, 51, 51, 1)":
                    raise CVTestStepFailure("Validation Failed: Since the cell {0} under  "
                                            "column '{1}' received the font_color property {2}."
                                            .format(value["data"], key, value["font_color"]))

                if value["font_size"] != "18.2px":
                    raise CVTestStepFailure("Validation Failed: Since the cell {0} under "
                                            "column '{1}' received the font_size  property {2}."
                                            .format(value["data"], key, value["font_size"]))

                if key == 'colCSS' and value["bg_color"] != "rgba(255, 255, 0, 1)":
                    raise CVTestStepFailure("Validation Failed: Since the cell {0}  under column "
                                            "'{1}' received the colCSS with bg_color property {2}."
                                            .format(value["data"], key, value["bg_color"]))

                elif key != 'colCSS' and value["bg_color"] != "rgba(0, 0, 0, 0)":
                    raise CVTestStepFailure("Validation Failed: Since the cell {0}  under "
                                            "column '{1}' received the bg_color property {2}."
                                            .format(value["data"], key, value["bg_color"]))

                list_.append(value["data"])
            dict_[key] = list_
        SQLQueries.validate_equality(data, dict_)

    def run(self):
        try:
            self.init_tc()
            self.page_level_script()
            self.page_level_css()
            self.table_level_script()
            self.table_level_css()
            self.column_level_expression()
            self.column_level_script()
            self.column_level_css()
            self.validate_table()
            self.export_as_html()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
