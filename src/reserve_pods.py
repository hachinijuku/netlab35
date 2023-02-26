#! /usr/bin/env python3
"""
reserve_pods.py

usage: reserve_pods.py [-h] [-n]
          [--start "[MM/DD/YYYY ]HH:MM"]
          --end "[MM/DD/YYYY ]HH:MM"
          --class_spec <partial (class name>|<cls_id>)
          --ex_name <exercise_name>
          

Identifies pods based on class specification and exercise name.
Attempts to reserve one for each team in the class
during time period specified.

Flags
          -h : print help message
          -n : dry run (don't make the reservations)
Arguments         
       start : start (date and) time (assumed to be now if omitted)
         end : end (date and) time
  class_spec : either a cls_id (number)
               or a string that uniquely matches a class name
     ex_name : string that uniquely matches an exercise in the class
      
"""

import argparse
import enum
import sys
import random

import datetime
from datetime import timedelta, datetime
import re

from netlab.sync_client import SyncClient
from netlab.enums import ReservationType

TEAMS=list(map(chr,range(ord('A'),ord('Z')+1)))
WILSON_ACC_ID = 100162
def main():
    parser = argparse.ArgumentParser(description='Reserve NDG pods for teams in a class')
    parser.add_argument('-n',
                        action='store_true',
                        help="dry run--do exerything but reserve the pods.")
    parser.add_argument('--start', help='start time in form "[MM/DD/YYYY] HH:MM"')
    parser.add_argument('--end', help='end time', required=True)
    parser.add_argument('--class_spec', help='cls_id or (partial) name of class to schedule for', required=True)
    parser.add_argument('--ex_name', help='exercise name', required=True)
    #parser.add_argument('--ex_id', help='exercise id', required=True)

    args = parser.parse_args()
    api = SyncClient()

    # 1. Try to match class name and bail if impossible with
    # message listing classes and their cls_ids

    this_cls_id = None
    if args.class_spec.isnumeric():
        this_cls_id = int(args.class_spec)

        # verify class exists by attempting a class_get
        api.class_get(cls_id=this_cls_id)
    else:
        class_list = api.class_list(properties=['cls_name', 'cls_id'])
        matches = [match for match in class_list if args.class_spec in match["cls_name"]]
        print(matches)
        if len(matches) == 1:
            this_cls_id = matches[0]["cls_id"]
    assert this_cls_id !=  None, f'Class "{args.class_spec}" not found'
    

    # 2. Get this_ex_id from args.ex_name and grab this_pt_id from exercise

    exlist = api.lab_exercise_list(properties=['ex_id','ex_name','ex_pt_id'])
    exes = list(filter(lambda x:True if args.ex_name in x['ex_name'] else False, exlist))
    assert len(exes) == 1, 'Too many matching Lab Names: {exes}'
    this_ex_id = exes[0]['ex_id']
    this_pt_id = exes[0]['ex_pt_id']
    print(f'this_pt_id is {this_pt_id}');

    # 3. Get pod start and end times
    
    current_time = datetime.now()
    tt = datetime.timetuple(current_time)
    if args.start != None:
        if "/" in args.start:
            start = datetime.strptime(args.start, '%m/%d/%Y %H:%M')
        else:
            start = datetime.strptime(str(tt.tm_mon) + '/' + str(tt.tm_mday) + '/' + str(tt.tm_year) + ' ' + args.start,'%m/%d/%Y %H:%M')
    else:
        start = datetime.now()


    if args.end and '/' in args.end:
        end = datetime.strptime(args.end,'%m/%d/%Y %H:%M')
    else:
        end = datetime.strptime(str(tt.tm_mon) + '/' + str(tt.tm_mday) + '/' + str(tt.tm_year) + ' ' + args.end,'%m/%d/%Y %H:%M')

    # 4. Get team info from class roster
    class_team_list = api.class_roster_list(cls_id=this_cls_id)
    class_team_list = list(map(lambda x: x["ros_team"], class_team_list))
    all_teams = {}
    for x in class_team_list:
        all_teams[x] = 1
    class_team_list = list(all_teams.keys())
    class_team_list.sort()
       
    # 5. Get list of VMs with pod type this_pt_id
    all_pods = api.pod_list()
    pods  = list(filter(lambda x: this_pt_id == x['pt_id'], all_pods))

    print(f'pods: {pods}')

    pod_names = [x['pod_name'] for x in pods]
    pod_pids = [x['pod_id'] for x in pods]

    print('Pods to reserve from ' + str(start) + ' to ' + str(end) + ':')

    # 7. Verify intent to make this reservation
    for name in pod_names:
        print('  '+name)

    yes_no = input('Do you want to reserve these pods from ' + str(start) + ' to ' + str(end) + ' (y/n)? ')

    if args.n:
        print('Dry run--no pods reserved')
        exit(0)
        
    if yes_no[0].lower() == 'y':
        # 8. Reserve Pods
        assert len(pod_pids) >= len(class_team_list), "Not enough pods!"

        pod_index = 0
        team_index = 0
        while team_index < len(class_team_list):
            if args.start == None:
                #print ('Doing none case')
                #print(f'reserving {pod_pids[pod_index]} for {team}')
                result = api.reservation_make(type=ReservationType.TEAM,
                                              cls_id=this_cls_id,
                                              team=TEAMS[team_index],
                                              ex_id=this_ex_id,
                                              pod_id=pod_pids[pod_index],
                                              end_time=end,
                                              acc_id=WILSON_ACC_ID)

            else:
                try:
                    #print(f'reserving {pod_pids[pod_index]} for {team}')
                    result = api.reservation_make(type=ReservationType.TEAM,
                                                  cls_id=this_cls_id,
                                                  team=TEAMS[team_index],
                                                  ex_id=this_ex_id,
                                                  pod_id=pod_pids[pod_index],
                                                  end_time=end,
                                                  start_time=start,
                                                  acc_id=WILSON_ACC_ID) 
                except BaseException as err:
                    print('Problem reserving pod ' + str(pod_names[pod_index]) + ' -- pod skipped')
                    print(format(err))
                    pod_index += 1
                    continue
            pod_index += 1
            team_index += 1
            
if __name__ == "__main__":
   main()
