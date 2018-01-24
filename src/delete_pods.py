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
from multiprocessing import Pool
import random

from netlab.client import Client
from netlab.enums import RemoveVMS
from netlab.enums import PodCategory

Global_results = []

## Sorry to ask this.
# Need to change this to be dynamically determined
NUM_VMS = 4

def printer_func(this_pod_id):
    return "stand-in for removal of pod" + str(this_pod_id)

def remove_func(this_pod_id, remove_vms_arg, api):
    try:
        print('starting removal of %d' % this_pod_id)
        result = api.pod_remove_task(pod_id = this_pod_id,
                                     remove_vms = remove_vms_arg);
        return 'Pod ' + str(this_pod_id) + ': OK'
    except:
        #result = result = {'status':'Failed'}
        return 'Pod ' + str(this_pod_id) + ':' + str(sys.exc_info()[0])

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
    pod_vms = [None]*len(pod_ids)

    for index in range(len(pod_indices)):
        # print('this pod_id is ' + str(pod_ids[index]))
        this_pod_id = pod_ids[index]
        property = api.pod_get(pod_id = this_pod_id, properties = 'remote_pc');
        pod_pc = api.pod_pc_get(pod_id = this_pod_id, pl_index = 1)
        if 'vh_id' in pod_pc.keys():
            vm_index = pod_pc['vh_id']
        else:
            vm_index = random.uniform(1,NUM_VMS)
        # print('vm_index of ' + str(pod_names[index]) + ' is ' + str(vm_index))
        pod_vms[index] = vm_index
        try:
            vm_pods[vm_index-1].append(index)
            print("vm_pods[" + str(vm_index-1) + "] is now " + str(vm_pods[vm_index-1]))
        except:
            vm_pods[vm_index-1] = [index]
            print("vm_index is %d, appending %d.\n" % (vm_index,index))

    print("pod_vms: " + str(pod_vms))
    vm_pods = {k: v for k,v in vm_pods.items() if v}

    print("vm pods value: "+ str(vm_pods))
    for vm_num in vm_pods.keys():
        print("vm[" + str(vm_num) + "] has pods " + str(vm_pods[vm_num]))


    while vm_pods != {}:

        # pool = Pool(processes=len(vm_pods))
        # results = []

        # grab initial element from each pod vm list
        pod_ids_to_delete = list(map(lambda x:pod_ids[x],list(map(lambda x:x[0],vm_pods.values()))))

        #delete initial element from each pod vm list (and squeeze out empties)
        vm_pods = {k: vm_pods[k][1:] for k in vm_pods}
        vm_pods = {k: v for k,v in vm_pods.items() if v}

        map(lambda x:x.pop(0), vm_pods.values())

        # [pool.map_async(remove_func, (pod_id, removal_type, api), callback = lambda x: Global_results.append(x)) for pod_id in pod_ids_to_delete]
        # [pool.map_async(printer_func, (pod_id,), callback = lambda x: Global_results.append(x)) for pod_id in pod_ids_to_delete]
        for pod_id in pod_ids_to_delete:
            print(remove_func(pod_id, removal_type, api))

        # print('Starting pool for pods: ' + str(pod_ids_to_delete))
        # pool.close()
        # pool.join()
   
    # for result in Global_results:
    #     print(result)




if __name__ == "__main__":
   main()
