# Copyright 2017-2018 Wind River
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


import hashlib
import logging
import json
from collections import OrderedDict

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError



LOGGER = logging.getLogger(__name__)


class SupplierTransactionHandler(TransactionHandler):

    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'supplier'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def encodings(self):
        return ['csv-utf8']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):

        header = transaction.header

        self._context = context
        stored_supplier = ""
        try:
            supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id = transaction.payload.decode().split(",")
        except ValueError:
            raise InvalidTransaction("Invalid payload serialization")

        validate_transaction(supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id)
               
        data_address = make_supplier_address(self._namespace_prefix,supplier_id)
        
        state_entries = self._context.get_state(
                [data_address])
          
      
        if len(state_entries) != 0:
            try:
                   
                    stored_supplier_id, stored_supplier = \
                    state_entries[0].data.decode().split(",",1)
                             
                    stored_supplier = json.loads(stored_supplier)
            except ValueError:
                raise InternalError("Failed to deserialize data.")
            
        else:
            stored_supplier_id = stored_supplier = None
            
      
        if action == "create" and stored_supplier_id is not None:
            raise InvalidTransaction("Invalid Action-supplier already exists.")
               
           
        if action == "create":
            supplier = create_supplier(supplier_id,short_id,supplier_name,passwd,supplier_url)
            stored_supplier_id = supplier_id
            stored_supplier = supplier
            _display("Created a supplier.")
        
        
           
        if action == "AddPart":
            if part_id not in stored_supplier:
                supplier = add_part(part_id,stored_supplier)
                stored_supplier = supplier  
            
        # Put data back in state storage
        stored_supp_json = json.dumps(stored_supplier)
        data=",".join([stored_supplier_id, stored_supp_json]).encode()
       
        self._context.set_state(
            {data_address: data})
        


def add_part(uuid,parent_supplier):    
    supplier_list = parent_supplier['parts']
    supplier_dic = {'part_id': uuid}
    supplier_list.append(supplier_dic)
    parent_supplier['parts'] = supplier_list
    return parent_supplier     


def create_supplier(supplier_id,short_id,supplier_name,passwd,supplier_url):
    supplierD = {'supplier_id': supplier_id,'short_id':short_id,'supplier_name': supplier_name,'passwd': passwd,'supplier_url': supplier_url,'parts':[]}
    return supplierD 
         


def validate_transaction( supplier_id,short_id,supplier_name,passwd,supplier_url,action,part_id):
    if not supplier_id:
        raise InvalidTransaction('Supplier ID is required') 
    if not action:
        raise InvalidTransaction('Action is required')

    if action not in ('create',"AddPart"):
        raise InvalidTransaction('Invalid action: {}'.format(action))

    
def make_supplier_address(namespace_prefix, supplier_id):
    return namespace_prefix + \
        hashlib.sha512(supplier_id.encode('utf-8')).hexdigest()[:64]




def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")