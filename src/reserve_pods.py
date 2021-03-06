#! /usr/bin/env python3

import argparse
import enum
import sys

import datetime
import pytz
from datetime import timedelta, datetime
import re

from netlab.client import Client
from netlab.enums import ReservationType

WILSON_ACC_ID = 100162
def main():

    si = None

    parser = argparse.ArgumentParser(description='Online a number of NDG Pods')
    parser.add_argument('podexpr', help='regular expression describing names of pods to modify')
    parser.add_argument('--start', help='start time in form "[MM/DD/YYYY] HH:MM"')
    parser.add_argument('--end', help='end time', required=True)

    args = parser.parse_args()

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

    print('Pods to reserve from ' + str(start) + ' to ' + str(end) + ':')



    for name in pod_names:
        print('  '+name)

    yes_no = input('Do you want to reserve these pods from ' + str(start) + ' to ' + str(end) + ' (y/n)? ')
    if yes_no[0].lower() == 'y':

#        localtz = pytz.timezone("America/New_York")
#        start = start.astimezone(pytz.utc)
#        end = end.astimezone(pytz.utc)

        for index in range(len(pod_indices)):
            if args.start == None:
                print ('Doing none case')
                result = api.reservation_make(type=ReservationType.INSTRUCTOR,
                                              pod_id=pod_pids[index],
                                              end_time=end,
                                              acc_id=WILSON_ACC_ID)

            else:
                try:
                    result = api.reservation_make(type=ReservationType.INSTRUCTOR,
                                                  pod_id=pod_pids[index],
                                                  end_time=end,
                                                  start_time=start,
                                                  acc_id=WILSON_ACC_ID) 
                    print('Reservation of pod ' + str(pod_names[index]) + ':'+str(datetime.now())+':'+str(result['res_id']))
                except BaseException as err:
                    print('Problem reserving pod ' + str(pod_names[index]) + ' -- pod skipped')
                    print(format(err))


            
if __name__ == "__main__":
   main()
