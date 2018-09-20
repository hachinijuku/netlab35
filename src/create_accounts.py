#! /usr/bin/env python3

import argparse

DEFAULT_COM_ID = 1

from netlab.client import Client
from netlab.enums import DateFormat, TimeFormat

def main():

    si = None

    parser = argparse.ArgumentParser(description='Create Netlab account block')
    parser.add_argument('--acct_prefix',
                        help='Prefix for numbered account numbers')
    parser.add_argument('--num_accts',
                        help='Number of accounts to create')
    parser.add_argument('-CSE235',
                        action='store_const',
                        const=True,
                        help='Give suffixes for CSE 235 seats')
    parser.add_argument('--passwd',
                        required=True,
                        help='Initial password for account')
    parser.add_argument('-n',
                        action='store_const',
                        const=True,
                        help='Dry run (no accounts are created')

    args = parser.parse_args()



    # Get list of all VMs.
    api = Client()

    # List class CLIs

    class_list = api.class_list(properties=['cls_name','cls_id'])
    print(class_list)

    print('\n length of class_list:' + str(len(class_list)))

    for cls_entry in range(len(class_list)):
        print(str(cls_entry) + ': ' + class_list[cls_entry]['cls_name'] + '\n')
    class_num = int(input('Enter class number for this account:'))
        
    if args.CSE235:
        suffixes = list(chr(x + ord('A')) + str(y) for x in range(0,14) for y in range(1,10))
    else:
        suffixes = list(map(str, range(1,int(args.num_accts))))

    for suffix in suffixes:
        acct_name = args.acct_prefix + suffix
        if not args.n:
            api.user_account_add(com_id = class_list[class_num]['com_id'],
                                 acc_user_id = acct_name,
                                 acc_password = args.passwd,
                                 acc_pw_change = False,
                                 cls_id = class_list[class_num]['cls_id'],
                                 acc_full_name = acct_name)
        else:
            print(acct_name)
            
if __name__ == "__main__":
   main()
