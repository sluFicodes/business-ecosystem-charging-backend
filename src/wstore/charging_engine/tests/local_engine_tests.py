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

import datetime
from django.test import TestCase
from parameterized import parameterized
from mock import MagicMock, patch

from wstore.charging_engine.engines.local_engine import LocalEngine


# Mock prices returned by PriceEngine
PRICE_ONETIME = [
    {
        "priceType": "one time",
        "recurringChargePeriod": "onetime",
        "price": {
            "taxRate": "21.0",
            "dutyFreeAmount": {"unit": "EUR", "value": "10.0"},
            "taxIncludedAmount": {"unit": "EUR", "value": "12.10"}
        }
    }
]

PRICE_RECURRING = [
    {
        "priceType": "recurring",
        "recurringChargePeriod": "1 month",
        "price": {
            "taxRate": "21.0",
            "dutyFreeAmount": {"unit": "EUR", "value": "15.0"},
            "taxIncludedAmount": {"unit": "EUR", "value": "18.15"}
        }
    }
]

PRICE_USAGE = [
    {
        "priceType": "usage",
        "recurringChargePeriod": "month",
        "price": {
            "taxRate": "21.0",
            "dutyFreeAmount": {"unit": "EUR", "value": "5.0"},
            "taxIncludedAmount": {"unit": "EUR", "value": "6.05"}
        }
    }
]

PRICE_MULTIPLE = [
    {
        "priceType": "one time",
        "recurringChargePeriod": "onetime",
        "price": {
            "taxRate": "21.0",
            "dutyFreeAmount": {"unit": "EUR", "value": "10.0"},
            "taxIncludedAmount": {"unit": "EUR", "value": "12.10"}
        }
    },
    {
        "priceType": "recurring",
        "recurringChargePeriod": "1 month",
        "price": {
            "taxRate": "21.0",
            "dutyFreeAmount": {"unit": "EUR", "value": "15.0"},
            "taxIncludedAmount": {"unit": "EUR", "value": "18.15"}
        }
    }
]

# Expected results for _build_charges
EXPECTED_CHARGE_ONETIME = [
    {
        "appliedBillingRateType": "one time",
        "isBilled": False,
        "appliedTax": [
            {
                "taxCategory": "VAT",
                "taxRate": "21.0",
                "taxAmount": {
                    "unit": "EUR",
                    "value": "2.10"
                }
            }
        ],
        "taxIncludedAmount": {
            "unit": "EUR",
            "value": "12.10"
        },
        "taxExcludedAmount": {
            "unit": "EUR",
            "value": "10.0"
        },
        "billingAccount": {"id": "test-billing-account"},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z"
        }
    }
]

EXPECTED_CHARGE_RECURRING = [
    {
        "appliedBillingRateType": "recurring",
        "isBilled": False,
        "appliedTax": [
            {
                "taxCategory": "VAT",
                "taxRate": "21.0",
                "taxAmount": {
                    "unit": "EUR",
                    "value": "3.15"
                }
            }
        ],
        "taxIncludedAmount": {
            "unit": "EUR",
            "value": "18.15"
        },
        "taxExcludedAmount": {
            "unit": "EUR",
            "value": "15.0"
        },
        "billingAccount": {"id": "test-billing-account"},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    }
]

EXPECTED_CHARGE_USAGE = [
    {
        "appliedBillingRateType": "usage",
        "isBilled": False,
        "appliedTax": [
            {
                "taxCategory": "VAT",
                "taxRate": "21.0",
                "taxAmount": {
                    "unit": "EUR",
                    "value": "1.05"
                }
            }
        ],
        "taxIncludedAmount": {
            "unit": "EUR",
            "value": "6.05"
        },
        "taxExcludedAmount": {
            "unit": "EUR",
            "value": "5.0"
        },
        "billingAccount": {"id": "test-billing-account"},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    }
]

EXPECTED_CHARGE_MULTIPLE = [
    {
        "appliedBillingRateType": "one time",
        "isBilled": False,
        "appliedTax": [
            {
                "taxCategory": "VAT",
                "taxRate": "21.0",
                "taxAmount": {
                    "unit": "EUR",
                    "value": "2.10"
                }
            }
        ],
        "taxIncludedAmount": {
            "unit": "EUR",
            "value": "12.10"
        },
        "taxExcludedAmount": {
            "unit": "EUR",
            "value": "10.0"
        },
        "billingAccount": {"id": "test-billing-account"},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z"
        }
    },
    {
        "appliedBillingRateType": "recurring",
        "isBilled": False,
        "appliedTax": [
            {
                "taxCategory": "VAT",
                "taxRate": "21.0",
                "taxAmount": {
                    "unit": "EUR",
                    "value": "3.15"
                }
            }
        ],
        "taxIncludedAmount": {
            "unit": "EUR",
            "value": "18.15"
        },
        "taxExcludedAmount": {
            "unit": "EUR",
            "value": "15.0"
        },
        "billingAccount": {"id": "test-billing-account"},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    }
]


class LocalEngineTestCase(TestCase):
    tags = ("local_engine", "billing", "charges")
    maxDiff = None

    @parameterized.expand([
        (
            "onetime_period",
            "onetime",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z"
            }
        ),
        (
            "one_month_period",
            "1 month",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2024-02-14T00:00:00Z"
            }
        ),
        (
            "month_period",
            "month",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2024-02-14T00:00:00Z"
            }
        ),
        (
            "three_months_period",
            "3 month",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2024-04-14T00:00:00Z"
            }
        ),
        (
            "two_weeks_period",
            "2 week",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2024-01-29T00:00:00Z"
            }
        ),
        (
            "seven_days_period",
            "7 day",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2024-01-22T00:00:00Z"
            }
        ),
        (
            "one_year_period",
            "1 year",
            datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc),
            {
                "startDateTime": "2024-01-15T00:00:00Z",
                "endDateTime": "2025-01-14T00:00:00Z"
            }
        ),
    ])
    def test_build_period_coverage(self, name, charge_period, now, expected_result):
        order = MagicMock()
        engine = LocalEngine(order)

        result = engine._build_period_coverage(charge_period, now)

        self.assertEqual(result, expected_result)

    @parameterized.expand([
        ("invalid_format", "invalid"),
        ("empty_period", ""),
        ("unknown_unit", "3 fortnights"),
    ])
    def test_build_period_coverage_invalid(self, name, charge_period):
        order = MagicMock()
        engine = LocalEngine(order)
        now = datetime.datetime(2024, 1, 15, 0, 0, 0, tzinfo=datetime.timezone.utc)

        with self.assertRaises(ValueError):
            engine._build_period_coverage(charge_period, now)

    @parameterized.expand([
        ("onetime_charge", PRICE_ONETIME, EXPECTED_CHARGE_ONETIME),
        ("recurring_charge", PRICE_RECURRING, EXPECTED_CHARGE_RECURRING),
        ("usage_charge", PRICE_USAGE, EXPECTED_CHARGE_USAGE),
        ("multiple_charges", PRICE_MULTIPLE, EXPECTED_CHARGE_MULTIPLE),
    ])
    def test_build_charges(self, name, mock_prices, expected_result):
        order = MagicMock()
        order.tax_address = {"country": "ES"}
        engine = LocalEngine(order)

        # Mock the price engine
        engine._price_engine = MagicMock()
        engine._price_engine.calculate_prices.return_value = mock_prices

        # Mock datetime to have consistent test results
        fixed_datetime = datetime.datetime(2024, 1, 15, 10, 30, 45, tzinfo=datetime.timezone.utc)

        item = {
            "itemTotalPrice": [
                {
                    "productOfferingPrice": {
                        "id": "urn:ngsi-ld:productOfferingPrice:1"
                    }
                }
            ]
        }

        billing_account = {"id": "test-billing-account"}

        with patch('wstore.charging_engine.engines.local_engine.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = fixed_datetime
            mock_datetime.timezone = datetime.timezone
            mock_datetime.timedelta = datetime.timedelta

            result = engine._build_charges(item, billing_account)

        self.assertEqual(result, expected_result)
        engine._price_engine.calculate_prices.assert_called_once_with(
            {
                "productOrderItem": [item],
                "billingAccount": {"resolved": "ES"}
            },
            preview=False
        )
