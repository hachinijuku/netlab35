#! /usr/bin/env python3

import argparse
import datetime
import math

from netlab.client import Client
from netlab.enums import PodCategory

DATASTORE='nfs-vm2'
VHOST_IDS=[1, 2, 3, 4]

def get_unused_pid(id_list,hwm,index):
    num_in_list = len(id_list)
    if index < num_in_list:
        return id_list[index]
    else:
        return index - num_in_list + hwm + 1

def main():

    si = None

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
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')



    args = parser.parse_args()
    api = Client()

    pod_ids = list(map(lambda x: x["pod_id"], api.pod_list()))
    pid_hwm = max(pod_ids)
    unused_pods = list(set(range(1,pid_hwm)) - set(pod_ids))

    

    num_hosts = len(VHOST_IDS)
    num_clones = int(args.num_clones)
    # determine number of clones to allocate to each vhost
    min_clones = math.floor(num_clones/num_hosts)
    extra_clones = num_clones - min_clones*num_hosts
    pc_count = api.pod_get(pod_id=args.src_pid, properties='remote_pc_count')['remote_pc_count']

    src_pod_cat = api.pod_get(pod_id=args.src_pid, properties='pod_cat')['pod_cat']
    if src_pod_cat != PodCategory.MASTER_VM:
        print('Sorry. We will not copy from a non-Master pod.')
        sys.exit()

    current_pod_ordinal = 0
    for host_num in range(num_hosts):

        clone_specs = []

        for _ in range(pc_count):
            clone_specs.append({"clone_datastore":DATASTORE,
                                "clone_vh_id":VHOST_IDS[host_num]})
        if (extra_clones > 0):
            num_on_this_vhost = min_clones + 1
            extra_clones -= 1
        else:
            num_on_this_vhost = min_clones
        for clone_num in range(num_on_this_vhost):
            this_pid = get_unused_pid(unused_pods, pid_hwm, current_pod_ordinal)
            current_pod_ordinal += 1
            if (args.n):
                print('clone('+args.src_pid+', '+str(this_pid+','+args.pod_prefix+str(this_pid)+','+clone_specs[0]["clone_datastore"]+','+str(clone_specs[0]["clone_vh_id"])+')'))
            else:
                print("Attempting to create clone. PID="+str(this_pid))
                clone_pod_name = args.pod_prefix+str(this_pid)
                output = \
                    api.pod_clone_task(source_pod_id=args.src_pid,
                                       clone_pod_id=this_pid,
                                       clone_pod_name=clone_pod_name,
                                       pc_clone_specs=clone_specs)
                print("Clone result:"+str(datetime.datetime.now())+':'+clone_pod_name +':' + str(output['status']))



if __name__ == "__main__":
   main()
