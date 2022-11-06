#! /usr/bin/env python3
'''
set_pod_state.py

usage: set_pod_state.py [-h] [--state {online,offline,resume}] [-n] ...

Online a number of NDG Pods

positional arguments:
  podexprs              regular expression describing names of pods to modify

options:
  -h, --help            show this help message and exit
  --state {online,offline,resume}
  -n                    dry run

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
import enum
import sys

import datetime
import re
import asyncio
from netlab.async_client import NetlabClient
from netlab.enums import PodState


##
#
# change_one_pod_state
#
# api: netlab client connection
# pod_id: id pod to change
# pod_name: name of pod to change
# state: PodState to change to
#
async def change_one_pod_state(api,
                               pod_id,
                               pod_name,
                               state):
    result = await api.pod_state_change(pod_id=pod_id,
                                        state=state)
    print(f'{pod_name} state {state} {datetime.datetime.now()} {result}')


async def main():
    parser = argparse.ArgumentParser(description='Online a number of NDG Pods')
    parser.add_argument("--state",
                        action="store",
                        choices=tuple(t.name.lower() for t in PodState),
                        default=PodState.ONLINE.name.lower(),
                        dest="state")
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument('podexprs',
                        help='regular expression for names of pods to set',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()

    args.state = PodState[args.state.upper()]

    # Get list of all VMs.
    async with NetlabClient() as api:
        all_pods = await api.pod_list()
        pod_indices = []
        for expr in args.podexprs:
            prog = re.compile(expr)
            pod_indices = pod_indices + \
                list(filter(lambda x: x is not None,
                            list(map(lambda x, y: y
                                     if prog.match(x['pod_name'])
                                     else None,
                                     all_pods,
                                     range(len(all_pods))))))
        pod_names = [all_pods[x]['pod_name'] for x in pod_indices]
        pod_pids = [all_pods[x]['pod_id'] for x in pod_indices]

        # Verify intent to change pod state
        print('Pods to set to ' + str(args.state))
        for name in pod_names:
            print('  '+name)
        yes_no = input(f'Do you want to set these pods to {args.state}'
                       ' (y/n)?')

        # Create and await tasks to change pod states
        if yes_no[0].lower() == 'y':
            tasks = []
            for index in range(len(pod_indices)):
                if (args.n):
                    print(f'Setting State to {args.state}'
                          f'{pod_pids[index]}:{pod_names[index]}')
                else:
                    tasks.append(asyncio.create_task(
                        change_one_pod_state(api,
                                             pod_pids[index],
                                             pod_names[index],
                                             args.state)))
                await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
