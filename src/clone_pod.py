#! /usr/bin/env python3

"""
clone_pods.py

Run with --help to find calling sequence. This discusses the philosophy.

If called without the --vm_host parameter set (the normal method),
this script clones a master pod and distributes the clones evenly
across a set of hosts in a datacenter given by environment variable

  NETLAB_VDC

To get the desired behavior, it determines the number of clones and
available pod numbers and shuffles them across datacenter hosts.
Then it calls itself recursively using the --vm_host parameter to
allocate pods one at a time to specific hosts.


MIT License

Copyright (c) 2020 Joseph N. Wilson

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
from typing import List, Any, Tuple, Union

from netlab.client import Client
from netlab.enums import PodCategory
import sys
import os
import subprocess
import time


Debug = None

def get_unused_pid(id_list, hwm, index):
    num_in_list = len(id_list)
    if index < num_in_list:
        return id_list[index]
    else:
        return index - num_in_list + hwm + 1

def do_clone(api, src_pid, pids_to_assign, pod_prefix, host_id, do_this_clone, datastore):
    time.sleep(5)
    if not pids_to_assign:
        return []
    elif do_this_clone:
        clone_pod_name = pod_prefix + str(pids_to_assign[0])
        if Debug:
            print(f'calling api.pod_clone_task({src_pid},\n\t{pids_to_assign}')
        try:
            result = api.pod_clone_task(source_pod_id=src_pid,
                                        clone_pod_id=pids_to_assign[0],
                                        clone_pod_name=clone_pod_name,
                                        pc_clone_specs={'clone_datastore': datastore,
                                                        'clone_role':'NORMAL',
                                                        'clone_vh_id':host_id})
            print(f'{clone_pod_name}({pids_to_assign[0]}):{result["status"]}')
        except Exception as err:
            print(f'clone_pod_id={pids_to_assign[0]}\n' +
                  f'clone_pod_name={clone_pod_name}\n' +
                  f'  pc clone_datastore={datastore}\n' +
                  f'  pc clone_vn_id={host_id}',
                  file=sys.stderr)
            print(f'Clone failed:{str(err)}', file=sys.stderr)
            sys.exit(1)
        return []
    else:
        if Debug:
            print(f'pids to assign {pids_to_assign}')
        sub_procs = []
        interpreter_path = sys.executable
        script_path = os.path.realpath(__file__)
        for this_pid in pids_to_assign:
            args = [interpreter_path, script_path,
                    '--src_pid', src_pid,
                    '--num_clones', '1',
                    '--pod_prefix', pod_prefix,
                    '--pid', str(this_pid),
                    '--vm_host', str(host_id)]
            sub_procs.append(subprocess.Popen(args))
        return sub_procs

def main():
    global Debug
    
    parser = argparse.ArgumentParser(description='Remove VMs from vcenter host')
    parser.add_argument('--src_pid',
                        required=True,
                        help='source pod id')
    #    parser.add_argument('--pod_rng', required=True, help='cloned pod id range')
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
    parser.add_argument('--vm_host',
                        required=False,
                        type=int,
                        default=-1)
    parser.add_argument('--pid',
                        required=False,
                        type=int,
                        default=0)
    parser.add_argument('-debug',
                        action='store_const',
                        const=True,
                        help='debug mode (kind of verbose)')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    args = parser.parse_args()
    api = Client()
    num_clones = int(args.num_clones)
    Debug = args.debug
     

    datacenter_id = api.vm_datacenter_find(vdc_name=os.environ['NETLAB_VDC'])
    vh_ids = list(map(lambda x: x['vh_id'], api.vm_host_list(vdc_id=datacenter_id)))

   
    # Check to see if we're doing just 1 pod
    if args.vm_host != -1:
        assert(num_clones == 1)
        assert(args.pid != 0)
        do_clone(api, args.src_pid, [args.pid], args.pod_prefix, args.vm_host, True, args.clone_datastore)
    else:
        # find available pods
        pod_ids = list(map(lambda x: x["pod_id"], api.pod_list()))
        pid_hwm = max(pod_ids)

        unused_low_pods = list(set(range(1, pid_hwm)) - set(pod_ids))

        # identify available hosts for VMs
        num_hosts = len(vh_ids)

        src_pod_cat = api.pod_get(pod_id=args.src_pid, properties='pod_cat')['pod_cat']
        if src_pod_cat != PodCategory.MASTER_VM:
            print('Sorry. We will not copy from a non-Master pod.')
            sys.exit()

        # Divvy up pods (or at least args to create them) to VM hosts in round robin fashion.
        #
        # The theory is students will grab them in order and this will do
        # a static load balancing based on expected human behavior
        pids_to_assign = list(map(lambda x: get_unused_pid(unused_low_pods, pid_hwm, x),
                                  range(num_clones)))

        if Debug:
            print(f'{vh_ids}, {len(vh_ids)}')
            print(f'{pids_to_assign}')
        #return
        
        pid_assignment_dict = {vh_ids[i]:pids_to_assign[i:len(pids_to_assign):len(vh_ids)] for i in range(0,len(vh_ids))}
        if Debug:
            print(f'{args.src_pid} {args.pod_prefix} {vh_ids}{pid_assignment_dict} {num_hosts}');
        #return
        pool_args: List[Tuple[Client, Any, List[Union[int, Any]], Any, int, bool]] = \
            [(api,
              args.src_pid,
              pid_assignment_dict[vh_id],
              args.pod_prefix,
              vh_id,
              False,
              args.clone_datastore)
             for vh_id in vh_ids]
        sub_procs = list(map(lambda x: do_clone(*x), pool_args))
        list(map(lambda x: [y.wait(timeout=100) for y in x], sub_procs))


if __name__ == "__main__":
    main()
