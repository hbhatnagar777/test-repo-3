# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

This module provides the function or operations that can be used to run
basic operations on theme customization page.

CustomizeThemeMain : This class provides methods for theme customization related operations

 __init__()                                 --  Initialize object of TestCase class associated

 navigate_to_theme_customization_page()     --  To navigate to theme customization page of the admin console

 add_theme_customization()                  --  To set the theme customization on the commcell

 edit_theme_customization()                 --  To edit the commcell theme customization

 remove_theme_customization()               --  To remove the existing theme customization values

 validate_theme_customization()             --  To validate the theme customization settings

 validate_theme_logo()                      --  To validate commcell logo

NavPrefsHelper  :   This class has test utils and steps for testing Navigation Preferences

    properties:
        nav_list_json           --  nav list parsed from input json
        all_nav_routes          --  dict containing tree structure of all nav routes in command center
        all_nav_route_links     --  dict containing all nav endpoints and their urls
        default_grid_content    --  expected grid structure on reset to default

    staticmethods:
        get_navs_dict()         --  parses nav_list_json to filter out personas, roles, etc..
        get_random_navs()       --  parses nav_list_json and returns random nav routes of all levels
        get_navs_for_test()     --  gets navs to test for given persona
        route_ancestors()       --  returns all ancestor nav routes of given nav route

    utils:
        set_prefs_using_api()   --  sets nav settings using API call and verifies it
        get_nav_states()        --  gets list of cvStates for given nav route
        get_prefs_to_test()     --  gets combined navs to test for all personas
        setup_navs_page()       --  sets up navigation preferences page
        setup_personas()        --  sets up all required user persona objects for test
        validate_nav_login()    --  worker thread for validating the left nav for single persona
        validate_nav_logins()   --  driver thread for controlling all the nav tests for different personas

    teststeps:
        test_nav_prefs()        --  validates the nav prefs from persona logins
        validate_prefs()        --  validates the nav prefs displayed properly in UI
        test_reset_prefs()      --  validates reset prefs button from UI

"""
import concurrent.futures
import copy
import itertools
import json
import os
import random
import threading
import time
import traceback
from urllib.parse import urlparse

import pandas as pd
from typing import Union

from AutomationUtils.constants import TEMP_DIR
from cvpysdk.commcell import Commcell
from selenium.common import NoSuchElementException

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.AdminConsolePages.navigation_preferences import NavigationPreferences
from Web.AdminConsole.AdminConsolePages.theme import Theme
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure, CVWebAutomationException
from Web.Common.page_object import TestStep
from cvpysdk.security.security_association import SecurityAssociation

CONFIG = get_config()


class CustomizeThemeMain:
    """Admin console helper for theme customization related operations"""

    def __init__(self, admin_console):
        """
        Helper for schedule policy related files

        Args:
            testcase    (object)    -- object of TestCase class

        """
        self.driver = admin_console.driver
        self.log = admin_console.log
        self.admin_console = admin_console

        self.logo_file_path = None

        self.theme = None
        self.theme = Theme(admin_console)

    def navigate_to_theme_customization_page(self):
        """ To navigate to theme customization page of the admin console """
        self.admin_console.navigate_to_theme()
        self.log.info("successfully navigated to theme customization page")

    def add_theme_customization(self, primary_color=None, header_color=None, header_text_color=None,
                                navigation_color=None, link_color=None):
        """
        To set theme customization in the commcell

        Args:

            primary_color(str)          --  primary color of the commcell.      eg.#841a1a

            header_color(str)           --  header color of the commcell.       eg.#31b7a5

            header_text_color(str)      --  header text color of the commcell.  eg.#d6d8e9

            navigation_color(str)       --  navigation color of the commcell.   eg.#152a0f

            link_color(str)             --  logo color of the commcell.         eg.#d83ba7


        Returns:
                None
        Raises:
                Exception:
                    --- if failed to set the customization values

        """
        self.navigate_to_theme_customization_page()
        self.log.info("setting new logo")
        self.theme.set_logo(self.logo_file_path)
        self.log.info("adding new color settings")
        self.theme.set_color_settings(primary_color=primary_color,
                                      header_color=header_color,
                                      header_text_color=header_text_color,
                                      navigation_color=navigation_color,
                                      link_color=link_color)
        self.log.info("New theme settings were applied successfully")

    def edit_theme_customization(self, new_primary_color=None, new_header_color=None, new_header_text_color=None,
                                 new_navigation_color=None, new_link_color=None):
        """
        Method to edit the theme customization on the commcell

        Args:

            new_primary_color(str)          --  new primary color of the commcell.      eg.#1a8428

            new_header_color(str)           --  new header color of the commcell.       eg.#ac5ca6

            new_header_text_color(str)      --  new header text color of the commcell.  eg.#223c0b

            new_navigation_color(str)       --  new navigation color of the commcell.   eg.#cfc3d8

            new_link_color(str)             --  new logo color of the commcell.         eg.#d83ba7

        Returns:
                None
        Raises:
                Exception:
                    --- if failed to set the customization values

        """
        self.navigate_to_theme_customization_page()
        self.theme.set_color_settings(primary_color=new_primary_color,
                                      header_color=new_header_color,
                                      header_text_color=new_header_text_color,
                                      navigation_color=new_navigation_color,
                                      link_color=new_link_color)
        self.log.info("color settings were modified successfully ")

    def remove_theme_customization(self):
        """
        To reset the theme customization on the commcell

        Returns:
                None
        Raises:
                Exception:
                    --- if failed to reset the customization values

        """
        self.navigate_to_theme_customization_page()
        self.log.info("Resetting the theme customization")
        self.theme.reset_theme()
        self.log.info("Theme settings were reset successfully")

    def validate_theme_customization(self, primary_color='#2f4e66',
                                     header_color='#e4e7ea',
                                     header_text_color='#2f4e66',
                                     navigation_color='#eeeeee',
                                     link_color='#4B8DCC'):
        """
        method to validate the color settings

        Args:
            primary_color(str)          --  primary color of the commcell.      eg.#841a1a

            header_color(str)           --  header color of the commcell.       eg.#31b7a5

            header_text_color(str)      --  header text color of the commcell.  eg.#d6d8e9

            navigation_color(str)       --  navigation color of the commcell.   eg.#152a0f

            link_color(str)             --  logo color of the commcell.         eg.#d83ba7

        Returns:
                None
        Raises:
                Exception:
                    --- if failed to validate the theme customization values
        """
        self.navigate_to_theme_customization_page()
        theme_dictionary = self.theme.get_theme_values()
        if not theme_dictionary['primary_color_value'] == primary_color:
            exp = "primary color value was not set correctly"
            raise Exception(exp)

        if not theme_dictionary['header_color_value'] == header_color:
            exp = "header color value was not set correctly"
            raise Exception(exp)

        if not theme_dictionary['header_text_color_value'] == header_text_color:
            exp = "header text color value was not set correctly"
            raise Exception(exp)

        if not theme_dictionary['navigation_color_value'] == navigation_color:
            exp = "navigation color value was not set correctly"
            raise Exception(exp)

        if not theme_dictionary['link_color_value'] == link_color:
            exp = "link color value was not set correctly"
            raise Exception(exp)
        self.log.info("successfully validated the color settings")

    def validate_theme_logo(self, logo_file_path):
        """
        Method to validate the custom theme logo

        Args:
            logo_file_path(str) -- custom logo file path

        Returns:
            None
        Raise:
            Exception:
                    -- if failed to validate the custom logo

        """
        self.navigate_to_theme_customization_page()
        theme_dictionary = self.theme.get_theme_values()
        path, file_name = os.path.split(logo_file_path)
        if not theme_dictionary['logo_value'] == file_name:
            exp = "Logo was not set correctly"
            raise Exception(exp)
        self.log.info("successfully validated the commcell logo name")


class NavPrefsHelper:
    test_step = TestStep()
    roles = ["msp_admin", "tenant_admin", "msp_user", "tenant_user", "restricted_user"]
    screenshot_path = os.path.join(TEMP_DIR, '56618')

    def __init__(self, commcell: Commcell, admin_console: AdminConsole = None, **options) -> None:
        """
        Initializes NavPrefsHelper Class

        Args:
            commcell            (Commcell)  -   SDK commcell object
            admin_console   (AdminConsole)  -   adminconsole object

        options:
            'admin_password':       password for commcell sdk login passed earlier
            'default_password':     password for all persona entities,

            'msp_user':             msp_user persona's name to setup/reuse
            'company':              name of company to test on/create (for tenant personas),
            'company_alias':        alias name for company to create
            'tenant_admin':         tenant admin login name to create/reuse
            'tenant_user':          tenant user login name to create/reuse

            'nav_routes_json':      filepath with json response to GET getNavList.do?orgId=0 from browser network tab
            'max_thread':           number of thread to limit while testing personas in parallel
            'validate_load':        if False, will ignore errors related to permission and rights
                                    during certain nav page loads
        """
        self._all_nav_route_links = None
        self._default_nav_grid = None
        self._all_nav_routes = None
        self._nav_list_json = None
        self.error_tracking = {}
        self.lock = threading.Lock()
        self.tenant_user = None
        self.tenant_admin = None
        self.commcell_user = None
        self.commcell = commcell
        self.admin_console = admin_console
        self.log = logger.get_log()
        if admin_console:
            self.navigator = self.admin_console.navigator
            self.nav_page = NavigationPreferences(admin_console)
        self.options = {
                           'default_password': CONFIG.ADMIN_PASSWORD or OptionsSelector.get_custom_password(
                               strong=True),
                           'company': 'navprefs_company',
                           'company_alias': 'npc'
                       } | options
        if 'admin_password' not in options:
            self.options['admin_password'] = self.options['default_password']
        self.personas = {
            'msp_admin': commcell.commcell_username,
            'msp_user': options.get('msp_user') or 'navprefs_commcell_user',
        }
        self.log.info("initializes navprefshelper with options:")
        self.log.info(json.dumps(self.options, indent=4))

    # ========================== NAV JSON PROCESSING UTILS =================================
    @property
    def nav_list_json(self) -> list:
        """
        Property to store the json returned from getNavList.do call in UI
        """
        if self._nav_list_json is None:
            if not self.options.get('nav_routes_json'):
                self.log.warn('Need Nav routes json not given')
                self.log.info('As MSP admin, in CC, copy the response to getNavList.do?orgId=0 [with default navs]')
                self.log.info('And save it as a json file and pass the json filepath to nav_routes_json TC param')
                raise CVTestCaseInitFailure('Cannot design test steps without nav routes json')
            self.log.info(f">> reading navs json from {self.options.get('nav_routes_json')}")
            with open(self.options.get('nav_routes_json'), 'r') as f:
                self._nav_list_json = json.load(f)['routes']
            self.log.info(">> Successfully read nav routes json!")
        return copy.deepcopy(self._nav_list_json)
        # TODO: Figure out java layer code, how nav list is processed, and maybe avoid this dependency
        # seems to involve jsons from [ContentStore\AdminConsole\res] and lot of other configs

    @property
    def all_nav_routes(self) -> dict:
        """
        Property to store all nav routes parsed from the nav list json
        """
        if self._all_nav_routes is None:
            self._all_nav_routes = self.get_navs_dict(self.nav_list_json, role='all', value_map='state')
        return copy.deepcopy(self._all_nav_routes)

    @property
    def all_nav_route_links(self) -> dict:
        """
        Property to store all nav routes, along with their href links
        """
        if self._all_nav_route_links is None:
            self._all_nav_route_links = self.get_navs_dict(self.nav_list_json, role='all', value_map='url')
        return copy.deepcopy(self._all_nav_route_links)

    @property
    def default_grid_content(self) -> dict:
        """
        Property to store the expected navprefs grid default settings
        """
        if self._default_nav_grid is None:
            self._default_nav_grid = self.get_navs_dict(
                self.nav_list_json, role='all', localize=self.admin_console.props['NavigationPreferences']
            )
        return self._default_nav_grid

    @staticmethod
    def get_navs_dict(parent_node: list[dict] = None, role: Union[str, list[str]] = None,
                      selection: bool = None, localize: dict = None,
                      value_map: str = None) -> dict:
        """
        Util to parse the nav list json and return dict with nav labels for given role and selection

        Args:
            parent_node (list)  -   a list of nav node dicts (from the navList json), used in recursion
            role    (str)       -   name of persona (msp_admin, msp_user, tenant_admin, tenant_user)
                                    to select the default navs associated with that persona
            selection   (bool)  -   whether to get the navs that are selected for persona or pick what is unselected
            localize    (dict)  -   dict with localization mappings to apply if required
            value_map   (str)   -   what to return as value of each leaf / what property from json to return
        Returns:
            nav_tree    (dict)  -   nested dict with nav labels as key and values are None for leaf, children dict for
                                    parent nav nodes
        """
        if selection is not None and not role:
            raise Exception("Cannot perform navs selection without roles to select for!")
        if role == 'all':
            role = NavPrefsHelper.roles[:]
        elif isinstance(role, str):
            role = [role]
        root_dict = {}
        for nav_node in parent_node:
            if not nav_node.get('showNavItem'):
                continue
            if nav_title := nav_node.get('cvTitle'):
                nav_label = nav_title if not localize else localize[nav_title]
                nav_property = nav_node.get(value_map) if value_map else None
                if value_map == 'url':
                    nav_property = urlparse(nav_node.get(value_map, '')).path
                    nav_property = nav_property.replace(':tab', 'Overview')
                    nav_property = nav_property.replace(':dashboardId', 'commcell')
                if nav_node.get('children'):
                    if child_routes := NavPrefsHelper.get_navs_dict(
                            nav_node['children'], role, selection, localize, value_map):
                        root_dict[nav_label] = {}
                        if value_map:
                            root_dict[nav_label][value_map] = nav_property
                        if role and (selection is None):
                            root_dict[nav_label]['children'] = child_routes
                            for each_role in role:
                                all_for_role = all(child_routes[route][each_role] for route in child_routes)
                                none_for_role = all(not child_routes[route][each_role] for route in child_routes)
                                root_dict[nav_label][each_role] = True if all_for_role else \
                                    False if none_for_role else None
                        else:
                            root_dict[nav_label] = child_routes
                else:
                    if selection is not None:
                        is_selected_for_given_roles = all(
                            any(
                                (each_role.lower() in nav_role.lower())
                                for nav_role in nav_node.get('roles', [])
                            ) for each_role in role
                        )
                        if is_selected_for_given_roles != selection:
                            continue
                        else:
                            root_dict[nav_label] = nav_property
                    else:
                        if role:
                            root_dict[nav_label] = {}
                            for each_role in role:
                                root_dict[nav_label][each_role] = any(
                                    (each_role.lower() in nav_role.lower())
                                    for nav_role in nav_node.get('roles', [])
                                )
                            if value_map:
                                root_dict[nav_label][value_map] = nav_property
                        else:
                            root_dict[nav_label] = nav_property
        return root_dict

    @staticmethod
    def get_random_navs(navs_dict: dict, num_navs: int = 5,
                        substr_exceptions: list = None, specific_exceptions: list = None) -> dict:
        """
        Given navs dict, selects random distributed nav routes of all levels

        Args:
            navs_dict   (dict)  -   nested dict with nav labels
            num_navs    (int)   -   number of routes to select
            substr_exceptions  (list)  -   list of routes to avoid, will be matches as substr
            specific_exceptions (list)  -   list of routes to avoid specified strictly

        Returns:
            random_routes   (dict)  -   dict with route address as key and a dict as value
                                        the value dict contains useful info about nav node selected
        """
        if substr_exceptions is None:
            substr_exceptions = []
        if specific_exceptions is None:
            specific_exceptions = []
        flattened_nav_routes = pd.json_normalize(navs_dict, sep='/').to_dict(orient='records')[0]
        max_depth = max(route.count('/') for route in flattened_nav_routes) + 1
        nav_routes = [
            route for route in flattened_nav_routes if
            (not any(avoiding_label in route for avoiding_label in substr_exceptions))  # no substr matches
            and (route not in specific_exceptions)  # no direct matches
        ]
        random_routes = {}
        avoid_parents = {}
        count = num_navs
        depth_cycle = itertools.cycle(range(max_depth)[::-1])
        while count and nav_routes:
            depth = next(depth_cycle)
            nav_routes_this_depth = [route for route in nav_routes if route.count('/') == depth]
            if nav_routes_this_depth:
                # leaf selection
                random_leaf_route = random.choice(nav_routes_this_depth)
                random_routes.update({
                    random_leaf_route: {
                        "nav_type": f"leaf",
                        "level": depth
                    }
                })
                nav_routes.remove(random_leaf_route)
                count -= 1
                # print("--------------")
                # print(f"picked leaf = {random_leaf_route} for depth {depth}")
                # make sure the ancestors of this route does not get selected ever as parent nodes
                for each_depth in range(1, depth + 1):
                    ancestor_route = "/".join(random_leaf_route.split('/')[:each_depth])
                    avoid_parents[each_depth] = avoid_parents.get(each_depth, []) + [ancestor_route]
                    # print(f"locking parent: {ancestor_route} at depth {each_depth}")

                # parent selection
                if depth > 0 and count > 0:
                    free_parent_routes = [
                        "/".join(route.split('/')[:-1]) for route in nav_routes_this_depth if not any(
                            avoid_parent in route for avoid_parent in avoid_parents[depth]
                        )
                    ]
                    free_parent_routes = [route for route in free_parent_routes if route not in specific_exceptions]
                    if free_parent_routes:
                        random_parent_route = random.choice(free_parent_routes)
                        random_routes.update({
                            random_parent_route: {
                                "nav_type": f"parent",
                                "level": depth - 1
                            }
                        })
                        count -= 1
                        # print("--------------")
                        # print(f"picked parent = {random_parent_route} at depth {depth}")
                        # clear all child for this parent, they are now unusable
                        for route in nav_routes[:]:
                            if random_parent_route in route:
                                nav_routes.remove(route)
                                # print(f"removing child: {route}")
        return random_routes

    @staticmethod
    def get_navs_for_test(navs_list: list[dict], persona: str,
                          num_navs: int = 5, avoid_nav_routes: list[str] = None) -> tuple[dict, dict]:
        """
        Returns a diverse collection of navs to test for persona, returns navs to enable, navs to disable

        Args:
            navs_list   (list)          -   full list of nav node dicts to select from
            persona (str)               -   the persona to get optimal nav test steps for
            num_navs    (int)           -   number of navs to limit the test steps
            avoid_nav_routes    (list)  -   list of nav routes to avoid from picking

        Returns:
            navs_to_enable  (dict)  -   optimal navs to enable and test visibility for persona
            navs_to_disable (dict)  -   optimal navs to disable and test invisibility for persona
        """
        if avoid_nav_routes is None:
            avoid_nav_routes = []

        # HARDCODE ANY NAVS STEPS THAT CANNOT BE TESTED BY DEFAULT, SUBSTRING BLOCKS FIRST, THEN SPECIFIC BLOCKS
        # TODO: USE REGEX TO DESCRIBE BLOCKED ROUTES, MUCH SIMPLER
        hardcoded_blocks = {
            'msp_admin': [
                {},  # msp admin cannot disable manage, or manage/customization, ui checkbox is disabled
                {
                    False: ['label.nav.manage', 'label.nav.manage/label.nav.customization']
                }
            ],
            'msp_user': [
                {
                    True: ['label.nav.manage/label.nav.system', 'label.nav.manage/label.nav.reports']
                },
                {
                    True: [
                        'label.nav.monitoring', 'label.nav.monitoring/label.nav.securityDashboard',
                        'label.nav.manage', 'label.nav.manage/label.nav.license'
                    ]
                }
            ],
            'tenant_admin': [
                {
                    True: ['label.nav.manage/label.nav.system', 'label.nav.manage/label.nav.reports']
                },
                {
                    True: [
                        'label.nav.manage', 'label.nav.manage/label.nav.license',
                        'label.nav.manage/label.nav.subscription', 'label.nav.manage/label.nav.subscriptions'
                    ]
                }
            ],
            'tenant_user': [
                {
                    True: ['label.nav.manage/label.nav.system', 'label.nav.manage/label.nav.reports']
                },
                {
                    True: [
                        'label.nav.monitoring', 'label.nav.monitoring/label.nav.securityDashboard',
                        'label.nav.manage', 'label.nav.manage/label.nav.license',
                        'label.nav.manage/label.nav.subscription', 'label.nav.manage/label.nav.subscriptions',
                    ]
                }
            ]
        }
        avoid_nav_routes += ['label.nav.webconsole']

        start_with_enable = random.choice([True, False])  # if True, starts with routes to enable first
        default_routes_for_pick = NavPrefsHelper.get_navs_dict(navs_list, persona, not start_with_enable)

        rand_routes_to_change = NavPrefsHelper.get_random_navs(
            default_routes_for_pick, num_navs,
            avoid_nav_routes + hardcoded_blocks.get(persona, [{}, {}])[0].get(start_with_enable, []),
            hardcoded_blocks.get(persona, [{}, {}])[1].get(start_with_enable, []),
        )

        specific_avoids_for_next_pick = []
        substr_avoids_for_next_pick = []
        for route, route_info in rand_routes_to_change.items():
            specific_avoids_for_next_pick += NavPrefsHelper.route_ancestors(route)
            # make sure ancestors of this nav node
            # remain untouched by next case random pick
            if route_info['nav_type'] == 'parent':
                substr_avoids_for_next_pick += [route]  # make sure children of this route are untouched as we
                # will validate in UI for children presence/absence
        default_routes_for_other_pick = NavPrefsHelper.get_navs_dict(navs_list, persona, start_with_enable)
        rand_routes_for_other_change = NavPrefsHelper.get_random_navs(
            default_routes_for_other_pick, num_navs,
            substr_avoids_for_next_pick + avoid_nav_routes +
            hardcoded_blocks.get(persona, [{}, {}])[0].get(not start_with_enable, []),
            specific_avoids_for_next_pick + hardcoded_blocks.get(persona, [{}, {}])[1].get(not start_with_enable, [])
        )
        # TODO: AS WE IMPLEMENTED AVOIDS, WE CAN PROBABLY IMPLEMENT PREFERENCE TO PICK ROUTES ALREADY PICKED FOR OTHER
        # TO AVOID NEW AND NEWER ROUTES BEING USED
        # ALSO CHANGE GET_RANDOM_NAVS TO PREFER WHEN PICKING A LEAF, PREFER WHOSE PARENT IS NOT ALSO PICKED FOR SAME

        return (rand_routes_to_change, rand_routes_for_other_change)[::1 if start_with_enable else -1]

    @staticmethod
    def route_ancestors(route: str) -> list[str]:
        """
        Returns all ancestors of this route
        """
        as_list = route.split('/')
        return [
            "/".join(as_list[:depth]) for depth in range(1, len(as_list))
        ]

    def set_prefs_using_api(self, prefs_to_set: dict) -> None:
        """
        Method to set preferences using API (much quicker than UI for complex nav settings)

        Args:
            prefs_to_set    (dict)  -   dict with nav_route key, and persona settings value
                                        similar to input to UI
        """
        current_prefs = self.commcell.get_navigation_settings()
        for nav_route, route_info in prefs_to_set.items():
            for each_role in NavPrefsHelper.roles:
                if route_info.get(each_role):  # we need to enable this nav, so remove all states from denied items
                    current_prefs[each_role] = list(set(current_prefs[each_role]) - set(route_info["states"]))
                if route_info.get(each_role) is False:  # we need to disable this nav so add it to denied items
                    current_prefs[each_role] = list(set(current_prefs[each_role]) | set(route_info["states"]))
        self.commcell.set_navigation_settings(current_prefs)
        prefs_set = self.commcell.get_navigation_settings()
        for persona in current_prefs:
            if set(current_prefs[persona]) != set(prefs_set[persona]):
                self.log.error(f'error validating nav preferences post edit! for {persona}')
                self.log.error('expected:', json.dumps(current_prefs))
                self.log.error('but got:', json.dumps(prefs_set))
                raise CVTestStepFailure('Failed to validate Nav prefs API post edit!')

    def get_nav_states(self, route: str) -> list[str]:
        """
        Gets the route's title as well as all derived route titles

        Args:
            route   (str)   -   the route address without localization

        Returns:
            node_states (list)  -   list of nav node cvtitle values that represent this nav route
        """
        def get_node_states(node):
            if not node.get('children'):
                return [node.get('state')]
            derivates = []
            for child_route, child_node in node.get('children', {}).items():
                derivates.extend(get_node_states(child_node))
            return derivates

        navs_dict = self.all_nav_routes.get(route.split('/')[0], {})
        for nav_node in route.split('/')[1:]:
            navs_dict = navs_dict.get("children", {}).get(nav_node)
        return get_node_states(navs_dict)

    def get_prefs_to_test(self, num_navs: int = 5, avoid_nav_routes: list[str] = None,
                          avoid_personas: list[str] = None):
        """
        Util to get prefs settings to set and validate for all personas

        Args:
            num_navs    (int)           -   number of navs to limit test steps
            avoid_nav_routes    (list)  -   list of nav routes to avoid testing
            avoid_personas  (list)      -   list of personas to avoid testing
        """
        if not avoid_personas:
            avoid_personas = []
        prefs_to_test = {}
        prefs_to_expect = {}
        if avoid_nav_routes is None:
            avoid_nav_routes = []
        for persona in self.personas:
            if persona in avoid_personas:
                self.log.info(f">> Skipping persona: {persona}")
                continue
            self.log.info(f"> Generating random navs to test for {persona}!")

            navs_to_enable, navs_to_disable = self.get_navs_for_test(
                self.nav_list_json, persona, num_navs, avoid_nav_routes)
            self.log.info(f"Navs to enable = {navs_to_enable}")
            self.log.info(f"Navs to disable = {navs_to_disable}")
            for action, routes_to_change in zip([True, False], [navs_to_enable, navs_to_disable]):
                for route in routes_to_change:
                    localized_route = "/".join(
                        self.admin_console.props['NavigationPreferences'][label] for label in route.split("/")
                    )
                    route_node_type = routes_to_change[route]['nav_type']  # leaf or parent
                    route_level = routes_to_change[route]['level']  # 0, 1, 2 ..

                    prefs_to_test[localized_route] = (prefs_to_test.get(localized_route, {}) | {
                        persona: action,
                        'node_type': f"{route_node_type} level {route_level}",
                        'states': self.get_nav_states(route)
                    })
                    prefs_to_expect[localized_route] = (prefs_to_expect.get(localized_route, {}) | {
                        persona: action
                    })

                    if route_node_type == 'parent':
                        children_dict = self.all_nav_routes.copy().get(route.split('/')[0], {})
                        for nav_node in route.split('/')[1:]:
                            children_dict = children_dict.get('children', {}).get(nav_node, {}).copy()
                        children_dict = children_dict.get('children', {})
                        prefs_to_test[localized_route]['children'] = [
                            self.admin_console.props['NavigationPreferences'][child_nav] for child_nav in
                            children_dict.keys()
                        ]
        return prefs_to_test, prefs_to_expect

    # ========================== UI TEST UTILS =============================
    def setup_navs_page(self) -> None:
        """
        util to setup nav preference page
        """
        if '/navigationPreferences' not in self.admin_console.current_url():
            self.navigator.navigate_to_navigation()

    def setup_personas(self) -> None:
        """
        Setup util to create all required user personas and store them for later use
        """
        # SETUP MSP USER
        self.log.info(f">>Setting up commcell user")
        if self.commcell.users.has_user(self.personas['msp_user']):
            self.commcell_user = self.commcell.users.get(self.personas['msp_user'])
            self.commcell_user.update_user_password(
                self.options['default_password'],
                self.options['admin_password']
            )
        else:
            self.commcell_user = self.commcell.users.add(
                self.personas['msp_user'],
                'commcelluser@navprefstest.com',
                self.personas['msp_user'] + ' FN',
                password=self.options['default_password']
            )
        self.log.info("adding view permission")  # some navs fail even when enabled if no view permissions
        SecurityAssociation(self.commcell, self.commcell)._add_security_association([{
            "user_name": self.personas['msp_user'],
            "role_name": 'View'
        }], user=True, request_type='UPDATE')

        self.log.info(f">Commcell user {self.personas['msp_user']} setup successfully")
        # SETUP COMPANY
        self.log.info(f">>Setting up company")
        if not self.commcell.organizations.has_organization(self.options['company']):
            self.commcell.organizations.add(
                self.options['company'],
                'tenant_admin@navprefstest.com',
                'tenant_admin',
                self.options['company_alias']
            )
        else:
            self.options['company_alias'] = self.commcell.organizations.get(self.options['company']).domain_name
        self.personas.update({
            'tenant_user': self.options.get('tenant_user') or self.options['company_alias'] + '\\tenant_user',
            'tenant_admin': self.options.get('tenant_admin') or self.options['company_alias'] + '\\tenant_admin'
        })
        self.log.info(f">Company {self.options['company']} setup successfully")
        # SETUP TENANT ADMIN
        self.log.info(f">>Setting up tenant admin")
        self.commcell.switch_to_company(self.options['company'])
        self.commcell.users.refresh(mongodb=True, hard=True)
        if not self.commcell.users.has_user(self.personas['tenant_admin']):
            self.tenant_admin = self.commcell.users.add(
                self.personas['tenant_admin'],
                'tenant_admin@navprefstest.com',
                self.personas['tenant_admin'].split('\\')[-1] + ' FN',
                password=self.options['default_password']
            )
        else:
            self.tenant_admin = self.commcell.users.get(self.personas['tenant_admin'])
            self.tenant_admin.update_user_password(
                self.options['default_password'],
                self.options['admin_password']
            )
            self.tenant_admin.add_usergroups([self.options['company_alias'] + '\\Tenant Admin'])
        self.log.info(f">Company TA {self.personas['tenant_admin']} setup successfully")
        self.commcell.users.refresh(mongodb=True, hard=True)
        # SETUP TENANT USER
        self.log.info(f">>Setting up tenant user")
        if not self.commcell.users.has_user(self.personas['tenant_user']):
            self.tenant_user = self.commcell.users.add(
                self.personas['tenant_user'],
                'tenant_user@navprefstest.com',
                self.personas['tenant_user'].split('\\')[-1] + ' FN',
                password=self.options['default_password']
            )
        else:
            self.tenant_user = self.commcell.users.get(self.personas['tenant_user'])
            self.tenant_user.update_user_password(
                self.options['default_password'],
                self.options['admin_password']
            )
            self.tenant_admin.add_usergroups([self.options['company_alias'] + '\\Tenant Users'])
        self.commcell.reset_company()
        self.commcell.users.refresh(mongodb=True, hard=True)
        self.log.info(f">Company TU {self.personas['tenant_user']} setup successfully")

    @test_step
    def test_nav_prefs(self, num_navs: int = 5, avoid_nav_routes: list[str] = None,
                       avoid_personas: list[str] = None) -> dict[str, list[str]]:
        """
        Tests Nav prefs for all 4 personas

        Args:
            num_navs    (int)               -   number of navs to test
            avoid_nav_routes    (list[str]) -   nav routes to avoid testing
            avoid_personas      (list[str]) -   personas to avoid testing

        Returns:
            error_tracking  (dict)  -   dict with persona as key and list of strings as value, describing what failed
                                        for that persona
        """
        self.setup_navs_page()
        self.nav_page.reset_to_default()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.admin_console.browser)

        orig_settings = self.commcell.get_navigation_settings()
        if avoid_personas is None:
            avoid_personas = []
        prefs_to_test, prefs_to_expect = self.get_prefs_to_test(num_navs, avoid_nav_routes, avoid_personas)
        self.log.info(">> Altering Nav Preferences as below")
        self.log.info(json.dumps(prefs_to_test, indent=2))
        self.log.info(">> Testing API call first")
        self.set_prefs_using_api(prefs_to_test)
        self.log.info(">> API call validated successfully!")
        self.log.info(">> Now validating UI navs for individual logins!")
        self.error_tracking = {}
        self.validate_nav_logins(prefs_to_test, avoid_personas)
        self.log.info(">> Resetting NavPrefs to default")
        self.commcell.set_navigation_settings(orig_settings)
        return self.error_tracking

    @test_step
    def validate_prefs(self, prefs_to_expect: dict, search_coverage: int = 3) -> None:
        """
        validates the nav prefs in UI are set as expected

        Args:
            prefs_to_expect (dict)  -   dict that was input while setting nav prefs
            search_coverage (int)   -   number of searches to cover search function in nav prefs grid
        """
        self.log.info(">> Validating if prefs got set properly")
        self.log.info("> Searching few random routes")
        random_routes = sorted(prefs_to_expect) if len(prefs_to_expect) <= search_coverage \
            else random.sample(sorted(prefs_to_expect), search_coverage)
        self.log.info(f"> {random_routes}")
        visible_state = {
            route: self.nav_page.read_preferences(route) for route in random_routes
        }
        for nav_route, visible_selection in visible_state.items():
            if visible_selection | prefs_to_expect[nav_route] != visible_selection:
                self.log.error(f">> Failed for {nav_route}")
                self.log.error(f">> Expected: {prefs_to_expect}")
                self.log.error(f">> Got: {visible_state}")
                raise CVTestStepFailure("Nav settings table not matching expected! Failed on search")
        self.log.info(">> Search works as expected. Now reading entire preferences grid")

        visible_grid = self.nav_page.read_all_navs()
        for nav_route, expected_selection in prefs_to_expect.items():
            level_nodes = nav_route.split('/')
            visible_selection = visible_grid[level_nodes[0]].copy()
            for each_title in level_nodes[1:]:
                visible_selection = visible_selection.get('children', {}).get(each_title, {}).copy()

            if visible_selection | expected_selection != visible_selection or len(visible_selection) == 0:
                self.log.error(f">> Failed for {nav_route}")
                self.log.error(f">> Expected: {expected_selection}")
                self.log.error(f">> Got visible navs")
                self.log.error(f">> {json.dumps(visible_grid, indent=2)}")
                raise CVTestStepFailure("Nav settings table not matching expected! Failed on Grid Read")
        self.log.info(">> Entire Grid is Consistent with the expected settings")

    @test_step
    def test_reset_prefs(self) -> list[str]:
        """
        Tests if the nav preferences reset properly

        Returns:
            errors  (list)  -   list of strings describing what failed to validate
        """
        self.nav_page.reset_to_default()
        visible_settings = self.nav_page.read_all_navs()
        if visible_settings != self.default_grid_content:
            return [
                "Reset Prefs Failed!",
                "*** Got Nav Settings After Reset ***",
                json.dumps(visible_settings, indent=2),
                "*** Expected Nav Settings After Reset ***",
                json.dumps(self.default_grid_content, indent=2)
            ]

    def validate_nav_login(self, user: str, nav_settings: dict,
                           this_persona: str, validate_load: bool = False) -> None:
        """
        Worker thread, Validate navs for a single persona. Saves results to self.error_tracking

        Args:
            user    (str)           -   username to login as
            nav_settings    (dict)  -   the nav settings dict applied/expected to validate
            this_persona    (str)   -   persona type
            validate_load   (bool)  -   if True will test page load in addition to accessibility
        """
        test_errors = []
        browser, admin_console = None, None
        pwd = self.options['default_password']
        if user == self.admin_console.username:
            pwd = self.options['admin_password']
        try:
            browser = BrowserFactory().create_browser_object(name="User Browser")
            browser.open()
            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            admin_console.login(username=user, password=pwd)

            def take_screenshot():
                sht = self.screenshot_path + f"_{this_persona}_" + str(time.time()).split(".")[0] + ".png"
                admin_console.driver.save_screenshot(sht)
                test_errors.append(f"See screenshot {sht}")

            for nav_route in nav_settings:
                if this_persona in nav_settings[nav_route]:
                    self.log.info(f"> [{this_persona}] testing route {nav_route}, expecting {nav_settings[nav_route].get(this_persona)}")
                    try:
                        nav_search_result = admin_console.navigator.access_nav_route(nav_route, validate_load)
                        if not nav_settings[nav_route].get(this_persona):
                            # if this nav is disabled, access_nav_route should have thrown error by now
                            self.log.error(f"> [{this_persona}] validation failed! it is not blocked!")
                            test_errors.append(f"Nav route {nav_route} accessed for {this_persona} after disabling!")
                            take_screenshot()
                            continue
                        else:
                            if children := nav_settings[nav_route].get('children'):
                                self.log.info(f"> [{this_persona}] validating children are visible..")
                                if nav_settings[nav_route]['node_type'] == "parent level 0":
                                    # only 1st layer parents show children submenu
                                    if (visible_childs := set(nav_search_result[nav_route].keys())) != set(children):
                                        if visible_childs:
                                            # only if no other navs match, children submenu opens default
                                            self.log.error(f"[{this_persona}] Got search result = {nav_search_result}")
                                            self.log.error(f"[{this_persona}] Expected = {children}")
                                            test_errors.append(f"Nav route {nav_route}, didn't show children submenu!")
                                            test_errors.append(f"Missing child navs: {set(children) - visible_childs}")
                                            take_screenshot()
                                        else:
                                            self.log.info(f'[{this_persona}] no visible children, maybe its collapsed')
                                    else:
                                        self.log.info(f"[{this_persona}] children submenu validated")
                                random_child = random.choice(children)
                                self.log.info(f"[{this_persona}] validating random child {random_child}")
                                try:
                                    admin_console.navigator.access_nav_route(
                                        nav_route + '/' + random_child, validate_load)
                                    self.log.info(f'[{this_persona}] random child accessed successfully')
                                except (NoSuchElementException, CVWebAutomationException) as exp:
                                    self.log.error(f"> [{this_persona}] validation failed! child is blocked!")
                                    test_errors.append(
                                        f"child {random_child} of route {nav_route} blocked for {this_persona}"
                                        f"despite parent being enabled")
                                    test_errors.append(f'got error -> {str(exp)}')
                                    take_screenshot()
                                    continue

                            # TODO: ADD ANOTHER RANDOM CHILD ACCESS CHECK, THIS TIME TRY ACCESS BY URL
                            # UPDATE: URL SUPPORT ADDED self.all_nav_route_links
                            self.log.info(f"> [{this_persona}] validated successfully! it is accessible!")

                    except (NoSuchElementException, CVWebAutomationException) as exp:
                        if nav_settings[nav_route].get(this_persona):
                            self.log.error(f"> [{this_persona}] Nav route {nav_route} failed/blocked for {user}")
                            test_errors.append(
                                f"Nav route {nav_route} failed/blocked for {this_persona} after enabling!")
                            test_errors.append(f'got error -> {str(exp)}')
                            take_screenshot()
                        else:
                            if children := nav_settings[nav_route].get('children'):
                                self.log.info(f"[{this_persona}] validating if children are blocked properly..")
                                random_child = random.choice(children)
                                self.log.info(f"[{this_persona}] random child {random_child} selected")
                                try:
                                    admin_console.navigator.access_nav_route(
                                        nav_route + '/' + random_child, validate_load)
                                    self.log.error(f"> [{this_persona}] validation failed! child is not blocked!")
                                    test_errors.append(
                                        f"child {random_child} of route {nav_route} not blocked for {this_persona}"
                                        f"despite parent being disabled"
                                    )
                                    take_screenshot()

                                except (NoSuchElementException, CVWebAutomationException):
                                    self.log.info(f"[{this_persona}] route failed as expected, nav block validated!")

                            # TODO: ADD URL ACCESS BLOCK TOAST VALIDATION
                            self.log.info(f"> [{this_persona}] validated successfully! it is blocked, as expected")

        except Exception as exp:
            test_errors = [str(exp), traceback.format_exc()]
        finally:
            with self.lock:
                self.error_tracking[this_persona] = test_errors
            AdminConsole.logout_silently(admin_console)
            Browser.close_silently(browser)

    def validate_nav_logins(self, expected_nav_settings: dict, avoid_personas: list[str]) -> None:
        """
        Driver thread, validates nav logins for all personas and verifies if they match the expected pref settings

        Args:
            expected_nav_settings   (dict)  -   nav prefs dict that was used to apply
            avoid_personas  (list)          -   list of personas to avoid testing
        """
        num_threads = int(self.options.get('max_threads') or 4)
        validate_load = True if self.options.get('validate_load') else False
        self.log.info(f'>>> validating nav logins for all personas with threads: {num_threads}, '
                      f'and validate_load: {validate_load}')
        futures = []
        with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
            for persona in self.personas:
                if persona in avoid_personas:
                    continue
                user = self.personas[persona]
                futures.append(
                    executor.submit(
                        self.validate_nav_login, user, expected_nav_settings, persona, validate_load
                    )
                )
            concurrent.futures.wait(futures)
