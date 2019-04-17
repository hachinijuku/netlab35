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
    parser.add_argument('vmexprs',
                        help='regular expressions describing names of unused vms to remove',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()

    api = Client()
    all_vms = api.vm_inventory_list()
    unused_vms = list(filter(lambda x: x['pc_pod_id'] == 0, all_vms))
    #unused_vms = all_vms

    # Verify VM deletion:

    relevant_unused_vms = []
    if args.vmexprs:
        for expr in args.vmexprs:
            prog = re.compile(expr)
            these_vms = list(filter(lambda x: prog.match(x['vm_name']), unused_vms))
            relevant_unused_vms += these_vms
    else:
        relevant_unused_vms = unused_vms
        
    for vm in relevant_unused_vms:
        print('  '+vm["vm_name"]+': '+str(vm['pc_pod_id']))
 
if __name__ == "__main__":
   main()
