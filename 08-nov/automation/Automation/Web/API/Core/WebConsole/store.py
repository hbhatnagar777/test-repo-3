
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" API to work on Software store"""
from functools import lru_cache

from Web.Common.exceptions import CVWebAPIException, CVNotFound
from AutomationUtils.logger import get_log
from Web.WebConsole.Store import storeapp
from Web.API.Core import cvsessions

_STORE_CONSTANTS = storeapp.get_store_config()


class Store:
    """Software store API

    Networks calls on cloud are quite time consuming and have a huge response. So the
    responses are cached, the following points needs to kept int mind.

        * We use `functools.lru_cache`, but since max_size is None, LRU algo is not
        used and entries are never evicted till its garbage collected.

        * Python cache provided is not thread safe, so writes needs to be serialized.
        However reads can be concurrent from multiple threads. For simplicity, simply
        call the get_packages("Reports", None, None) before spawning any threads to
        populate the cache, after that you are good to use the api in multiple threads
        for reads.

        * To debug or check caching performance, use api.get_packages.cache_info() and
        api.get_all_categories.cache_info()
    """
    def __init__(self, cvsession: cvsessions.Store):
        self._base_url = cvsession.base_url
        self._session = cvsession.session
        self._csrf = cvsession.csrf
        self._LOG = get_log()

    def __get_pkg_details_by_page(self, category, page, sub_category=None):
        resp_txt = ""
        url = ""
        try:
            c = self.get_category_detail(category)["id"]
            if sub_category:
                sc = self.get_sub_category(category, sub_category)
                sc_url = f"&subcategoryId={sc['id']}"
            else:
                sc_url = ""
            url = (
                self._base_url + "softwarestore/store-package-list.do?"
                f"categoryId={c}{sc_url}&page={page}"
            )
            self._LOG.info(f"API - Retrieving packages [GET {url}]")
            resp = self._session.get(url)
            resp_txt = resp.text
            resp.raise_for_status()
            return resp.json()[0]
        except Exception as e:
            raise CVWebAPIException(
                f"Unable to retrieve packages from [{category}]",
                url,
                resp_txt
            ) from e

    def install(self, name, category, sub_category=None):
        """
        Install the given package

        Args:
            name (str): Package name
            category (str): Category of the package
            sub_category (str): Sub-category of the package
        """
        detail = self.get_package(name, category, sub_category)
        url = (
            self._base_url +
            f"softwarestore/store-installFromAppstore.do?packageId={detail['id']}"
            f"&platformId=1&updateMethod=0"
        )
        resp_txt = ""
        self._LOG.info(
            f"API - Installing Name [{name}], Category [{category}], "
            f"Sub-Category [{sub_category}] [POST {url}]"
        )
        try:
            resp = self._session.post(url)
            resp_txt = resp.text
            resp.raise_for_status()
            assert "installed successfully." in resp.json()['msg']['errorMessage']
        except Exception as e:
            raise CVWebAPIException(
                f"Unable to install [{name}]", url, resp_txt
            ) from e

    def install_report(self, name):
        """Install the report
        Args:
            name (str): Name of the report
        """
        self.install(name, "Reports")

    def install_workflow(self, name):
        """Install the workflow
        Args:
            name (str): name of the workflow
        """
        self.install(name, "Workflows")

    @lru_cache(maxsize=None)
    def get_all_categories(self, detailed=False):
        """
        Return all the store categories

        Args:
             detailed (bool): If enabled, a detailed response is returned
             else, only the category name is returned
        """
        url = self._base_url + "softwarestore/store-categories.do"
        self._LOG.info(f"API - Retrieving store categories [GET {url}]")
        resp_txt = ""
        try:
            resp = self._session.get(url)
            resp_txt = resp.text
            resp.raise_for_status()
            categories = resp.json()
            assert len(categories) > 0
            if detailed:
                return categories
            return [category["name"] for category in categories]
        except Exception as e:
            raise CVWebAPIException(
                "Unable to retrieve the categories", url, resp_txt
            ) from e

    @lru_cache(maxsize=None)
    def get_packages(self, category_name, sub_category=None, details=False):
        """
        Get all the packages

        Response will be cached. Use the following code to clear cache
        >>> api = Store()
        >>> api.get_packages.cache_clear()

        Args:
            category_name (str): Name of the category on store
            sub_category (str/None): Name of the sub-category
            details (bool): If true, returns a more detailed response
            else, only a list of package names
        """
        pkg_details = self.__get_pkg_details_by_page(
            category_name, 1000, sub_category
        )
        pages = range(pkg_details["pageCount"])
        packages_list = [
            self.__get_pkg_details_by_page(
                category_name, page, sub_category
            )["packages"]
            for page in pages
        ]
        return [
            package if details else package["name"]
            for packages in packages_list
            for package in packages
        ]

    def get_category_detail(self, name):
        """
        Get category detail

        Response will be cached. Use the following code to clear cache
        >>> api = Store()
        >>> api.get_all_categories.cache_clear()

        Args:
            name (str): name of category
        """
        try:
            categories = self.get_all_categories(detailed=True)
            return next(filter(
                lambda x: x["name"] == name,
                categories
            ))
        except StopIteration:
            raise CVNotFound(f"Category [{name}] not found")

    def get_package(self, name, category, sub_category=None):
        """
        Returns detailed info on the package

        Response will be cached. Use the following code to clear cache
        >>> api = Store()
        >>> api.get_packages.cache_clear()

        Args:
            name (str): name of the package
            category (str): Category name
            sub_category (str): Subcategory name

        Returns:
            dict: JSON response as dictionary

        Raises:
            CVNotFound: when package is not found
            Exception: As raised by get_packages
        """
        try:
            return next(filter(
                lambda pkg: pkg["name"].lower() == name.lower(),
                self.get_packages(category, sub_category, details=True)
            ))
        except StopIteration:
            raise CVNotFound(f"Package [{name}] not found")

    def get_sub_category(self, category, sub_category):
        """
        Returns detailed info on the subcategory

        Args:
            category (str): Category name
            sub_category (str): Subcategory name

        Returns:
            dict: JSON response as dictionary

        Raises:
            CVNotFound: When package is not found
            Exception: As raised from get_category_detail
        """
        try:
            category = self.get_category_detail(category)
            return next(filter(
                lambda pkg: pkg["name"] == sub_category,
                category["subcategories"]
            ))
        except StopIteration:
            raise CVNotFound(f"SubCategory [{sub_category}] not found")

    def get_reports(self, detailed=False):
        """Get the list of reports, set the details flag to
        true for getting all the info on each report
        """
        return self.get_packages("Reports", None, details=detailed)

    def get_workflows(self, detailed=False):
        """
        Get the list of all the workflow names, set the details flag to
        true for getting all the info on each report
        """
        return self.get_packages("Workflows", None, details=detailed)
