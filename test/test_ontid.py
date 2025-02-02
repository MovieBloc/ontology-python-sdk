#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright (C) 2018 The ontology Authors
This file is part of The ontology library.

The ontology is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The ontology is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with The ontology.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import unittest

from Cryptodome.Random.random import randint

from test import sdk, acct2, acct3, acct4, password, not_panic_exception

from ontology.utils import utils
from ontology.crypto.curve import Curve
from ontology.utils.contract import Data
from ontology.utils.contract import Event
from ontology.common.define import DID_ONT
from ontology.account.account import Account
from ontology.crypto.signature import Signature
from ontology.contract.native.ontid import Attribute
from ontology.exception.exception import SDKException
from ontology.crypto.signature_scheme import SignatureScheme


class TestOntId(unittest.TestCase):
    def setUp(self):
        self.gas_price = 500
        self.gas_limit = 20000

    @not_panic_exception
    def check_pk_by_ont_id(self, ont_id):
        pub_keys = sdk.native_vm.ont_id().get_public_keys(ont_id)
        for pk in pub_keys:
            self.assertIn(ont_id, pk['PubKeyId'])
            self.assertEqual('ECDSA', pk['Type'])
            self.assertEqual('P256', pk['Curve'])
            self.assertEqual(66, len(pk['Value']))

    @not_panic_exception
    def test_get_public_keys(self):
        ont_id_list = ['did:ont:APywVQ2UKBtitqqJQ9JrpNeY8VFAnrZXiR', 'did:ont:ANDfjwrUroaVtvBguDtrWKRMyxFwvVwnZD']
        for ont_id in ont_id_list:
            self.check_pk_by_ont_id(ont_id)
        try:
            sdk.default_network.connect_to_main_net()
            ont_id = 'did:ont:ATZhaVirdEYkpsHQDn9PMt5kDCq1VPHcTr'
            self.check_pk_by_ont_id(ont_id)
        finally:
            sdk.default_network.connect_to_test_net()

    @not_panic_exception
    def get_ddo_test_case(self, ont_id: str):
        ddo = sdk.native_vm.ont_id().get_ddo(ont_id)
        for pk in ddo['Owners']:
            self.assertIn(ont_id, pk['PubKeyId'])
            self.assertEqual('ECDSA', pk['Type'])
            self.assertEqual('P256', pk['Curve'])
            self.assertEqual(66, len(pk['Value']))
        self.assertEqual(ont_id, ddo['OntId'])

    @not_panic_exception
    def test_get_ddo(self):
        ont_id = 'did:ont:AazEvfQPcQ2GEFFPLF1ZLwQ7K5jDn81hve'
        try:
            self.get_ddo_test_case(ont_id)
        finally:
            sdk.default_network.connect_to_test_net()
        try:
            sdk.default_network.connect_to_main_net()
            ont_id = 'did:ont:AP8n55wdQCRePFiNiR4kobGBhvBCMkVPun'
            self.get_ddo_test_case(ont_id)
        finally:
            sdk.default_network.connect_to_test_net()

    @not_panic_exception
    def test_new_registry_ont_id_transaction(self):
        ont_id = sdk.native_vm.ont_id()
        hex_public_key = acct2.get_public_key_hex()
        b58_address = acct2.get_address_base58()
        acct_did = DID_ONT + b58_address
        tx = ont_id.new_registry_ont_id_tx(acct_did, hex_public_key, b58_address, self.gas_price, self.gas_limit)
        tx.sign_transaction(acct2)
        self.assertEqual(64, len(tx.hash256(is_hex=True)))
        self.assertEqual(598, len(tx.serialize(is_hex=True)))
        try:
            sdk.rpc.send_raw_transaction(tx)
        except SDKException as e:
            self.assertEqual(59000, e.args[0])
            self.assertIn('already registered', e.args[1])

    @not_panic_exception
    def test_registry_ont_id(self):
        ont_id = sdk.native_vm.ont_id()
        try:
            identity = sdk.wallet_manager.create_identity(password)
            ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        except SDKException as e:
            self.assertIn('Wallet identity exists', e.args[1])
            return
        try:
            ont_id.registry_ont_id(identity.ont_id, ctrl_acct, acct2, self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertEqual(59000, e.args[0])
            self.assertIn('already registered', e.args[1])

    @not_panic_exception
    def test_add_and_remove_public_key(self):
        identity = sdk.wallet_manager.create_identity(password)
        ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        ont_id = sdk.native_vm.ont_id()
        tx_hash = ont_id.registry_ont_id(identity.ont_id, ctrl_acct, acct3, self.gas_price, self.gas_limit)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        event = sdk.restful.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = ont_id.contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Register', notify['States'][0])
        self.assertEqual(identity.ont_id, notify['States'][1])

        private_key = utils.get_random_bytes(32)
        public_key = Signature.ec_get_public_key_by_private_key(private_key, Curve.P256)
        hex_new_public_key = public_key.hex()

        tx_hash = sdk.native_vm.ont_id().add_public_key(identity.ont_id, ctrl_acct, hex_new_public_key, acct4,
                                                        self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = sdk.native_vm.ont_id().contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertIn('PublicKey', notify['States'])
        self.assertIn('add', notify['States'])
        self.assertIn(identity.ont_id, notify['States'])
        self.assertIn(hex_new_public_key, notify['States'])
        try:
            ont_id.add_public_key(identity.ont_id, ctrl_acct, hex_new_public_key, acct4, self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertIn('already exists', e.args[1])
        tx_hash = sdk.native_vm.ont_id().revoke_public_key(identity.ont_id, ctrl_acct, hex_new_public_key, acct3,
                                                           self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertIn('PublicKey', notify['States'])
        self.assertIn('remove', notify['States'])
        self.assertIn(identity.ont_id, notify['States'])
        self.assertIn(hex_new_public_key, notify['States'])
        try:
            ont_id.revoke_public_key(identity.ont_id, ctrl_acct, hex_new_public_key, acct3, self.gas_price,
                                     self.gas_limit)
        except SDKException as e:
            self.assertIn('public key has already been revoked', e.args[1])

    @not_panic_exception
    def test_add_and_remove_attribute(self):
        ont_id = sdk.native_vm.ont_id()
        identity = sdk.wallet_manager.create_identity(password)
        ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        tx_hash = ont_id.registry_ont_id(identity.ont_id, ctrl_acct, acct3, self.gas_price, self.gas_limit)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        event = sdk.restful.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = sdk.native_vm.ont_id().contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Register', notify['States'][0])
        self.assertEqual(identity.ont_id, notify['States'][1])

        attribute = Attribute('hello', 'string', 'attribute')
        tx_hash = ont_id.add_attribute(identity.ont_id, ctrl_acct, attribute, acct2, self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual('Attribute', notify['States'][0])
        self.assertEqual('add', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual('hello', Data.to_utf8_str(notify['States'][3][0]))

        attrib_key = 'hello'
        tx_hash = ont_id.remove_attribute(identity.ont_id, ctrl_acct, attrib_key, acct3, self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual('Attribute', notify['States'][0])
        self.assertEqual('remove', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual('hello', Data.to_utf8_str(notify['States'][3]))
        try:
            ont_id.remove_attribute(identity.ont_id, ctrl_acct, attrib_key, acct3, self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertIn('attribute not exist', e.args[1])
        attrib_key = 'key'
        try:
            ont_id.remove_attribute(identity.ont_id, ctrl_acct, attrib_key, acct3, self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertIn('attribute not exist', e.args[1])

    @not_panic_exception
    def test_new_remove_attribute_transaction(self):
        ont_id = sdk.native_vm.ont_id()
        hex_public_key = acct2.get_public_key_hex()
        b58_address = acct2.get_address_base58()
        acct_did = "did:ont:" + b58_address
        path = 'try'
        tx = ont_id.new_remove_attribute_tx(acct_did, hex_public_key, path, b58_address, self.gas_price, self.gas_limit)
        tx.sign_transaction(acct2)
        try:
            tx_hash = sdk.rpc.send_raw_transaction(tx)
            self.assertEqual(tx.hash256_explorer(), tx_hash)
            time.sleep(randint(10, 15))
            notify = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)['Notify']
            self.assertEqual('Attribute', notify[0]['States'][0])
            self.assertEqual('remove', notify[0]['States'][1])
            self.assertEqual(acct_did, notify[0]['States'][2])
            self.assertEqual('try', bytes.fromhex(notify[0]['States'][3]).decode())
        except SDKException as e:
            self.assertEqual(59000, e.args[0])
            self.assertIn('attribute not exist', e.args[1])

    @not_panic_exception
    def test_add_recovery(self):
        identity = sdk.wallet_manager.create_identity(password)
        ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        tx_hash = sdk.native_vm.ont_id().registry_ont_id(identity.ont_id, ctrl_acct, acct3, self.gas_price,
                                                         self.gas_limit)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        event = sdk.default_network.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = sdk.native_vm.ont_id().contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Register', notify['States'][0])
        self.assertEqual(identity.ont_id, notify['States'][1])

        rand_private_key = utils.get_random_bytes(32).hex()
        recovery = Account(rand_private_key, SignatureScheme.SHA256withECDSA)
        b58_recovery_address = recovery.get_address_base58()
        tx_hash = sdk.native_vm.ont_id().add_recovery(identity.ont_id, ctrl_acct, b58_recovery_address, acct2,
                                                      self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Recovery', notify['States'][0])
        self.assertEqual('add', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual(recovery.get_address_hex(little_endian=False), notify['States'][3])
        ddo = sdk.native_vm.ont_id().get_ddo(identity.ont_id)
        self.assertIn(ctrl_acct.get_ont_id(), ddo['Owners'][0]['PubKeyId'])
        self.assertEqual('ECDSA', ddo['Owners'][0]['Type'])
        self.assertEqual('P256', ddo['Owners'][0]['Curve'])
        self.assertEqual(ctrl_acct.get_public_key_hex(), ddo['Owners'][0]['Value'])
        self.assertEqual(0, len(ddo['Attributes']))
        self.assertEqual(recovery.get_address_base58(), ddo['Recovery'])
        self.assertEqual(identity.ont_id, ddo['OntId'])

        rand_private_key = utils.get_random_bytes(32).hex()
        new_recovery = Account(rand_private_key, SignatureScheme.SHA256withECDSA)
        b58_new_recovery_address = new_recovery.get_address_base58()
        try:
            sdk.native_vm.ont_id().add_recovery(identity.ont_id, ctrl_acct, b58_new_recovery_address, acct2,
                                                self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertIn('already set recovery', e.args[1])

        private_key = utils.get_random_bytes(32)
        public_key = Signature.ec_get_public_key_by_private_key(private_key, Curve.P256)
        hex_new_public_key = public_key.hex()
        tx_hash = sdk.native_vm.ont_id().add_public_key(identity.ont_id, recovery, hex_new_public_key, acct2,
                                                        self.gas_price, self.gas_limit, True)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('PublicKey', notify['States'][0])
        self.assertEqual('add', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual(2, notify['States'][3])
        self.assertEqual(hex_new_public_key, notify['States'][4])

        ddo = sdk.native_vm.ont_id().get_ddo(identity.ont_id)
        self.assertIn(ctrl_acct.get_ont_id(), ddo['Owners'][0]['PubKeyId'])
        self.assertEqual('ECDSA', ddo['Owners'][0]['Type'])
        self.assertEqual('P256', ddo['Owners'][0]['Curve'])
        self.assertEqual(ctrl_acct.get_public_key_hex(), ddo['Owners'][0]['Value'])
        self.assertIn(ctrl_acct.get_ont_id(), ddo['Owners'][1]['PubKeyId'])
        self.assertEqual('ECDSA', ddo['Owners'][1]['Type'])
        self.assertEqual('P256', ddo['Owners'][1]['Curve'])
        self.assertEqual(hex_new_public_key, ddo['Owners'][1]['Value'])
        self.assertEqual(0, len(ddo['Attributes']))
        self.assertEqual(recovery.get_address_base58(), ddo['Recovery'])
        self.assertEqual(identity.ont_id, ddo['OntId'])
        self.assertEqual(b58_recovery_address, ddo['Recovery'])

        tx_hash = sdk.native_vm.ont_id().revoke_public_key(identity.ont_id, recovery, hex_new_public_key, acct3,
                                                           self.gas_price, self.gas_limit, True)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertIn('PublicKey', notify['States'])
        self.assertIn('remove', notify['States'])
        self.assertIn(identity.ont_id, notify['States'])
        self.assertIn(hex_new_public_key, notify['States'])
        try:
            sdk.native_vm.ont_id().revoke_public_key(identity.ont_id, recovery, hex_new_public_key, acct3,
                                                     self.gas_price, self.gas_limit, True)
        except SDKException as e:
            self.assertIn('public key has already been revoked', e.args[1])

        private_key = utils.get_random_bytes(32)
        public_key = Signature.ec_get_public_key_by_private_key(private_key, Curve.P256)
        hex_new_public_key = public_key.hex()
        try:
            sdk.native_vm.ont_id().add_public_key(identity.ont_id, new_recovery, hex_new_public_key, acct2,
                                                  self.gas_price, self.gas_limit, True)
        except SDKException as e:
            self.assertIn('no authorization', e.args[1])

    @not_panic_exception
    def test_change_recovery(self):
        identity = sdk.wallet_manager.create_identity(password)
        ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        tx_hash = sdk.native_vm.ont_id().registry_ont_id(identity.ont_id, ctrl_acct, acct3, self.gas_price,
                                                         self.gas_limit)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        event = sdk.restful.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = sdk.native_vm.ont_id().contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Register', notify['States'][0])
        self.assertEqual(identity.ont_id, notify['States'][1])

        rand_private_key = utils.get_random_bytes(32).hex()
        recovery = Account(rand_private_key, SignatureScheme.SHA256withECDSA)
        b58_recovery_address = recovery.get_address_base58()
        tx_hash = sdk.native_vm.ont_id().add_recovery(identity.ont_id, ctrl_acct, b58_recovery_address, acct2,
                                                      self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Recovery', notify['States'][0])
        self.assertEqual('add', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual(recovery.get_address_hex(little_endian=False), notify['States'][3])
        ddo = sdk.native_vm.ont_id().get_ddo(identity.ont_id)
        self.assertIn(ctrl_acct.get_ont_id(), ddo['Owners'][0]['PubKeyId'])
        self.assertEqual('ECDSA', ddo['Owners'][0]['Type'])
        self.assertEqual('P256', ddo['Owners'][0]['Curve'])
        self.assertEqual(ctrl_acct.get_public_key_hex(), ddo['Owners'][0]['Value'])
        self.assertEqual(0, len(ddo['Attributes']))
        self.assertEqual(recovery.get_address_base58(), ddo['Recovery'])
        self.assertEqual(identity.ont_id, ddo['OntId'])

        rand_private_key = utils.get_random_bytes(32).hex()
        new_recovery = Account(rand_private_key, SignatureScheme.SHA256withECDSA)
        b58_new_recovery_address = new_recovery.get_address_base58()

        try:
            sdk.native_vm.ont_id().change_recovery(identity.ont_id, b58_new_recovery_address, ctrl_acct, acct2,
                                                   self.gas_price, self.gas_limit)
        except SDKException as e:
            self.assertIn('operator is not the recovery', e.args[1])
        tx_hash = sdk.native_vm.ont_id().change_recovery(identity.ont_id, b58_new_recovery_address, recovery, acct2,
                                                         self.gas_price, self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)

        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Recovery', notify['States'][0])
        self.assertEqual('change', notify['States'][1])
        self.assertEqual(identity.ont_id, notify['States'][2])
        self.assertEqual(new_recovery.get_address_hex(little_endian=False), notify['States'][3])

    @not_panic_exception
    def test_verify_signature(self):
        identity = sdk.wallet_manager.create_identity(password)
        ctrl_acct = sdk.wallet_manager.get_control_account_by_index(identity.ont_id, 0, password)
        ont_id = sdk.native_vm.ont_id()
        tx_hash = ont_id.registry_ont_id(identity.ont_id, ctrl_acct, acct3, self.gas_price, self.gas_limit)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        event = sdk.default_network.get_contract_event_by_tx_hash(tx_hash)
        hex_contract_address = ont_id.contract_address
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertEqual(hex_contract_address, notify['ContractAddress'])
        self.assertEqual('Register', notify['States'][0])
        self.assertEqual(identity.ont_id, notify['States'][1])

        private_key = utils.get_random_bytes(32)
        public_key = Signature.ec_get_public_key_by_private_key(private_key, Curve.P256)
        new_ctrl_acct = Account(private_key)
        hex_new_public_key = public_key.hex()

        tx_hash = ont_id.add_public_key(identity.ont_id, ctrl_acct, hex_new_public_key, acct4, self.gas_price,
                                        self.gas_limit)
        time.sleep(randint(10, 15))
        event = sdk.default_network.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, hex_contract_address)
        self.assertIn('PublicKey', notify['States'])
        self.assertIn('add', notify['States'])
        self.assertIn(identity.ont_id, notify['States'])
        self.assertIn(hex_new_public_key, notify['States'])
        result = ont_id.verify_signature(identity.ont_id, 1, ctrl_acct)
        self.assertTrue(result)
        result = ont_id.verify_signature(identity.ont_id, 2, ctrl_acct)
        self.assertFalse(result)
        result = ont_id.verify_signature(identity.ont_id, 1, new_ctrl_acct)
        self.assertFalse(result)
        result = ont_id.verify_signature(identity.ont_id, 2, new_ctrl_acct)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
