from django.test import TestCase
from mock import MagicMock, patch

from wstore.charging_engine.management.commands import payment_scheduler


class PaymentSchedulerTestCase(TestCase):
    tags = ("payment-scheduler",)

    def setUp(self):
        self.command = payment_scheduler.Command()
        self.command._billing_client = MagicMock()
        self.command._inventory_client = MagicMock()
        self.command._get_payment_info_from_cb = MagicMock(
            return_value=("redsys", "pre-auth-id")
        )

        self.client = MagicMock()
        self.client.NAME = "redsys"
        self.client_class = MagicMock(return_value=self.client)

        self.real_does_not_exist = payment_scheduler.PaymentRecord.DoesNotExist

        self.payment_record = MagicMock()
        self.payment_record.DoesNotExist = self.real_does_not_exist

        self.payment_record_patch = patch.object(
            payment_scheduler,
            "PaymentRecord",
            self.payment_record,
        )
        self.payment_client_patch = patch.object(
            payment_scheduler.PaymentClient,
            "get_payment_client_class",
            return_value=self.client_class,
        )

        self.payment_record_patch.start()
        self.payment_client_patch.start()
        self.addCleanup(self.payment_record_patch.stop)
        self.addCleanup(self.payment_client_patch.stop)

        self.cb = {
            "id": "cb-1",
            "taxIncludedAmount": {
                "value": 18.39,
                "unit": "EUR",
            },
        }

    def test_new_cb_passes_none_and_client_creates_record(self):
        record = MagicMock(
            customerBill_id="cb-1", payment_type="redsys", payment_reference="redsys-payment-1", retry_count=0, pk=None
        )
        self.payment_record.get_by_customer_bill_id.side_effect = [self.real_does_not_exist, record]
        self.client.charge_recurring.return_value = ("redsys-payment-1", "succeeded")

        self.command._process_cb(self.cb)

        self.client.charge_recurring.assert_called_once_with(self.cb, None, "pre-auth-id", 18.39, "EUR")
        self.payment_record.update_payment_reference.assert_not_called()
        self.command._billing_client.set_customer_bill.assert_called_once_with("settled", "cb-1")

    def test_failed_payment_retries_with_pre_auth_and_updates_reference(self):
        record = MagicMock(
            customerBill_id="cb-1", payment_type="redsys", payment_reference="redsys-payment-old", retry_count=1
        )
        self.payment_record.get_by_customer_bill_id.return_value = record
        self.client.check_payment_status.return_value = "failed"
        self.client.charge_recurring.return_value = ("redsys-payment-new", "succeeded")

        self.command._process_cb(self.cb)

        self.client.check_payment_status.assert_called_once_with("redsys-payment-old")
        self.client.charge_recurring.assert_called_once_with(self.cb, record, "pre-auth-id", 18.39, "EUR")
        self.payment_record.update_payment_reference.assert_not_called()

    def test_pending_payment_is_checked_without_starting_another_payment(self):
        record = MagicMock(customerBill_id="cb-1", payment_type="redsys", payment_reference="redsys-payment-1")
        self.payment_record.get_by_customer_bill_id.return_value = record
        self.client.check_payment_status.return_value = "pending"

        self.command._process_cb(self.cb)

        self.client.check_payment_status.assert_called_once_with("redsys-payment-1")
        self.client.charge_recurring.assert_not_called()
        self.command._get_payment_info_from_cb.assert_not_called()
        self.command._billing_client.set_customer_bill.assert_not_called()

    def test_succeeded_payment_is_settled_without_starting_another_payment(self):
        record = MagicMock(customerBill_id="cb-1", payment_type="redsys", payment_reference="redsys-payment-1")
        self.payment_record.get_by_customer_bill_id.return_value = record
        self.client.check_payment_status.return_value = "succeeded"

        self.command._process_cb(self.cb)

        self.client.check_payment_status.assert_called_once_with("redsys-payment-1")
        self.client.charge_recurring.assert_not_called()
        self.command._billing_client.set_customer_bill.assert_called_once_with("settled", "cb-1")

    def test_attempt_without_reference_does_not_increment_retry(self):
        self.payment_record.get_by_customer_bill_id.side_effect = self.real_does_not_exist
        self.client.charge_recurring.return_value = (None, "failed")

        self.command._process_cb(self.cb)

        self.client.charge_recurring.assert_called_once_with(self.cb, None, "pre-auth-id", 18.39, "EUR")
        self.payment_record.increment_retry_count.assert_not_called()
        self.command._billing_client.set_customer_bill.assert_not_called()

    def test_get_payment_info_reads_redsys_pre_authorization(self):
        command = payment_scheduler.Command()
        command._billing_client = MagicMock()
        command._inventory_client = MagicMock()
        command._billing_client.get_product_id_by_cb.return_value = "product-1"
        command._inventory_client.get_product.return_value = {
            "productCharacteristic": [
                {
                    "name": "redsysPreAuthorizationId",
                    "value": "redsys-token:cof-transaction",
                }
            ]
        }

        payment_type, pre_auth_id = command._get_payment_info_from_cb("cb-1")

        self.assertEqual(payment_type, "redsys")
        self.assertEqual(pre_auth_id, "redsys-token:cof-transaction")
