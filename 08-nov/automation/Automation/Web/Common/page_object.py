# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module has the necessary classes to support the PagedObject design for
automating any Web based code in our Automation framework.

Since PageObject is not a standard design pattern as described in the GOF, we will
use https://github.com/SeleniumHQ/selenium/wiki/PageObjects as a reference document

-----------------------------
PagedObject Design Highlights
-----------------------------

* Creating classes:
    You are allowed to create individual classes for each and every page, however
    creating individual classes for each and every page is not mandated and this
    decision has to be made depending on the application. eg, If we consider
    Google Docs as a feature to automate, it has hundreds of options in one page
    and putting them all together in a single class is not advisable, however if
    you consider Google Search page, adding the necessary options in a single
    class might be beneficial.

    Summary: PagedObject model is not about mapping classes to Pages, it is about
    classifying methods into two main categories as PageServices and WebActions like
    explained below

* PageServices (Public methods/APIs):
    This is the most crucial element of the PagedObject design and its well explained
    by SeleniumHQ at https://github.com/SeleniumHQ/selenium/wiki/PageObjects, in simple
    words your helper files should only expose the functionality/services/use-cases that
    are exposed by the WebApp under test. For eg, if we were automating GMail, some of
    the services offered could be 'send_email' and 'delete_email' and its advised that
    we create public methods only for such functions, creating public methods like
    set_search_field, click_send_button is not a very good idea.

* WebActions (Private methods):
    These methods form the internal operations of a PageService method. So in our GMail
    example methods like __click_button, __set_search_field are good examples of WebAction
    methods. These methods should follow the following rules
        * Should have ONLY ONE XPath inside them.
        * Should be marked private or protected

    SeleniumHQ explains about WebElement in the link given below, the WebElements
    declared in the documentation are Java centric. There is also a class inside
    Selenium library with the same name WebElement, so to avoid confusion we renamed
    the Java WebElements to WebActions in our codebase.
    Link: https://github.com/SeleniumHQ/selenium/wiki/PageFactory

----------------------
PagedObject Decorators
----------------------

*   To support the PageObject design, we have written some default decorators which help
    you do the following
        *   Automatically log the flow of control to the testcase log file
        *   Record screenshot and URL at the point where selenium exception is raised and
            add it to Error summary which can be logged later by using formatted_error_summary
            method, we call this 'error summary'.
        *   Provide support for integration testing

*   If the method has to be decorated, they are expected to follow the following rules
        *   Any method decorated should have a valid doc string
        *   WebAction decorator is only supposed to throw WebDriverException, so the below
            code example would be considered as an incorrect usage of function for the following
            reason
            By default find_element_by_xpath or click would only raise WebDriverException, and
            here we are re-raising the exception as 'Exception' object type, and now the caller
            has no idea why the exception was raised as the type information was lost. Re-raising
            exceptions as 'Exception' type is always bad, you should only catch specific exception
            types like IndexError, ValueError, WebdriverException etc etc .., but never re raise
            any specific exception type as Exception. An example of incorrect Exception handling is
            shown below,

    >>> def __click_button(self):
    >>>     '''Click button'''
    >>>     try:
    >>>         button = self.driver.find_element(By.XPATH, "//*[li]")
    >>>         button.click()
    >>>     except Exception as e:
    >>>         raise Exception("Something went wrong while clicking button " + str(e))

        One possible reason why someone would do the below is to add extra information to
        the error, but that part will automatically be done by the WebAction decorator. The
        correct implementation of the above code would be like below

    >>>
    >>> @WebAction()
    >>> def __click_button(self):
    >>>     '''Click button'''
    >>>     button = self.driver.find_element(By.XPATH, "//*[li]")
    >>>     button.click()


It is strongly advised that you use these decorators inside your helper files

--------------------------------------------------
Example GMail PagedObject Helper file and TestCase
--------------------------------------------------

The below example explains how the WebAction and PageService decorator can be used
in the helper files. The TestCase class here attempts to simulate how the user can
extract the Error Summary from the exception raised.

>>> # gmail.py helper file
>>> from Web.Common.page_object import (
>>>     WebAction,
>>>     PageService
>>> )
>>>
>>>
>>> class GMail:
>>>
>>>    def __init__(self, browser_obj):
>>>        self.driver = browser_obj.driver
>>>
>>>    # this method is an example of WebAction
>>>    @WebAction()
>>>    def __set_search_field(self, string):
>>>        '''Set search string on Search Field'''
>>>        search_field = self.driver.find_element(By.XPATH, "//textbox[@id='q']")
>>>        search_field.send_keys(string)
>>>
>>>    @WebAction() # this decorator now logs the doc string along with the string argument
>>>    def __click_inbox_tab(self): # please note that this method is private
>>>        '''Click the Inbox tab'''  # its mandated that you add doc string to all PagedObject methods
>>>        # must have only one XPath here, if you depend on one more field, add it to a new method
>>>       self.driver.find_elements(By.ID, "inbox").click()
>>>
>>>    # Please note how all the actions related to unread_emails are completely done inside a single method
>>>    # using one more XPath inside this method could have ended up against our design
>>>    @WebAction()
>>>    def __read_all_listed_emails(self):
>>>        '''Get email content of all unread emails'''
>>>        email_texts = []
>>>        elements = self.driver.find_elements(By.ID, "email_text_content")
>>>        for element in elements:
>>>            email_texts.append(element.text)
>>>        return email_texts
>>>
>>>    # This method is an example of Service method
>>>    @PageService()
>>>    def get_email(self, sent_from, to, subject):
>>>        '''Get all emails matching the given to, from and subject'''
>>>        self.__click_inbox()
>>>        search_str = "from:" + sent_from + " to:" + to + " subject:" + subject
>>>        self.__set_search_field(search_str)
>>>        email_list = self.__read_all_listed_emails()
>>>        return email_list
>>>
>>>
>>> # TestCase file, eg. 51001.py
>>>
>>> from Web.Common.page_object import formatted_error_summary
>>>
>>> class TestCase(CVTestCase):  # This is the testcase class you would use
>>>
>>>     def __init__(self):
>>>         self.name = "Verify email works"
>>>         # ... the usual stuff done in testcase
>>>
>>>     # Error summary has the URL, Screenshot and Docstrings of the method which fails
>>>     # These information are added by the WebAction and PageService decorators, you need
>>>     # to log this info from the exception in your testcase like below
>>>
>>>     def run(self):
>>>         try:
>>>             browser = BrowserFactory().create_browser_object()
>>>             gmail = GMail(browser)
>>>             emails = gmail.get_email("god@heaven.com", "me@cv.com", "Lunch Invite")
>>>         except Exception as e:
>>>             error_summary = formatted_error_summary(e)
>>>             self.log.error(error_summary)
>>> # A sample error summary is as below, formatted_error_summary(e) will return the string representing the error summary
>>> # 'SeleniumError':   'no such element: Unable to locate element: {"method":"xpath","selector":"//input[@id='email_text_content']'
>>> # 'Web Operation':  'Set username'
>>> # 'Functionality':  'Login using store login popup; '
>>> # 'Screenshot'   :  'C:\\Automation\\Log Files\\Screenshot_50167 1507871141.png'
>>> # 'URL'          :  'http://machine/webconsole/login.do?disableSSO'

-------------------
Integration Testing
-------------------

One of the most important reason for using the default decorators provided is Integration
testing. Using integration test script you will help you execute all the helper file's
WebActions without executing TestCases. This is very helpful during service pack upgrades,
when you only execute the WebAction, you get all the broken XPaths in you helper file a
single email. As a result all the broken XPaths can be identified early, the accuracy and
confidence of a regular testcase increases.

Below are the key constructs of integration test,
    * IntegrationTestCase class: This class extends the AutomationUtils.CVTestCase class
      and adds the extra code necessary for integration test. The main difference between the
      CVTestCase and IntegrationTestCase class is, you don't need to define run method. So
      the testcase result string and status are set automatically. All the integration
      TestSteps would be executed automatically. Rest of the functionality like inputJSON
      file, testcase name and everything stays the same.

    * IntegrationTestStep decorator

    * WebActionsExecutor: This is the class which extracts all the WebActions inside the
      given helper file and manages the WebDriverException associated to the WebAction. This
      class helps execute the next method even if one method fails.

consider the following class in the helper file webconsole.py

>>>
>>> class WebConsole:
>>>     @WebAction()
>>>     def __set_username(self):
>>>         ...
>>>
>>>     @WebAction()
>>>     def __set_password(self):
>>>         ...

If you were to integration test the above helper file, your test case would look like below

>>>
>>> class TestCase(IntegrationTestCase):
>>>
>>>     def __init__(self):
>>>         super().__init__()
>>>         self.name = "Integration test for WebConsole"
>>>         self.applicable_os = self.os_list.WINDOWS
>>>         self.feature = self.features_list.WEBCONSOLE
>>>         self.browser = None
>>>
>>>     @IntegrationTestStep(WebConsole)  # Pass the class which you are trying to integration test as arg
>>>     def test_login():
>>>         '''This integration test method tests the login WebActions of WebConsole'''
>>>         browser = BrowserFactory().create_browser_object()
>>>         wc = Webconsole(b, "######")
>>>         webconsole_web_actions = WebActionsExecutor(wc)  # you now have an object which will execute the web actions
>>>         print(webconsole_web_actions.all_methods())   # This method will list all the executable web actions inside the
>>>                                                       # WebConsole class
>>>         browser.driver.get("login page url here")
>>>         webconsole_web_actions.set_username("admin")  # please note that the leading __ and _ are not used, its not
>>>                                                       # necessary to specify that when executed via WebrActionsExecutor
>>>         webconsole_web_actions.set_password("######")
>>>         webconsole_web_actions.finish_and_exit()

That is it, you have your integration test, if you open the log corresponding to the above testcase
you will see the execution result of all WebActions

"""
import inspect
import logging
import os
import re
import sys
import threading
import time
import traceback
import types
from abc import (
    ABC,
    abstractmethod
)
from collections import OrderedDict
from itertools import chain
from functools import wraps

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

from AutomationUtils.config import get_config
from AutomationUtils.constants import LOG_DIR, FAILED
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.logger import get_log
from Web.Common.exceptions import (
    CVException,
    CVTestStepFailure,
    CVTimeOutException,
    CVTestCaseInitFailure,
)

_CONF = get_config().Common.PagedObject


class _ProxyFunction:

    """Internal execution unit"""

    def __new__(cls, self_, mangle, un_mangle, store, *args, **kwargs):
        args = tuple(args)
        self = super(_ProxyFunction, cls).__new__(cls)
        self.self_ = self_
        self.args = args
        self.mangle = mangle
        self.un_mangle = un_mangle
        self.store = store
        self.excp = None
        self.ret = None

        if hasattr(self_, "self_"):
            args = self_.args + args
            tmp_kw = self_.keywords.copy()
            tmp_kw.update(kwargs)
            kwargs = tmp_kw
            del tmp_kw
            self_ = self_.self_

        self.self_ = self_
        self.args = args
        self.kwargs = kwargs
        self.log = get_log()
        return self

    def __doc(self):
        if self.mangle.find("__") == -1:
            m_name = self.mangle
        else:
            m_name = "__" + self.mangle.split("__", 1)[1:][0]
        return DocTablePlugin.get_doc(
            self.self_.__class__.__name__, m_name
        )

    def __m_info(self, ret, excp):
        func = getattr(self.self_, self.mangle)
        exec_info = ExecInfo(func, self.args, self.kwargs)
        summary = ExceptionStore.get_errors(excp) if excp else None
        return self.mangle, {
            "MangledName": self.mangle,
            "UnMangledName": self.un_mangle,
            "Description": self.__doc(),
            "Args": exec_info.args_str,
            "Return": ret,
            "Exception": excp,
            "ErrorSummary": summary
        }

    def __log_m_info(self, m_info):
        excp = m_info["Exception"]
        if excp:
            status = "FAILED"
            log = self.log.error
        else:
            status = "PASSED"
            log = self.log.info

        prefix = ".  .    "
        log(f"{prefix}{status}")
        if m_info["Return"] is not None:
            log(f"{prefix}{m_info['MangledName']}() -> {m_info['Return']}")

        summary = m_info["ErrorSummary"]
        if summary:
            log(f"{prefix}URL: {summary.get('URL', '')}")
            log(f"{prefix}Screenshot: {summary.get('Screenshot', '')}")

        if excp:
            err_str = " ".join(str(excp).splitlines())
            log(f"{prefix}Error: " + err_str)

    @staticmethod
    def __validate_result(ret, result_validator):
        if result_validator:
            if isinstance(result_validator, ResultValidator):
                if result_validator.test_return(ret) is False:
                    raise _CVResultValidationFailure(
                        result_validator.failure_message(ret)
                    )
            else:
                raise ValueError(
                    "result_validator argument is of unexpected "
                    "object type. Please pass any object of a class "
                    "which extends ResultValidator class and implements "
                    "the test_return method"
                )

    def __call__(self, *args, result_validator=None, **kwargs):
        try:
            func = getattr(self.self_, self.mangle)
            ret = func(*args, **kwargs)
            self.__validate_result(ret, result_validator)
            self.__log_m_info(self.__m_info(ret, None)[1])
            self.ret = ret
            return ret
        except (WebDriverException, _CVResultValidationFailure) as excp:
            self.excp = excp
            self.__log_m_info(self.__m_info(None, excp)[1])
        finally:
            cls_name = self.self_.__class__.__name__
            m_name, m_info = self.__m_info(self.ret, self.excp)
            if cls_name not in self.store.keys():
                self.store[cls_name] = {}
            self.store[cls_name][m_name] = m_info


class _CVIntegrationTestStepComplete(CVException):
    """Internal exception type for TestStep failure message propagation"""

    def __init__(self, err_store, clazz, skip_parent_methods, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.err_store = err_store
        self.clazz = clazz
        self.skip_parent_methods = skip_parent_methods


class _CVResultValidationFailure(CVException):
    """Internal exception type for WebAction failure message propagation"""

    def __init__(self, failure_msg, *args, **kwargs):
        self.failure_msg = failure_msg
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.failure_msg


class _ClosureHandler:

    """Wrapper for closure"""

    def __init__(
            self, obj, clazz, extraction_target,
            skip_parent_methods=False):
        self.self_ = obj
        self.clazz = clazz if clazz else obj.__class__
        self.skip_parent_methods = skip_parent_methods
        self.target = extraction_target

    def __attribs(self):
        if self.skip_parent_methods:
            callable_objects = self.clazz.__dict__
        else:
            callable_objects = dir(self.clazz)
        return {
            attr: getattr(self.clazz, attr)
            for attr in callable_objects
        }

    def __closures__(self):  # Fake recursive closure to mimic actual closure
        attribs = self.__attribs().items()
        return {
            callable_name: callable_value.__closure__
            for callable_name, callable_value in attribs
            if (callable(callable_value) and
                getattr(callable_value, "__closure__", None))
        }

    def __mangled(self):
        closures = self.__closures__().items()
        return {
            cell_name: cell_values
            for cell_name, cell_values in closures
            for cell_value in cell_values
            if isinstance(
                cell_value.cell_contents, self.target
            )
        }

    def cell_methods(self):
        """List of methods available WebAction methods available inside executor"""
        methods = []
        for method, cells in self.__mangled().items():
            for cell in cells:
                if isinstance(cell.cell_contents, types.FunctionType):
                    methods.append((
                        method,
                        cell.cell_contents.__code__.co_firstlineno
                    ))
        return [m[0] for m in sorted(methods, key=lambda m: m[1])]

    def methods(self):
        """
        Returns the dict representation of method names in the following format
        {
            'un_mangled_name': manged_name,
            ...
        }
        """
        return {
            re.sub("^[^A-Za-z0-9]*", "", um): m
            for m, um in {
                func: func.split("__")[-1]
                for func in self.__mangled().keys()
            }.items()
        }


class BaseDecorator:

    """
    Base decorator which coordinates the execution of Plugins
    """

    def __init__(self):
        self.__plugins = []
        self.__exception = None
        self.__no_raise_list = []

    def _rmap(self, func, *args, **kwargs):
        return [
            getattr(object_, func)(*args, **kwargs)
            for object_ in self.__plugins
            if getattr(object_, func, None)
        ]

    def __call__(self, function_object):

        self._rmap("init", function_object)

        # Support displaying the funtion's docstring and not the decorator's for pdoc3
        @wraps(function_object)

        def _executor(*args, **kwargs):
            try:

                exec_info = ExecInfo(function_object, *args, **kwargs)
                self._rmap("pre", exec_info)
                ret = function_object(*args, **kwargs)
                self._rmap("post", exec_info, result=ret)
                return ret

            except Exception as exception:
                self.__exception = exception
                self._rmap("excep", exec_info, exception)
                raise exception

            finally:
                self._rmap("final", exec_info, self.__exception)

        return _executor

    def add_plugin(self, plugin):
        self.__plugins.append(plugin)


class ExecInfo:
    """Utility class to pass the execution env info"""

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.func_name = self.func.__name__

    @property
    def doc(self):
        """Doc string of the method"""
        try:
            return self.func.__doc__.strip().splitlines()[0]
        except Exception as e:
            raise ValueError(
                "Not doc string found for method [%s]" %
                self.func_name
            ) from e

    @property
    def self_(self):
        """Self instance variable of the method being decorated"""
        if self.args:
            return self.args[0]
        else:
            raise ValueError("No instance object found")

    @property
    def arg_dict(self):
        """Dict representing the keyword and positional args"""
        arg_specs = inspect.getfullargspec(self.func)
        func_arg_names = arg_specs.args
        func_defaults = arg_specs.defaults if arg_specs.defaults else ()
        func_arg_values = list(self.args) + list(func_defaults)
        arg_dict_ = dict(zip(func_arg_names, func_arg_values))
        arg_dict_.update(self.kwargs)
        return arg_dict_

    @property
    def args_str(self):
        """String representation of arg_dict"""
        def arg_val(value):
            if isinstance(value, str):
                return "'" + value + "'"
            else:
                return str(value)
        return ", ".join([
            (str(name) + "=" + arg_val(value))
            for name, value in self.arg_dict.items()
            if name != "self"
        ])

    def extract_object(self, type_):
        """Utility to extract object of given type"""
        return [
            attrib for attrib in self.self_.__dict__.values()
            if isinstance(attrib, type_)
        ]


class Plugin(ABC):
    """
    All plugins which has to plug into the BaseDecorator need to
    inherit this class
    """

    def init(self, func):
        pass

    @abstractmethod
    def pre(self, exec_info: ExecInfo):
        raise NotImplementedError

    @abstractmethod
    def post(self, exec_info: ExecInfo, result):
        raise NotImplementedError

    @abstractmethod
    def excep(self, exec_info: ExecInfo, exception: Exception):
        raise NotImplementedError

    @abstractmethod
    def final(self, exec_info: ExecInfo, exception: Exception):
        raise NotImplementedError


class WebExecInfo:
    """Expands the exec_info object with the web execution utilities"""

    def __init__(self, exec_info_object, excp_type_to_process):
        self.exec_info = exec_info_object
        self.excp_type = excp_type_to_process

    def __lookup_webconsole_for_driver(self):
        from Web.WebConsole.webconsole import WebConsole
        for wc in self.exec_info.extract_object(WebConsole):
            yield wc.browser.driver

    def __lookup_browser_for_driver(self):
        from Web.Common.cvbrowser import Browser
        for wc in self.exec_info.extract_object(Browser):
            try:
                yield wc.driver
            except Exception:
                pass

    def __lookup_selenium_for_driver(self):
        from selenium.webdriver.remote.webdriver import WebDriver
        for webdriver in self.exec_info.extract_object(WebDriver):
            yield webdriver

    def __lookup_drivers(self):
        g_drivers = chain(
            self.__lookup_selenium_for_driver(),
            self.__lookup_browser_for_driver(),
            self.__lookup_webconsole_for_driver()
        )
        return set(driver for driver in g_drivers)

    def move_to_angular(self, frame):
        """switch to given frame"""
        for driver in self.__lookup_drivers():
            try:
                frame_element = driver.find_elements(By.ID, frame)
            except:
                return False
            if frame_element and frame_element[0].size['height'] > 0:  # all pages has iframe
                pane = driver.find_elements(By.XPATH, "//body[@class ='modal-open']")
                if not pane:
                    driver.switch_to.frame(frame_element[0])
                    return True
        return False

    def move_to_react(self):
        """comes out of frame and points to default window"""
        for driver in self.__lookup_drivers():
            if 'commandcenter' in driver.current_url or 'cloudconsole' in driver.current_url:
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)

    def save_screenshot(self):
        screenshots = []
        for driver in self.__lookup_drivers():
            file_name = (
                "Screenshot TC "
                + threading.current_thread().getName() + " "
                + str(time.time()).split(".")[0]
                + ".png"
            )
            file_path = os.path.join(LOG_DIR, file_name)
            try:
                if driver.save_screenshot(file_path):
                    screenshots.append(file_path)
            except Exception:
                return ""
        if screenshots:
            if len(screenshots) == 1:
                return screenshots[0]
            else:
                return "; ".join(screenshots)
        return ""

    def url(self):
        urls = {
            "Browser " + str(i + 1): driver.current_url
            for i, driver in enumerate(self.__lookup_drivers())
        }
        if len(urls) == 1:
            return list(urls.values())[0]
        else:
            return "; ".join([
                browser + ": " + url
                for browser, url in urls.items()
            ])
        return ""


class ExcpWrapper:
    """Wrapper utility for exception"""

    def __init__(self, excp, type_, order, msg):
        self.excp = excp
        self.type_ = type_
        self.order = order
        self.msg = msg

    @property
    def id(self):
        return id(self.excp)

    def __str__(self):
        return "<b>%-27s  </b>: %s" % (self.type_, self.msg)


class ExceptionStore:
    """Exception store house"""
    __errors = {}

    @classmethod
    def __get_excp(cls, excp):
        return cls.__errors.get(cls.__id(excp), [])

    @classmethod
    def __sorted_excp_summary(cls, excp):
        error_summary = cls.__get_excp(excp)
        sorted(
            error_summary,
            key=lambda entry: entry.order
        )
        return error_summary

    @classmethod
    def __id(cls, excp):
        excp_ = excp
        for _ in range(10):
            if excp_:
                if id(excp_) in cls.__errors.keys():
                    return id(excp_)
                else:
                    excp_ = excp.__context__
            else:
                break
        return id(excp)

    @classmethod
    def store_excp(cls, excp_wrapper: ExcpWrapper):
        """Save exception to the store"""
        id_ = cls.__id(excp_wrapper.excp)
        if id_ in cls.__errors.keys():
            cls.__errors[id_].append(excp_wrapper)
        else:
            cls.__errors[id_] = [excp_wrapper]

    @classmethod
    def has_type(cls, excp, type_):
        return type_ in [excp_.type_ for excp_ in cls.__get_excp(excp)]

    @classmethod
    def formatted_error_str(cls, excp):
        """Format the exception which can be printed"""
        return "Error Summary\n" + "\n".join([
            str(error) for error in cls.get_errors(excp)
        ]) + "\n"

    @classmethod
    def trimmed_exception_str(cls, excp):
        """Remove all traces or page_object.py methods from the stacktrace"""
        excp_str = " ".join(str(excp).splitlines())
        prefix = f"{excp_str}\nTrace from page_object.py is removed, "
        return prefix + "".join([
            tb for tb in traceback.format_exception(*sys.exc_info())
            if "page_object.py" not in tb
        ])

    @classmethod
    def get_errors(cls, excp):
        """Get the list of error handles associated to the exception"""
        excp_type_name = excp.__class__.__name__ + "; "
        excp_args_str = " ".join(str(excp).splitlines())
        excp_wrapper = ExcpWrapper(
            excp, "Error", 1, excp_type_name + excp_args_str
        )
        return [excp_wrapper] + cls.__sorted_excp_summary(excp)


class LoggerPlugin(Plugin):
    """Plugin to log the events"""
    log_return_value = True

    def __init__(self, log_code, level, hide_args=False, prefix="",
                 hide_ret=False, post_prefix=None, log=True):
        self.level = level
        self.log_code = log_code
        self.hide_args = hide_args
        self.prefix = prefix
        self.hide_ret = hide_ret
        self.log = log
        self.post_prefix = post_prefix if post_prefix else ".. "

    def _log_maker(self, exec_info: ExecInfo, msg):
        return logging.makeLogRecord({
            "module": exec_info.func.__module__.split(".")[-1],
            "levelname": self.log_code,
            "levelno": self.level,
            "lineno": exec_info.func.__code__.co_firstlineno + 1,
            "funcName": str(exec_info.self_.__class__.__name__),
            "msg": msg
        })

    def __is_args_logging_allowed(self):
        return (not self.hide_args) or _CONF.LoggerPlugin.FORCE_ALL_LOGS

    def __is_logging_allowed(self):
        return self.log or _CONF.LoggerPlugin.FORCE_ALL_LOGS

    def __is_result_logging_allowed(self, result):
        flags = (
            LoggerPlugin.log_return_value and
            (not self.hide_ret) and
            (result is not None) and
            self.log
        )
        return flags or _CONF.LoggerPlugin.FORCE_ALL_LOGS

    def init(self, func):
        ExecInfo(func).doc

    def final(self, exec_info, exception):
        # do nothing
        pass

    def excep(self, exec_info, excp_instance):
        # do nothing
        pass

    def post(self, exec_info, result):
        if self.__is_result_logging_allowed(result) is False:
            return
        msg = self.post_prefix + exec_info.func.__name__ + "(): -> " + str(result)
        msg = self.prefix + self.prefix + msg
        msg = " ".join(msg.splitlines())[:350]
        get_log().handle(self._log_maker(exec_info, msg))

    def pre(self, exec_info: ExecInfo):
        if not self.__is_logging_allowed():
            return
        if self.__is_args_logging_allowed():
            args_str = exec_info.args_str
        else:
            args_str = ""
        msg = "%s%s [%s(%s)]" % (
            self.prefix,
            exec_info.doc,
            exec_info.func.__name__,
            args_str
        )
        record = self._log_maker(exec_info, msg.strip())
        get_log().handle(record)


class TestStepLoggerPlugin(LoggerPlugin):
    """Plugin to log the execution of TestStep"""

    def pre(self, exec_info: ExecInfo):
        log_msgs = ["-" * 30 + " Starting Test Step " + "-" * 30]
        log_msgs += ["   " + exec_info.doc]
        log_msgs += ["-" * 80]
        for log_msg in log_msgs:
            get_log().handle(
                self._log_maker(exec_info, log_msg)
            )

    def post(self, exec_info, result):
        pass


class InitStepLoggerPlugin(LoggerPlugin):
    """Plugin to log the execution of InitStep and handle exception"""

    def __init__(self, msg=""):
        super(InitStepLoggerPlugin, self).__init__(
            "INIT", logging.INFO
        )
        self.msg = msg

    def pre(self, exec_info: ExecInfo):
        log_msgs = ["-" * 30 + " Starting Init Step " + "-" * 30]
        log_msgs += ["   " + self.msg if self.msg else exec_info.doc]
        log_msgs += ["-" * 80]
        for log_msg in log_msgs:
            get_log().handle(
                self._log_maker(exec_info, log_msg)
            )

    def post(self, exec_info, result):
        pass

    def excep(self, exec_info: ExecInfo, excp):
        if self.msg:
            msg = f"Initialization step failed to execute : {self.msg}"
        else:
            msg = f"Initialization step failed at function : {exec_info.func.__name__}"

        raise CVTestCaseInitFailure(msg) from excp


class DelayPlugin(Plugin):
    """Plugin to add delay to execution"""

    def __init__(self, delay):
        self.delay = delay

    def excep(self, exec_info, exception):
        pass

    def pre(self, exec_info):
        time.sleep(self.delay)

    def post(self, exec_info, result):
        pass

    def final(self, exec_info, exception):
        pass


class WebSupportPlugin(Plugin):
    """Plugin to save screenshot and URL"""

    def __init__(
            self, operation_name, operation_order, excp_type_to_process,
            enable_args=True, hide_method=False):
        self.web_exec_info = None
        self.operation_name = operation_name
        self.excep_type_to_process = excp_type_to_process
        self.operation_order = operation_order
        self.enable_args = enable_args
        self.hide_method = hide_method

    def excep(self, exec_info: ExecInfo, excp):

        self.web_exec_info = WebExecInfo(
            exec_info, self.excep_type_to_process
        )

        if self.hide_method is False:
            msg = exec_info.doc + "; " + exec_info.func.__name__
            msg = msg + "(" + (exec_info.args_str if self.enable_args else "") + ")"
        else:
            msg = exec_info.doc

        ExceptionStore.store_excp(
            ExcpWrapper(
                excp,
                self.operation_name,
                self.operation_order,
                msg
            )
        )

        if isinstance(excp, self.excep_type_to_process) is False:
            return

        if not ExceptionStore.has_type(excp, "Screenshot"):
            screenshot = self.web_exec_info.save_screenshot()
            if screenshot:
                e = ExcpWrapper(excp, "Screenshot", 100, screenshot)
                ExceptionStore.store_excp(e)

        if not ExceptionStore.has_type(excp, "URL"):
            url = self.web_exec_info.url()
            if url:
                e = ExcpWrapper(excp, "URL", 110, url)
                ExceptionStore.store_excp(e)

    def pre(self, exec_info):
        pass

    def post(self, exec_info, result):
        pass

    def final(self, exec_info, exception):
        pass


class IntegrationTestPlugin(Plugin):
    """Plugin to configure other plugins for Integration test"""

    def __init__(self, clazz):
        WebAction.enable_doc_table = True
        LoggerPlugin.log_return_value = False
        self.clazz = clazz

    def post(self, exec_info: ExecInfo, result):
        raise ValueError("finish_and_exit() method not called")

    def final(self, exec_info: ExecInfo, exception):
        pass

    def excep(self, exec_info: ExecInfo, exception):
        pass

    def pre(self, exec_info: ExecInfo):
        pass


class DocTablePlugin(Plugin):
    """HashTable to for doc string lookup"""
    __doc_table = {}

    def excep(self, exec_info: ExecInfo, exception):
        pass

    def post(self, exec_info: ExecInfo, result):
        pass

    def pre(self, exec_info: ExecInfo):
        if WebAction.enable_doc_table:
            key = exec_info.self_.__class__.__name__ + "." + exec_info.func_name
            DocTablePlugin.__doc_table[key] = exec_info.doc

    @classmethod
    def get_doc(cls, class_name, method_name):
        return cls.__doc_table.get(class_name + "." + method_name)

    def final(self, exec_info: ExecInfo, exception):
        pass


class WebAction(BaseDecorator):
    """Decorator to decorate all the WebActions on the HelperFile"""
    enable_doc_table = False

    def __init__(self, log=True, hide_args=False,
                 delay=_CONF.WebAction.DELAY, hide_ret=False):
        super().__init__()
        self.load_plugin(log, hide_args, delay, hide_ret)

    def load_plugin(self, log, hide_args, delay, hide_ret):
        self.add_plugin(
            LoggerPlugin(
                "WEB",
                logging.DEBUG,
                hide_args=hide_args,
                prefix=".  ",
                hide_ret=hide_ret,
                log=log
            )
        )
        if delay > 0:
            self.add_plugin(DelayPlugin(delay))
        self.add_plugin(
            WebSupportPlugin(
                "Web Operation",
                2,
                WebDriverException,
                enable_args=log and not hide_args
            )
        )
        self.add_plugin(DocTablePlugin())


class PageService(BaseDecorator):
    """Decorator to decorate all the PageService methods on the HelperFile"""

    def __init__(self, log=True, hide_args=False, hide_ret=False, react_frame=True, frame_name="ac-iframe"):
        super().__init__()
        self.load_plugins(log, hide_args, hide_ret, react_frame, frame_name)

    def load_plugins(self, log, hide_args, hide_ret, react_frame, frame_name):
        self.add_plugin(
            LoggerPlugin(
                "SVC",
                logging.INFO,
                hide_args=hide_args,
                hide_ret=hide_ret,
                log=log
            )
        )

        selenium_plugin = WebSupportPlugin(
            "Functionality",
            3,
            CVException,
            enable_args=log and not hide_args
        )
        self.add_plugin(selenium_plugin)
        #angular_plugin = AngularPlugin(frame_name, react_frame)
        #self.add_plugin(angular_plugin)


class TestStep(BaseDecorator):
    """Decorator to decorate the TestStep inside the TestCases"""

    def __init__(self):
        super().__init__()
        self.load_plugins()

    def load_plugins(self):
        self.add_plugin(
            TestStepLoggerPlugin("TS", logging.INFO)
        )
        self.add_plugin(
            WebSupportPlugin(
                "TestStep", 4, CVTestStepFailure, hide_method=True
            )
        )


class IntegrationTestStep(TestStep):
    """Decorator to decorate the Integration TestStep on the TestCase"""

    def __init__(self, clazz):
        super().__init__()
        self.add_plugin(IntegrationTestPlugin(clazz))


def get_errors(excp):
    return ExceptionStore.get_errors(excp)


def formatted_error_summary(excp):
    return ExceptionStore.formatted_error_str(excp)


def trimmed_excp(excp):
    return ExceptionStore.trimmed_exception_str(excp)


def handle_testcase_exception(testcase_obj, excp):
    """Set the result string and status from the exception"""
    exception_string = str(excp)
    if isinstance(excp, (WebDriverException, CVException)):
        exception_string = formatted_error_summary(excp)
        testcase_obj.log.error(
            f"\n{('-' * 300)}\n{exception_string.replace('<b>','').replace('</b>','')}{('-' * 300)}"
        )
        exception_string = exception_string.replace('\n', '<br>')
    testcase_obj.log.error(trimmed_excp(excp))
    testcase_obj.status = FAILED
    testcase_obj.result_string = exception_string


class WebActionsExecutor:
    """Extracts all the web actions on the helper, use this for Integration test"""

    def __init__(self, obj, skip_parent_methods=False):
        self.self_ = obj
        self.clazz = obj.__class__
        self.skip_parent_methods = skip_parent_methods
        self.__closure_handler = _ClosureHandler(
            self.self_, self.clazz, WebAction, skip_parent_methods
        )
        self.__method_table = self.__closure_handler.methods()
        self.__remaining_methods = list(self.__method_table.keys())
        self.__local_store = {}

    def __getattr__(self, func):
        try:
            proxy_methods = _ProxyFunction(
                self.self_,
                self.__method_table[func],
                func,
                self.__local_store,
            )
            try:
                self.__remaining_methods.remove(func)
            except ValueError:
                pass
            return proxy_methods
        except KeyError:
            raise AttributeError(
                func + " not found, please call WebActionsExecutor.all_methods "
                       "function to see the list of functions available for "
                       "integration testing.")

    def all_methods(self):
        return list(self.__method_table.keys())

    def remaining_methods(self):
        """Get the list of WebAction methods"""
        return self.__remaining_methods

    def finish_and_exit(self):
        """Call this method at the end of test completion"""
        raise _CVIntegrationTestStepComplete(
            self.__local_store,
            self.clazz,
            self.skip_parent_methods
        )


class ResultValidator(ABC):
    @abstractmethod
    def test_return(self, return_):
        raise NotImplementedError

    @abstractmethod
    def failure_message(self, return_):
        raise NotImplementedError


class IntegrationTestCase(CVTestCase):
    """
    Inherit this class instead of extending the CVTestCase class
    for integration tests
    """

    def __init__(self):
        super().__init__()
        self.__it_results = OrderedDict()

    def __build_result_for_clazz(self, clazz, skip_parent_methods):
        if clazz.__name__ not in self.__it_results.keys():
            closure = _ClosureHandler(
                None, clazz, WebAction,
                skip_parent_methods=skip_parent_methods
            )
            self.__it_results[clazz.__name__] = {
                name: None
                for name in [
                    m for um, m in closure.methods().items()
                ]
            }

    def __add_error(self, err_store):
        for cls_name in err_store.keys():
            for method in err_store[cls_name].keys():
                m_info = err_store[cls_name][method]
                self.__it_results[cls_name][method] = m_info

    def __log_integration_results(self):
        log = get_log().info
        s = "\n\n\n"
        s += "-" * 30 + " Test Summary " + "-" * 30
        for cls_name, method in self.integration_results().items():
            s += "\n\n" + " " * 15 + f"{cls_name} :\n"
            for name, info in method.items():
                s += f"   {name:<40} {info['Description']:<60} {info['Result']}\n"
        s += "\n" + "-" * 72
        log(s.replace("  ", ". "))

    def verbose_integration_results(self):
        return self.__it_results

    def integration_results(self):
        v_results = self.verbose_integration_results().items()
        ret_res = {}
        for cls_name, methods in v_results:
            ret_res[cls_name] = {}
            for m_name, m_info in methods.items():
                ret_res[cls_name][m_name] = {}
                res_p = ret_res[cls_name][m_name]
                if m_info is None:
                    res_p["Result"] = "Not automated"
                    res_p["Description"] = "N/A"
                else:
                    if m_info["Exception"]:
                        res_p["Result"] = "FAILED"
                    else:
                        res_p["Result"] = "PASSED"
                    res_p["Description"] = m_info["Description"]
        return ret_res

    def run(self):
        closures = _ClosureHandler(
            None, self.__class__, TestStep
        )
        for method in closures.cell_methods():
            try:
                getattr(self, method)()
            except _CVIntegrationTestStepComplete as excp:
                self.__build_result_for_clazz(
                    excp.clazz, excp.skip_parent_methods
                )
                self.__add_error(excp.err_store)
        self.__log_integration_results()


def wait_for_condition(timeout=300, poll_frequency=1, log=True):
    """
    Waits for a condition to be satisfied i.e method returns true
    :param timeout: the amount of time in seconds the condition is waited to be true,
    after which is throws CVTimeoutException
    :param poll_frequency: The amount of time in seconds that the function sleeps for before polling again
    """
    # TODO: Convert to plugin and then make decorator
    def decorator_wrapper(method):
        """A decorator for executing the method as a waiter"""
        def until(*args, **kwargs):
            """Returns the function which is provided as a wrapper from the decorator"""
            end_time = time.time() + timeout
            while True:
                exception = None
                try:
                    if not log:
                        get_log().disabled = True
                    value = method(*args, **kwargs)
                    if value:
                        get_log().disabled = False
                        return value
                except Exception as exp:
                    exception = exp
                time.sleep(poll_frequency)
                if time.time() > end_time:
                    raise CVTimeOutException(timeout, str(exception))
        return until
    return decorator_wrapper


class AngularPlugin(Plugin):
    """Plugin to handle switch frame for react table access"""

    def __init__(self, frame, react_enabled):
        self.web_exec_info = None
        self.frame = frame
        self.frame_switched = False
        self.angular_enabled = not react_enabled

    def excep(self, exec_info, exception):
        pass

    def pre(self, exec_info):
        self.web_exec_info = WebExecInfo(
            exec_info, ""
        )
        if self.angular_enabled:
            self.web_exec_info.move_to_angular(self.frame)
        else:
            self.web_exec_info.move_to_react()

    def post(self, exec_info, result):
        pass

    def final(self, exec_info, exception):
        if self.web_exec_info:
            if self.angular_enabled:
                self.web_exec_info.move_to_react()  # move back to root frame
            self.web_exec_info.move_to_angular(self.frame)  # move based on page


class InitStep(BaseDecorator):
    """Class for decorating functions to perform testcase init steps"""

    def __init__(self, msg=""):
        """
        Constructor function for the class

        Args:
            msg     (str)   :   Message to describe functionality of the method
        """
        super().__init__()
        self.msg = msg
        self.load_plugin()

    def load_plugin(self):
        self.add_plugin(
            InitStepLoggerPlugin(
                msg=self.msg
            )
        )
