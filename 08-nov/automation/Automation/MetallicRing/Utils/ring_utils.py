# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper utils class for carrying out basic ring related tasks

    RingUtils:

        __init__()                      --  Initializes Ring Utils Helper

        get_ring_string                 --  Returns the ring ID string for a given ring ID

        read_from_file                  --  Reads a file and returns the content

        write_to_file                   --  Writes the content to a file

        get_ring_name                   --  Returns the ring ring for a given ring ID

"""
import json


class RingUtils:
    def __init__(self):
        pass

    @staticmethod
    def get_ring_string(ring_id):
        """
        Returns the ring ID string for a given ring ID
        Args:
            ring_id(int/str)        --  ID of ring
        """
        if isinstance(ring_id, int):
            ring_id = str(ring_id)
        if len(ring_id) <= 2:
            ring_id = f"0{ring_id}"
        return ring_id

    @staticmethod
    def read_from_file(file_name, read_json=False):
        """
        Reads a file and returns the content
        Args:
            file_name(str)      --  Name of the file
            read_json(bool)     --  True - File is a json file
                                    False - Normal string file
        Returns:
            str/json            --  Return the file content as string
        """
        with open(file_name, 'r') as file:
            if read_json:
                return json.load(file)
            return file.read()

    @staticmethod
    def write_to_file(file_name, data, write_json=False):
        """
        Writes the content to a file
        Args:
            file_name(str)      --  Name of the file to write the data to
            data(str)           --  data to be written to file
            write_json(bool)    --  True - if content needs to be written in the form of json
                                    False- if normal string content
        """
        with open(file_name, 'w') as file:
            if write_json:
                json.dump(data, file, indent=4)
            else:
                file.write(data)

    @staticmethod
    def get_ring_name(ring_id):
        """
        Returns the ring ring for a given ring ID
        Args:
            ring_id(int/str)        --  ID of ring
        """
        ring_id = RingUtils.get_ring_string(ring_id)
        ring_name = f"m{ring_id}"
        return ring_name
