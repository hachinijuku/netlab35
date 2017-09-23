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
    unused_vms = list(filter(lambda x: x['pc_pod_id'] != None, all_vms))
    vm_names = [x['vm_name'] for x in unused_vms]

    # Verify VM deletion:
    print('Unused VMs:')
    for name in vm_names:
        print('  '+name)
 
if __name__ == "__main__":
   main()
