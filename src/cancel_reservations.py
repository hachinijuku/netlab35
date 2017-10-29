#! /usr/bin/env python3

import argparse
import enum
import sys
import exrex

import datetime
import re

from netlab.client import Client
from netlab.enums import PodState
def main():

    si = None

    parser = argparse.ArgumentParser(description='Cancel a number of NDG Reservations')
    parser.add_argument('res_ids',
                        help='reservation ids of pods to modify')

    args = parser.parse_args()

    if not args.res_ids:
        print('No reservation IDs specified', file=sys.stderr)
        sys.exit(1)

    args.res_ids = exrex.generate(args.res_ids)

    # Get list of all VMs.
    api = Client()

    for res_id in args.res_ids:
        print('  '+res_id)

    yes_no = input("Do you want to cancel these reservations? (y/n)? ")
    if yes_no[0].lower() == 'y':

        for res_id in args.res_ids:
            result = api.reservation_cancel(res_id=int(res_id))
            print('Cancellation Result:'+str(datetime.datetime.now())+':'+res_id+':'+result)



if __name__ == "__main__":
   main()
