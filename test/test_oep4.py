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

from ontology.utils.contract import Event, Data
from test import sdk, acct1, acct2, acct3, acct4, not_panic_exception


class TestOep4(unittest.TestCase):
    def setUp(self):
        sdk.default_network = sdk.rpc
        self.networks = [sdk.rpc, sdk.restful]
        self.contract_address = '1ddbb682743e9d9e2b71ff419e97a9358c5c4ee9'

    def test_set_contract_address(self):
        oep4 = sdk.neo_vm.oep4(self.contract_address)
        self.assertEqual(self.contract_address, oep4.hex_contract_address)

    @not_panic_exception
    def test_query_name(self):
        for network in self.networks:
            sdk.default_network = network
            oep4 = sdk.neo_vm.oep4('d7b6a47966770c1545bf74c16426b26c0a238b16')
            self.assertEqual('DXToken', oep4.name())

    @not_panic_exception
    def test_get_symbol(self):
        for network in self.networks:
            sdk.default_network = network
            oep4 = sdk.neo_vm.oep4('d7b6a47966770c1545bf74c16426b26c0a238b16')
            self.assertEqual('DX', oep4.symbol())

    @not_panic_exception
    def test_get_decimal(self):
        contract_list = ['1ddbb682743e9d9e2b71ff419e97a9358c5c4ee9', '165b1227311d47c22cd073ef8f285d3bddc858ca',
                         '8fecd2740b10a7410026774cc1f99fe14860873b']
        decimal_list = [10, 32, 255]
        for network in self.networks:
            sdk.default_network = network
            for index, address in enumerate(contract_list):
                oep4 = sdk.neo_vm.oep4(address)
                self.assertEqual(decimal_list[index], oep4.decimals())

    @not_panic_exception
    def test_init(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        tx_hash = oep4.init(acct1, acct2, 500, 20000000)
        self.assertEqual(len(tx_hash), 64)
        time.sleep(randint(10, 15))
        event = sdk.rpc.get_contract_event_by_tx_hash(tx_hash)
        notify = Event.get_notify_by_contract_address(event, oep4.hex_contract_address)
        self.assertEqual('Already initialized!', Data.to_utf8_str(notify['States']))

    @not_panic_exception
    def test_get_total_supply(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        self.assertEqual(10000000000000000000, oep4.total_supply())
        try:
            sdk.rpc.connect_to_main_net()
            oep4 = sdk.neo_vm.oep4()
            oep4.hex_contract_address = '6c80f3a5c183edee7693a038ca8c476fb0d6ac91'
            self.assertEqual(10000000000, oep4.total_supply())
        finally:
            sdk.rpc.connect_to_test_net()

    @not_panic_exception
    def test_transfer(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        from_acct = acct1
        b58_to_address = acct2.get_address_base58()
        value = 10
        tx_hash = oep4.transfer(from_acct, b58_to_address, value, from_acct, 500, 20000000)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        notify = oep4.query_transfer_event(tx_hash)
        self.assertEqual('transfer', notify['States'][0])
        self.assertEqual(from_acct.get_address_base58(), notify['States'][1])
        self.assertEqual(b58_to_address, notify['States'][2])
        self.assertEqual(value, notify['States'][3])

    @not_panic_exception
    def test_balance_of(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        b58_address1 = acct3.get_address_base58()
        b58_address2 = acct4.get_address_base58()
        balance = oep4.balance_of(b58_address1)
        self.assertGreaterEqual(balance, 10)
        balance = oep4.balance_of(b58_address2)
        self.assertGreaterEqual(balance, 1)

    @not_panic_exception
    def test_transfer_multi(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        transfer_list = list()

        b58_from_address1 = acct1.get_address_base58()
        b58_from_address2 = acct2.get_address_base58()
        from_address_list = [b58_from_address1, b58_from_address2]

        b58_to_address1 = acct2.get_address_base58()
        b58_to_address2 = acct3.get_address_base58()
        to_address_list = [b58_to_address1, b58_to_address2]

        value_list = [1, 2]

        transfer1 = [b58_from_address1, b58_to_address1, value_list[0]]
        transfer2 = [b58_from_address2, b58_to_address2, value_list[1]]

        signers = [acct1, acct2, acct3]
        transfer_list.append(transfer1)
        transfer_list.append(transfer2)

        tx_hash = oep4.transfer_multi(transfer_list, signers, acct1, 500, 20000000)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(10, 15))
        notify_list = oep4.query_multi_transfer_event(tx_hash)
        self.assertEqual(len(transfer_list), len(notify_list))
        for index, notify in enumerate(notify_list):
            self.assertEqual('transfer', notify['States'][0])
            self.assertEqual(from_address_list[index], notify['States'][1])
            self.assertEqual(to_address_list[index], notify['States'][2])
            self.assertEqual(value_list[index], notify['States'][3])

    @not_panic_exception
    def test_approve(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        b58_spender_address = acct2.get_address_base58()
        amount = 10
        tx_hash = oep4.approve(acct1, b58_spender_address, amount, acct1, 500, 20000000)
        self.assertEqual(len(tx_hash), 64)
        time.sleep(randint(16, 20))
        event = oep4.query_approve_event(tx_hash)
        self.assertEqual(self.contract_address, event.get('ContractAddress', ''))
        states = event['States']
        self.assertEqual('approval', states[0])
        self.assertEqual(acct1.get_address_base58(), states[1])
        self.assertEqual(b58_spender_address, states[2])
        self.assertEqual(amount, states[3])

    @not_panic_exception
    def test_allowance(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        allowance = oep4.allowance(acct1.get_address(), acct2.get_address())
        self.assertGreaterEqual(allowance, 1)

    @not_panic_exception
    def test_transfer_from(self):
        oep4 = sdk.neo_vm.oep4()
        oep4.hex_contract_address = self.contract_address
        b58_from_address = acct1.get_address_base58()
        b58_to_address = acct3.get_address_base58()
        value = 1
        tx_hash = oep4.transfer_from(acct2, b58_from_address, b58_to_address, value, acct1, 500, 20000000)
        self.assertEqual(64, len(tx_hash))
        time.sleep(randint(16, 20))
        event = oep4.query_transfer_from_event(tx_hash)
        self.assertEqual(self.contract_address, event.get('ContractAddress', ''))
        self.assertEqual('transfer', event['States'][0])
        self.assertEqual(b58_from_address, event['States'][1])
        self.assertEqual(b58_to_address, event['States'][2])
        self.assertEqual(value, event['States'][3])


if __name__ == '__main__':
    unittest.main()
