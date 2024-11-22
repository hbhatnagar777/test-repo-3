# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

This file is used for maintaining the configuration file during installation

"""

import json
import os
from jsonmerge import Merger


def retain_json():
    """"creates a config file with updated keys and values

    Args:
        None

    Returns:
         None

    Raises:
        Exception:

            if error in json files

    """

    path = os.path.dirname(os.path.abspath(__file__))

    # Check if Template_config.json file exists or not
    if not os.path.exists(os.path.join(path, 'Templates', 'template-config.json')):
        return
    else:
        with open(os.path.join(path, 'Templates', 'template-config.json')) as json_file:
            template_config = json.load(json_file)

        # Check if config.json file exists or not
        if not os.path.exists(os.path.join(path, 'Templates', 'config.json')):
            with open(os.path.join(path, 'Templates', 'config.json'), 'w') as config_file:
                json.dump(template_config, config_file, ensure_ascii=False, indent=4)
        else:
            with open(os.path.join(path, 'Templates', 'config.json')) as json_file:
                config_file = json.load(json_file)

            schema = {
                "mergeStrategy": "objectMerge"
            }

            merger = Merger(schema)
            new_config_file = merger.merge(template_config, config_file)
            with open(os.path.join(path, 'Templates', 'config.json'), 'w') as config_file:
                json.dump(new_config_file, config_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    retain_json()
