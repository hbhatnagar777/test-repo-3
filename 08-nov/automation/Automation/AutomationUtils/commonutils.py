import json
import pandas
import threading
import importlib.abc
import os
import sys
import uuid
import time
import calendar
import random
import re
import string
from typing import Callable, Any

import yaml
import zlib
import re
from urllib import request
from deepdiff import DeepDiff
from . import cvhelper
from .machine import Machine


def enum(**enums):
    return type('Enum', (), enums)


def download_url(url, download_path, download_timeout=120):
    """Download file from the given url..

        Args:
            url   (str)     -- valid url from where file will be downloaded

            download_path      (str)     -- existing directory where file will be downloaded

            download_timeout   (int)     -- timeout to be considered while download

        Returns:
            downloaded file path

        Raises:
            Exception:
                if any error occurs in the downloading url
    """
    if not os.path.exists(os.path.dirname(download_path)):
        raise Exception("download path %s doesn't exists".format(path=os.path.dirname(download_path)))

    try:
        res = request.urlopen(url=url, timeout=download_timeout)
    except BaseException as err:
        raise Exception("Following Exception was raised while downloading. Details: {err}\nExiting".format(err=err))

    if res.code != 200:
        raise Exception("Unsuccessful downloading attempt. Details: {info}\tExiting".format(info=res))

    try:
        with open(download_path, "wb") as fd_handle:
            for chunk in res:
                fd_handle.write(chunk)
        fd_handle.close()
    except Exception as error:
        raise Exception("Unable to download file from url %s. Error %s" % (url, error))


class MyThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.parent = threading.current_thread().ident
        threading.Thread.__init__(self, *args, **kwargs)


def threadLauncher(tCount, q, target):
    for i in range(tCount):
        uniqueID = str(uuid.uuid1())
        theThread = MyThread(target=target, name=uniqueID, args=(uniqueID, q))
        theThread.daemon = True
        theThread.start()

    return True


def import_module(dir_path, module_name):
    filename = resolve_filename(dir_path, module_name)
    if module_name in sys.modules:
        return sys.modules[module_name]

    return Loader(module_name, filename).load_module(module_name)


def resolve_filename(dir_path, module_name):
    filename = os.path.join(dir_path, *module_name.split('.'))
    if os.path.isdir(filename):
        filename = os.path.join(filename, '__init__.py')
    else:
        filename += '.py'
    return filename


class Loader(importlib.abc.FileLoader, importlib.abc.SourceLoader):
    pass


def set_defaults(main, defaults):
    """Sets default value for the main dictionary using the defaults dictionary

        Args:
            main        (dict)      The dictionary to set default values
            defaults    (dict)      The dictionary which has default values

        Returns:
            Dictionary with default values applied

    """

    for key in defaults:
        if key not in main:
            main[key] = defaults[key]
        else:
            # If key is present, then make the value of same type
            if type(defaults[key]) is int:
                main[key] = get_int(main[key])

        if type(defaults[key]) == dict:
            set_defaults(main[key], defaults[key])


def get_dictionary_difference(dict1, dict2):
    """Gets the difference between the two dictionaries provided

        Args:
            dict1       (dict)      Dictionary 1 to compare
            dict2       (dict)      Dictionary 2 to compare

        Returns:
            added       (set)       Keys which are present in dict 1 but not in dict 2
            removed     (set)       Keys which are present in dict 2 but not in dict 1
            modified    (dict)      Keys which are present in both dict 1 and 2 but with
                                    modified values.

    """

    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        raise Exception('Cannot get difference as one of them is not a dictionary')

    d1_keys = set(dict1.keys())
    d2_keys = set(dict2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {}

    for o in intersect_keys:
        if dict1[o] != dict2[o]:
            modified[o] = (dict1[o], dict2[o])

    return added, removed, modified


def get_random_string(length=8, lowercase=True, uppercase=False,
                      digits=True, special_chars=False, custom_chars=None):
    """Generates a random string of the specified length

        Args:
             length         (int)      Length of the random string

             lowercase      (bool)     Include lowercase ASCII characters

             uppercae       (bool)     Include uppercase ASCII characters

             digits         (bool)     Include digits

             special_chars  (bool)     Include special characters

             custom_chars   (str)      Include custom characters like unicode

         Returns:
             (str)  --  A random string of specified length with the selected characters.
    """

    the_string = ''

    the_string += string.ascii_lowercase if lowercase else ''
    the_string += string.ascii_uppercase if uppercase else ''
    the_string += string.digits if digits else ''
    the_string += string.punctuation if special_chars else ''
    the_string += custom_chars if isinstance(custom_chars, str) else ''

    return ''.join(random.choice(the_string) for s in range(length))


def get_int(data, default=0):
    """Gets the int value of a string, returns default value on exception

        Args:
            data    (str/int)       The string to parse the integer from

            default (int)           The default integer value to return upon integer exception

        Returns:
            Parsed int from the string.
            0 if cannot parse int from string

    """

    try:
        return int(data)
    except ValueError:
        return default


def convert_to_timestamp(formatted_time):
    """Converts formatted time (%Y-%m-%d %H:%M:%S) to epoch timestamp in UTC timezone

        Args:
            formatted_time  (str)   Formatted time to convert to timestamp

        Returns:
            timestamp       (int)   Timestamp got from formatted time

    """

    # Using calendar.gmtime instead of time.mktime as time.mktime assumes its arg as local time,
    # whereas calendar.gmtime assumes the arg as epoch which is what we want

    return int(calendar.timegm(time.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')))


def convert_to_formatted_time(timestamp):
    """Converts epoch timestamp to formatted time (%Y-%m-%d %H:%M:%S) in UTC timezone

        Args:
            timestamp   (int/str)   Timestamp to convert to formatted time

        Returns;
            Formatted time  (str)   Formatted time of the timestamp

    """

    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))


def get_parent_path(path, separator):
    """Gets the parent directory for any given path

        Args:
            path        (str)       Path to get parent for
            separator   (str)       Separator present in the path

        Returns:
            Parent directory of the given path

        Example:
            C:\folder\file.txt -> C:\folder

    """

    if separator is None or separator == '':
        raise Exception('Invalid separator provided.')

    if not path:  # when the path itself is empty, the parent is the separator
        return separator

    path_split = path.split(separator)
    if not path_split[-1]:  # Remove the last item if it is empty
        path_split.pop()
    path_split.pop()
    parent = separator.join(path_split)
    parent = separator if parent == '' else parent
    return parent


def add_prefix_sep(path, separator):
    """Adds a sep to the beginning of the path if not already prefixed

        Args:
            path        (str)       Path to prefix sep with
            separator   (str)       Separator of the path

        Returns:
            path with prefixed sep

        Example:
            C:\file.txt -> \C:\file.txt
            /home/file.txt -> /home/file.txt

    """

    if separator is None or separator == '':
        raise Exception('Invalid separator provided.')

    if path == '':
        return separator

    path = separator + path if path[0] != separator else path
    return path


def add_trailing_sep(path, separator=''):
    """Adds a trailing sep to the given path if present

        Args:
            path        (str)       Path to add the trailing sep
            separator   (str)       Separator of the path

        Returns:
            path with trailing sep added

        Example:
            C:\folder -> C:\folder\
            /home/folder/ -> /home/folder/

    """

    if separator is None or separator == '':
        raise Exception('Invalid separator provided.')

    if path == '':
        return separator

    path = path + separator if path[-1] != separator else path
    return path


def remove_prefix_sep(path, separator=''):
    """Removes the prefixed sep for the given path if present

        Args:
            path        (str)       Path to remove the prefixed sep
            separator   (str)       Separator of the path

        Returns:
            path with prefixed sep removed

        Example:
            \C:\file.txt -> C:\file.txt
            C:\file.txt -> C:\file.txt

    """

    if separator is None or separator == '':
        raise Exception('Invalid separator provided.')

    path = path[1:] if path[0] == separator else path
    return path


def remove_trailing_sep(path, separator=''):
    """Removes trailing sep for the given path

        Args:
            path        (str)       Path to remove the trailing sep
            separator   (str)       Separator of the path

        Returns:
            path with trailing sep removed

        Example:
            C:\folder\ -> C:\folder
            /home/folder/ -> /home/folder

    """

    if separator is None or separator == '':
        raise Exception('Invalid separator provided.')

    path = path[:-1] if path[-1] == separator else path
    return path


def get_cvadmin_password(commcell):
    """gets password for commcell sql server

    Args:
        commcell        (commcell object)       the commcell whose server password is to be obtained

    Returns     password    (str)"""
    cs_machine = Machine(commcell.commserv_client)
    encrypted_pass = cs_machine.get_registry_value(r"Database", "pAccess")
    cvadmin_password = cvhelper.format_string(commcell, encrypted_pass).split("_cv")[1]
    return cvadmin_password


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. The ``merge_dct`` is merged into `dct``.

        Args:
            :param dct: dict onto which the merge is executed

            :param merge_dct: dct which needs to be merged into dct

        Returns:

            None
    """
    for k, v in merge_dct.items():
        if k in dct and isinstance(
                dct[k], dict) and isinstance(
            merge_dct[k], dict):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def convert_json_to_html(input_json):
    """converts json to html table

            Args:

                input_json      list(dict)      --  Json to be converted to html table

            Returns:

                str --  html code for table with json values
    """
    try:
        _data_frame = pandas.DataFrame(input_json)
        # optional params - remove row index and make header center in table
        return _data_frame.to_html(index=False, justify='center')
    except Exception as ep:
        raise Exception(f"Failed to load json into data frame. Please check input json - {ep}")


def convert_json_to_yaml(input_list):
    """converts json to yaml file

        Args:

            input_list      (list(dict))      --  Input list to convert to yaml

        Returns:

            str --  Yaml file content
    """
    return yaml.dump_all(
        input_list,
        explicit_start=True,
        default_flow_style=False,
        sort_keys=False)


def convert_yaml_to_json(yaml_file):
    """Converts yaml file to json and return it as dict

        Args:

            yaml_file       (str)       --  Yaml file path

        Returns:

            dict -- Containing yaml details

        Raises:

            Exception:

                if failed to convert yaml to json
    """
    if not os.path.exists(yaml_file):
        raise Exception("Yaml file doesn't exists on given path")
    file_obj = open(yaml_file, "r")
    content = file_obj.read()
    file_obj.close()
    return list(yaml.safe_load_all(content))


def compare_list(list1, list2):
    """
    compares list1 and list2

    args:
        list1, list2 - two lists to compare

    returns: (list)
            list3 -> exists in both
            list4 -> list values missing in list2
            list5 -> list values missing in lis1

    """
    try:
        list3 = []
        list4 = []
        list5 = []
        for val in list1:
            if val in list2:
                list3.append(val)
            else:
                list4.append(val)
        for val in list2:
            if val in list1:
                continue
            else:
                list5.append(val)
        return list3, list4, list5

    except Exception as err:
        raise Exception("Could not compare the list with error %s", str(err))


def crc(file):
    """
        Calcualte CRC for each file passed in 8 bits format in Hexadec

        args:
            file - file for which crc needs to be calculated

        returns:
            crc in 8 bit format in hexadecimal
    """
    try:
        fd = open(file, "rb")
    except IOError:
        raise Exception("Unable to open the file in readmode:", file)

    each_line = fd.readline()
    prev = None
    while each_line:
        if not prev:
            prev = zlib.crc32(each_line)
        else:
            prev = zlib.crc32(each_line, prev)
        each_line = fd.readline()
    fd.close()
    return format(prev & 0xFFFFFFFF, '08x')


def compare_dict(dict1, dict2):
    """
            Compares 2 dicts having list values and return 3 dicts

            args:
                dict1, dict2 - two dictionaries to compare

            returns:
                missing_in_dict1 -> dict values missing in dict1
                missing_in_dict2 -> dict values missing in dict2
                exist_in_both -> dict values present in both dict1 and dict2
    """
    try:
        missing_in_dict1 = {}
        missing_in_dict2 = {}
        exist_in_both = {}
        for key1, value1 in dict1.items():
            if key1 in dict2.keys():
                if type(dict1[key1]) == list and type(dict2[key1]) == list:
                    _exist_in_both, _only_in_dict1, _only_in_dict2 = compare_list(dict1[key1], dict2[key1])
                    if _only_in_dict2:
                        missing_in_dict1[key1] = _only_in_dict2
                    if _only_in_dict1:
                        missing_in_dict2[key1] = _only_in_dict1
                    if _exist_in_both:
                        exist_in_both[key1] = _exist_in_both
                else:
                    raise Exception('Cannot get difference as one of them is not a dictionary')
            else:
                missing_in_dict2[key1] = dict1[key1]
        for key2, value2 in dict2.items():
            if key2 in dict1.keys():
                if type(dict1[key2]) == list and type(dict2[key2]) == list:
                    _val_exist_in_both, _only_in_dict1, _only_in_dict2 = compare_list(dict1[key2], dict2[key2])
                    if _only_in_dict2:
                        missing_in_dict1[key2] = _only_in_dict2
                    if _only_in_dict1:
                        missing_in_dict2[key2] = _only_in_dict1
                else:
                    raise Exception('Cannot get difference as one of them is not a dictionary')
            else:
                missing_in_dict1[key2] = dict2[key2]

        return missing_in_dict1, missing_in_dict2, exist_in_both

    except Exception as err:
        raise Exception('Could not compare the dictionaries - %s, err')


def parse_size(size_str: str) -> int:
    """
    converts size str under size column to computable bytes (int)

    Args:
        size_str    (str)   -   the size str (Ex: '12B', '11KB', '15GB')

    Returns:
        size    (int)   -   the integer representing total number of bytes
    """
    size_units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    size_str = size_str.upper()
    if not re.match(r' ', size_str):
        # if no space between number and unit, add space
        size_str = re.sub(r'([KMGTPEZY]?B)', r' \1', size_str)
    number, unit = [token.strip() for token in size_str.split()]
    return int(float(number) * 1024 ** size_units.index(unit))


def parse_duration(duration: str) -> int:
    """
    Parses the duration string under elapsed column, converts to seconds (int)

    Args:
        duration(str)   -   the duration string to parse

    Returns:
        seconds (int)   -   the number of seconds the string represents
    """
    in_seconds = {
        'second': 1,
        'minute': 60,
        'hour': 60 * 60,
        'day': 60 * 60 * 24
    }
    in_seconds['month'] = in_seconds['day'] * 30
    in_seconds['year'] = in_seconds['day'] * 365
    seconds = 0
    for dur in ['second', 'minute', 'hour', 'day']:
        pattern = f'(\d{"{1,2}"}) {dur}s?'
        f = re.search(pattern, duration)
        if f:
            seconds += int(f.group(1)) * in_seconds[dur]
    return seconds


def process_text(text: Any) -> str:
    """
    Strips all whitespace, converts to lower and returns string for comparison

    Args:
        text    (obj)       -   any object with a str repr to clean

    Returns:
        processed   (str)   -   processed into clean text ready for comparison
    """
    return str(text).strip().lower().translate(str.maketrans('', '', string.whitespace))


def is_sorted(unsorted_list: list, comparator: Callable[[Any, Any], bool] = None, asc: bool = True) -> bool:
    """
    Checks if an iterable is sorted or not

    Args:
        unsorted_list (iterable)        : the iterable to test sorting
        comparator (func)               : a bool-returning function with 2 params (a,b) to determine if b >= a
                                          default: python's default comparator b >= a
        asc (bool)                      : check for ascending or descending
                                          default: ascending

    Returns:
        True, if sorted correctly
        False, if not sorted
    """
    if comparator is None:
        comparator = lambda a, b: b >= a
    if asc:
        return all(comparator(unsorted_list[i], unsorted_list[i + 1]) for i in range(len(unsorted_list) - 1))
    else:
        return all(comparator(unsorted_list[i + 1], unsorted_list[i]) for i in range(len(unsorted_list) - 1))


def convert_size_string_to_bytes(size):
    """
        converts size in "x.yz KB" format to bytes
        Args:
            size (str) : size string
                        Ex: "70.78 MB"
    """
    size_value, size_type = size.split()
    size_value = float(size_value)
    mapping = {
        "B": 1,
        "KB": 1 << 10,
        "MB": 1 << 20,
        "GB": 1 << 30,
        "TB": 1 << 40,
        "PB": 1 << 50
    }
    bytes_size = size_value * mapping[size_type]
    return bytes_size


def get_job_starting_time(date_time, language):
    """
        Extracts the details from different formats of start time of the job
        args:
            date_time (str) : the entire string corresponding to Start time label in job details page.
            language (str) : selected locale
        returns:
            year (str): example: '2024'
            month (str): example: 'Feb' (could be different for different languages)
            date (str): example: '20'
            start_time (str): example: '11:42 AM'
    """
    if language == 'de':  # german
        day_year, start_time = date_time.split(", ")
        date, month, year = day_year.split('. ')
    elif language == 'es' or language == 'es_MX' or language == 'fr':  # spanish, spanish-mexican, french
        day_year, start_time = date_time.split(", ")
        date, month, year = day_year.split()
    elif language == 'zh' or language == 'ja':  # chinese, japanese
        day_year, start_time = date_time.split()
        year, month, date = re.findall(r'\d+', day_year)
    elif language == 'ru':  # russian
        day_year, start_time = date_time.split(", ")
        date, month, year, _ = day_year.split()
    else:  # english
        day, year, start_time = date_time.split(", ")
        month, date = day.split()

        month_abbr = {
            "Jan": "january",
            "Feb": "february",
            "Mar": "march",
            "Apr": "april",
            "May": "may",
            "Jun": "june",
            "Jul": "july",
            "Aug": "august",
            "Sep": "september",
            "Oct": "october",
            "Nov": "november",
            "Dec": "december"
        }
    month = month_abbr[month]

    if language != 'en':  # non-english are following 24 hr system
        t = time.strptime(start_time, "%H:%M:%S")
        start_time = time.strftime("%I:%M %p", t)
        if start_time[0] == '0':
            start_time = start_time[1:]
    else:
        hour_min, period = start_time.split()
        hour_min = hour_min[:-3]
        start_time = hour_min + " " + period

    return year, month, date, start_time


def get_differences(obj1: object, obj2: object, **diff_params) -> str:
    """
    Given 2 Objects, can be any type, list, dict, etc.... Returns list of error messages describing the difference

    Args:
        obj1    (Object)    -   object1 for comparison
        obj2    (Object)    -   object2 for comparison
        diff_params         -   params to pass to DeepDiff, (see DeepDiff docs)

    Returns:
        errors  (str)   -   string describing the differences between both objects
        None            -   if there are no differences
    """
    diff = DeepDiff(obj1, obj2, **diff_params)
    if diff:
        return json.dumps(diff, indent=4)
