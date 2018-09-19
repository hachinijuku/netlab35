#! /usr/bin/env python3

import argparse
import enum
import sys
import exrex

import datetime
import re

CISE_COM_ID = 1

from netlab.client import Client

def main():

    si = None

    parser = argparse.ArgumentParser(description='Create Netlab account block')
    parser.add_argument('acct_prefix',
                        help='Prefix for numbered account numbers')
    parser.add_argument('num_accts',
                        help='Number of accounts to create')
    parser.add_argument('passwd',
                        help='Initial password for account')

    args = parser.parse_args()



    # Get list of all VMs.
    api = Client()

    # List class CLIs

    class_list = api.class_list(properties=['cls_name','cls_id'])
    cls_id = input('Enter class ID\n' + map(lambda x: x[0] + str(x[1]) + '\n'))
    for suffix in range(1,args.num_accts + 1):
        api.class_add(com_id = CISE_COM_ID,
                      acc_user_id = args.acct_prefix + str(suffix),
                      acc_password = args.passwd,
                      acc_pw_change = TRUE)


if __name__ == "__main__":
   main()
