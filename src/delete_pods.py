#! /usr/bin/env python3
'''
delete_pods.py

Delete NDG netlab pods.

positional arguments:
  podexprs              regular expressions describing names of pods to remove

optional arguments:
  -h, --help            show this help message and exit
  -n                    dry run
  -r {none,local,datacenter,disk}, --removal_type {none,local,datacenter,disk}
'''
import argparse
import enum
import sys
import os
import subprocess
import datetime
import re
from multiprocessing import Pool
import random

from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory

Global_results = []

## Sorry to ask this.
# Need to change this to be dynamically determined
NUM_VMS = 4

def delete_pod(api, this_pod_id, this_pod_name, remove_vms_arg):
    result = api.pod_state_change(pod_id=this_pod_id, state = "OFFLINE")
    try:
        result = api.pod_remove_task(pod_id = this_pod_id,
                                     remove_vms = remove_vms_arg);
        return 'Pod ' + str(this_pod_id) + ': OK'
    except:
        return 'Pod ' + str(this_pod_id) + ':' + str(sys.exc_info()[0])


def main():
    parser = argparse.ArgumentParser(description='Delete NDG Netlab Pods')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument('-force',
                        action='store_const',
                        const=True)
    parser.add_argument("-r",
                        "--removal_type", 
                        action="store",
                        choices=tuple(t.name.lower() for t in RemoveVMS),
                        default=RemoveVMS.NONE.name.lower())
    parser.add_argument('podexprs',
                        help='regular expressions describing names of pods to remove',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()
    removal_type = RemoveVMS[args.removal_type.upper()]

    # Check if any arguments are provided
    if not args.podexprs:
        print('No pods specified',file=sys.stderr)
        sys.exit(1)

    # Identify the pod names matching the regular expressions
    api = Client()
    all_pods = api.pod_list()
    pod_indices=[]
    for expr in args.podexprs:
        prog = re.compile(expr)
        this_index = list(filter(lambda x: x != None,
                                 list(map(lambda x, y: y if prog.match(x['pod_name']) else None,
                                          all_pods,
                                          range(len(all_pods))))))
        pod_indices += this_index

    pod_names = [all_pods[x]['pod_name'] for x in pod_indices]
    pod_ids = [all_pods[x]['pod_id'] for x in pod_indices]

    # Verify pod deletion

    if not args.force:
        print('Pods to be deleted')
        for name in pod_names:
            print('  '+name)
        print('Removal type is '+args.removal_type)
        yes_no = input("Do you want to remove all these pods (y/n)? ")
        if yes_no[0].lower() != 'y':
            sys.exit(2)

    # First offline all the pods
    if len(pod_indices) == 1:
        print('Deleting' + str(pod_ids[0]) + ':' + pod_names[0])
        delete_pod(api, pod_ids[0], pod_names[0], removal_type)
    else:
        sub_procs = []
        interpreter_path = sys.executable;
        script_path = os.path.realpath(__file__)
        for index in range(len(pod_indices)):
            if args.n:
                print('Deleting ' + str(pod_ids[index]) + ':' + pod_names[index])
            else:
                cmd_args = [interpreter_path, script_path,
                            '--removal_type', args.removal_type,
                            '-force', pod_names[index]]

                print(cmd_args)
                sub_procs.append(subprocess.Popen(cmd_args))
        list(map(lambda x: x.wait(timeout=100), sub_procs))


if __name__ == "__main__":
   main()
