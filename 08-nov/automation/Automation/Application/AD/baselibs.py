# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This  is common code used in other related library and modules

Class:

Functions:

    tc : time count , return time in differnte format.

"""
__all__ = ["tc"]

from time import time
from time import sleep
from datetime import datetime

def tc(ptime=None, timeformat=None, delay=None):
    """
    return time and check the time different
    also can working as sleep with delay option

    Args:
        ptime         (int)        Unix time for prior time

        timeformat    (str)        format to return, can be choiced from "ISO", "filename", "date"

        delay            (int)    delay seconds
    Return:
        None:
    Exception:
        None
    """
    returnvalue = None
    if delay is not None:
        sleep(delay)
    if ptime is None:
        if timeformat is None:
            returnvalue = time()
        elif timeformat == "ISO":
            returnvalue = datetime.now().isoformat().split('.')[0]
        elif timeformat == "filename":
            isostring = datetime.now().isoformat().split('.')[0].split("T")
            returnvalue = isostring[0]+"_"+"".join(isostring[1].split(":"))
        elif timeformat == "date":
            returnvalue = datetime.today().isoformat().split("T")[0]
    else:
        ctime = time()
        returnvalue = ctime-ptime
    return returnvalue
