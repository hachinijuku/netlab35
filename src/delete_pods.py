#! /usr/bin/env python3
'''
delete_pods.py

usage: delete_pods.py [-h] [-n] [-offline_only] [-force] [-q]
                      [-r {none,local,datacenter,disk}]
                      ...

Delete NDG Netlab Pods

positional arguments:
  podexprs              regular expressions describing names of pods to remove

options:
  -h, --help            show this help message and exit
  -n                    dry run
  -offline_only         delete only offline pods
  -force
  -q
  -r {none,local,datacenter,disk}, --removal_type {none,local,datacenter,disk}

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

'''

import argparse
import sys
import os
import subprocess
import re

import asyncio
from netlab.async_client import NetlabClient

from netlab.enums import RemoveVMS
from netlab.enums import PodState

Summary = 'Pod Summary:'


##
# delete_pods: Deletes pods in a list sequentially
#
#  pod_list: pods to delete
#  removal_type: RemoveVMS enum value
#
async def delete_pods(api, pod_list, removal_type):
    global Quiet
    global Summary

    for this_pod_id in pod_list:
        if not Quiet:
            print(f'deleting: {this_pod_id}')
        try:
            await api.pod_remove_task(pod_id=this_pod_id,
                                      remove_vms=removal_type)
            Summary = Summary + f'\n' + f'  {this_pod_id}: OK'
            print(f'{this_pod_id}: OK')
        except Exception as err:
            Summary = Summary + f'  {this_pod_id}: {sys.exc_info()[0]}' + '\n'
            print(f'Exception: {err}')
            print(f'{this_pod_id}:{sys.exc_info()[0]}')


async def main():
    global Quiet
    global Summary

    parser = argparse.ArgumentParser(description='Delete NDG Netlab Pods')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument('-offline_only',
                        action='store_const',
                        const=True,
                        help='delete only offline pods')
    parser.add_argument('-force',
                        action='store_const',
                        const=True)
    parser.add_argument('-q',
                        action='store_const',
                        const=True)
    parser.add_argument("-r",
                        "--removal_type",
                        action="store",
                        choices=tuple(t.name.lower() for t in RemoveVMS),
                        default=RemoveVMS.NONE.name.lower())
    parser.add_argument('podexprs',
                        help='regular expressions for names of pods to remove',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()
    removal_type = RemoveVMS[args.removal_type.upper()]
    Quiet = args.q

    # Check if any arguments are provided
    if not args.podexprs:
        print('No pods specified', file=sys.stderr)
        sys.exit(1)

    async with NetlabClient() as api:
        all_pods = await api.pod_list()

        # Filter out offline pods if cmd-line argument provided
        if args.offline_only:
            all_pods = list(filter(lambda x:
                                   x['pod_current_state'].name == 'OFFLINE',
                                   all_pods))

        # Get ids and names of pods to be deleted
        pod_indices = []
        for expr in args.podexprs:
            prog = re.compile(expr)
            this_index = \
                list(filter(lambda x: x is not None,
                            list(map(lambda x, y:
                                     y if prog.match(x['pod_name'])
                                     else None,
                                     all_pods,
                                     range(len(all_pods))))))
            pod_indices += this_index
        pod_names = [all_pods[x]['pod_name'] for x in pod_indices]
        pod_ids = [all_pods[x]['pod_id'] for x in pod_indices]

        # Verify pods to delete
        if not args.force:
            print('Pods to be deleted')
        for name in pod_names:
            print('  '+name)
        print('Removal type is '+args.removal_type)
        yes_no = input("Do you want to remove all these pods (y/n)? ")
        if yes_no[0].lower() != 'y':
            sys.exit(2)

        # Offline the pods to be deleted
        pod_dict = {}
        for pod_id in pod_ids:
            try:
                props = await api.pod_get(pod_id=pod_id,
                                          properties='remote_pc')
                state_result = \
                    await api.pod_state_change(pod_id=pod_id,
                                               state=PodState.OFFLINE)
                vh_id = props['remote_pc'][0]['vh_id']
                try:
                    pod_dict[vh_id].append(pod_id)
                except Exception:
                    pod_dict[vh_id] = [pod_id]
            except Exception as err:
                print(f'Pod {pod_id}: Exception - [{err}] [{state_result}]')

        if args.n:
            print(f'Would be removing:{pod_dict}')
            return

        # Delete pods in parallel tasks, one task per vm_host
        tasks = []
        for vh_id in pod_dict.keys():
            print(f'appending {pod_dict[vh_id]}')
            tasks.append(asyncio.create_task(delete_pods(api,
                                                         pod_dict[vh_id],
                                                         removal_type)))
        await asyncio.gather(*tasks, return_exceptions=True)

    print(Summary)

if __name__ == "__main__":
    asyncio.run(main())
