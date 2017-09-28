#! /usr/bin/env python3

import argparse
import enum
import sys

import datetime
import re

from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory
def main():

    si = None

    parser = argparse.ArgumentParser(description='List unused VMs in the netlab inventory')
    args = parser.parse_args()

    api = Client()
    all_vms = api.vm_inventory_list()
    unused_vms = list(filter(lambda x: x['pc_pod_id'] == None, all_vms))

    # Verify VM deletion:
    for vm in unused_vms:
        print('  '+vm["vm_name"])
 
if __name__ == "__main__":
   main()
