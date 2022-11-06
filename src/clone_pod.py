#! /usr/bin/env python3

"""
clone_pod.py

usage: clone_pod.py [-h] --src_pid SRC_PID --num_clones NUM_CLONES
                    --pod_prefix POD_PREFIX
                    [--clone_datastore CLONE_DATASTORE] [-debug] [-n] [-q]

Remove VMs from vcenter host

options:
  -h, --help            show this help message and exit
  --src_pid SRC_PID     source pod id
  --num_clones NUM_CLONES
                        number of clones to generate
  --pod_prefix POD_PREFIX
                        prefix for cloned pod names
  --clone_datastore CLONE_DATASTORE
                        datastore for clones
  -debug                debug mode (kind of verbose)
  -n                    dry run
  -q                    quiet (no pod messages)

This script clones a master Netlab-VE+ pod and distributes the clones evenly
across a set of hosts in a datacenter given by environment variable

  NETLAB_VDC

To get the desired behavior, it determines the number of clones and
available pod numbers and shuffles them across datacenter hosts.

MIT License

Copyright (c) 2022 Joseph N. Wilson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import argparse
import asyncio
from netlab.async_client import NetlabClient
from typing import List, Any, Tuple, Union

from netlab.enums import PodCategory
from netlab.enums import HDRSeverity
import sys
import os


##
# do_one_vh: Clones the src_pid pod to each of the pod_ids,
# creating cloned vms on host vh_id associated with
# the specified datastore.
#
# api: netlab client connection
# src_pid: id of pod to clone
# vh_id: id of vmhost to clone vms to
# pod_ids: ids of pods to be created
# pod_prefix: prefix of name to assign to pod. Suffix is the pod_id
# datastore: Either '' or name of datastore on which to store the vms
#
async def do_one_vh(api,
                    src_pid,
                    vh_id,
                    pod_ids,
                    pod_prefix,
                    datastore):
    global Debug
    global Dryrun
    global Quiet
    global Summary

    for pod_id in pod_ids:
        try:
            pod_name = f'{pod_prefix}{pod_id}'
            if Dryrun or not Quiet:
                print(f'requested pod_clone_task({src_pid},'
                      f'{pod_id},{pod_name},{vh_id})')
            if Dryrun:
                return

            specs = {'clone_datastore': datastore,
                     'clone_role': 'NORMAL',
                     'clone_vh_id': vh_id}
            result = \
                await api.pod_clone_task(source_pod_id=src_pid,
                                         clone_pod_id=pod_id,
                                         clone_pod_name=pod_name,
                                         pc_clone_specs=specs,
                                         severity_level=HDRSeverity.TRACE0)
            Summary.append(f'{result["status"]}:{pod_id}')
            if not Quiet:
                print(f'{result["status"]}:{pod_id}')
            if Debug:
                print(f'result:{result}')
        except Exception as err:
            print(f'Exception:{err}')
            print(f'  pod_id:{pod_id},pod_name:{pod_name},'
                  f'datastore:"{datastore}",vh_id:{vh_id}')


##
# do_clone: Clone pods
#
# api: netlab client connection
# src_pid: id of pod to clone
# pid_assignment_dict: map from vm_host id to list of pods on that vm_host
# pod_prefix: Prefix of name of pod to be created. Suffix will be pod_id
# datastore: Either '' or name of datastore on which to store the vms
#
async def do_clone(api,
                   src_pid,
                   pid_assignment_dict,
                   pod_prefix,
                   datastore):
    if Debug:
        print(f'do_clone({src_pid},pid_assignment_dict,'
              f'{pod_prefix},"{datastore}")')
    tasks = []
    for vh_id in pid_assignment_dict.keys():
        tasks.append(asyncio.create_task(do_one_vh(api,
                                                   src_pid,
                                                   vh_id,
                                                   pid_assignment_dict[vh_id],
                                                   pod_prefix,
                                                   datastore)))
    await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    global Debug
    global Dryrun
    global Quiet
    global Summary

    Summary = []

    parser = \
        argparse.ArgumentParser(description='Remove VMs from vcenter host')
    parser.add_argument('--src_pid',
                        required=True,
                        help='source pod id')
    parser.add_argument('--num_clones',
                        required=True,
                        help='number of clones to generate')
    parser.add_argument('--pod_prefix',
                        required=True,
                        help='prefix for cloned pod names')
    parser.add_argument('--clone_datastore',
                        required=False,
                        help='datastore for clones',
                        default='')
    parser.add_argument('-debug',
                        action='store_const',
                        const=True,
                        help='debug mode (kind of verbose)')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument('-q',
                        action='store_const',
                        const=True,
                        help='quiet (no pod messages)')
    args = parser.parse_args()
    num_clones = int(args.num_clones)
    Debug = args.debug
    Dryrun = args.n
    Quiet = args.q

    async with NetlabClient() as api:
        datacenter_id = \
            await api.vm_datacenter_find(vdc_name=os.environ['NETLAB_VDC'])
        vh_ids = list(map(lambda x: x['vh_id'],
                          await api.vm_host_list(vdc_id=datacenter_id)))

        # Check for valid source pid
        src_pod_cat = (await api.pod_get(pod_id=args.src_pid,
                                         properties='pod_cat'))['pod_cat']
        if src_pod_cat != PodCategory.MASTER_VM:
            print('Sorry. We will not copy from a non-Master pod.')
            sys.exit()

        # find currently allocated pods
        pod_ids = list(map(lambda x: x["pod_id"], await api.pod_list()))
        pid_hwm = max(pod_ids)

        # get sorted list of available pids
        # (assign unused low pod numbers first)
        unused_low_pods = list(set(range(1, pid_hwm)) - set(pod_ids))
        pids_to_assign = unused_low_pods[:num_clones] \
            + list(range(pid_hwm+1, pid_hwm+1+num_clones-len(unused_low_pods)))

        # identify available hosts for VMs
        num_hosts = len(vh_ids)

        # Divvy up pods (or at least args to create them) to VM hosts
        # in round robin fashion.
        #
        # The theory is that students will grab them in order and this will
        # do a static load balancing based on expected human behavior

        if Debug:
            print(f'{vh_ids}, {len(vh_ids)}')
            print(f'pids to assign:{pids_to_assign}')

        pid_assignment_dict = {vh_ids[i]:
                               pids_to_assign[i:
                                              len(pids_to_assign):
                                              len(vh_ids)]
                               for i in range(0, len(vh_ids))}

        if Debug:
            print(f'{args.src_pid} {args.pod_prefix}'
                  f'{vh_ids} {pid_assignment_dict} {num_hosts}')

        await do_clone(api,
                       args.src_pid,
                       pid_assignment_dict,
                       args.pod_prefix,
                       args.clone_datastore)

    if Dryrun:
        print('No action taken (dry run).')
    Summary.sort()
    separator = '\n  '
    print(f'Pod Summary:{separator}{separator.join(Summary)}')

if __name__ == "__main__":
    asyncio.run(main())
