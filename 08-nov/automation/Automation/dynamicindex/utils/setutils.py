# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module contains the various set utility functions.

These are the functions defined in this module:

get_setname()               --  Returns the setname visible to the user with whom the set is shared

generate_charstream()       --  Generates a random string containing characters & digits.

generate_created_setname()  --  Replaces all the characters not allowed in setnames by '_'.

generate_random_name()      --  Appends a random string in the itemname.

"""
import random
import string
from .constants import CHARS_NOT_ALLOWED_IN_SETNAME, NUM_CHARS, NUM_DIGITS
from .constants import RANDOM_INT_LOWER_LIMIT, RANDOM_INT_UPPER_LIMIT


def get_setname(shared_by_user, setname):
    """Returns the setname visible to the user with whom the set is shared.

    Args:
        shared_by_user    (str)  --  User who owns this set.

        setname           (str)  --  The set which is shared.

    Returns:
        str  -  setname of the shared set.
    """
    username = shared_by_user.split("\\")[1]
    domain = shared_by_user.split("\\")[0]
    new_username = username + "@" + domain
    shared_setname = new_username + "\\" + setname
    return shared_setname


def generate_charstream():
    """Generates a random string containing characters (not allowed in setname) and digits.

    Returns:
        str  -  A random string.
    """
    chars_not_allowed = CHARS_NOT_ALLOWED_IN_SETNAME
    temp_chars = ''.join(random.choices(chars_not_allowed, k=NUM_CHARS))
    temp_digits = ''.join(random.choices(string.digits, k=NUM_DIGITS))
    return temp_chars + temp_digits


def generate_created_setname(setname):
    """Replaces all the characters not allowed in setnames by '_'.

    Args:
        setname    (str)  --  setname to append characters to.

    Returns:
        str  -  Returns the setname.
    """
    for char in CHARS_NOT_ALLOWED_IN_SETNAME:
        if char in setname:
            setname = str(setname).replace(char, "_")
    return setname


def generate_random_name(item_name):
    """Appends a random string in the itemname.

    Args:
        item_name    (str) --  Itemname to append characters to.

    Returns:
        str  -  Itemname with random string appended to it at the end.
    """
    return item_name + str(random.randint(RANDOM_INT_LOWER_LIMIT, RANDOM_INT_UPPER_LIMIT))
