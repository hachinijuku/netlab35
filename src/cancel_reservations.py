#! /usr/bin/env python3

import argparse
import enum
import sys

import datetime
from datetime import timedelta, datetime
import re

from netlab.client import Client
from netlab.enums import ReservationType

def main():

    si = None

    parser = argparse.ArgumentParser(description='Online a number of NDG Pods')
    parser.add_argument('res_ids',
                        help='reservation ids to cancel',
                        nargs= argparse.REMAINDER)

    args = parser.parse_args()

    # Get list of all VMs.
    api = Client()

    for x in args.res_ids:
        print(x)
    yes_no = input('Do you want to cancel these reservations (y/n)? ')
    if yes_no[0].lower() == 'y':

        for res_id in args.res_ids:
            print('Argument is [' + str(int(res_id)) + ']')
            result = api.reservation_cancel(res_id = int(res_id))
            print('Cancellation of reservation ' + str(res_id) + ':'+str(datetime.now())+':'+result)
            
if __name__ == "__main__":
   main()
