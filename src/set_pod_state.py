#! /usr/bin/env python3

import argparse
import enum
import sys

import datetime
import re

from netlab.client import Client
from netlab.enums import PodState
def main():

    si = None

    parser = argparse.ArgumentParser(description='Online a number of NDG Pods')
    parser.add_argument('podexpr', help='regular expression describing names of pods to modify')
    parser.add_argument("--state", 
                        action="store",
                        choices=tuple(t.name.lower() for t in PodState),
                        default=PodState.ONLINE.name.lower(),
                        dest="state")
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='dry run')
    args = parser.parse_args()


    args.state = PodState[args.state.upper()]
    

    prog = re.compile(args.podexpr)

    # Get list of all VMs.
    api = Client()
    all_pods = api.pod_list()

    pod_indices = list(filter(lambda x: x != None,
                              list(map(lambda x, y: y if prog.match(x['pod_name']) else None,
                                       all_pods,
                                       range(len(all_pods))))))
    pod_names = [all_pods[x]['pod_name'] for x in pod_indices]
    pod_pids = [all_pods[x]['pod_id'] for x in pod_indices]

    print('Pods to set to ' + str(args.state))
    for name in pod_names:
        print('  '+name)

    yes_no = input("Do you want to put set these pods to " + str(args.state) + " (y/n)? ")
    if yes_no[0].lower() == 'y':

        for index in range(len(pod_indices)):
            if (args.n):
                print('Setting State to '+ str(args.state) +':'+str(pod_pids[index])+':'+pod_names[index])
            else:
                result = api.pod_state_change(pod_id=pod_pids[index],
                                          state=args.state)
                print("Pod state "+str(args.state)+':'+str(datetime.datetime.now())+':'+pod_names[index]+':'+result)



if __name__ == "__main__":
   main()
