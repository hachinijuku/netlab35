#! /usr/bin/env python3

import argparse
import re
DEFAULT_COM_ID = 1

from netlab.client import Client
from netlab.enums import DateFormat, TimeFormat

def main():

    si = None

    parser = argparse.ArgumentParser(description='Reset Netlab account block passwords')
    parser.add_argument('--passwd',
                        required=True,
                        help='Initial password for account')
    parser.add_argument('acctexprs',
                        help='regular expressions describing accounts to change',
                        nargs=argparse.REMAINDER)

    args = parser.parse_args()

    # Check if any arguments are provided
    if not args.acctexprs:
        print('No accts specified',file=sys.stderr)
        sys.exit(1)

    # Identify the pod names matching the regular expressions
    api = Client()

    all_accts = api.user_account_list()
    print(all_accts)
    acct_indices = []
    for expr in args.acctexprs:
        prog = re.compile(expr)
        this_index = list(filter(lambda x: x != None,
                                 list(map(lambda x, y: y if prog.match(x['acc_user_id']) else None,
                                          all_accts,
                                          range(len(all_accts))))))
        acct_indices += this_index

    print('Resetting passwords for these accounts:')
    print('\n'.join(list(map(lambda x: x['acc_user_id'], (all_accts[i] for i in acct_indices)))))

    yes_no = input("Do you want to reset the password for all these accounts (y/n)? ")
    if yes_no[0].lower() != 'y':
        sys.exit(2)

    for acct_id in list(map(lambda x: x['acc_id'], (all_accts[i] for i in acct_indices))):
        api.user_account_password_set(acc_id = acct_id,
                             new_password = args.passwd,
                             force_reset = False)
            
if __name__ == "__main__":
   main()
