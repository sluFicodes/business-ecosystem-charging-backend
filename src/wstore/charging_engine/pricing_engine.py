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

from logging import getLogger
import requests
from decimal import ROUND_HALF_UP, Decimal
from datetime import datetime
from zeep import Client, Settings

from django.conf import settings

from wstore.store_commons.utils.url import get_service_url

WSDL_URL = "https://ec.europa.eu/taxation_customs/tedb/ws/VatRetrievalService.wsdl"
ENDPOINT_URL = "https://ec.europa.eu/taxation_customs/tedb/ws/"
logger = getLogger("wstore.default_logger")

class PriceEngine:
    def _download_pricing(self, pop_id):
        price_url = get_service_url("catalog", "/productOfferingPrice/{}".format(pop_id))
        request = requests.get(price_url, verify=settings.VERIFY_REQUESTS)
        pricing = request.json()
        return pricing

    def _process_usage_value(self, component, usage):
        for usage_item in usage:
            if (
                "usageSpecification" in usage_item
                and "id" in usage_item["usageSpecification"]
                and "usageSpecId" in component
                and usage_item["usageSpecification"]["id"] == component["usageSpecId"]
            ):
                for usage_char in usage_item["usageCharacteristic"]:
                    if usage_char["name"] == component["unitOfMeasure"]["units"]:
                        return Decimal(str(usage_char["value"])) * Decimal(str(component["price"]["value"]))

        return Decimal("0")

    def _process_price_component(self, component, options, aggregated, usage):
        # Check if the component needs to be applied
        tail_value = None
        if "prodSpecCharValueUse" in component:
            conditions = {}

            for val in component["prodSpecCharValueUse"]:
                value = "tailored"
                if "productSpecCharacteristicValue" in val and len(val["productSpecCharacteristicValue"]) > 0:
                    value = val["productSpecCharacteristicValue"][0]["value"]
                conditions[val["name"].lower()] = value

            found = 0
            for option in options:
                if option["name"].lower() in conditions:
                    if conditions[option["name"].lower()] == "tailored":
                        found += 1
                        tail_value = Decimal(str(option["value"]))
                        continue

                    if str(conditions[option["name"].lower()]) == str(option["value"]):
                        found += 1

            if len(conditions) != found:
                # The component is not processed
                return

        if component["priceType"] not in aggregated:
            aggregated[component["priceType"]] = {}

        period_key = "onetime"
        if "recurringChargePeriodType" in component and "recurringChargePeriodLength" in component:
            period_key = "{} {}".format(
                component["recurringChargePeriodLength"], component["recurringChargePeriodType"]
            )

        if component["priceType"].lower() == "usage":
            period_key = "month"

        if period_key not in aggregated[component["priceType"]]:
            aggregated[component["priceType"]][period_key] = {"value": Decimal("0")}

        component_value = Decimal(str(component["price"]["value"]))
        if component["priceType"] == "usage" and len(usage) > 0:
            component_value = self._process_usage_value(component, usage)

        if tail_value is None:
            aggregated[component["priceType"]][period_key]["value"] += component_value
        else:
            tailored_price = component_value * tail_value
            aggregated[component["priceType"]][period_key]["value"] += tailored_price

    def _get_party_char(self, party_id):
        # Check if the party is an individual or an organization
        user_type = party_id.rsplit(sep=":")[2]
        try:
            party_url = get_service_url("party", f"/{user_type}/{party_id}")
            response = requests.get(party_url)
            response.raise_for_status()
            result = response.json()
            return result["partyCharacteristic"]
        except:
            raise ValueError("Error fetching party information")

    def _get_countries(self, related_party):
        customer_country = None
        seller_country = None
        for party_ref in related_party:
            party_chars = self._get_party_char(party_ref["id"])
            country = None
            for char in party_chars:
                if char["name"].lower() == "country" and "value" in char:
                    country = char["value"]
            if "role" in party_ref and party_ref["role"].lower() == settings.CUSTOMER_ROLE.lower():
                customer_country = country
            elif "role" in party_ref and party_ref["role"].lower() == settings.PROVIDER_ROLE.lower():
                seller_country = country
            # else cannot find the role

        return customer_country, seller_country

    def _calculate_org_taxes(self, related_party):
        # only between org taxes
        customer_country, seller_country = self._get_countries(related_party)
        if (
            customer_country is None
            or seller_country is None
            or (customer_country is not None and seller_country is not None and customer_country != seller_country)
        ):
            return 0
        date_now = datetime.now().date().isoformat()
        customer_country = (
            customer_country if customer_country.lower() != "gr" else "EL"
        )  # Greece in fiscal contexts uses EL as country code
        args = {"memberStates": {"isoCode": customer_country}, "situationOn": date_now}

        client = Client(wsdl=WSDL_URL, settings=Settings())

        # Establecer endpoint manualmente (por si el WSDL apunta a http)
        client.service._binding_options["address"] = ENDPOINT_URL

        # Realizar la petición
        try:
            response = client.service.retrieveVatRates(**args)
            results = response.vatRateResults
            standard = list(filter(lambda item: "type" in item and item["type"].lower() == "standard", results))
            if len(standard) == 1:
                return standard[0]["rate"]["value"]
            else:
                for vat in standard:
                    if vat["comment"] is None:
                        return vat["rate"]["value"]
            raise ValueError("Standard VAT rate unavailable for the selected country.")
        except ValueError as e:
            logger.error("Error calling the service", e)
            raise

    def calculate_prices(self, data, usage=[]):
        aggregated = {}

        item = data["productOrderItem"][0]
        # 1) Download the POP
        if "itemTotalPrice" not in item or len(item["itemTotalPrice"]) == 0:
            # The item has no price, it is free
            return []

        pop_id = item["itemTotalPrice"][0]["productOfferingPrice"]["id"]

        pricing = self._download_pricing(pop_id)

        # If the price is a bundle download the components
        to_process = []
        if pricing["isBundle"]:
            to_process = [self._download_pricing(pop["id"]) for pop in pricing["bundledPopRelationship"]]
        else:
            to_process = [pricing]

        options = []
        if "product" in item and "productCharacteristic" in item["product"]:
            options = item["product"]["productCharacteristic"]

        for component in to_process:
            self._process_price_component(component, options, aggregated, usage)

        # If the POP is not a bundle check the pricing
        # If the bundle is a pop download the models

        # If a characteristic has been defined check if the component have to be applied
        # If the charactristic is tailored apply the value

        result = []
        tax = Decimal(
            repr(self._calculate_org_taxes(data["relatedParty"]))
        )  # Needs to repr() first because Decimal(20.1) returns 20.10000000000000142108547152020037174224853515625
        for priceType in aggregated.keys():
            for period in aggregated[priceType].keys():
                result.append(
                    {
                        "priceType": priceType,
                        "recurringChargePeriod": period,
                        "price": {
                            "taxRate": str(tax),
                            "dutyFreeAmount": {"unit": "EUR", "value": str(aggregated[priceType][period]["value"])},
                            "taxIncludedAmount": {
                                "unit": "EUR",
                                "value": str(
                                    (
                                        Decimal(aggregated[priceType][period]["value"])
                                        + (Decimal(aggregated[priceType][period]["value"]) * tax / Decimal(100))
                                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                                ),
                            },
                        },
                        "priceAlteration": [],
                    }
                )

        return result
