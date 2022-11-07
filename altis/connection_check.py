#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Test Internet connection
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------

import requests
import re

def check_internet(url):
    timeout = 5
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False
    except requests.exceptions.InvalidSchema:
        return False


def check_altis_version(current_version):
    url = 'https://gitlab.com/ctoh/altis/-/raw/main/version.txt?inline=false'
    timeout = 5
    pattern_regex_version = (r".*(?P<version>V[\d]{1,3}.[\d]{1,3}.[\d]{1,3})-(?P<git_post>[\d]{1,3})-(?P<gir_version>[a-z,0-9]{8})")
    pattern = re.compile(pattern_regex_version)
    
    latest_version = requests.get(url, timeout=timeout).text
    match = pattern.search(latest_version)
    
    if match is not None:
        if match.groupdict()["version"] == current_version:
            return True, match.groupdict()["version"]
        else:
            return False, match.groupdict()["version"]
    else : 
            return None, None 




