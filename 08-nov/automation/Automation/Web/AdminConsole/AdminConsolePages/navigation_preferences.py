# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
the Navigation Preference page in Command Center

Class:

    NavigationPreferences() -> AdminConsoleBase() -> object()

Functions:

    set_search                          :   Sets string in search bar

    reset_to_default                    :   Resets all the entities to Default values

    save_changes                        :   Saves all the updated entities

    read_preferences                    :   Reads the preference options set for a particular route

    read_all_navs                       :   Reads the entire page's nav options

    set_selection_data                  :   Sets preferences for a particular route

"""
from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService

PERSONA_MAP = {
    'CommcellAdmin': 'msp_admin',
    'CommcellUser': 'msp_user',
    'TenantAdmin': 'tenant_admin',
    'TenantUser': 'tenant_user',
    'RestrictedUser': 'restricted_user'
}


class NavigationPreferences:
    """ Class for Navigation Preference page of AdminConsole """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.log = self.__admin_console.log
        self.__grid_xp = "(//div[@class='grid-body'])[1]"
        self.__admin_console.load_properties(self, unique=True)

    # WEB ACTIONS
    @WebAction()
    def _get_navprefs_grid(self) -> WebElement:
        """Returns the root nav prefs grid element"""
        return self.__driver.find_element(By.XPATH, self.__grid_xp)

    @WebAction()
    def _get_row_elem(self, nav: str, parent: WebElement) -> WebElement:
        """
        Util to get row element from nav label, within parent scope

        Args:
            nav (str)               -   name of label of the page from nav list
            parent  (WebElement)    -   parent grid element [used for recursion]

        Returns:
            row_elem  (WebElement)  -   the corresponding tr element
        """
        xpath = f".//*[text()='{nav}']/ancestor::tr[contains(@class, 'k-master-row')]"
        if parent is None:
            parent = self.__driver
            xpath = xpath.lstrip(".")
        return parent.find_element(By.XPATH, xpath)

    @WebAction()
    def _are_children_minimized(self, parent: WebElement) -> bool:
        """
        Web action to check if all Navs are minimized

        Args:
            parent  (WebElement)    -   parent grid element [used for recursion]

        Returns:
            bool    -   True if all navs are minimized else False
        """
        children_grid_html = etree.HTML(parent.get_attribute('innerHTML'))
        open_grids = children_grid_html.xpath(".//tr[contains(@class, 'k-detail-row')]")
        return len(open_grids) == 0

    @WebAction()
    def _click_children_collapse(self, parent: WebElement) -> None:
        """
        Web action to click the group collapse multiple rows button in the top left table headers

        Args:
            parent  (WebElement)    -   parent grid element [used for recursion]
        """
        xpath = "(.//tr[1])[1]//th[1]//button"  # the first row, first column, first button
        btn = parent.find_element(By.XPATH, xpath)
        if btn.is_displayed():
            btn.click()

    @WebAction()
    def _expand_all_children(self, parent: WebElement, collapse: bool = False) -> None:
        """
        Web action to collapse all children

        Args:
            parent  (WebElement)    -   parent element [used for recursion]
            collapse    (bool)      -   set True to collapse children instead of expand
        """
        if self._are_children_minimized(parent) != collapse:
            self._click_children_collapse(parent)
            if self._are_children_minimized(parent) != collapse:
                self._click_children_collapse(parent)

    @WebAction()
    def _get_expandable_subgrids(self, parent: WebElement) -> list[WebElement]:
        """
        Web action to get all expandable nav subgrids

        Args:
            parent  (WebElement)    -   parent element [used for recursion]

        Returns:
            subgrid  (list)  -   list of all subgrid div elements with their own navs grid still hidden
        """
        xpath = ("(.//tr[contains(@class, 'k-master-row')]/..)[1]"
                 "//div[contains(@class, 'teer-grid') and @aria-colcount=7]")  # colcount ensure subgrid is collapsible
        # <the first of the possible parents of tr's> -> their immediate children - this ensures rows of same level
        return parent.find_elements(By.XPATH, xpath)

    @WebAction()
    def _nav_collapse_button(self, row_elem: WebElement) -> WebElement:
        """
        Web action to get nav collapse button left of label

        Args:
            row_elem  (WebElement)  -   the row tr element to collapse

        Returns:
            btn  (WebElement)  -   the corresponding row collapse button element
        """
        xpath = f".//td[contains(@class, 'k-hierarchy')]//button"
        btn_elem = row_elem.find_elements(By.XPATH, xpath)
        if btn_elem:
            return btn_elem[0]

    @WebAction()
    def _get_subgrid(self, row_elem: WebElement) -> WebElement:
        """
        Web action to get subgrid under expanded nav if present

        Args:
            row_elem  (WebElement)  -   the row tr element to get children grid of

        Returns:
            children  (WebElement)  -   the children grid container tr element
        """
        xpath = f"./following-sibling::tr[1][contains(@class, 'k-detail-row')]"
        subgrid_container = row_elem.find_elements(By.XPATH, xpath)
        if subgrid_container:
            return subgrid_container[0]

    @WebAction()
    def _expand_nav(self, row_elem: WebElement, collapse: bool = False, collapse_child: bool = None) -> None:
        """
        Expands/Collapses the nav list grid corresponding to given label

        Args:
            row_elem    (str)       -   the nav item label
            collapse    (bool)      -   will collapse if True, else expand
            collapse_child  (bool)  -   will collapse all child navs if True and expand if False
                                        default: None, no action
        """
        button = self._nav_collapse_button(row_elem)
        if not button:
            raise CVWebAutomationException(f'No collapse button found!')
        is_collapsed = not self._get_subgrid(row_elem)
        if collapse != is_collapsed:
            button.click()
        self.__admin_console.wait_for_completion()
        if (not collapse) and (collapse_child is not None):
            # if the child grid is expanded and children need to be controlled
            child_grid = self._get_subgrid(row_elem)
            are_children_collapsed = self._are_children_minimized(child_grid)
            if collapse_child != are_children_collapsed:
                self._click_children_collapse(child_grid)

    @staticmethod
    def _read_selection(row_elem: etree.Element) -> dict:
        """
        Reads the nav personas selection data using row TR eTree Element (for quicker parsing)

        Args:
            row_elem    (etree.Element) -   an eTree static element of the TR row

        Returns:
            perona_data (dict)  -   dict with persona:selection pairs
        """
        data = {}
        for input_elem in row_elem.xpath(".//input"):
            persona = PERSONA_MAP[input_elem.get('id').split("-")[0]]
            if input_elem.get('data-indeterminate') == 'true':
                value = 'partial'
            else:
                value = 'Mui-checked' in input_elem.getparent().get('class')
            data[persona] = value
        return data

    @WebAction()
    def _recurse_expand(self, parent: WebElement = None) -> None:
        """
        Recursively expands all the nav collapse buttons

        Args:
            parent  (WebElement)    -   the parent grid element to expand under
        """
        if parent is None:
            parent = self._get_navprefs_grid()
        self._expand_all_children(parent)
        for subgrid in self._get_expandable_subgrids(parent):
            self._recurse_expand(subgrid)

    @WebAction()
    def _read_all_navs(self, parent_tree: etree.Element) -> dict:
        """
        Gets all the navs' selection data recursively

        Args:
            parent_tree (etree.Element) -   the parent grid under which to read navs settings

        Returns:
            navs_data (dict)  -   dict with nav:persona_data pairs along with children nested dict
        """
        data = {}
        xpath = "(.//tr[contains(@class, 'k-master-row')]/..)[1]/tr[contains(@class, 'k-master-row')]"
        for row_elem in parent_tree.xpath(xpath):
            nav_label = "".join(row_elem.xpath(".//div[@aria-label]")[0].itertext()).strip()
            data.update({
                            nav_label: self._read_selection(row_elem)
                        })
            if next_row := row_elem.getnext():
                if 'k-detail-row' in next_row.get('class'):
                    data[nav_label].update({
                        'children': self._read_all_navs(next_row)
                    })
        return data

    @WebAction()
    def _set_selection(self, row_elem: WebElement, data: dict) -> None:
        """
        Web action to set the selection checkboxes for given nav row element

        Args:
            row_elem    (WebElement)    -   the row elem to set selection for
            data    (dict)      -       the nav persona settings to apply
        """
        for input_elem in row_elem.find_elements(By.XPATH, ".//input"):
            persona = PERSONA_MAP[input_elem.get_attribute('id').split("-")[0]]
            if data.get(persona) is not None:
                if data.get(persona) != input_elem.is_selected():
                    input_elem.click()
                if data.get(persona) != input_elem.is_selected():
                    input_elem.click()

    @WebAction()
    def set_search(self, keyword: str) -> None:
        """
        Sets keyword to search

        Args:
            keyword (str)   -   search sting to apply on nav prefs grid
        """
        self.__driver.find_element(By.ID, 'navigationPreferencesSearch').click()
        self.__admin_console.fill_form_by_id('navigationPreferencesSearch', '')
        self.__admin_console.fill_form_by_id('navigationPreferencesSearch', keyword)

    # PAGE SERVICES
    @PageService()
    def save_changes(self) -> None:
        """ Saves all the updated entities """
        self.__admin_console.click_button('Save')
        self.__admin_console.click_button('Yes')
        self.__admin_console.wait_for_completion()

    # PAGE SERVICES
    @PageService()
    def reset_to_default(self) -> None:
        """ Resets all the entities to Default values """
        self.__admin_console.click_button('Reset to default')
        self.__admin_console.click_button('Yes')
        self.__admin_console.wait_for_completion()

    @PageService()
    def read_preferences(self, nav_route: str, read_children: bool = False) -> dict:
        """
        Reads selection data of given Nav preference

        Args:
            nav_route   (str)   -   string with '/' separated names from parent to child nav for ambiguous navs
                                    example: 'Reports', 'Manage/Reports', 'Manage/Reports/Reports' are not all same
                                    if the child nav name is unique, no need to specify path from parent
                                    example: 'Application groups' is same as 'Protect/Kubernetes/Application groups'
            read_children (bool)-   will recurse and read all the children navs if True

        Returns:
            selection   (dict)  -   dict with checkbox status for all personas
                                    example: {
                                        'msp_admin': True,
                                        'msp_user': False,
                                        'tenant_admin': 'partial',
                                        'tenant_user': 'partial',

                                        if read_children is True...
                                        'children': {
                                            'child_row1': {'msp_admin': True, ....},
                                            'child_parent1': {
                                                'msp_admin': ...,
                                                'children':
                                                    {
                                                    'nested_child1': {...}, ...
                                                    },
                                            ...
                                        }
                                    }
                                    True -> Fully Selected, False -> Zero selection, 'partial' -> Partially selected
        """
        nav_route = [nav.strip() for nav in nav_route.split('/')]
        self.set_search(nav_route[-1])

        # CLOSE ALL CHILDREN SO IN CASE NAV NAME SAME AS CHILD, THE CHILD IS OUT OF VIEW
        temp_parent = self._get_navprefs_grid()
        self._expand_all_children(temp_parent, collapse=True)

        # KEEP EXPANDING TILL LAST PARENT
        for nav in nav_route[:-1]:
            row = self._get_row_elem(nav, temp_parent)
            try:
                self._expand_nav(row, collapse_child=False)
            except Exception as exp:
                self.log.error(f"Error during expand nav -> {nav} in route {nav_route}")
                raise exp
            temp_parent = self._get_subgrid(row)

        final_row = self._get_row_elem(nav_route[-1], temp_parent)
        data = self._read_selection(etree.HTML(final_row.get_attribute('innerHTML')))

        if read_children:
            collapse_btn = self._nav_collapse_button(final_row)
            if collapse_btn:
                try:
                    self._expand_nav(final_row)
                except Exception as exp:
                    self.log.error(f"Error during expand nav -> {nav_route[-1]} in route {nav_route}")
                    raise exp
                data.update({
                    'children': self._read_all_navs(
                        etree.HTML(self._get_subgrid(final_row).get_attribute('innerHTML'))
                    )
                })

        self.set_search('')
        return data

    @PageService()
    def read_all_navs(self) -> dict:
        """
        Returns all the navs in the page with their selected values

        Returns:
            navs_data   (dict)  -   nested dict with navs hierarchy and selection data
                                    example: {
                                        'Protect': {
                                            'msp_admin': True,
                                            'msp_user': False,
                                            'tenant_admin': 'partial',
                                            'tenant_user': 'partial',
                                            'children': {
                                                'File System': {
                                                    'msp_admin': True,
                                                    'msp_user': False,
                                                    'tenant_admin': 'partial',
                                                    'tenant_user': 'partial',
                                                    'children': {...}
                                                },
                                                ...
                                            }
                                        },
                                        'Dashboard': {...},
                                        ...
                                    }
                                    True -> Fully Selected, False -> Zero selection, 'partial' -> Partially selected
        """
        parent = self._get_navprefs_grid()
        self._expand_all_children(parent, True)
        self._recurse_expand(parent)
        full_html = etree.HTML(parent.get_attribute('innerHTML'))
        return self._read_all_navs(full_html)

    @PageService()
    def set_selection_data(self, nav_settings: dict) -> None:
        """
        Sets the nav preference settings as given

        Args:
            nav_settings    (dict)  -   similar format to input of read_selection_data
                                        dict with nav route key and value as selection data
                                example:
                                {
                                    'Protect/File Servers': {
                                        'msp_admin': True, 'msp_user': False,
                                        'tenant_admin': None, 'tenant_user': None
                                    },
                                    'Nav route 2': ...,
                                    ...
                                }
                                True/False to completely select or unselect. None to leave as is.
        """
        for route in nav_settings:
            nav_route = [nav.strip() for nav in route.split('/')]
            self.set_search(nav_route[-1])
            temp_parent = self._get_navprefs_grid()

            # CLOSE ALL CHILDREN SO IN CASE NAV NAME SAME AS CHILD, THE CHILD IS OUT OF VIEW
            self._expand_all_children(temp_parent, collapse=True)

            # KEEP EXPANDING TILL LAST PARENT
            for nav in nav_route[:-1]:
                row = self._get_row_elem(nav, temp_parent)
                try:
                    self._expand_nav(row, collapse_child=False)
                except Exception as exp:
                    self.log.error(f"error during expand nav {nav} in route {nav_route}")
                    raise exp
                temp_parent = self._get_subgrid(row)

            final_row = self._get_row_elem(nav_route[-1], temp_parent)
            self._set_selection(final_row, nav_settings[route])
        self.set_search('')
        self.save_changes()
