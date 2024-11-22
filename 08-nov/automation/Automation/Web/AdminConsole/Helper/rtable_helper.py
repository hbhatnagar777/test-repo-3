# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

This module provides generic functions or operations that can be used to run
basic operations and validation tests on any RTable component of any listing page

---------------------------------------------------------------------------------------------

RTableHelper : This class provides generic test methods that can test common grid functions in any listing page

__init__()                                 --  Initialize object of RTableHelper class associated

================================= SUBCLASSES ===================================

ParsingCriteria:    Class containing methods to parse cell elements to extract cell value

SortingCriteria:    Class containing methods to validate sort among elements of a column

MatchingCriteria:   Class containing methods to match expected value for a cell and the UI value of that cell

================================= SETUP UTILS ==================================

setup_table_columns_as_specified()  --  setup up the UI grid with only the columns specified, and max pagination

clean_up()                          --  deletes any csv files downloaded

parse_table_from_csv()              --  reads table content from csv downloaded

parse_table_from_html()             --  reads table content from innerHTML value

verify_id_column()                  --  checks if input table, can have given columns as primary key or ID

intersect_tables()                  --  performs intersection operation among given tables and returns result

union_tables()                      --  performs union operation from given table and returns result

pprint_table()                      --  returns formatter printable string for logging tables

random_truncate_string()            --  randomly truncates given string within given parameters

get_ui_row_id()                     --  gets the identifying tuple for given UI row

get_api_row_id()                    --  gets the identifying tuple for given API row

match_row_ids()                     --  matches the identifying tuples for UI and API rows

================================= VALIDATION UTILS ============================

compare_row_contents()              --  compares the row contents match the contents of corresponding expected row

generate_unit_filters()             --  generates all possible single column value filters from given table

apply_ui_filter()                   --  simulates filter operation on table and returns expected result

generate_column_filters()           --  generates all possible column filters of various sizes

generate_search_tests()             --  generates best list of keywords and expected result for search test

generate_filter_tests()             --  generates best list of filters and expected result for filter test

table_content_from_csv()            --  reads table content using csv method

table_content_from_html()           --  reads table content using html method

validate_expected_content()         --  validates the table contents as equal to given rows

================================= GRID TEST FUNCTIONS =====================================

compare_table_contents()            --  compares the contents in table match expected values

validate_sorting()                  --  tests complete sorting functionality in grid

validate_search()                   --  tests complete search functionality in grid

validate_filters()                  --  tests complete filter functionlity in grid

validate_views()                    --  tests complete custom views functionality in grid

"""
import csv
import functools
import itertools
import os
import random
from collections import OrderedDict
from typing import Union, Callable, Any

from dateutil.parser import parse
from lxml import etree
from selenium.webdriver.common.by import By
from tabulate import tabulate

from AutomationUtils import logger
from AutomationUtils.commonutils import parse_size, parse_duration, process_text, is_sorted
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, WebAction, PageService


def distributed_sample(dic: dict, n: int, criteria: Callable = None) -> dict:
    """
    Util to randomly pick distributed 'n' items from dictionary
    with equal chance for all dict item groups.
    (this dictionary item group criteria can be passed as input)

    Args:
        dic (dict)           -   the dict with value as iterable type
        n   (int)            -   the number of random items to pick
        criteria (func(k,v)) -   function that returns a grouping_category for key value
                                 default: it is len(value)
    Returns:
        sample  (dict)  -   dict with n random selected items
    """
    if not criteria:
        criteria = lambda key, value: len(value)
    subgroup = {}
    for k, v in dic.items():
        subgroup[criteria(k, v)] = subgroup.get(criteria(k, v), []) + [{
            k: v
        }]
    subgroups = list(subgroup.values())
    selection = {}
    for count in range(n):
        current_group = subgroups[count % len(subgroups)]
        if not current_group:
            subgroups.remove(current_group)
            current_group = subgroups[count % len(subgroups)]
        pick = random.choice(current_group)
        selection.update(pick)
        current_group.remove(pick)
    return selection


class RTableHelper(Rtable):
    """
    Helper class for RTable related tests from UI

    See 62677 and 62661 for usage in testing jobs tables
    """

    test_step = TestStep()
    rehydrator = Rehydrator('rtable_helper')

    class ParsingCriteria:
        """Class for storing methods to extract cell value from <td> element"""

        @staticmethod
        def default(elem: etree.Element) -> str:
            """
            gets all text content, except callouts and aria-hidden texts
            """
            text_parts = []
            if elem.get('aria-hidden') == 'true':
                return ""  # ignore callouts texts
            if elem.text:
                text_parts.append(elem.text.strip())
            for child in elem:
                text_parts.append(RTableHelper.ParsingCriteria.default(child))
            if elem.tail:
                text_parts.append(elem.tail.strip())
            return ''.join(text_parts)

        @staticmethod
        def apply_typecast(func: Callable) -> Callable:
            """
            gets all text content and applies func on it
            Note: this returns the callable so include the brackets ()
            """
            return lambda elem: func(RTableHelper.ParsingCriteria.default(elem))

        @staticmethod
        def tick_or_cross(elem: etree.Element) -> bool:
            """
            extracts svg icon tick and cross to True or False
            (based on users page 'Locked' and 'Enabled' columns)
            """
            svg_elem_viewbox = elem.xpath('.//svg')[0].get('viewbox')
            # using viewbox to identify for now...todo: full svg pixel comparisons with ui teer library icons
            if svg_elem_viewbox == "0 0 512 512":
                return True  # it's a tick icon
            return False

        @staticmethod
        def toggle_status(elem: etree.Element) -> bool:
            """
            extracts toggle status in the cell as True or False
            (based on Triggered alerts page 'Pin' column)
            """
            toggle_elem = elem.xpath('.//input[contains(@class, "MuiSwitch")]')[0]
            if 'Mui-checked' in toggle_elem.getparent().get('class'):
                return True
            return False

    class SortingCriteria:
        """Class for storing criterias to determine values in sequence are in sorted order"""

        @staticmethod
        def default(a: Any, b: Any) -> bool:
            """case-insensitive lexicographic comparison on string and default <= comparison on rest"""
            if isinstance(a, str):
                return a.lower() <= b.lower()
            else:
                return a <= b

        @staticmethod
        def with_nulls(nulls: list[str], func: Callable) -> Callable:
            """
            given null values is always the lowest in order, if no nulls
            the given Callable takes precedence.
            Note: This returns a callable, not a bool, so do include the brackets! ()
            """
            def criteria(a, b):
                if a in nulls:
                    return True
                return func(a, b)
            return criteria

        @staticmethod
        def numeric(a: Any, b: Any) -> bool:
            """ for comparing numbers """
            return float(a) <= float(b)

        @staticmethod
        def size_type(a: str, b: str) -> bool:
            """ for comparing size strings, like 0.00B, 24 MB, 35.65 KB, etc """
            return parse_size(a) <= parse_size(b)

        @staticmethod
        def datetime_mdy(a: str, b: str) -> bool:
            """ for comparing datetimes in day first formats """
            return parse(a, dayfirst=False) <= parse(b, dayfirst=False)

        @staticmethod
        def datetime_dmy(a: str, b: str) -> bool:
            """ for comparing datetimes in month after date type formats """
            return parse(a, dayfirst=True) <= parse(b, dayfirst=True)

        @staticmethod
        def duration_type(a: str, b: str) -> bool:
            """ for comparing duration type strings like 1hr 2 mins, etc .."""
            return parse_duration(a) <= parse_duration(b)

        @staticmethod
        def percentage_str(a: str, b: str) -> bool:
            """ for comparing percentage strings """
            return int(a.strip("% ")) <= int(b.strip("% "))

    class MatchingCriteria:
        """Class for storing criterias to determine if expected value matches cell value in UI"""
        @staticmethod
        def default(ui: Any, api: Any) -> bool:
            """default python equality operator"""
            return ui == api

        @staticmethod
        def numeric(ui: Any, api: Any) -> bool:
            """for comparing strings to numbers"""
            return float(ui) == float(api)

        @staticmethod
        def raw_string(ui: str, api: str) -> bool:
            """for comparing strings completely ignoring any whitespaces"""
            return process_text(ui) == process_text(api)

        @staticmethod
        def size_str_vs_bytes(ui: str, api: Any) -> bool:
            """for comparing size string in UI with number of bytes returned by API"""
            divisor = 1
            ui_bytes = parse_size(ui)
            if 'kb' in ui.lower():
                divisor = 2 ** 10
            elif 'mb' in ui.lower():
                divisor = 2 ** 20
            elif 'gb' in ui.lower():
                divisor = 2 ** 30
            elif 'tb' in ui.lower():
                divisor = 2 ** 40
            ui_for_compare = round(ui_bytes / divisor, 2)
            api_for_compare = round(int(api) / divisor, 2)
            return ui_for_compare == api_for_compare

        @staticmethod
        def date_str_vs_timestamp_dmy(ui: str, api: Any) -> bool:
            """for comparing date string in UI ddmmyyyy with unix timestamp in API"""
            colon_count = ui.count(':')
            diff_limit = 0
            if colon_count == 1:  # seconds is hidden, just HH:MM
                diff_limit = 59  # allow 59-second difference
            if colon_count == 0:  # no time, only date
                diff_limit = 60 * 60 * 24 - 1  # allow close to 1 day difference
            return abs(parse(ui, dayfirst=True).timestamp() - float(api)) <= diff_limit

        @staticmethod
        def date_str_vs_timestamp_mdy(ui: str, api: Any) -> bool:
            """for comparing date string in UI mmddyyyy with unix timestamp in API"""
            colon_count = ui.count(':')
            diff_limit = 0
            if colon_count == 1:  # seconds is hidden, just HH:MM
                diff_limit = 59  # allow 59-second difference
            if colon_count == 0:  # no time, only date
                diff_limit = 60 * 60 * 24 - 1  # allow close to 1 day difference
            return abs(parse(ui, dayfirst=False).timestamp() - float(api)) <= diff_limit

        @staticmethod
        def duration_str_vs_seconds(ui: str, api: Any) -> bool:
            """for comparing duration string in UI with total seconds returned in API"""
            return parse_duration(ui) == int(api)

        @staticmethod
        def percentage_str_vs_int(ui: str, api: Any) -> bool:
            """compares percentage string in UI with percent number returned by API"""
            return int(ui.strip("% ")) == int(api)

    def __init__(self, admin_console=None, title=None, id=None, xpath=None, **options) -> None:
        """
        Initializes the RTableHelper class

        Args:
            admin_console (AdminConsole)    -   instance of AdminConsole class
            title, id, xpath same as RTable class
            options:
                conjunctive_filters (bool)      -   How filter logic works in this table UI grid. Set to false if
                                                    combinations of filters use the 'OR' logic,
                                                    default: True, uses 'AND' logic

                filter_translations (dict)      -   Dict with lambda functions to imitate how filter is supposed to work
                                                    in this UI grid... (see self.filter_translations for default)
                                                    Dict keys are the filter enum and value is the lambda func,
                                                    the lambda func should return True if a row belongs in that criteria
                                                    filter for that column and value.

                Example format:
                {
                    Rfilter.equals: lambda row, col, val: row[col] == val
                    Rfilter.is_empty: lambda row, col, val: row[col] == ''
                    etc ... [make sure to only use the same argument variables row, col, val]
                }
                This will be used along with filter_criteria param of column_specifications

                column_specifications   (dict)  -   A dict containing information about each column in this table

                Example format:
                {
                    'column1': {
                        'cell_value':       a method to parse the <td> element as an eTree.HTML element and return
                        [[ function obj ]]  the value intended to be captured from that <td> element.
                                            Usefull for handling special cases like toggles or svg tick and cross icons.
                                            Default: the entire text value in the cell, ignoring callouts

                        'api_value_key':    a method to get the same column value from API returned json dict for a row
                        [[ function obj ]]  that takes 1 param, api_row, and returns that column value.
                                            Default: api_row.get('column1')

                        'match_key':        the criteria to match UI column value with API column value from above,
                        [[ function obj ]]  that takes 2 params, ui_val, api_val, and return True if match
                                            Default: ui_val == api_val

                        'is_primary_key':   this column can be used to identify rows uniquely, like primary key in DB
                        [[ boolean value ]] set True if this column is part of primary key,
                                            multiple columns can have this property and will be used together
                                            Default: False,
                                            if no primary key columns at all, all columns will be primary key

                        'is_sortable':      if given column is sortable, will be used for testing sort
                        [[ boolean value ]] Default: True, set false explicitly to stop sorting this column

                        'sort_key':         the criteria to validate if cells under that column are sorted,
                        [[ function obj ]]  that takes 2 params, a,b, values of that column in sequence,
                                            must return True if its in sorted order.
                                            Default: a <= b,

                        'is_searchable':    if given column is searchable, will be used to generate and test search
                        [[ boolean value ]] Default: True, set false explicitly for columns to avoid matching search

                        'search_value_key': a method to convert cell value under this column to searchable value
                        [[ function obj ]]  that takes 1 param, ui_value, and returns a str that is entered in search
                                            Default: str, applies the str() built-in function

                        'is_filterable':    if given column is filterable, will be used to generate and test filters
                        [[ boolean value ]] Default: True, set false explicitly for columns to avoid attempting filter

                        'filter_value_key': a method to convert cell value under this column to filterable value
                        [[ function obj ]]  that takes 1 param, ui_value, and returns a value that is filtered for
                                            Default: ui_value, direct pass, no processing

                        'filter_criteria' : filters for this column will only use given criteria,
                        [[ function obj ]]  must be one of enum Rfilter.Equals or Rfilter.Contains
                                            (only these two supported for now, more coming soon)
                                            Default: Rfilter.Equals
                    },
                    'column2': {...},
                    ...
                }
                Only columns specified here will be tested, all other columns will be ignored

                Here's a template to copy and paste:
                    'cell_value': '',
                    'api_value_key': '',
                    'match_key': '',
                    'is_primary_key': '',
                    'is_sortable': '',
                    'sort_key': '',
                    'is_searchable': '',
                    'search_value_key': '',
                    'is_filterable': '',
                    'filter_value_key': '',
                    'filter_criteria': ''
        """
        super().__init__(admin_console=admin_console, title=title, id=id, xpath=xpath)
        self.log = logger.get_log()
        self.__init_params__(options)

    def __init_params__(self, options: dict) -> None:
        """
        Initializes all test params from options given, and sets defaults

        Args:
            options (dict)  -   dict with all optional parameters

        Returns:
            None
        """
        self.use_csv = (str(options.get('use_csv')).lower()) == 'true'
        self.conjunctive_filters = (str(options.get('conjunctive_filters')).lower()) != 'false'
        self.clean_csv = []
        self.column_specifications = {}
        for column, props in options.get('column_specifications', {}).items():
            self.column_specifications[column] = {
                'cell_value': props.get('cell_value', self.ParsingCriteria.default),
                'sort_key': props.get('sort_key', self.SortingCriteria.default),
                'api_value_key': props.get('api_value_key', lambda api_row: api_row.get(column)),
                'match_key': props.get('match_key', self.MatchingCriteria.default),
                'is_primary_key': props.get('is_primary_key', False),
                'is_filterable': props.get('is_filterable', True),
                'is_searchable': props.get('is_searchable', True),
                'is_sortable': props.get('is_sortable', True),
                'search_value_key': props.get('search_value_key', str),
                'filter_criteria': props.get('filter_criteria', Rfilter.equals),
                'filter_value_key': props.get('filter_value_key', lambda value: value)
            }
        self.id_columns = [
            col for col in self.column_specifications if self.column_specifications[col]['is_primary_key']]
        if not self.id_columns:
            self.id_columns = list(self.column_specifications.keys())
        self.filter_cols = [
            col for col in self.column_specifications if self.column_specifications[col]['is_filterable']]
        self.search_cols = [
            col for col in self.column_specifications if self.column_specifications[col]['is_searchable']
        ]
        self.sort_cols = [
            col for col in self.column_specifications if self.column_specifications[col]['is_sortable']
        ]
        self.sort_groups = {}
        for col in self.column_specifications:
            sort_key = self.column_specifications[col]['sort_key']
            self.sort_groups[sort_key] = self.sort_groups.get(sort_key, []) + [col]

        self.ui_nulls = ["", "notapplicable", "n/a", "null", "nil", "0", "0.0"]  # nulls to avoid filter and search
        self.filter_translations = {
                                       Rfilter.equals: lambda row, col, val: row[col] == val,
                                       Rfilter.contains: lambda row, col, val: val.lower() in str(row[col]).lower()
                                       # TODO: Handle other criteria
                                   } | options.get('filter_translations', {})

    # =============================== SETUP UTILS ============================================
    def setup_table_columns_as_specified(self) -> None:
        """
        Hides all columns not in column_specifications, and unhides all missing columns
        """
        visible_cols = set(self.get_visible_column_names()) - {'Actions'}
        hide_cols = list(visible_cols - set(list(self.column_specifications.keys())))
        show_cols = list(set(list(self.column_specifications.keys())) - visible_cols)
        if hide_cols:
            self.hide_selected_column_names(hide_cols)
        if show_cols:
            self.display_hidden_column(show_cols)
        try:
            self.set_pagination('max')
        except:
            pass

    def clean_up(self) -> None:
        """
        Method to clean up any changes made by this helper
        """
        self.log.info(">>> Deleting parsed CSVs")
        for csv_file in self.clean_csv:
            os.remove(csv_file)
        self.log.info(">>> CSV cleaned")

    @staticmethod
    def parse_table_from_csv(filepaths: list[str]) -> list[dict]:
        """
        parses table content from given csv filepaths

        Args:
            filepaths   (list)  -   list of filepaths of the csv files

        Returns:
            table_data  (list)  -   list of dicts for each row of table
        """
        ui_data = []
        for filepath in filepaths:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                records = csv.DictReader(f)
                for row in records:
                    ui_data.append({
                        col.strip(): cell.strip() for col, cell in dict(row).items()
                    })
        return ui_data

    @WebAction()
    def parse_table_from_html(self, table_html: str) -> list[dict]:
        """
        Method to parse entire table data from given html string

        Args:
            table_html  (str)   -   the innerHTML value of grid holder div

        Returns:
            table_data  (list)  -   list of dicts for each row of table
        """
        xml_tree = etree.HTML(table_html)
        if xml_tree.xpath("//*[text()='No results found']"):
            return []
        columns_list = [
            "".join(col.itertext()) for col in
            xml_tree.xpath("//th[@role='columnheader' and not(@style='display:none')]")
        ]
        checkbox_column = False
        if columns_list[0] == '':
            columns_list.pop(0)
            checkbox_column = True
        table_data = []
        for row_elem in xml_tree.xpath("//tr")[1:]:
            row_as_list = row_elem.xpath(".//td[not(@style='display:none')]")
            if checkbox_column:
                row_as_list.pop(0)

            row_dict = {}
            for col_name, cell in zip(columns_list, row_as_list):
                if col_name != 'Actions':
                    try:
                        parsed_cell = self.column_specifications[col_name]['cell_value'](cell)
                    except Exception as exp:
                        self.log.error(f'exception during parse of cell value: {cell} of column {col_name}')
                        self.log.error(f'full cell html stored in bucket -> parse_error')
                        self.rehydrator.bucket('parse_error').set({
                            'cell_html': cell,
                            'col_name': col_name,
                        })
                        raise exp
                    row_dict[col_name] = parsed_cell

            table_data.append(row_dict)
        return table_data

    @staticmethod
    def verify_id_column(rows: list[dict], column_names: list[str]) -> str:
        """
        validation check to make sure specified id columns are present
        and can be used to identify each row uniquely

        Args:
            rows (list)  -   list of dicts for each row of table
            column_names    (list)  -   list of column names to check uniqueness

        Returns:
            errors_str  (str)   -   error string if any failures
        """
        seen_combinations = set()
        for row in rows:
            try:
                combination = tuple(row[col] for col in column_names)
            except KeyError:
                return f'id columns missing in row = {row}'
            if combination in seen_combinations:
                return 'id columns cannot be primary key, duplicates found'
            seen_combinations.add(combination)

    @staticmethod
    def intersect_tables(tables: list[list[dict]]) -> list[dict]:
        """
        Util to calculate the common rows from given list of tables

        Args:
            tables  (list)  -   list of tables to intersect

        Returns:
            table_data  (list)  -   resulting table of intersection operation
        """
        # Compute intersection
        intersection = set.intersection(*[
            {frozenset(row.items()) for row in table}
            for table in tables
        ])
        # Convert back to list of dicts
        return [dict(fs) for fs in intersection]

    @staticmethod
    def union_tables(tables: list[list[dict]]) -> list[dict]:
        """
        Util to calculate the union of all rows from given list of tables

        Args:
            tables  (list)  -   list of tables to combine

        Returns:
            table_data  (list)  -   resulting table of union operation
        """
        union = set.union(*[
            {frozenset(row.items()) for row in table}
            for table in tables
        ])
        # Convert back to list of dicts
        return [dict(fs) for fs in union]

    @staticmethod
    def pprint_table(table: list[dict]) -> str:
        """
        function to return printable str for logging table rows neatly

        Args:
            table   (list)  -   list of dicts for each row of table

        Returns:
            formatted_str   -   string with table neatly formatted for printing or logging
        """
        if len(table) > 30:
            return (f'\n ... {len(table)} rows table, too large to log all rows ...\n' +
                    tabulate(table[:10], headers="keys", tablefmt="pretty"))
        return '\n' + tabulate(table, headers="keys", tablefmt="pretty")

    @staticmethod
    def random_truncate_string(string: str, limit: int, new_size: int = None) -> str:
        """
        truncates given string to under given limit

        Args:
            string  (str)   -   the string to truncate
            limit   (int)   -   upper limit on size
            new_size    (int)   -    precise size of truncated string

        Returns:
            truncated_string    -   the truncated part of input string
        """
        rand_idx = random.randrange(0, len(string) - limit + 1)
        reduced_keyword_size = new_size or random.randrange(max(3, limit - 3), limit)
        return string[rand_idx: (rand_idx + reduced_keyword_size)].strip()

    def get_ui_row_id(self, row: dict) -> tuple:
        """
        gets the tuple to identify given UI row with, using primary key column

        Args:
            row (dict)  -   a single row in table
        Returns:
            identifier  (tuple) -   tuple identifying that row
        """
        try:
            return tuple([row[column] for column in self.id_columns])
        except KeyError as exp:
            self.log.error(f'Cannot get row identifier, Exception = {str(exp)}'),
            self.log.error(f'Id columns given = {self.id_columns}')
            self.log.error(f'But some column is missing in below row {self.pprint_table([row])}')
            raise exp

    def get_api_row_id(self, row: dict) -> tuple:
        """
        gets the tuple to identify given API row with, using primary key columns and api value key

        Args:
            row (dict)  -   a single row from API response json, can be any format
        Returns:
            identifier  (tuple) -   tuple identifying that row
        """
        row_identifier = []
        for column in self.id_columns:
            try:
                api_col_val = self.column_specifications[column]['api_value_key'](row)
            except Exception as exp:
                self.log.error(f'Id columns given = {self.id_columns}')
                self.log.error(f'Cannot get column {column} from api_row, Exception = {str(exp)}')
                self.log.error(f'api_row below := {self.pprint_table([row])}')
                self.log.error('full row stored in bucket -> api_value_error')
                self.rehydrator.bucket('api_value_error').set({
                    'api_row': row,
                    'column': column
                })
                raise exp
            row_identifier.append(api_col_val)
        return tuple(row_identifier)

    def match_row_ids(self, ui_row_id: tuple, api_row_id: tuple) -> bool:
        """
        Matches row identifies for UI and API using match_key from column_specifications

        Args:
            ui_row_id   (tuple) -   row identifier for UI row
            api_row_id  (tuple) -   row identifier for API row

        Returns:
            True if both match else False
        """
        try:
            return all([
                self.column_specifications[id_column]['match_key'](ui_row_id[idx], api_row_id[idx])
                for idx, id_column in enumerate(self.id_columns)
            ])
        except Exception as exp:
            self.log.error('error during check row_ids match')
            self.log.error(f'id columns = {self.id_columns}')
            self.log.error(f'api row id tuple = {api_row_id}')
            self.log.error(f'ui row id tuple = {ui_row_id}')
            raise exp

    # # =============================== RTABLE OVERRIDES =================================
    @WebAction()
    def __get_column_names(self):
        """
        Quickly Read Column names from React Table Using Static html Parsing
        """
        col_xp = "//th[@role='columnheader' and not(@style='display:none')]"
        xml_tree = etree.HTML(self._driver.find_element(By.XPATH, self._xpath).get_attribute('innerHTML'))
        columns_list = []
        for col in xml_tree.xpath(col_xp):
            if col_name := "".join(col.itertext()):
                columns_list.append(col_name)
        return columns_list

    # =============================== VALIDATION UTILS =======================================

    def compare_row_contents(self, ui_row: dict, api_row: dict) -> list:
        """
        Compares the UI row dict with API row dict to validate if match

        Args:
            ui_row  (dict)  -   the ui row data
            api_row (dict)  -   the API returned json for that row

        Returns:
            errors  (list)   -   list with info on what columns mismatched
        """
        errors = []
        for column in self.column_specifications:
            ui_value = ui_row[column]
            try:
                api_value = self.column_specifications[column]['api_value_key'](api_row)
            except Exception as exp:
                errors.append(f'Failed to read column {column} from api row = {api_row}')
                errors.append(f'Exception = {exp}')
                return errors
            try:
                if not self.column_specifications[column]['match_key'](ui_value, api_value):
                    errors.append(f'Match returned False for column {column}, '
                                  f'ui value = {ui_value}, api value = {api_value}')
            except Exception as exp:
                errors.append(f'Match function for column {column} errored out matching '
                              f'ui value = {ui_value} and api value = {api_value}')
                errors.append(f'Exception = {exp}')
        return errors

    def generate_unit_filters(self, table_content: list[dict], restrict_columns: list[str],
                              size_cap: int = None) -> dict[tuple[str, str, Rfilter], list[dict]]:
        """
        Generates all possible unit filters for given table

        Args:
            table_content   (list)      -   the table contents as list of dicts
            restrict_columns    (list)  -   column names to restrict filter generation to
            size_cap    (int)           -   size limit for long values to truncate if crossed

        Returns:
            unit_filters    (dict)  -   dict with a unit filter as key and expected rows as value
                                        each filter is a 3-tuple (col, value, criteria)
            Example:
                {
                    (colA, valueX, Rfilter.contains): [{colA: valueX, colB: valueY, colC: valC}, {...}],
                    (colB, valueY, Rfilter.equals): [row1, row2, ...],
                    filter: rows_expected,
                    ....
                }

        """
        unit_filters = {}
        for ui_row in table_content:
            for col in restrict_columns:
                if process_text(ui_row[col]) not in self.ui_nulls:  # TODO: make null handling more flexible to caller
                    try:
                        filter_value = self.column_specifications[col]['filter_value_key'](ui_row[col])
                    except Exception as exp:
                        self.log.error(f'exception when applying filter key on value: {ui_row[col]} of column {col}')
                        raise exp
                    filter_key = (col, filter_value, self.column_specifications[col]['filter_criteria'])
                    if isinstance(filter_value, str):
                        if size_cap and len(filter_value) > size_cap:
                            if self.column_specifications[col]['filter_criteria'] == Rfilter.contains:
                                truncated_value = self.random_truncate_string(filter_value, size_cap)
                                filter_key = (col, truncated_value, Rfilter.contains)
                    if filter_key not in unit_filters:
                        unit_filters[filter_key] = self.apply_ui_filter(table_content, [filter_key])
        return unit_filters

    def apply_ui_filter(self, table_content: list[dict], filters: list[tuple[str, str, Rfilter]]) -> list[dict]:
        """
        utility to apply the filter to a table to generate result expected from UI Grid component

        Args:
            table_content   (list)      -   the table contents as list of dicts
            filters (list)              -   list of 3-tuples (col, value, criteria)

        Returns:
            filtered_result (list)      -   list of dicts, expected rows after filter
        """
        map_conditions = [
            functools.partial(self.filter_translations[criteria], col=col, val=val)
            for col, val, criteria in filters
        ]
        filter_combination_type = all if self.conjunctive_filters else any
        return [
            row for row in table_content
            if filter_combination_type(
                [condition(row) for condition in map_conditions]
            )
        ]

    def generate_column_filters(self, table_content: list[dict], columns: list[str] = None,
                                dimensions: int = 1, size_cap: int = None) -> list[Union[dict, OrderedDict]]:
        """
        Generates filter values and expected table rows

        Args:
            table_content     (list)    -   The rtable content visible in UI
                                            list of rows, each row is a dict like -> {col: value, col2: value2...}
            columns (list)              -   list of columns names to restrict filters to. default: all
            dimensions  (int)           -   number of filters at once
            size_cap    (int)           -   size or length of filter values to limit to (No limit by default)
                                            only applies to columns which have filter_criteria: Rfilter.contains

        Returns:
            filters_database (list)     -   list of dicts, each dict contains filters of each dimension from 1

            example:
                when dimension = 1
                    [{
                        (("value1", "column1", Rfilter.contains)) : [row1, row2, row3],
                        (("value2", "column2", Rfilter.equals)) : [row3, row2]
                    }]
                when dimension=3
                    [
                                            <dim 1 filters>
                        {(("value1", "column1", Rfilter.contains)) : [row1, row2, row3],...},

                                            <dim 2 filters>
                        {
                            (("val1", "col1", Rfilter.contains), ("val2", "col2", Rfilter.equals)): [rows]
                            (filter1, filter2): [rows],
                            ....
                        },

                                            <dim 3 filters>
                        {
                            (filt1, filt2, filt3): [],
                            (filtA, filtB, filtC): [row1, row2],
                            (filtX, filtY, filtZ): [row1, row2, row3]
                        }
                    ]
                    Each dict is Ordered by size of result so the most resultive filters appear in last
        """
        table_cols = columns
        if columns is None:
            table_cols = list(table_content[0].keys())
        if dimensions > len(table_cols):
            raise Exception(
                "Filter dimension cannot be above number of columns, repeated column filters arent supported yet")

        filters_database = [{} for _ in range(dimensions)]

        unit_filters = self.generate_unit_filters(table_content, table_cols, size_cap)
        filters_database[0] = {(test,): result for test, result in unit_filters.items()}
        for dimension in range(1, dimensions):
            combs = {}
            previous_dimension = filters_database[dimension - 1].copy()
            overhead_limit = 1000000
            if len(previous_dimension) * len(unit_filters) > overhead_limit:
                cutoff_amount = len(previous_dimension) - int(overhead_limit / len(unit_filters))
                if len(previous_dimension) - cutoff_amount >= 1:
                    for key in list(previous_dimension.keys())[:cutoff_amount]:
                        del previous_dimension[key]

            for raw_comb in itertools.product(previous_dimension, unit_filters):
                comb = (*raw_comb[0], raw_comb[1])
                unique_column = True
                # SAME COLUMN FILTERS CANNOT BE APPLIED SIMULTANEOUSLY
                for i, j in itertools.combinations(comb, 2):
                    if i[0] == j[0]:  # if any 2 filters within combinations apply on same column
                        unique_column = False
                        break  # TODO: handle same column filters, make customizable by caller
                if unique_column:
                    expected_rows = ((self.intersect_tables if self.conjunctive_filters else self.union_tables)
                                     ([previous_dimension[raw_comb[0]], unit_filters[raw_comb[1]]]))
                    combs[tuple(sorted(comb))] = expected_rows
            filters_database[dimension] = OrderedDict(sorted(combs.items(), key=lambda item: len(item[1])))
        return filters_database

    def generate_search_tests(self, table_content: list[dict], search_selection: list[str] = None,
                              truncate_size: int = None, new_min_size: int = None) -> OrderedDict:
        """
        Generates search tests, from UI table data

        Args:
            table_content     (list)    -   The rtable content visible in UI
                                            list of rows, each row is a dict like -> {col: value, col2: value2...}
            search_selection (list)     -   use to restrict which columns to pull search words from
                                            list of columns only from which search terms will be taken
                                            all searchable columns will still be computed for match result
            truncate_size    (int)      -   search string size limit, to avoid large search terms
                                            default: no cap, full string is used
            new_min_size    (int)       -   minimum size for substring cut out from the strings above size cap
                                            default: random size close to size_cap

        Returns:
            search_dict (dict)  -   dict with search string as key and matched rows data as value
                                    matched row data is dict with tuple of matched columns as key
                                    and the value is the list of row dicts that matched for this search string
                                    example: {
                                        "searchstring1": {
                                            (col1, col2): [matched_row_dict1, matched_row_dict3],
                                            (col3,): [matched_row_dict2]
                                        },
                                        "searchstring2": [...]
                                    }
        """
        search_dict = {}
        unit_filters = self.generate_unit_filters(table_content, self.search_cols)
        for unit_filter in unit_filters:
            column, search_string, criteria = unit_filter
            if search_selection and column not in search_selection:
                continue  # avoid search string generation from this column
            try:
                proper_search_string = self.column_specifications[column]['search_value_key'](search_string)
                if truncate_size and len(proper_search_string) > truncate_size:
                    # if search string too long, take only small random section of it
                    proper_search_string = self.random_truncate_string(
                        proper_search_string, truncate_size, new_min_size)
            except Exception as exp:
                self.log.error(f'error attempting to process value {search_string} of column {column} for search')
                raise exp
            matched_dict = search_dict.get(proper_search_string, {})

            for row in unit_filters[unit_filter]:
                if column not in matched_dict.get(frozenset(row.items()), []):
                    matched_dict[frozenset(row.items())] = sorted(
                        matched_dict.get(frozenset(row.items()), []) + [column])

            # appending job ids of superstring matches also
            for unit_filter2 in unit_filters:
                column2, search_string2, criteria2 = unit_filter2
                try:
                    proper_search_string2 = self.column_specifications[column2]['search_value_key'](search_string2)
                except Exception as exp:
                    self.log.error(f'error attempting to process value {search_string2} of column {column2} for search')
                    raise exp
                if proper_search_string.lower() in proper_search_string2.lower():  # todo: make this condition custom
                    for row2 in unit_filters[unit_filter2]:
                        if column2 not in matched_dict.get(frozenset(row2.items()), []):
                            matched_dict[frozenset(row2.items())] = sorted(
                                matched_dict.get(frozenset(row2.items()), []) + [column2])
            search_dict[proper_search_string] = matched_dict

        for search_term in search_dict:
            reformat_match_dict = {}
            for row_frozenset, matched_column_list in search_dict[search_term].items():
                restored_row = dict(row_frozenset)
                columns_key = tuple(matched_column_list)
                if restored_row not in reformat_match_dict.get(columns_key, []):
                    reformat_match_dict[columns_key] = reformat_match_dict.get(columns_key, []) + [restored_row]
            search_dict[search_term] = reformat_match_dict
        # more diverse matching search terms appear in the last
        return OrderedDict(sorted(search_dict.items(), key=lambda item: len(item[1])))

    def generate_filter_tests(self, table_content: list[dict], columns: list[str] = None, dimensions: int = 3,
                              avoid_null_filter: bool = True, size: int = 3,
                              truncate_size: int = None, intermediate_steps: bool = True,
                              avg_result_size: int = 10, filter_metric: Callable = None
                              ) -> tuple[dict[tuple, list[dict]], list[tuple]]:
        """
        Generates filter tests from UI table data

        Args:
            table_content     (list)    -   The rtable content visible in UI
                                            list of rows, each row is a dict like -> {col: value, col2: value2...}
            columns           (list)    -   list of columns to restrict filtering to. default: all
            dimensions  (int)           -   number of simultaneous filters
            avoid_null_filter   (bool)  -   whether to include filters that yield no results
            size    (int)               -   amount of tests per dimension (selected randomly)
                                            (total filter steps approx =  dimensions * size)
            truncate_size   (int)       -   the size limit after which long filter values will be truncated
                                            and criteria changed to 'contains' instead of 'equals'
            intermediate_steps  (bool)  -   whether to include intermediate steps between when switching between
                                            filters as part of validation filter steps
            avg_result_size (int)       -   average result size desired, will return filters that produce close to
                                            that many rows. 0 will make maximum rows prioritized.
            filter_metric   (func)      -   a metric function taking args, (filter_group, new_filter, new_filter_res)
                                            returns a score or preference for using this new_filter as the
                                            next test step along with previous steps in filter_group
                                            [this overrides the avoid_null_filter and avg_result_size params]

        Returns:
            filter_keys (dict)          -   dict with all possible filters as keys and list of expected rows as values
                                            example: {
                                                filt_combination: expected_rows
                                                ...
                                            }
            filter_tests (list)         -   list of filters to test, in the order of filter operations path to follow
        """
        if columns is None:
            columns = self.filter_cols

        def coverage_metric(filters_group, new_filter, new_filter_results):
            # this is the metric to determine how good a new_filter is for testing along with filters_group
            num_unique_cols = len({col for filters in filters_group + [new_filter] for col, _, _2 in filters})
            result_size = len(new_filter_results)
            return num_unique_cols * (100 - abs(result_size - avg_result_size) * int(avoid_null_filter))
            # prefer filter choices to cover maximum columns, and also close to desired result size

        if filter_metric is None:
            filter_metric = coverage_metric

        # STORING ALL FILTER COMBINATIONS WITH THEIR RESULTS
        tests = {}
        all_combs = {}
        filters_collection = self.generate_column_filters(table_content, columns, dimensions, truncate_size)
        for tests in filters_collection:
            all_combs.update(tests)
        # NOW COMES THE FILTERS SELECTION BASED ON BEST TEST COVERAGE
        filter_choices = list(tests)
        if len(tests) < size:
            main_filters = filter_choices
        else:
            main_filters = []
            for _ in range(size):
                best_coverage = max(filter_metric(main_filters, filt, tests[filt]) for filt in filter_choices)
                best_next_choices = [
                    filt for filt in filter_choices if filter_metric(main_filters, filt, tests[filt]) == best_coverage
                ]
                main_filters.append(random.choice(best_next_choices))
                filter_choices.remove(main_filters[-1])

        if not intermediate_steps:
            return all_combs, main_filters

        # NOW WE SIMULATE THE STEPS BY STEP FILTERING PROCESS DONE IN UI TO COVER INTERMEDIATE FILTERS TOO
        filter_steps = [tuple(sorted(main_filters[0][:dim])) for dim in range(1, dimensions + 1)]
        # first intermediate steps are obvious for the first filter

        for filt in filter_steps:
            if filt not in all_combs:
                all_combs[filt] = self.apply_ui_filter(table_content, filt)

        # for the next filters, we need to calculate most covering intermediate steps
        # todo: can maybe allow caller to decide maximum or minimum intermediate steps
        last_active_filter = filter_steps[-1]
        for filtr in main_filters[1:]:
            to_be_deleted = set(last_active_filter) - set(filtr)
            deletes_ordered = sorted(
                to_be_deleted, key=lambda filtr: (
                    0 if tuple(sorted(set(last_active_filter) - {filtr})) not in filter_steps else 1
                )
            )
            for to_delete in deletes_ordered:
                intermediate_filter = tuple(sorted(set(last_active_filter) - {to_delete}))
                if intermediate_filter not in all_combs:
                    all_combs[intermediate_filter] = self.apply_ui_filter(table_content, intermediate_filter)
                last_active_filter = intermediate_filter
                if intermediate_filter and intermediate_filter not in filter_steps:
                    filter_steps.append(intermediate_filter)

            to_be_added = set(filtr) - set(last_active_filter)
            adds_ordered = sorted(
                to_be_added, key=lambda filtr: (
                    0 if tuple(sorted(set(last_active_filter) - {filtr})) not in filter_steps else 1
                )
            )
            for to_add in adds_ordered:
                intermediate_filter = tuple(sorted(set(last_active_filter) | {to_add}))
                if intermediate_filter not in all_combs:
                    all_combs[intermediate_filter] = self.apply_ui_filter(table_content, intermediate_filter)
                last_active_filter = intermediate_filter
                if intermediate_filter and intermediate_filter not in filter_steps:
                    filter_steps.append(intermediate_filter)
        # returning all data. no need to waste any stored filter results.
        return all_combs, filter_steps

    @PageService()
    def table_content_from_csv(self, pages: Union[int, str] = 1) -> list[dict]:
        """
        Gets the complete table data from csv export

        Args:
            pages       (int)       -   number of pages to extract as csv.
                                        (Note: some tables export all pages in just 1 csv)

        Returns:
            csv_Table    (list)     -   table content as list if dicts
                                        (as read from csv file exported from table)
        """
        filepaths = self.export_csv(pages=pages)
        self.log.info(f">> Parsing CSVs from {filepaths}")
        table_data = self.parse_table_from_csv(filepaths)
        self.log.info(f">> Read Table Data [{len(table_data)} Rows] From CSV")
        return table_data

    @PageService()
    def table_content_from_html(self, pages: Union[int, str] = 1) -> list[dict]:
        """
        Gets the complete table data from html content parsing

        Args:
            pages       (int)       -   number of pages to read

        Returns:
            table_dict    (dict)    -   table content as list of dicts
        """
        if pages == 'all':
            pages = 20  # limit max number of pages
        self.go_to_page('first')
        grid_html = self._driver.find_element(By.XPATH, self._xpath).get_attribute('innerHTML')
        table_data = self.parse_table_from_html(grid_html)
        pages -= 1
        # loop to add other pages data if required
        while pages > 0 and self.go_to_page('next'):
            grid_html = self._driver.find_element(By.XPATH, self._xpath).get_attribute('innerHTML')
            next_table_data = self.parse_table_from_html(grid_html)
            table_data.extend(next_table_data)
            pages -= 1
        if 'no results found' in str(table_data).lower():
            return []
        self.log.info(f">> Parsed Table Data [{len(table_data)} Rows] from Table HTML")
        return table_data

    def validate_expected_content(self, expected_result: list[dict], missing_only: bool) -> list[str]:
        """
        Validates that the table is currently showing only expected result

        Args:
            expected_result (list)  -   list of row dicts expected to be shown in table
            missing_only    (bool)  -   whether to report only missing rows, will ignore extra rows

        Returns:
            errors  (list)  -   list of error messages if any
        """
        errors = []
        table_content = self.table_content_from_html('all')
        missing_rows = [row for row in expected_result if row not in table_content]
        if missing_only:
            unexpected_rows = []
        else:
            unexpected_rows = [row for row in table_content if row not in expected_result]
        if missing_rows + unexpected_rows:
            errors.append(f"Expected {len(expected_result)} rows")
            errors.append(f"But got {len(table_content)} rows")
            if missing_rows:
                errors.append(f"Missing {len(missing_rows)} rows below: {self.pprint_table(missing_rows)}")
            if unexpected_rows:
                errors.append(
                    f"Unexpected {len(unexpected_rows)} rows below: {self.pprint_table(unexpected_rows)}")
        return errors

    # # ============================== GRID TEST FUNCTIONS ==============================

    def compare_table_contents(self, table_content: list[dict], expected_content: list[dict]) -> list[str]:
        """
        Compares the UI table content with expected content from API response

        Args:
            table_content     (list)    -   The rtable content visible in UI
                                            list of rows, each row is a dict like -> {col: value, col2: value2...}
            expected_content    (list)  -   The expected content in that table, pass API response json
                                            should be list of dicts, the dict format will be handled as specified
                                            in column_specifications during init

        Returns:
            errors  (list)  -   list of strings with errors found if any
        """
        if id_column_error := self.verify_id_column(table_content, self.id_columns):
            return [
                f'given id_column = {self.id_columns}', id_column_error,
                'please set the correct is_primary_key property in column specifications during init'
            ]

        indexed_table_content = {self.get_ui_row_id(row): row for row in table_content}
        indexed_expected_content = {self.get_api_row_id(api_row): api_row for api_row in expected_content}

        errors = []
        for ui_row_id in list(indexed_table_content.keys()):
            ui_row_value = indexed_table_content[ui_row_id]
            api_row_value = None
            for api_row_id in list(indexed_expected_content.keys()):
                if self.match_row_ids(ui_row_id, api_row_id):
                    api_row_value = indexed_expected_content[api_row_id]
                    break

            if api_row_value is None:
                errors.append(f'No match found for UI row id = {ui_row_id}')
                errors.append(f'ui row value = {ui_row_value}')
                errors.append(indexed_expected_content)
            else:
                row_errors = self.compare_row_contents(ui_row_value, api_row_value)
                if row_errors:
                    errors.append(f"!!! --- Error in validating row - {ui_row_id} --- !!!")
                    errors.extend(row_errors)
                del indexed_expected_content[api_row_id]  # remove the api row so it won't match again
        if errors:
            self.log.info('error during table content validation. '
                          'storing debuginfo to bucket -> compare_table_contents_error')
            self.rehydrator.bucket('compare_table_contents_error').set({
                'table_content': table_content,
                'expected_content': expected_content,
                'errors': errors
            })
        return errors

    @test_step
    def validate_sorting(self, columns: Union[str, list] = 'random', **sort_params) -> None:
        """
        Sorts and validates columns of table

        Args:
            columns      (str/list) -   columns to test sort on. 'all' will test on all sortable columns
                                        'random' will pick one random column for each sort key type
            sort_params:
                ignore_error_count  (int)   -   number of incorrect sorted adjacent row pairs to ignore
                                                no error will be raised unless the sort errors exceed this amount
                                                default 0
                ignore_error_percent (float)-   percentage of incorrect row positions to ignore as error
                                                relative to total rows in column, must be between 0 and 1.
                                                default is 0
                ignore_special_first  (bool)-   ignores any order when both values start with special characters

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        error_limit = sort_params.get('ignore_error_count') or 0
        percent_error = sort_params.get('ignore_error_percent') or 0
        if columns == 'all':
            columns = self.sort_cols
        elif columns == 'random':
            columns = []
            for group in self.sort_groups:
                columns.append(random.choice(self.sort_groups[group]))

        self.log.info(f">>> testing sort over columns {columns}")
        self.log.info(f">>> with error tolerance {percent_error or error_limit}")
        errors = []
        for column in columns:
            for ascending in [True, False]:
                order = ["descending", "ascending"][ascending]
                self.apply_sort_over_column(column, ascending=ascending)
                column_data = [row[column] for row in self.table_content_from_html()]
                if percent_error:
                    error_limit = int(len(column_data) * percent_error)
                    self.log.info(f'calculated error limit = {error_limit}')
                try:
                    if not is_sorted(column_data, self.column_specifications[column]['sort_key'], ascending):
                        error_pairs = [
                            (prev, nex) for prev, nex in zip(column_data[:-1], column_data[1:])
                            if self.column_specifications[column]['sort_key'](prev, nex) != ascending
                        ]
                        if sort_params.get('ignore_special_first', True):
                            error_pairs = [
                                (prev, nex) for prev, nex in error_pairs if not (prev[0].isalnum() and nex[0].isalnum())
                            ]
                        if len(error_pairs) > error_limit:
                            errors.append(f"column {column} failed to sort {order}")
                            errors.append(f"Visually incorrect sorting: {column_data}")
                            errors.append("To be specific, here are the sub sequences that are not in sorted order:")
                            for pair in error_pairs:
                                errors.append(pair)
                        else:
                            self.log.info(f"> Got {len(error_pairs)} sort mistakes, ignoring as it is within limit")
                    else:
                        self.log.info(f">> Sorting verified for {column} - {ascending}")
                except Exception as exp:
                    self.log.error(f'exception while evaluating column {column} sort using given sort key')
                    self.log.error(f'storing debuginfo to bucket -> sort_key_error')
                    self.rehydrator.bucket('sort_key_error').set({
                        'column_data': column_data,
                        'column': column
                    })
                    raise exp

        if not errors:
            self.log.info(f">>> Table columns sort validated!")
        else:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure(f"Table Sort Validation Failed")

    @test_step
    def validate_search(self, columns: Union[str, list] = 'random', **search_params) -> None:
        """
        Performs random search and verifies the result

        Args:
            columns      (str/list) -   specific columns to pull search words from,
                                        str if single column or 'all'
                                        'random' selects 5 random columns
                                        list of column names for multiple columns
                                        other columns will still be included for matching result
            search_params:
                ui_data         (dict)      -   the UI data to generate search from
                search_size    (int/str)    -   number of searches to test per column
                                                default is 1
                missing_only    (bool)      -   only reports missing rows from search result,
                                                ignores unexpected rows
                search_keyword_size (int)   -   upper limit of size of search keywords

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        # SETUPS AND PRE-REQUISITES
        if columns == 'all':
            columns = self.search_cols
        elif columns == 'random':
            columns = self.search_cols
            if len(self.search_cols) > 5:
                columns = list(random.sample(columns, 5))
        elif isinstance(columns, str):
            columns = [col.strip() for col in columns.split(',')]

        ui_data = search_params.get('ui_data')
        if not ui_data:
            ui_data = self.table_content_from_html(pages='all')

        # TEST STEPS GENERATION LOGIC
        coverage = int(search_params.get('search_size') or 1)
        len_cap = int(search_params.get('search_keyword_size') or 20)
        search_dict = {}
        self.log.info(f">>> Generating {coverage} tests for each column from {columns}")
        for search_column in columns:
            column_search_terms = self.generate_search_tests(ui_data, [search_column], len_cap)
            if len(column_search_terms) > coverage:
                column_search_terms = distributed_sample(column_search_terms, coverage)
            search_dict.update(column_search_terms)
            self.log.info(f">> for column {search_column}, search test plan is := ")
            for search_str, search_result in column_search_terms.items():
                self.log.info(f"> string to search: {search_str} , expected result is := ")
                for column_match, rows_matched in search_result.items():
                    self.log.info(
                        f"based on columns {column_match}, expected rows below:{self.pprint_table(rows_matched)}")
        # SEARCH DICT HAS STRUCTURE LIKE THIS:
        # {   'searchword': { (colsmatch): [rows match], (colsmatch): [rows match], ... }   }

        # SEARCH TEST LOGIC
        errors = []
        for search_string, expected_result in search_dict.items():
            self.log.info(f">>> Testing search string: {search_string}")
            self.search_for(search_string)
            search_result = self.table_content_from_html('all')
            search_test_fail = False
            total_expected_rows = []
            for matched_cols, expected_rows in expected_result.items():
                total_expected_rows += expected_rows
                missing_rows = [row for row in expected_rows if row not in search_result]
                if missing_rows:
                    self.log.error(f">> Search failed for {search_string}!")
                    errors.append("------------------------------")
                    errors.append(f"Search failed for {search_string}!")
                    errors.append(f"Expected {len(expected_rows)} rows based on match over columns -> {matched_cols}")
                    errors.append(f"But got {len(search_result)} rows")
                    errors.append(f"Missing {len(missing_rows)} rows below: {self.pprint_table(missing_rows)}")
                    search_test_fail = True
                    break
            if search_test_fail:
                continue
            unexpected_rows = [row for row in search_result if row not in total_expected_rows]
            if unexpected_rows and not search_params.get('missing_only'):
                self.log.error(f">> Search failed for {search_string}!")
                errors.append("------------------------------")
                errors.append(f"Search failed for {search_string}!")
                errors.append(f"Expected {len(total_expected_rows)} rows based on match over all searchable columns")
                errors.append(f"But got {len(search_result)} rows")
                errors.append(
                    f"Unexpected {len(unexpected_rows)} rows below: {self.pprint_table(unexpected_rows)}")
        self.clear_search()

        # CONCLUSION
        if errors:
            self.log.info('> error during table search validation. '
                          'storing debuginfo to bucket -> validate_search_error')
            self.rehydrator.bucket('validate_search_error').set({
                'ui_data': ui_data,
                'search_dict': search_dict,
                'errors': errors
            })
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure(f"Search test failed!")
        else:
            self.log.info(f">>> Search Test Passed!")

    @test_step
    def validate_filters(self, columns: Union[str, list] = 'all', **filter_params) -> None:
        """
        Performs filter of each/multiple columns and verifies result

        Args:
            columns      (str/list) -   specific columns to test filter, str if single column or 'all', or
                                        list of column names for multiple columns
            filter_params:
                ui_data         (dict)      -   the UI data to generate filter tests form
                dimensions      (int)       -   maximum number of columns filtered at once (default 3)
                filter_size     (int)       -   number of filters to test per dimension (default 1)
                avoid_null_filter   (bool)  -   whether to avoid filters that yield empty result (default True)
                missing_only    (bool)      -   only reports missing rows from filter result if True,
                                                ignores unexpected rows. default is False
                truncate_size   (int)       -   number of characters to limit to, when filtering for long cell values
                                                default: 40
                intermediate_steps  (bool)  -   tests the intermediate filters also while changing between filters
                                                default: True
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        # SETUPS AND PRE-REQUISITES
        if columns == 'all':
            columns = self.filter_cols
        elif isinstance(columns, str):
            columns = [col.strip() for col in columns.split(',')]

        ui_data = filter_params.get('ui_data')
        if not ui_data:
            ui_data = self.table_content_from_html(pages='all')

        # TEST STEPS GENERATION LOGIC
        size = int(filter_params.get('filter_size') or 1)
        null_coverage = filter_params.get('avoid_null_filter', True)
        dimensions = int(filter_params.get('dimensions') or 3)
        truncate_size = int(filter_params.get('truncate_size') or 40)
        intermediate_steps = filter_params.get('intermediate_steps', True)
        filters_key, filter_steps = self.generate_filter_tests(
            ui_data, columns, dimensions, null_coverage, size, truncate_size, intermediate_steps
        )

        self.log.info(
            f">>> Generating {size} filter tests, each till dimension {dimensions}, for each column from {columns}")
        self.log.info(f">>> In total, we have {len(filter_steps)} filters to test. Filter steps path below:")
        for filter_step in filter_steps:
            if filter_step:
                self.log.info(f"> filter to apply: {filter_step} ,"
                              f"expected result is:{self.pprint_table(filters_key[filter_step])}")

        # FILTER TEST LOGIC
        currently_filtered = set()
        errors = []
        for filtr in filter_steps:
            if filters_to_delete := list(currently_filtered - set(filtr)):
                for unit_filter in filters_to_delete:
                    self.clear_column_filter(*unit_filter[:-1])
            if filters_to_add := list(set(filtr) - currently_filtered):
                for unit_filter in filters_to_add:
                    self.apply_filter_over_column(*unit_filter)
            if not filtr:
                continue
            currently_filtered = set(filtr)
            self.log.info(f">> Validating filter : {filtr}")
            if filter_errors := self.validate_expected_content(filters_key[filtr], filter_params.get('missing_only')):
                self.log.error(f">> Filter failed for {filtr}!")
                errors.append("------------------------------")
                errors.append(f"Filter failed for {filtr}!")
                errors.extend(filter_errors)
            else:
                self.log.info("Filter validated successfully!")

        self.log.info('clearing all filters to default state')
        if currently_filtered:
            for unit_filter in currently_filtered:
                self.clear_column_filter(*unit_filter[:-1])

        if errors:
            self.log.info('> error during table filters validation. '
                          'storing debuginfo to bucket -> validate_filters_error')
            self.rehydrator.bucket('validate_filters_error').set({
                'ui_data': ui_data,
                'filters_key': filters_key,
                'errors': errors
            })
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure(f"Filter test failed!")
        else:
            self.log.info(f"All Filters Validated amd Passed!")

    @test_step
    def validate_views(self, max_view: str = 'All', columns: Union[str, list] = 'all', **view_params) -> None:
        """
        Creates, edits, deletes a user defined view and verifies result

        Args:
            max_view    (str)       -   name of the maximum view, the view that shows all rows
                                        it is 'All' view by default.
            columns      (str/list) -   specific columns to test filter, str if single column or 'all'
                                        list of column names for multiple columns
            view_params:
                ui_data         (dict)      -   the UI data to generate view tests form
                dimensions      (int)       -   maximum number of columns filtered at once (default 3)
                avoid_null_filter   (bool)  -   whether to avoid view that yield empty result (default True)
                missing_only    (bool)      -   only reports missing rows from filter (default False)
                truncate_size   (int)       -   number of characters to limit to, when filtering for long cell values
                                                default: 40
                change_page_function (func) -   a function to change the page, to test view preferences retention.
                                                Can be a method to relogin, refresh, etc
                                                Default: navigates to dashboard page and returns to initial url
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        # SETUPS AND PRE-REQUISITES
        self.select_view(max_view)
        this_page_url = self._admin_console.current_url()

        def navigate_away_and_return():
            self._admin_console.navigator.navigate_to_getting_started()
            self._admin_console.navigate(this_page_url)

        change_page_function = view_params.get('change_page_function', navigate_away_and_return)

        if columns == 'all':
            columns = self.filter_cols
        elif isinstance(columns, str):
            columns = [col.strip() for col in columns.split(',')]

        ui_data = view_params.get('ui_data')
        if not ui_data:
            ui_data = self.table_content_from_html(pages='all')

        # TEST STEPS GENERATION LOGIC
        null_coverage = view_params.get('avoid_null_filter', True)
        dimensions = int(view_params.get('dimensions') or 3)
        truncate_size = int(view_params.get('truncate_size') or 40)

        def max_variation_metric(fg, nf, nr):
            new_cols = {col for col, _, _2 in nf}
            if fg:
                new_cols = new_cols - {col for col, _, _2 in fg[-1]}
            return int(len(new_cols) > 0) * (1 + len(nr) * int(null_coverage))

        view_results, views = self.generate_filter_tests(
            ui_data, columns, dimensions, size=3, truncate_size=truncate_size,
            intermediate_steps=False, filter_metric=max_variation_metric
        )
        self.log.info(
            f">>> Generating view tests, each with dimension {dimensions}, on columns {columns}")

        for view, purpose in zip(views, ['save_from_filter', 'create', 'update']):
            self.log.info(f"> view to {purpose}: {view} ,"
                          f"expected result is:{self.pprint_table(view_results[view])}")

        # VIEWS TEST LOGIC
        errors = []
        view_names = ['test_view_from_filter', 'test_default_view', 'test_modified_view']

        # FIRST VIEW - APPLY AS FILTERS THEN SAVE AS VIEW
        for unit_filter in views[0]:
            self.apply_filter_over_column(*unit_filter)
        self.create_view(view_names[0])

        # SECOND VIEW - APPLY AS DEFAULT
        self.create_view(view_names[1], {
            col: val for col, val, criteria in views[1]
        }, True)

        # VALIDATE BOTH VIEWS ARE ADDED IN VIEW TABLE HEADER
        view_list = self.list_views()
        if view_names[0] not in view_list:
            raise CVTestStepFailure(f"Save as view feature failed, view is missing!")
        if view_names[1] not in view_list:
            raise CVTestStepFailure("Create view feature failed, view is missing!")

        # VALIDATE CONTENT FOR FIRST VIEW
        self.log.info(f">> Validating view : {view_names[0]} = {views[0]}")
        self.view_by_title(view_names[0])
        if view_errors := self.validate_expected_content(view_results[views[0]], view_params.get('missing_only')):
            self.log.error(f">> View {view_names[0]} failed to validate - {views[0]}!")
            errors.append("------------------------------")
            errors.append(f"View {view_names[0]} failed with filters:- {views[0]}!")
            errors.extend(view_errors)
        else:
            self.log.info(f"View {view_names[0]} validated successfully!")

        # TEST RETENTION, AND DEFAULT VIEW SETTING ON SECOND VIEW
        self.log.info("> changing the page to test view preferences retention")
        change_page_function()
        view_list = self.list_views()
        if view_names[0] not in view_list:
            raise CVTestStepFailure(f"Save as view feature failed, view is missing after page changed!")
        if view_names[1] not in view_list:
            raise CVTestStepFailure("Create view feature failed, view is missing after page changed!")
        if self.currently_selected_view() != view_names[1]:
            errors.append("set default option failed on view creation, the view didnt open by default")
            self.select_view(view_names[1])

        # VALIDATE CONTENT FOR SECOND VIEW
        self.log.info(f">> Validating view : {view_names[1]} = {views[1]}")
        if view_errors := self.validate_expected_content(view_results[views[1]], view_params.get('missing_only')):
            self.log.error(f">> View {view_names[1]} failed to validate - {views[1]}!")
            errors.append("------------------------------")
            errors.append(f"View {view_names[1]} failed with filters:- {views[1]}!")
            errors.extend(view_errors)
        else:
            self.log.info(f"View {view_names[1]} validated successfully!")

        # DELETE FIRST VIEW, EDIT SECOND VIEW (UNSET DEFAULT)
        self.delete_view(view_names[0])
        self.edit_view(view_names[1], view_names[2], {
            col: val for col, val, criteria in views[2]
        }, False)

        # VALIDATE FIRST VIEW DELETED, SECOND VIEW NAME CHANGED
        view_list = self.list_views()
        if view_names[0] in view_list:
            raise CVTestStepFailure(f"Delete view failed, view is still present after delete!")
        if view_names[1] in view_list:
            raise CVTestStepFailure("Edit view failed, view still has same name!")
        if view_names[2] not in view_list:
            raise CVTestStepFailure("Edit view failed, looks like view got deleted after edit!")

        # TEST RETENTION
        self.log.info("> changing the page to test view preferences retention")
        change_page_function()
        view_list = self.list_views()
        if view_names[0] in view_list:
            raise CVTestStepFailure(f"Delete view failed, view appeared again after page changed!")
        if view_names[1] in view_list:
            raise CVTestStepFailure("Edit view failed, view reverted to old name after page changed!")
        if view_names[2] not in view_list:
            raise CVTestStepFailure("Edit view failed, view disappeared after page changed!")
        if self.currently_selected_view() == view_names[2]:
            errors.append("set default option off failed on view edit, the view is still opening by default!")

        # VALIDATE EDITED VIEW CONTENT
        self.log.info(f">> Validating post edit - view : {view_names[2]} = {views[2]}")
        self.view_by_title(view_names[2])
        if view_errors := self.validate_expected_content(view_results[views[2]], view_params.get('missing_only')):
            self.log.error(f">> View {view_names[2]} failed to validate - {views[2]}!")
            errors.append("------------------------------")
            errors.append(f"View {view_names[2]} failed with filters:- {views[2]}!")
            errors.extend(view_errors)
        else:
            self.log.info(f"View {view_names[2]} validated successfully!")

        # DELETE THE MODIFIED VIEW AND END TEST
        self.delete_view(view_names[2])
        if view_names[2] in self.list_views():
            raise CVTestStepFailure(f"Delete view failed, modified view is still visible after delete!")

        if errors:
            self.log.info('error during table views validation. storing debuginfo to bucket -> validate_views_error')
            self.rehydrator.bucket('validate_views_error').set({
                'ui_data': ui_data,
                'view_results': view_results,
                'errors': errors
            })
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure(f"View test failed!")
        else:
            self.log.info(f"Custom Views Validated!")

    """ 
    coming soon 
    
    validate_system_created_views() --  to validate system created default views in many grid
    
    validate_redirect_links()       --  to validate redirection links like row actions, hyperlink in cells, etc
    
    validate_push_updates()         --  to validate new rows updated within wait time, after some trigger function
    
    validate_column_sort_prefs()    --  to validate column selection and sort preference are retained
    """


if __name__ == '__main__':
    """
    You can debug issues with validations here
    
    Large errors are logged in these buckets
        -   parse_error
        -   api_value_error
        -   compare_table_contents_error
        -   sort_key_error
        -   validate_search_error
        -   validate_filters_error
        -   validate_views_error
    Search these errors to see how the debug info is logged
    """
    print('running debugmode')
    bucket_name = ''
    debug_info = RTableHelper.rehydrator.bucket(bucket_name).get()
    print(debug_info)
