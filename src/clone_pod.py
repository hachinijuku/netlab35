#! /usr/bin/env python3

import argparse
from typing import List, Any, Tuple, Union

from netlab.client import Client
from netlab.enums import PodCategory
import sys
import os
import subprocess

# Site specific information
DATASTORE = 'nfs-vm2'
VHOST_IDS = [1, 2, 3, 4]


def get_unused_pid(id_list, hwm, index):
    num_in_list = len(id_list)
    if index < num_in_list:
        return id_list[index]
    else:
        return index - num_in_list + hwm + 1


def do_clone(api, src_pid, pids_to_assign, pod_prefix, host_id, do_this_clone):
    if not pids_to_assign:
        return []
    elif do_this_clone:
        clone_pod_name = pod_prefix + str(pids_to_assign[0])
        result = api.pod_clone_task(source_pod_id=src_pid,
                                    clone_pod_id=pids_to_assign[0],
                                    clone_pod_name=clone_pod_name,
                                    pc_clone_specs={'clone_datastore': DATASTORE,
                                                    'clone_vh_id': host_id})
        #            except:
        #                result = {'status':'FAILED'}
        print(clone_pod_name + '(' + str(pids_to_assign[0]) + '):' + result['status'])
        return []
    else:
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
                        default=DATASTORE)
    parser.add_argument('--vm_host',
                        required=False,
                        type=int,
                        default=-1)
    parser.add_argument('--pid',
                        required=False,
                        type=int,
                        default=0)
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    args = parser.parse_args()
    api = Client()
    num_clones = int(args.num_clones)

    # Check to see if we're doing just 1 pod
    if args.vm_host != -1:
        assert(num_clones == 1)
        assert(args.pid != 0)
        do_clone(api, args.src_pid, [args.pid], args.pod_prefix, args.vm_host, True)
    else:
        # find available pods
        pod_ids = list(map(lambda x: x["pod_id"], api.pod_list()))
        pid_hwm = max(pod_ids)
        unused_low_pods = list(set(range(1, pid_hwm)) - set(pod_ids))

        # identify available hosts for VMs
        num_hosts = len(VHOST_IDS)

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
        pid_assignment_lists = [pids_to_assign[x::num_hosts] for x in range(num_hosts)]
        pool_args: List[Tuple[Client, Any, List[Union[int, Any]], Any, int, bool]] = \
            [(api,
              args.src_pid,
              pid_assignment_lists[x],
              args.pod_prefix,
              VHOST_IDS[x],
              False)
            for x in range(num_hosts)]
        sub_procs = list(map(lambda x: do_clone(*x), pool_args))
        list(map(lambda x: [y.wait(timeout=100) for y in x], sub_procs))


if __name__ == "__main__":
    main()
