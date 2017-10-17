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
import datetime
import re

from multiprocessing.pool import ThreadPool
from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory

Global_api = None
Global_results = []

def log_result(result):
    Global_results.append(result)

def pod_deleter(this_pod_pid, this_pod_name, this_remove_type):
    result = Global_api.pod_state_change(pod_id=this_pod_pid,
                                  remove_type=this_remove_type)
    print('Removing '+str(this_pod_pid)+':'+this_pod_name)
    

def main():
    parser = argparse.ArgumentParser(description='Delete NDG Netlab Pods')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    parser.add_argument("-r",
                        "--removal_type", 
                        action="store",
                        choices=tuple(t.name.lower() for t in RemoveVMS),
                        default=RemoveVMS.NONE.name.lower(),
                        dest="remove_type")
    parser.add_argument('podexprs',
                        help='regular expressions describing names of pods to remove',
                        nargs=argparse.REMAINDER)
    args = parser.parse_args()
    remove_type = RemoveVMS[args.remove_type.upper()]

    # Check if any arguments are provided
    if not args.podexprs:
        print('No pods specified',file=sys.stderr)
        sys.exit(1)

    # Identify the pod names matching the regular expressions
    Global_api = Client()
    all_pods = Global_api.pod_list()
    pod_indices=[]
    for expr in args.podexprs:
        print('expr is '+expr)
        prog = re.compile(expr)
        pod_indices = pod_indices + list(filter(lambda x: x != None,
                                                list(map(lambda x, y: y if prog.match(x['pod_name']) else None,
                                                         all_pods,
                                                         range(len(all_pods))))))
    pod_names = [all_pods[x]['pod_name'] for x in pod_indices]
    pod_pids = [all_pods[x]['pod_id'] for x in pod_indices]

    # Verify pod deletion
    print('Pods to be deleted')
    for name in pod_names:
        print('  '+name)

    print('Removal type is '+args.remove_type)
    yes_no = input("Do you want to remove all these pods (y/n)? ")
    if yes_no[0].lower() != 'y':
        sys.exit(2)

    print('Pod_indices')
    for i in pod_indices:
        print(' ' + str(i))

    # First offline all the pods
    for index in range(len(pod_indices)):
        print('loop: ' + str(index))
        if (args.n):
            print('Offlining '+str(pod_pids[index])+':'+pod_names[index])
        else:
            try:
                result = Global_api.pod_state_change(pod_id=pod_pids[index],
                                                     state="OFFLINE")
                print("Pod Offlined:"+str(datetime.datetime.now())+':'+pod_names[index]+':'+result)
            except:
                print("Couldn't offline pod " + pod_names[index])

    # Then delete them.
    for index in range(len(pod_indices)):
        result = Global_api.pod_remove_task(pod_id=pod_indices[index],
                                            remove_vms=remove_type)
        print('Removing '+str(this_pod_pid)+':'+this_pod_name)
        
    for index in range(len(Global_results)):
        print('  Pod Removal Status:' + pod_names[index] + ':' + Global_results[index]['status'])


if __name__ == "__main__":
   main()
