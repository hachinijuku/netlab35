#! /usr/bin/env python3

import argparse
import enum
import sys

import datetime
import re

from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory
def main():

    si = None

    parser = argparse.ArgumentParser(description='Delete a number of NDG Pods')
    parser.add_argument('podexpr', help='regular expression describing names of pods to remove')
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
    args = parser.parse_args()
    args.remove_type = RemoveVMS[args.remove_type.upper()]
    

    prog = re.compile(args.podexpr)

    api = Client()
    all_vms = api.vm_inventory_list()

    unused_vms = list(filter(lambda x: x['pc_pod_id'] != None, all_vms))

    vm_names = [x['vm_name'] for x in unused_vms]


    print('VMs to be deleted')
    for name in vm_names:
        print('  '+name)


    yes_no = input("Do you want to remove all these vms (y/n)? ")
    if yes_no[0].lower() == 'y':

        for x in range(len(unused_vms))
            if (args.n):
                print('Offlining '+str(pod_pids[index])+':'+pod_names[index])
            else:
                result = api.pod_state_change(pod_id=pod_pids[index],
                                          state="OFFLINE")
                print("Pod Offlined:"+str(datetime.datetime.now())+':'+pod_names[index]+':'+result)

        for index in range(len(pod_indices)):
            if (args.n):
                print('Removing '+str(pod_pids[index])+':'+pod_names[index])
            else:
                if (all_pods[pod_indices[index]]['pod_cat'] == PodCategory.MASTER_VM):
                    args.remove_type = RemoveVMS["NONE"]
                    print('Setting Remove Type to NONE for Master pod')
                result = api.pod_remove_task(pod_id=pod_pids[index],
                                             remove_vms=args.remove_type) 
                print('Pod Removed:'+str(datetime.datetime.now())+':'+pod_names[index] + ':'+result['status'])

        


if __name__ == "__main__":
   main()
