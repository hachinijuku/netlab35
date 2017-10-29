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

from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory

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
    print('Pods to be deleted')
    for name in pod_names:
        print('  '+name)

    print('Removal type is '+args.removal_type)
    yes_no = input("Do you want to remove all these pods (y/n)? ")
    if yes_no[0].lower() != 'y':
        sys.exit(2)

    # First offline all the pods
    for index in range(len(pod_indices)):
        if (args.n):
            print('Offlining '+str(pod_ids[index])+':'+pod_names[index])
        else:
            try:
                result = api.pod_state_change(pod_id=pod_ids[index],
                                                     state="OFFLINE")
                print("Pod Offlined:"+str(datetime.datetime.now())+':'+pod_names[index]+'(' + str(pod_ids[index]) + '):'+result)
            except:
                print("Couldn't offline pod " + pod_names[index])

    # Organize pods by vmhost
    vm_pods = {}
    for index in range(len(pod_indices)):
        property = api.pod_get(pod_id = pod_ids[index], properties = 'remote_pc');
        vm_index = api.pod_pc_get(pod_id = all_pods[0]['pod_id'],pl_index = 1)['vh_id']
        pod_vms[index] = vm_index
        try:
            vm_pods[vm_index].append(index)
        except:
            vm_pods[vm_index] = [index]

    for key in vm_pods:
        print('vm '+ str(key))
        for pod_index in vm_pods[key]:
            print(pod_name[pod_index])

    for index in range(len(pod_indices)):
        try:
            result = api.pod_remove_task(pod_id = pod_ids[index], remove_vms = removal_type);
        except:
            result = {'status':'FAILED'}
        print(pod_names[index] + '(' + str(pod_ids[index]) + '):' + result['status'])

if __name__ == "__main__":
   main()
