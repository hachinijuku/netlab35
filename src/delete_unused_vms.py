#! /usr/bin/env python3

import argparse
import enum
import sys
import inspect

import datetime
import re


from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory



def main():

    si = None

    parser = argparse.ArgumentParser(description='Delete a number of NDG Pods')
    parser.add_argument('vmexprs',
                        help='regular expressions describing names of vms to remove',
                        nargs=argparse.REMAINDER)
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
    


    api = Client()
    # print('\n'.join(list(map(str,inspect.getmembers(api,predicate=inspect.ismethod)))))
    all_vms = api.vm_inventory_list()

    unused_vms = list(filter(lambda x: x['pc_pod_id'] == None, all_vms))

    candidate_vm_names = [x['vm_name'] for x in unused_vms]
    

    vm_indices = []
    for expr in args.vmexprs:
        prog = re.compile(expr)
        print('prog expr is '+ expr)
        this_index = list(filter(lambda x: x != None,
                                 list(map(lambda x,y: y if prog.match(x) else None,
                                          candidate_vm_names,
                                          range(len(candidate_vm_names))))))
        vm_indices += this_index
    vm_names = [candidate_vm_names[x] for x in vm_indices]

    print('VMs to be deleted')
    for name in vm_names:
        print('  '+name)

    

    yes_no = input("Do you want to remove all these vms (y/n)? ")
    if yes_no[0].lower() == 'y':
        for x in vm_indices:
            #print('x is '+str(x)+'remove_type is'+args.remove_type)
            if args.remove_type == 'disk':
                api.vm_inventory_remove_disk_task(vm_id=unused_vms[x]['vm_id'])
            elif args.remove_type == 'datacenter':
                api.vm_inventory_remove_datacenter_task(vm_id=unused_vms[x]['vm_id'])
            elif args.remove_type == 'local':
                api.vm_inventory_remove_localvm_id=(unused_vms[x]['vm_id'])
            else:
                exit()

        #for x in range(len(unused_vms)):
        #    if (args.n):
        #        print('Offlining '+str(pod_pids[index])+':'+pod_names[index])
        #    else:
        #        result = api.pod_state_change(pod_id=pod_pids[index],
        #                                  state="OFFLINE")
        #        print("Pod Offlined:"+str(datetime.datetime.now())+':'+pod_names[index]+':'+result)

        #for index in range(len(pod_indices)):
        #    if (args.n):
        #        print('Removing '+str(pod_pids[index])+':'+pod_names[index])
        #    else:
        #        if (all_pods[pod_indices[index]]['pod_cat'] == PodCategory.MASTER_VM):
        #            args.remove_type = RemoveVMS["NONE"]
        #            print('Setting Remove Type to NONE for Master pod')
        #        result = api.pod_remove_task(pod_id=pod_pids[index],
        #                                     remove_vms=args.remove_type) 
        #        print('Pod Removed:'+str(datetime.datetime.now())+':'+pod_names[index] + ':'+result['status'])

        


if __name__ == "__main__":
   main()
