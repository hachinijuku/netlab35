#! /usr/bin/env python3
'''
usage: delete_unused_vms.py [-h] [--datacenter DATACENTER] [-n]
                            -r {none,local,datacenter,disk} ...

Delete vms in Netlab inventory not associate with pods

positional arguments:
  vmexprs               regular expressions describing names of vms to remove

options:
  -h, --help            show this help message and exit
  --datacenter DATACENTER
                        datacenter to remove vms from
                       (from environment var NETLAB_VDC if not specified)
  -n                    dry run
  -r {none,local,datacenter,disk}, --removal_type 
        {none,local,datacenter,disk}
'''

import argparse
import enum
import sys
import inspect
import os

import datetime
import re

import asyncio
from netlab.async_client import NetlabClient
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory

Summary = 'VM Summary:'


async def do_delete_vms(api, vm_ids, vm_names, removal_type):
    global Summary

    assert len(vm_ids) == len(vm_names), \
        'vm_id and vm_name list lenghts differed'

    for index in list(range(len(vm_ids))):
        try:
            if removal_type == 'disk':
                result = await api.vm_inventory_remove_disk_task(
                    vm_id=vm_ids[index])
            elif removal_type == 'datacenter':
                result = await api.vm_inventory_remove_datacenter_task(
                    vm_id=vm_ids[index])
            elif removal_type == 'local':
                result = api.vm_inventory_remove_local(vm_id=vm_ids[index])
            print(f'{vm_names[index]}: {result}')
            Summary = Summary + '\n' + f'  {vm_names[index]}: {result}'
        except Exception as err:
            Summary = Summary + '\n' + f'  {vm_names[index]}: {err}'
            print(f'{vm_names[index]}: Failed {err}',
                  file=sys.stderr,
                  flush=True)


async def main():
    global Summary

    parser = argparse.ArgumentParser(
        description='Delete vms in Netlab inventory '
        'not associate with pods')
    parser.add_argument(
        'vmexprs',
        help='regular expressions describing names of vms to remove',
        nargs=argparse.REMAINDER)
    parser.add_argument('--datacenter',
                        required=False,
                        help='datacenter to remove vms from '
                        '(from environment var NETLAB_VDC if not specified)',
                        default=os.environ['NETLAB_VDC'])
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument("-r",
                        "--removal_type",
                        required=True,
                        action="store",
                        choices=tuple(t.name.lower() for t in RemoveVMS),
                        default=RemoveVMS.NONE.name.lower(),
                        dest="removal_type")
    args = parser.parse_args()
    if not args.vmexprs:
        args.vmexprs = ['.*']
    if args.removal_type == 'none':
        print('Nothing to do because removal_type is "none"')
        exit(1)

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

        if not relevant_unused_vms:
            print(f'No unused VMs found in {args.datacenter}')
            exit(0)

        # Verify intent
        print(f'Unused VMs to be removed from {args.datacenter}:')
        for vm in relevant_unused_vms:
            print(f'  {vm["vm_name"]}')
        print('Removal type is '+args.removal_type)
        if args.n:
            exit()
        yes_no = input("Do you want to remove all these pods (y/n)? ")
        if yes_no[0].lower() != 'y':
            sys.exit(2)

        # Group vms by vm host
        vm_dict = {}
        vm_names = {}
        for vm_index in range(len(relevant_unused_vms)):
            try:
                vm_dict[relevant_unused_vms[vm_index]['vh_id']].append(
                    relevant_unused_vms[vm_index]['vm_id'])
                vm_names[relevant_unused_vms[vm_index]['vh_id']].append(
                    relevant_unused_vms[vm_index]['vm_name'])
            except Exception:
                vm_dict[relevant_unused_vms[vm_index]['vh_id']] = \
                    [relevant_unused_vms[vm_index]['vm_id']]
                vm_names[relevant_unused_vms[vm_index]['vh_id']] = \
                    [relevant_unused_vms[vm_index]['vm_name']]

        print(f'vm_dict.keys() {vm_dict.keys()}')
        # Delete vms in parallel tasks for each vm host
        tasks = []
        for vh_id in vm_dict.keys():
            try:
                tasks.append(
                    asyncio.create_task(do_delete_vms(api,
                                                      vm_dict[vh_id],
                                                      vm_names[vh_id],
                                                      args.removal_type)))
            except Exception as err:
                printf(f'Failed task append: {err}')
        await asyncio.gather(*tasks, return_exceptions=True)

        print(Summary)

if __name__ == "__main__":
    asyncio.run(main())
