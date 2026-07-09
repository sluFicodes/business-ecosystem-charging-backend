# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid

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


import mock
from django.test import TestCase
from mock import MagicMock
from parameterized import parameterized


from wstore.charging_engine.payment_client import payment_client
from wstore.charging_engine.payment_client import paypal_client
from wstore.charging_engine.payment_client import stripe_client


class _StripeCardError(Exception):
    """Stand-in for stripe.error.CardError so the ``except`` clause in
    charge_recurring catches a real exception class while ``stripe`` is mocked."""
    pass


class PaymentClientTestCase(TestCase):
    tags = "payment_client"

    @parameterized.expand(
        [
            ("wstore.charging_engine.payment_client.stripe_client.StripeClient", stripe_client.StripeClient),
            ("wstore.charging_engine.payment_client.error_client.ErrorClient"),
        ]
    )
    def test_get_payment_client_class(self, client_full_name, client_class=None):
        payment_client.settings = MagicMock(**{"PAYMENT_CLIENT": client_full_name})
        try:
            payment_client_class = payment_client.PaymentClient.get_payment_client_class()
            assert payment_client_class == client_class
        except ModuleNotFoundError:
            assert client_class is None


class PaypalTestCase(TestCase):
    tags = ("payment-client", "payment-client-paypal")

    def setUp(self):
        paypal_client.paypalrestsdk = MagicMock()

    def test_paypal(self):
        paypal = paypal_client.PayPalClient(None)
        paypal.batch_payout(["item1", "item2"])
        paypal_client.paypalrestsdk.Payout.assert_called_once_with(
            {
                "sender_batch_header": {
                    "sender_batch_id": mock.ANY,
                    "email_subject": "You have a payment",
                },
                "items": ["item1", "item2"],
            }
        )

        paypal_client.paypalrestsdk.Payout().create.assert_called_once()


class StripeTestCalse(TestCase):
    tags = ("payment-client", "payment-client-stripe")

    def setUp(self):
        stripe_client.stripe = MagicMock()
        stripe_client.stripe.error.CardError = _StripeCardError
        stripe_client.Offering = MagicMock(**{"objects.get.return_value": MagicMock()})

    @parameterized.expand(
        [
            (
                "success",
                MagicMock(name="order"),
                [{"currency": "EUR", "price": 1000, "item": "test", "description": "test", "item_id": "test", "billId": "bill-1"}],
            ),
            ("no_transactions", MagicMock(name="order"), []),
            ("session_error", MagicMock(name="order"), [], Exception("Test Exception")),
        ]
    )
    def test_start_redirection_payment(self, name, order, transactions, checkout_error=None):
        stripe_payment_client = stripe_client.StripeClient(order)
        stripe_payment_client._order = MagicMock(
            **{
                "contracts": [MagicMock(**transaction) for transaction in transactions],
                "hash_key": b"test-secret-key",
            }
        )

        checkout_session = MagicMock(name="checkout_session")
        checkout_session.id = "cs_test_a11lpqo9KV8xxEBtrURbzgouesMb3mEZnIosnHpOzVCrjQ7pHeSNDAHwUA"
        checkout_session.url = "https://checkout.stripe.com/c/pay/test"
        stripe_client.stripe.configure_mock(
            **{
                "checkout.Session.create.return_value": checkout_session,
                "checkout.Session.create.side_effect": checkout_error,
            }
        )

        try:
            stripe_payment_client.start_redirection_payment(transactions)
            error = None
        except Exception as e:
            error = e

        stripe_client.stripe.checkout.Session.create.assert_called_once()
        if error:
            self.assertIsInstance(error, payment_client.PaymentClientError)
        else:
            self.assertEquals(stripe_payment_client.get_checkout_url(), "https://checkout.stripe.com/c/pay/test")

    def test_end_redirection_payment(self):
        order = MagicMock()
        order.order_id = "order-1"
        stripe_payment_client = stripe_client.StripeClient(order)
        stripe_client.PaymentRecord = MagicMock()

        session = MagicMock(name="session")
        session.client_reference_id = order.order_id
        session.payment_status = "paid"

        item = MagicMock(name="line_item")
        item.metadata = {"paymentItemExternalId": "cb-1"}

        page = MagicMock(name="page")
        page.data = [item]
        page.has_more = False

        stripe_client.stripe.configure_mock(
            **{
                "checkout.Session.retrieve.return_value": session,
                "checkout.Session.list_line_items.return_value": page,
            }
        )

        result = stripe_payment_client.end_redirection_payment(session_id="test")
        self.assertEquals(result, (["test"], [{"paymentItemExternalId": "cb-1", "state": "processed"}]))

    def test_refund(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())

        checkout_session = MagicMock(name="checkout_session")
        checkout_session.id = "cs_test_a11lpqo9KV8xxEBtrURbzgouesMb3mEZnIosnHpOzVCrjQ7pHeSNDAHwUA"
        refund = MagicMock(name="refund")
        refund.id = "rf_test_a11lpqo9KV8xxEBtrURbzgouesMb3mEZnIosnHpOzVCrjQ7pHeSNDAHwUA"
        stripe_client.stripe.configure_mock(
            **{
                "checkout.Session.retrieve.return_value": checkout_session,
                "Refund.create.return_value": refund,
            }
        )

        self.assertEquals(stripe_payment_client.refund("test"), refund)

    def test_refund_error(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.checkout.Session.retrieve.side_effect = Exception("boom")

        with self.assertRaises(payment_client.PaymentClientError):
            stripe_payment_client.refund("test")

    def test_end_redirection_payment_manipulated(self):
        order = MagicMock()
        order.order_id = "order-1"
        stripe_payment_client = stripe_client.StripeClient(order)

        session = MagicMock(name="session")
        session.client_reference_id = "another-order"
        session.payment_status = "paid"
        stripe_client.stripe.checkout.Session.retrieve.return_value = session

        with self.assertRaises(stripe_client.PaymentError):
            stripe_payment_client.end_redirection_payment(session_id="test")

    def test_end_redirection_payment_pending(self):
        order = MagicMock()
        order.order_id = "order-1"
        stripe_payment_client = stripe_client.StripeClient(order)
        stripe_client.PaymentRecord = MagicMock()

        session = MagicMock(name="session")
        session.client_reference_id = order.order_id
        session.payment_status = "unpaid"

        item = MagicMock(name="line_item")
        item.metadata = {"paymentItemExternalId": "cb-1"}
        page = MagicMock(name="page", data=[item], has_more=False)

        stripe_client.stripe.configure_mock(
            **{
                "checkout.Session.retrieve.return_value": session,
                "checkout.Session.list_line_items.return_value": page,
            }
        )

        result = stripe_payment_client.end_redirection_payment(session_id="test")
        self.assertEquals(result, (["test"], [{"paymentItemExternalId": "cb-1", "state": "pending"}]))

    def test_end_redirection_payment_pagination(self):
        order = MagicMock()
        order.order_id = "order-1"
        stripe_payment_client = stripe_client.StripeClient(order)
        stripe_client.PaymentRecord = MagicMock()

        session = MagicMock(name="session")
        session.client_reference_id = order.order_id
        session.payment_status = "paid"

        item1 = MagicMock(name="line_item_1", id="li_1")
        item1.metadata = {"paymentItemExternalId": "cb-1"}
        item2 = MagicMock(name="line_item_2", id="li_2")
        item2.metadata = {"paymentItemExternalId": "cb-2"}

        page1 = MagicMock(name="page_1", data=[item1], has_more=True)
        page2 = MagicMock(name="page_2", data=[item2], has_more=False)

        stripe_client.stripe.checkout.Session.retrieve.return_value = session
        stripe_client.stripe.checkout.Session.list_line_items.side_effect = [page1, page2]

        result = stripe_payment_client.end_redirection_payment(session_id="test")
        self.assertEquals(
            result,
            (
                ["test"],
                [
                    {"paymentItemExternalId": "cb-1", "state": "processed"},
                    {"paymentItemExternalId": "cb-2", "state": "processed"},
                ],
            ),
        )

    @parameterized.expand(
        [
            ("pi_succeeded", "pi_123", "succeeded", "succeeded"),
            ("pi_processing", "pi_123", "processing", "pending"),
            ("pi_requires_action", "pi_123", "requires_action", "pending"),
            ("pi_requires_confirmation", "pi_123", "requires_confirmation", "pending"),
            ("pi_failed", "pi_123", "canceled", "failed"),
        ]
    )
    def test_check_payment_status_payment_intent(self, name, reference, pi_status, expected):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.PaymentIntent.retrieve.return_value = MagicMock(status=pi_status)

        self.assertEquals(stripe_payment_client.check_payment_status(reference), expected)

    @parameterized.expand(
        [
            ("session_paid", "cs_123", "paid", "succeeded"),
            ("session_unpaid", "cs_123", "unpaid", "pending"),
            ("session_failed", "cs_123", "no_payment_required", "failed"),
        ]
    )
    def test_check_payment_status_session(self, name, reference, payment_status, expected):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.checkout.Session.retrieve.return_value = MagicMock(payment_status=payment_status)

        self.assertEquals(stripe_payment_client.check_payment_status(reference), expected)

    @parameterized.expand(
        [
            ("succeeded", "succeeded", "succeeded"),
            ("processing", "processing", "pending"),
            ("requires_action", "requires_action", "pending"),
            ("failed", "canceled", "failed"),
        ]
    )
    def test_charge_recurring_payment_intent(self, name, new_status, expected_state):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.PaymentIntent.retrieve.return_value = MagicMock(
            customer="cus_1", payment_method="pm_1"
        )
        stripe_client.stripe.PaymentIntent.create.return_value = MagicMock(id="pi_new", status=new_status)

        result = stripe_payment_client.charge_recurring("pi_123", "10.00", "EUR")

        self.assertEquals(result, ("pi_new", expected_state))
        stripe_client.stripe.PaymentIntent.create.assert_called_once_with(
            amount=1000,
            currency="eur",
            customer="cus_1",
            payment_method="pm_1",
            off_session=True,
            confirm=True,
        )

    def test_charge_recurring_from_session(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.checkout.Session.retrieve.return_value = MagicMock(
            customer="cus_1", payment_intent="pi_old"
        )
        stripe_client.stripe.PaymentIntent.retrieve.return_value = MagicMock(payment_method="pm_1")
        stripe_client.stripe.PaymentIntent.create.return_value = MagicMock(id="pi_new", status="succeeded")

        result = stripe_payment_client.charge_recurring("cs_123", "5", "USD")

        self.assertEquals(result, ("pi_new", "succeeded"))

    def test_charge_recurring_missing_payment_method(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.PaymentIntent.retrieve.return_value = MagicMock(
            customer="cus_1", payment_method=None
        )

        self.assertEquals(stripe_payment_client.charge_recurring("pi_123", "10", "EUR"), (None, "failed"))
        stripe_client.stripe.PaymentIntent.create.assert_not_called()

    def test_charge_recurring_card_error(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.PaymentIntent.retrieve.return_value = MagicMock(
            customer="cus_1", payment_method="pm_1"
        )
        stripe_client.stripe.PaymentIntent.create.side_effect = _StripeCardError("card declined")

        self.assertEquals(stripe_payment_client.charge_recurring("pi_123", "10", "EUR"), (None, "failed"))

    def test_charge_recurring_generic_error(self):
        stripe_payment_client = stripe_client.StripeClient(MagicMock())
        stripe_client.stripe.PaymentIntent.retrieve.side_effect = Exception("boom")

        self.assertEquals(stripe_payment_client.charge_recurring("pi_123", "10", "EUR"), (None, "failed"))
