# -*- coding: utf-8 -*-

# Copyright (c) 2025 Future Internet Consulting and Development Solutions S.L.

# This file belongs to the business-charging-backend
# of the Business API Ecosystem.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uuid

from django.test import TestCase
from parameterized import parameterized
from mock import MagicMock, patch

from wstore.charging_engine.engines.engine import Engine


RAW_ORDER = {
    "productOrderItem": [
        {"id": "1", "name": "item-1"},
        {"id": "2", "name": "item-2"},
    ]
}


class EngineTestCase(TestCase):
    tags = ("engine", "billing", "charges")
    maxDiff = None

    @parameterized.expand([
        ("first_item_found", "1", {"id": "1", "name": "item-1"}),
        ("second_item_found", "2", {"id": "2", "name": "item-2"}),
        ("item_not_found", "3", None),
    ])
    def test_get_item(self, name, item_id, expected_result):
        engine = Engine(MagicMock())

        result = engine._get_item(item_id, RAW_ORDER)

        self.assertEqual(result, expected_result)

    def test_get_item_returns_first_match(self):
        raw_order = {
            "productOrderItem": [
                {"id": "1", "value": "a"},
                {"id": "1", "value": "b"},
            ]
        }
        engine = Engine(MagicMock())

        result = engine._get_item("1", raw_order)

        self.assertEqual(result, {"id": "1", "value": "a"})

    def test_resolve_charging_initial(self):
        engine = Engine(MagicMock())
        engine.process_initial_charging = MagicMock(return_value="http://checkout")
        related_contracts = [MagicMock()]

        result = engine.resolve_charging(
            type_="initial",
            related_contracts=related_contracts,
            raw_order=RAW_ORDER,
        )

        self.assertEqual(result, "http://checkout")
        engine.process_initial_charging.assert_called_once_with(RAW_ORDER, related_contracts)

    @parameterized.expand([
        ("renewal_type", "renewal"),
        ("usage_type", "usage"),
    ])
    def test_resolve_charging_unsupported_type(self, name, type_):
        engine = Engine(MagicMock())
        engine.process_initial_charging = MagicMock()

        result = engine.resolve_charging(type_=type_, raw_order=RAW_ORDER)

        self.assertIsNone(result)
        engine.process_initial_charging.assert_not_called()

    def _build_engine_with_contract(self):
        contract = MagicMock()
        contract.item_id = "1"
        contract.product_id = "old-product"

        order = MagicMock()
        order.order_id = "order-1"
        order.contracts = [contract]

        return Engine(order), order, contract

    @patch("wstore.charging_engine.engines.engine.PaymentClient")
    @patch("wstore.charging_engine.engines.engine.InventoryClient")
    @patch("wstore.charging_engine.engines.engine.BillingClient")
    def test_process_initial_charging_no_transactions(self, billing_client, inventory_client, payment_client):
        engine, order, contract = self._build_engine_with_contract()
        engine.execute_billing = MagicMock(return_value=(
            [],
            {},
            {"productPrice": [{"p": 1}], "productCharacteristic": [{"c": 2}]},
        ))

        inventory_client.return_value.create_product.return_value = {
            "id": "new-product",
            "relatedParty": [],
        }

        result = engine.process_initial_charging(RAW_ORDER)

        self.assertIsNone(result)

        # The created product is wired back into the contract
        self.assertEqual(contract.product_id, "new-product")
        self.assertEqual(contract.prd_after_paid, {
            "product_price": [{"p": 1}],
            "product_characteristic": [{"c": 2}],
        })

        # No billable rates means no payment redirection
        order.save.assert_called_once_with()
        billing_client.return_value.create_batch_customer_rates.assert_not_called()
        payment_client.get_payment_client_class.assert_not_called()

    @patch("wstore.charging_engine.engines.engine.PaymentClient")
    @patch("wstore.charging_engine.engines.engine.InventoryClient")
    @patch("wstore.charging_engine.engines.engine.BillingClient")
    def test_process_initial_charging_with_transactions(self, billing_client, inventory_client, payment_client):
        engine, order, contract = self._build_engine_with_contract()
        engine.execute_billing = MagicMock(return_value=(
            [{"name": "rate"}],
            {"some": "cb"},
            {"productPrice": [{"p": 1}], "productCharacteristic": [{"c": 2}]},
        ))

        inventory_client.return_value.create_product.return_value = {
            "id": "new-product",
            "relatedParty": [{"id": "party"}],
        }
        billing_client.return_value.create_batch_customer_rates.return_value = (
            [{"id": "acbr-1"}],
            True,
        )
        billing_client.return_value.create_customer_bill.return_value = {
            "id": "bill-1",
            "taxIncludedAmount": 12.10,
            "taxExcludedAmount": 10.0,
            "unit": "EUR",
        }

        payment_class = MagicMock()
        payment_class.return_value.get_checkout_url.return_value = "http://checkout"
        payment_client.get_payment_client_class.return_value = payment_class

        result = engine.process_initial_charging(RAW_ORDER)

        self.assertEqual(result, "http://checkout")

        # Contract bookkeeping
        self.assertEqual(contract.product_id, "new-product")
        self.assertEqual(contract.applied_rates, ["acbr-1"])
        self.assertEqual(contract.customer_bill["id"], "bill-1")

        # Pending payment stored on the order
        self.assertEqual(order.pending_payment["concept"], "initial")
        self.assertEqual(order.pending_payment["free_contracts"], [])
        transactions = order.pending_payment["transactions"]
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0], {
            "item": "1",
            "provider": None,
            "billId": "bill-1",
            "price": 12.10,
            "duty_free": 10.0,
            "description": "",
            "currency": "EUR",
            "recurring": True,
        })

        order.save.assert_called_once_with()
        payment_class.assert_called_once_with(order)
        payment_class.return_value.start_redirection_payment.assert_called_once_with(transactions)

    @patch("wstore.charging_engine.engines.engine.PaymentClient")
    @patch("wstore.charging_engine.engines.engine.InventoryClient")
    @patch("wstore.charging_engine.engines.engine.BillingClient")
    def test_process_initial_charging_generates_internal_bill(self, billing_client, inventory_client, payment_client):
        engine, order, contract = self._build_engine_with_contract()
        engine.execute_billing = MagicMock(return_value=(
            [{"name": "rate"}],
            {"some": "cb"},
            {"productPrice": [], "productCharacteristic": []},
        ))

        inventory_client.return_value.create_product.return_value = {
            "id": "new-product",
            "relatedParty": [{"id": "party"}],
        }
        billing_client.return_value.create_batch_customer_rates.return_value = (
            [{"id": "acbr-1"}],
            False,
        )
        # Customer bill without an id forces an internal one to be generated
        billing_client.return_value.create_customer_bill.return_value = {
            "taxIncludedAmount": 5.0,
        }

        payment_client.get_payment_client_class.return_value.return_value.get_checkout_url.return_value = "http://checkout"

        engine.process_initial_charging(RAW_ORDER)

        self.assertTrue(contract.customer_bill["internal"])
        # A valid uuid is generated and reused as the transaction bill id
        generated_id = contract.customer_bill["id"]
        uuid.UUID(generated_id)
        transactions = order.pending_payment["transactions"]
        self.assertEqual(transactions[0]["billId"], generated_id)
        # Defaults are applied when the bill omits optional amounts/currency
        self.assertEqual(transactions[0]["duty_free"], 0)
        self.assertEqual(transactions[0]["currency"], "EUR")

    @patch("wstore.charging_engine.engines.engine.PaymentClient")
    @patch("wstore.charging_engine.engines.engine.InventoryClient")
    @patch("wstore.charging_engine.engines.engine.BillingClient")
    def test_process_initial_charging_uses_related_contracts(self, billing_client, inventory_client, payment_client):
        contract = MagicMock()
        contract.item_id = "1"
        contract.product_id = "existing-product"

        order = MagicMock()
        order.order_id = "order-1"
        order.contracts = [MagicMock()]  # should be ignored in favour of related_contract

        engine = Engine(order)
        engine.execute_billing = MagicMock(return_value=(
            [],
            {},
            {"productPrice": [], "productCharacteristic": []},
        ))

        inventory_client.return_value.get_product.return_value = {
            "id": "existing-product",
            "relatedParty": [],
        }

        result = engine.process_initial_charging(RAW_ORDER, related_contract=[contract])

        self.assertIsNone(result)
        # For a modification the existing product is fetched, not created
        inventory_client.return_value.get_product.assert_called_once_with("existing-product")
        inventory_client.return_value.create_product.assert_not_called()

    @patch("wstore.charging_engine.engines.engine.InventoryClient")
    @patch("wstore.charging_engine.engines.engine.BillingClient")
    def test_process_initial_charging_propagates_errors(self, billing_client, inventory_client):
        engine, order, contract = self._build_engine_with_contract()
        engine.execute_billing = MagicMock(side_effect=ValueError("boom"))

        with self.assertRaises(ValueError):
            engine.process_initial_charging(RAW_ORDER)
