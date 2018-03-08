# Copyright 2017-2018 Wind River 
# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

from __future__ import print_function

import argparse
import getpass
import logging
import os
import traceback
import sys
import pkg_resources
import json
import re

from colorlog import ColoredFormatter

from sparts_supplier.supplier_batch import SupplierBatch
from sparts_supplier.exceptions import SupplierException


DISTRIBUTION_NAME = 'sparts-supplier'


DEFAULT_URL = 'http://127.0.0.1:8080'


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def add_create_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'create',
        help='Creates a supplier',
        description='Creates a supplier',
        parents=[parent_parser])

    parser.add_argument(
        'supplier_id',
        type=str,
        help='an identifier for the supplier')
    
    parser.add_argument(
        'short_id',
        type=str,
        help='an short identifier for the supplier')
    
    parser.add_argument(
        'supplier_name',
        type=str,
        help='Provide supplier name')
    
    parser.add_argument(
        'passwd',
        type=str,
        help='provide hashed password')
    
    parser.add_argument(
        'supplier_url',
        type=str,
        help='provide URL')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--disable-client-validation',
        action='store_true',
        default=False,
        help='disable client validation')


def add_list_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'list-supplier',
        help='List all the suppliers',
        parents=[parent_parser])

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')


def add_retrieve_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'retrieve',
        help='Get the supplier by supplier ID',
        description='',
        parents=[parent_parser])

    parser.add_argument(
        'supplier_id',
        type=str,
        help='an identifier for the supplier')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')


def add_part_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('AddPart', parents=[parent_parser])
    
    parser.add_argument(
        'supplier_id',
        type=str,
        help='the identifier for the supplier')

    parser.add_argument(
        'part_id',
        type=str,
        help='the identifier for Part')
    




def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_create_parser(subparsers, parent_parser)
    add_list_parser(subparsers, parent_parser)
    add_retrieve_parser(subparsers, parent_parser)

    return parser


def do_list_supplier(args):
    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = SupplierBatch(base_url=url, keyfile=None)

    result = client.list_supplier(auth_user=auth_user,
                                 auth_password=auth_password)

    if result is not None:
        out = refine_output_supplier(str(result))
        output = refine_output(out)
        print(output)
    else:
        raise SupplierException("Could not retrieve supplier listing.")
    
    
def refine_output_supplier(inputstr):
    inputstr = inputstr[1:-1]
    output = re.sub(r'\[.*?\]', '',inputstr)
    output = "["+output+"]"  
    return output

def refine_output(inputstr):
    
                subpartstr = "\"parts\": ,"
                outputstr=inputstr.replace(subpartstr,"").replace('b\'','').replace('}\'','}').replace(", \"parts\": ","")
                outputstr=outputstr.replace('b\'','').replace('}\'','}')
                slist = outputstr.split("},")
                supplierlist = []
                for line in slist:
                        record = "{"+line.split(",{",1)[-1]+"}"
                        supplierlist.append(record)
                joutput = str(supplierlist)
                joutput = joutput.replace("'{","{").replace("}'","}").replace(", { {",", {").replace("}]}]","}]")
                joutput = amend_supplier_fields(joutput)
                return joutput

def amend_supplier_fields(inputstr):
        output = inputstr.replace("\\","").replace('supplier_id','uuid').replace('supplier_name','name').replace('supplier_url','url')
        return output


def do_retrieve(args, config):
    supplier_id = args.supplier_id

    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = SupplierBatch(base_url=url, keyfile=None)

    result = client.retrieve_supplier(supplier_id, auth_user=auth_user, auth_password=auth_password).decode()

    if result is not None:
        result = filter_output(result)
        print(result)

    else:
        raise SupplierException("Supplier not found: {}".format(supplier_id))

def removekey(d,key):
    r = dict(d)
    del r[key]
    return r

def print_msg(response):
    if "batch_status?id" in response:
        print ("{\"status\":\"success\"}")
    else:
        print ("{\"status\":\"exception\"}")

def filter_output(result):
    
    supplierlist = result.split(',',1)
    suppstr = supplierlist[1]
    jsonStr = suppstr.replace('supplier_id','uuid').replace('supplier_name','name').replace('supplier_url','url')
    data = json.loads(jsonStr)
    jsonStr = json.dumps(data)
    return jsonStr



def do_create(args):
    supplier_id = args.supplier_id
    short_id = args.short_id
    supplier_name = args.supplier_name
    passwd = args.passwd
    supplier_url = args.supplier_url

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = SupplierBatch(base_url=url, keyfile=keyfile)

    response = client.create(
            supplier_id,short_id,supplier_name,passwd,supplier_url,
            auth_user=auth_user,
            auth_password=auth_password)

    print_msg(response)


def _get_url(args):
    return DEFAULT_URL if args.url is None else args.url


def _get_keyfile(args):
    username = getpass.getuser() if args.username is None else args.username
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, username)


def _get_auth_info(args):
    auth_user = args.auth_user
    auth_password = args.auth_password
    if auth_user is not None and auth_password is None:
        auth_password = getpass.getpass(prompt="Auth Password: ")

    return auth_user, auth_password


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose

    setup_loggers(verbose_level=verbose_level)

    if args.command == 'create':
        do_create(args)
    elif args.command == 'list-supplier':
        do_list_supplier(args)
    elif args.command == 'retrieve':
        do_retrieve(args)
    elif args.command == 'AddPart':
        do_addpart(args) 
        
    else:
        raise SupplierException("invalid command: {}".format(args.command))

def do_addpart(args):
    supplier_id = args.supplier_id
    part_id = args.part_id
   
    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = SupplierBatch(base_url=url,
                      keyfile=keyfile)
    response = client.add_part(supplier_id,part_id)
    print_msg(response)

def main_wrapper():
    try:
        main()
    except SupplierException as err:
        newstr = str(err)
        if '404' in newstr:
            print("{\"status\":\"404 Not Found\"}")
        else:
            error_message = "{\"error\":\"failed\",\"error_message\":\""
            closing_str = "\"}"
            print (error_message+newstr+closing_str)
            
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)