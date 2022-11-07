#! /usr/bin/env python3
'''
list_unused_vms.py

usage: list_unused_vms.py [-h] [--datacenter DATACENTER] ...

List unused VMs in the netlab inventory

positional arguments:
  vmexprs               regular expressions for names of
                        vms to remove (all if not specified)

options:
  -h, --help            show this help message and exit
  --datacenter DATACENTER
                        datacenter to remove vms from
                        (from environment var NETLAB_VDC if not specified)
'''

import argparse
import enum
import sys
import os

import datetime
import re

import asyncio
from netlab.async_client import NetlabClient
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory


async def main():
    parser = argparse.ArgumentParser(
        description='List unused VMs in the netlab inventory')
    parser.add_argument('--datacenter',
                        required=False,
                        help='datacenter to remove vms from '
                        '(from environment var NETLAB_VDC if not specified)',
                        default=os.environ['NETLAB_VDC'])
    parser.add_argument('vmexprs',
                        help='regular expressions for names of vms'
                        ' to remove (all if not specified)',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.vmexprs:
        args.vmexprs = ['.*']

    async with NetlabClient() as api:
        datacenter_id = await api.vm_datacenter_find(vdc_name=args.datacenter)
        all_vms = await api.vm_inventory_list(vdc_id=datacenter_id)
        unused_vms = list(filter(lambda x: x['pc_pod_id'] == 0, all_vms))

        # Filter to match argument vm name regular expressions
        relevant_unused_vms = []
        for expr in args.vmexprs:
            prog = re.compile(expr)
            these_vms = list(filter(lambda x:
                                    prog.match(x['vm_name']),
                                    unused_vms))
            relevant_unused_vms += these_vms

        for vm in relevant_unused_vms:
            print(f'  {vm["vm_name"]}')


if __name__ == "__main__":
    asyncio.run(main())
