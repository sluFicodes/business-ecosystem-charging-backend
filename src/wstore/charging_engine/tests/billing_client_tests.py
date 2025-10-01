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

from wstore.charging_engine.charging.billing_client import BillingClient


# Test data for ACBRs (Applied Customer Billing Rates)
# Single one time ACBR
ACBR_SINGLE_ONETIME = [
    {
        "id": "acbr-1",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 12.10},
        "taxExcludedAmount": {"unit": "EUR", "value": 10.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    }
]

# Multiple one time ACBRs with same period (should aggregate)
ACBR_MULTIPLE_ONETIME_SAME_PERIOD = [
    {
        "id": "acbr-1",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 12.10},
        "taxExcludedAmount": {"unit": "EUR", "value": 10.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    },
    {
        "id": "acbr-2",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 6.05},
        "taxExcludedAmount": {"unit": "EUR", "value": 5.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    }
]

# Multiple recurring ACBRs with same period (should aggregate)
ACBR_MULTIPLE_RECURRING_SAME_PERIOD = [
    {
        "id": "acbr-3",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    },
    {
        "id": "acbr-4",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 12.10},
        "taxExcludedAmount": {"unit": "EUR", "value": 10.0},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    }
]

# Mixed types with same period (should NOT aggregate together)
ACBR_MIXED_TYPES_SAME_PERIOD = [
    {
        "id": "acbr-5",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 12.10},
        "taxExcludedAmount": {"unit": "EUR", "value": 10.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    },
    {
        "id": "acbr-6",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    }
]

# Same type but different periods (should NOT aggregate)
ACBR_SAME_TYPE_DIFF_PERIOD = [
    {
        "id": "acbr-7",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    },
    {
        "id": "acbr-8",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-02-15T00:00:00Z",
            "endDateTime": "2024-03-16T00:00:00Z"
        }
    }
]

# Complex scenario: multiple types and periods
ACBR_COMPLEX = [
    {
        "id": "acbr-9",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 12.10},
        "taxExcludedAmount": {"unit": "EUR", "value": 10.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    },
    {
        "id": "acbr-10",
        "type": "one time",
        "taxIncludedAmount": {"unit": "EUR", "value": 6.05},
        "taxExcludedAmount": {"unit": "EUR", "value": 5.0},
        "periodCoverage": {"startDateTime": "2024-01-15T00:00:00Z"}
    },
    {
        "id": "acbr-11",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-01-15T00:00:00Z",
            "endDateTime": "2024-02-14T00:00:00Z"
        }
    },
    {
        "id": "acbr-12",
        "type": "recurring",
        "taxIncludedAmount": {"unit": "EUR", "value": 18.15},
        "taxExcludedAmount": {"unit": "EUR", "value": 15.0},
        "periodCoverage": {
            "startDateTime": "2024-02-15T00:00:00Z",
            "endDateTime": "2024-03-16T00:00:00Z"
        }
    }
]


class BillingClientTestCase(TestCase):
    tags = ("billing", "customer_bill", "aggregation")
    maxDiff = None

    @parameterized.expand([
        (
            "single_onetime",
            ACBR_SINGLE_ONETIME,
            1,  # Expected number of customer bills
            [
                {
                    "type": "one time",
                    "taxIncludedAmount": 12.10,
                    "taxExcludedAmount": 10.0,
                    "acbr_count": 1
                }
            ]
        ),
        (
            "multiple_onetime_same_period_aggregates",
            ACBR_MULTIPLE_ONETIME_SAME_PERIOD,
            1,  # Should aggregate into 1 customer bill
            [
                {
                    "type": "one time",
                    "taxIncludedAmount": 18.15,  # 12.10 + 6.05
                    "taxExcludedAmount": 15.0,    # 10.0 + 5.0
                    "acbr_count": 2
                }
            ]
        ),
        (
            "multiple_recurring_same_period_aggregates",
            ACBR_MULTIPLE_RECURRING_SAME_PERIOD,
            1,  # Should aggregate into 1 customer bill
            [
                {
                    "type": "recurring",
                    "taxIncludedAmount": 30.25,  # 18.15 + 12.10
                    "taxExcludedAmount": 25.0,    # 15.0 + 10.0
                    "acbr_count": 2
                }
            ]
        ),
        (
            "mixed_types_same_period_no_aggregate",
            ACBR_MIXED_TYPES_SAME_PERIOD,
            2,  # Should create 2 separate customer bills
            [
                {
                    "type": "one time",
                    "taxIncludedAmount": 12.10,
                    "taxExcludedAmount": 10.0,
                    "acbr_count": 1
                },
                {
                    "type": "recurring",
                    "taxIncludedAmount": 18.15,
                    "taxExcludedAmount": 15.0,
                    "acbr_count": 1
                }
            ]
        ),
        (
            "same_type_diff_period_no_aggregate",
            ACBR_SAME_TYPE_DIFF_PERIOD,
            2,  # Should create 2 separate customer bills
            [
                {
                    "type": "recurring",
                    "taxIncludedAmount": 18.15,
                    "taxExcludedAmount": 15.0,
                    "acbr_count": 1
                },
                {
                    "type": "recurring",
                    "taxIncludedAmount": 18.15,
                    "taxExcludedAmount": 15.0,
                    "acbr_count": 1
                }
            ]
        ),
        (
            "complex_scenario",
            ACBR_COMPLEX,
            3,  # Should create 3 customer bills: 1 onetime + 2 recurring (different periods)
            [
                {
                    "type": "one time",
                    "taxIncludedAmount": 18.15,  # 12.10 + 6.05
                    "taxExcludedAmount": 15.0,    # 10.0 + 5.0
                    "acbr_count": 2
                },
                {
                    "type": "recurring",
                    "taxIncludedAmount": 18.15,
                    "taxExcludedAmount": 15.0,
                    "acbr_count": 1
                },
                {
                    "type": "recurring",
                    "taxIncludedAmount": 18.15,
                    "taxExcludedAmount": 15.0,
                    "acbr_count": 1
                }
            ]
        ),
    ])
    def test_create_customer_bill_aggregation(self, name, acbrs, expected_cb_count, expected_cbs):
        client = BillingClient()

        billing_acc_ref = {"id": "billing-account-1"}
        party = [{"id": "party-1", "role": "Customer"}]

        # Mock _create_cb_api to return a mock customer bill
        mock_cb_responses = []
        for i in range(expected_cb_count):
            mock_cb_responses.append({
                "id": f"cb-{i+1}",
                "taxIncludedAmount": {"unit": "EUR", "value": 0.0},  # Will be overridden
                "taxExcludedAmount": {"unit": "EUR", "value": 0.0}   # Will be overridden
            })

        call_index = [0]  # Use list to allow modification in nested function

        def mock_create_cb_api(unit, taxIncluded, taxExcluded, billing_acc_ref, current_time, periodCoverage, party):
            response = mock_cb_responses[call_index[0]].copy()
            response["taxIncludedAmount"] = {"unit": unit, "value": taxIncluded}
            response["taxExcludedAmount"] = {"unit": unit, "value": taxExcluded}
            call_index[0] += 1
            return response

        client._create_cb_api = MagicMock(side_effect=mock_create_cb_api)
        client.set_acbrs_cb = MagicMock()

        # Execute
        result = client.create_customer_bill(acbrs, billing_acc_ref, party)

        # Assertions
        self.assertEqual(len(result), expected_cb_count,
                        f"Expected {expected_cb_count} customer bills, got {len(result)}")

        # Verify each customer bill
        for i, expected in enumerate(expected_cbs):
            actual = result[i]
            self.assertEqual(actual["type"], expected["type"])
            self.assertAlmostEqual(float(actual["taxIncludedAmount"]), expected["taxIncludedAmount"], places=2)
            self.assertAlmostEqual(float(actual["taxExcludedAmount"]), expected["taxExcludedAmount"], places=2)
            self.assertEqual(actual["unit"], "EUR")

        # Verify _create_cb_api was called the correct number of times
        self.assertEqual(client._create_cb_api.call_count, expected_cb_count)

        # Verify set_acbrs_cb was called correctly
        total_acbr_refs = sum(expected["acbr_count"] for expected in expected_cbs)
        self.assertEqual(client.set_acbrs_cb.call_count, expected_cb_count)

        # Verify that each set_acbrs_cb call has the correct number of ACBRs
        for i, call in enumerate(client.set_acbrs_cb.call_args_list):
            acbr_refs = call[0][0]  # First argument is the list of ACBR refs
            self.assertEqual(len(acbr_refs), expected_cbs[i]["acbr_count"],
                           f"Customer bill {i} should have {expected_cbs[i]['acbr_count']} ACBRs")
