# Copyright 2017-2018 Wind River
# Copyright 2016 Intel Corporation
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
import base64
from base64 import b64encode
import time
import requests
import yaml

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch

from sparts_supplier.exceptions import SupplierException


def _sha512(data):
    return hashlib.sha512(data).hexdigest()


class SupplierBatch:
    def __init__(self, base_url, keyfile=None):

        self._base_url = base_url

        if keyfile is None:
            self._signer = None
            return

        try:
            with open(keyfile) as fd:
                private_key_str = fd.read().strip()
        except OSError as err:
            raise SupplierException(
                'Failed to read private key {}: {}'.format(
                    keyfile, str(err)))

        try:
            private_key = Secp256k1PrivateKey.from_hex(private_key_str)
        except ParseError as e:
            raise SupplierException(
                'Unable to load private key: {}'.format(str(e)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(private_key)

        
    def create(self,supplier_id,short_id,supplier_name,passwd,supplier_url, auth_user=None, auth_password=None):
        return self.create_supplier_transaction(supplier_id,short_id,supplier_name,passwd,supplier_url, "create",
                                 auth_user=auth_user,
                                 auth_password=auth_password)

   
        
    def add_part(self,supplier_id,part_id):
        return self.create_supplier_transaction(supplier_id,"","","","","AddPart",part_id)

        
    def list_supplier(self, auth_user=None, auth_password=None):
        supplier_prefix = self._get_prefix()

        result = self._send_request(
            "state?address={}".format(supplier_prefix),
            auth_user=auth_user,
            auth_password=auth_password
        )

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                base64.b64decode(entry["data"]) for entry in encoded_entries
            ]

        except BaseException:
            return None

        
    def retrieve_supplier(self, supplier_id, auth_user=None, auth_password=None):
        address = self._get_address(supplier_id)

        result = self._send_request("state/{}".format(address), supplier_id=supplier_id,
                                    auth_user=auth_user,
                                    auth_password=auth_password)
        try:
            return base64.b64decode(yaml.safe_load(result)["data"])

        except BaseException:
            return None


    def _get_status(self, batch_id, wait, auth_user=None, auth_password=None):
        try:
            result = self._send_request(
                'batch_statuses?id={}&wait={}'.format(batch_id, wait),
                auth_user=auth_user,
                auth_password=auth_password)
            return yaml.safe_load(result)['data'][0]['status']
        except BaseException as err:
            raise SupplierException(err)

    def _get_prefix(self):
        return _sha512('supplier'.encode('utf-8'))[0:6]

    def _get_address(self, supplier_id):
        supplier_prefix = self._get_prefix()
        address = _sha512(supplier_id.encode('utf-8'))[0:64]
        return supplier_prefix + address
    
    
    def _send_request(
            self, suffix, data=None,
            content_type=None, supplier_id=None, auth_user=None, auth_password=None):
        if self._base_url.startswith("http://"):
            url = "{}/{}".format(self._base_url, suffix)
        else:
            url = "http://{}/{}".format(self._base_url, suffix)

        headers = {}
        if auth_user is not None:
            auth_string = "{}:{}".format(auth_user, auth_password)
            b64_string = b64encode(auth_string.encode()).decode()
            auth_header = 'Basic {}'.format(b64_string)
            headers['Authorization'] = auth_header

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if result.status_code == 404:
                raise SupplierException("No such supplier: {}".format(supplier_id))

            elif not result.ok:
                raise SupplierException("Error {}: {}".format(
                    result.status_code, result.reason))

        except BaseException as err:
            raise SupplierException(err)

        return result.text

    
    def create_supplier_transaction(self, supplier_id,short_id="",supplier_name="",passwd="",supplier_url="", action="",part_id="",
                     auth_user=None, auth_password=None):
        
        payload = ",".join([supplier_id,str(short_id),str(supplier_name),str(passwd),str(supplier_url), action,str(part_id)]).encode()

        # Construct the address
        address = self._get_address(supplier_id)

        header = TransactionHeader(
            signer_pubkey=self._signer.get_public_key().as_hex(),
            family_name="supplier",
            family_version="1.0",
            inputs=[address],
            outputs=[address],
            dependencies=[],
            payload_encoding="csv-utf8",
            payload_sha512=_sha512(payload),
            batcher_pubkey=self._signer.get_public_key().as_hex(),
            nonce=time.time().hex().encode()
        ).SerializeToString()

        signature = self._signer.sign(header)

        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=signature
        )

        batch_list = self._create_batch_list([transaction])
        batch_id = batch_list.batches[0].header_signature
        
        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream',
            auth_user=auth_user,
            auth_password=auth_password
        )

    
    def _create_batch_list(self, transactions):
        transaction_signatures = [t.header_signature for t in transactions]

        header = BatchHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            transaction_ids=transaction_signatures
        ).SerializeToString()

        signature = self._signer.sign(header)

        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature
        )
        return BatchList(batches=[batch])