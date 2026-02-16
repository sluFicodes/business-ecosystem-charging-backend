# -*- coding: utf-8 -*-

# Copyright (c) 2024 Future Internet Consulting and Development Solutions S.L.

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

from copy import deepcopy


BASIC_PROD_SPEC = {
    "id": "urn:ProductSpecification:12345",
    "name": "Basic Product",
    "productSpecCharacteristic": []
}

BASE_OFFERING = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "urn:ProductSpecification:12345", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [{
        "id": "urn:product-offering-price:1234",
        "href": "urn:product-offering-price:1234"
    }]
}

BASE_OFFERING_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "urn:ProductSpecification:12345", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [{
        "id": "urn:product-offering-price:1234",
        "href": "urn:product-offering-price:1234"
    }, {
        "id": "urn:product-offering-price:4567",
        "href": "urn:product-offering-price:4567"
    }]
}

OT_OFFERING_PRICE = {
    "id": "urn:product-offering-price:1234",
    "name": "plan",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "1.0"
    }
}

OT_OFFERING_PRICE_2 = {
    "id": "urn:product-offering-price:4567",
    "name": "plan",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "1.0"
    }
}

OPEN_OFFERING_PRICE = {
    "id": "urn:product-offering-price:1234",
    "name": "open",
    "description": "Open offering"
}

ZERO_PRICING = {
    "name": "plan",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "0"
    }
}

FREE_OFFERING = {
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
}

CUSTOM_OFFERING_PRICING = {
    "id": "urn:product-offering-price:1234",
    "name": "The custom pricing",
    "priceType": "custom",
    "description": "Custom pricing description"
}

CUSTOM_OFFERING_PRICING_2 = {
    "id": "urn:product-offering-price:4567",
    "name": "The custom pricing 2",
    "priceType": "custom",
    "description": "Custom pricing description"
}


CUSTOM_PRICING_OFFERING_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "The custom pricing",
            "priceType": "custom",
            "description": "Custom pricing description"
        },
        {
            "name": "The custom pricing 2",
            "priceType": "custom",
            "description": "Custom pricing description"
        }
    ],
}

CUSTOM_MULTIPLE = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "The custom pricing",
            "priceType": "custom",
            "description": "Custom pricing description"
        },
        {
            "name": "plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1"
                }
            },
        }
    ],
}

BUNDLE_OFFERING = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
    "bundledProductOffering": [{"id": "6"}, {"id": "7"}],
}

OPEN_BUNDLE = deepcopy(BUNDLE_OFFERING)
OPEN_BUNDLE["productOfferingPrice"] = [{
    "id": "urn:product-offering-price:1234",
    "href": "urn:product-offering-price:1234"
}]

BUNDLE_MISSING_FIELD = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
}

BUNDLE_MISSING_ELEMS = {
    "isBundle": True,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {},
    "bundledProductOffering": [{"id": "6"}],
}


MISSING_PRICETYPE = {
    "name": "plan",
    "price": {"currencyCode": "EUR"}
}

INVALID_PRICETYPE = {
    "name": "plan",
    "priceType": "invalid",
    "price": {"currencyCode": "EUR"}
}

MISSING_PERIOD = {
    "name": "plan",
    "priceType": "recurring",
    "price": {"currencyCode": "EUR"}
}

INVALID_PERIOD = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "invalid",
    "price": {"currencyCode": "EUR"},
}

MISSING_PRICE = {"name": "plan", "priceType": "recurring", "recurringChargePeriodType": "month"}

MISSING_CURRENCY = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "month",
    "price": {},
}

INVALID_CURRENCY = {
    "name": "plan",
    "priceType": "recurring",
    "recurringChargePeriodType": "month",
    "price": {
        "unit": "invalid"
    }
}

MISSING_NAME = {"priceType": "recurring", "recurringChargePeriod": "monthly", "price": {}}

MULTIPLE_NAMES = {
    "productSpecification": {"id": "20", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {
            "name": "plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1.0"
                }
            },
        },
        {
            "name": "Plan",
            "priceType": "one time",
            "price": {
                "taxIncludedAmount": {
                    "unit": "EUR",
                    "value": "1.0"
                }
            },
        },
    ],
}

OPEN_MIXED = {
    "id": "3",
    "href": "http://catalog.com/offerin3",
    "isBundle": False,
    "name": "TestOffering",
    "version": "1.0",
    "productSpecification": {"id": "urn:ProductSpecification:12345", "href": "http://catalog.com/products/20"},
    "productOfferingPrice": [
        {"id": "urn:price:1234", "href": "urn:price:1234"},
        {"id": "urn:price:5678", "href": "urn:price:5678"}
    ],
}

OPEN_MIXED_PRICE = {
    "id": "urn:price:5678",
    "name": "single",
    "priceType": "one time",
    "price": {
        "unit": "EUR",
        "value": "1.0"
    }
}

PROFILE_PROD_SPEC = {
    "id": "urn:ProductSpecification:12345",
    "name": "Linux VM",
    "brand": "FICODES",
    "productNumber": "CSC-340-NGFW",
    "description": "A Linux VM with multiple options",
    "isBundle": False,
    "lastUpdate": "2020-09-23T16:42:23.0Z",
    "lifecycleStatus": "Active",
    "relatedParty": [{
        "id": "1234",
        "href": "https://mycsp.com:8080/tmf-api/partyManagement/v4/partyRole/1234",
        "role": "Owner",
        "name": "Gustave Flaubert",
    }],
    "productSpecCharacteristic": [{
        "id": "urn:Characteristic:1234",
        "name": "CPU",
        "configurable": True,
        "valueType": "number",
        "productSpecCharacteristicValue": [{
            "isDefault": True,
            "value": "4",
            "unitOfMeasure": "cpus"
        }, {
            "isDefault": False,
            "value": "8",
            "unitOfMeasure": "cpus"
        }]
    }, {
        "id": "urn:Characteristic:5678",
        "name": "RAM Memory",
        "configurable": True,
        "valueType": "number",
        "productSpecCharacteristicValue": [{
            "isDefault": True,
            "value": "8",
            "unitOfMeasure": "gb"
        }, {
            "isDefault": False,
            "value": "16",
            "unitOfMeasure": "gb"
        }]
    }, {
        "id": "urn:Characteristic:09876",
        "name": "Storage",
        "configurable": True,
        "valueType": "number",
        "productSpecCharacteristicValue": [{
            "isDefault": True,
            "value": "10",
            "unitOfMeasure": "gb"
        }, {
            "isDefault": False,
            "value": "30",
            "unitOfMeasure": "gb"
        }, {
            "isDefault": False,
            "value": "50",
            "unitOfMeasure": "gb"
        }]
    }],
    "resourceSpecification": [{
        "id": "urn:ResourceSpecification:1234",
        "href": "urn:ResourceSpecification:1234"
    }]
}

PROFILE_PLAN = {
    "id": "urn:product-offering-price:1234",
    "href": "urn:product-offering-price:1234",
    "name": "Price SMALL",
    "description": "4CPU, 8GB RAM, 20GB HD: 24 eu per m, recurring prepaid",
    "version": "1.0",
    "priceType": "recurring-prepaid",
    "recurringChargePeriodType": "month",
    "recurringChargePeriodLength": 1,
    "isBundle": False,
    "lifecycleStatus": "Active",
    "price": {
        "unit": "EUR",
        "value": 24
    },
    "prodSpecCharValueUse": [{
      "id": "urn:Characteristic:1234",
      "name": "CPU",
      "valueType": "number",
      "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "4",
            "unitOfMeasure": "cpus"
        }
      ],
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }, {
      "id": "urn:Characteristic:5678",
      "name": "RAM Memory",
      "valueType": "number",
      "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "8",
            "unitOfMeasure": "gb"
        }
      ],
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }, {
      "id": "urn:Characteristic:09876",
      "name": "Storage",
      "valueType": "number",
      "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "10",
            "unitOfMeasure": "gb"
        }
      ],
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }]
}

PROFILE_PLAN_MULTIPLE = {
    "id": "urn:ProductOfferingPrice:1745",
    "href": "urn:ProductOfferingPrice:1745",
    "name": "Tailored Price",
    "description": "Tailored price plan",
    "version": "1.0",
    "isBundle": True,
    "lifecycleStatus": "Active",
    "bundledPopRelationship": [{
        "id": "urn:ProductOfferingPrice:1111",
        "href": "urn:ProductOfferingPrice:1111"
    }, {
        "id": "urn:ProductOfferingPrice:1112",
        "href": "urn:ProductOfferingPrice:1112"
    }],
    "prodSpecCharValueUse": [{
      "id": "urn:Characteristic:1234",
      "name": "CPU",
      "valueType": "number",
      "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "4",
            "unitOfMeasure": "cpus"
        }
      ],
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }, {
      "id": "urn:Characteristic:5678",
      "name": "RAM Memory",
      "valueType": "number",
      "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "8",
            "unitOfMeasure": "gb"
        }
      ],
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }]
}

PRICE_COMPONENT_1 = {
    "id": "urn:ProductOfferingPrice:1111",
    "href": "urn:ProductOfferingPrice:1111",
    "name": "CPU Price component",
    "description": "1.50 eu per CPU per month",
    "version": "1.0",
    "priceType": "recurring-prepaid",
    "recurringChargePeriodType": "month",
    "recurringChargePeriodLength": 1,
    "isBundle": False,
    "lifecycleStatus": "Active",
    "unitOfMeasure": {
        "amount": 1,
        "units": "cpu"
    },
    "price": {
        "unit": "EUR",
        "value": 1.50
    }
}

PRICE_COMPONENT_2 = {
    "id": "urn:ProductOfferingPrice:1112",
    "href": "urn:ProductOfferingPrice:1112",
    "name": "RAM Price component",
    "description": "1 eu per GB per m",
    "version": "1.0",
    "priceType": "recurring-prepaid",
    "recurringChargePeriodType": "month",
    "recurringChargePeriodLength": 1,
    "isBundle": False,
    "lifecycleStatus": "Active",
    "unitOfMeasure": {
        "amount": 1,
        "units": "gb"
    },
    "price": {
        "unit": "EUR",
        "value": 1
    }
}

COMPONENT_PLAN = {
    "id": "urn:ProductOfferingPrice:1745",
    "href": "urn:ProductOfferingPrice:1745",
    "name": "Tailored Price",
    "description": "Tailored price plan",
    "version": "1.0",
    "isBundle": True,
    "lifecycleStatus": "Active",
    "bundledPopRelationship": [{
        "id": "urn:ProductOfferingPrice:1111",
        "href": "urn:ProductOfferingPrice:1111"
    }, {
        "id": "urn:ProductOfferingPrice:1112",
        "href": "urn:ProductOfferingPrice:1112"
    }]
}


PRICE_COMPONENT_3 = {
    "id": "urn:ProductOfferingPrice:1111",
    "href": "urn:ProductOfferingPrice:1111",
    "name": "CPU Price component",
    "description": "1.50 eu per CPU per month",
    "version": "1.0",
    "priceType": "recurring-prepaid",
    "recurringChargePeriodType": "month",
    "recurringChargePeriodLength": 1,
    "isBundle": False,
    "lifecycleStatus": "Active",
    "unitOfMeasure": {
        "amount": 1,
        "units": "cpu"
    },
    "price": {
        "unit": "EUR",
        "value": 1.50
    },
    "tax": [{
        "taxAmount": {
            "unit": "EUR",
            "value": 0.2
        },
        "taxCategory": "VAT",
        "taxRate": 20.0
    }],
    "prodSpecCharValueUse": [{
      "id": "urn:Characteristic:1234",
      "name": "CPU",
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }]
}

PRICE_COMPONENT_4 = {
    "id": "urn:ProductOfferingPrice:1112",
    "href": "urn:ProductOfferingPrice:1112",
    "name": "RAM Price component",
    "description": "1 eu per GB per m",
    "version": "1.0",
    "priceType": "recurring-prepaid",
    "recurringChargePeriodType": "month",
    "recurringChargePeriodLength": 1,
    "isBundle": False,
    "lifecycleStatus": "Active",
    "unitOfMeasure": {
        "amount": 1,
        "units": "gb"
    },
    "price": {
        "unit": "EUR",
        "value": 1
    },
    "tax": [{
        "taxAmount": {
            "unit": "EUR",
            "value": 0.2
        },
        "taxCategory": "VAT",
        "taxRate": 20.0
    }],
    "prodSpecCharValueUse": [{
      "id": "urn:Characteristic:5678",
      "name": "RAM",
      "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
      }
    }]
}

INVALID_PROD_SPEC = {
    "id": "urn:ProductSpecification:20",
    "name": "Invalid Product Spec",
    "productSpecCharacteristic": []
}

INVALID_SPEC = deepcopy(BASE_OFFERING)
INVALID_SPEC["productSpecification"] =  {"id": "urn:ProductSpecification:20"}

INVALID_USE = deepcopy(PROFILE_PLAN)
INVALID_USE["prodSpecCharValueUse"] = [{
    "id": "urn:Characteristic:5555",
    "name": "CPU",
    "valueType": "number",
    "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "4",
            "unitOfMeasure": "cpus"
        }
    ],
    "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
    }
}]

INVALID_USE_VALUE = deepcopy(PROFILE_PLAN)
INVALID_USE_VALUE["prodSpecCharValueUse"] = [{
    "id": "urn:Characteristic:1234",
    "name": "CPU",
    "valueType": "number",
    "productSpecCharacteristicValue": [
        {
            "isDefault": True,
            "value": "27",
            "unitOfMeasure": "cpus"
        }
    ],
    "productSpecification": {
        "id": "urn:ProductSpecification:12345",
        "href": "urn:ProductSpecification:12345"
    }
}]

# Anti-collision test data for range collision tests
ANTICOLLISION_CONTINUOUS_SINGLE = {
    "urn:Characteristic:1234": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 100
        },
        "from-1": [50],
        "from-51": [100]
    }
}

ANTICOLLISION_CONTINUOUS_MULTIPLE_SEGMENTS = {
    "urn:Characteristic:5678": {
        "total_range": {
            "valueFrom": 0,
            "valueTo": 1000
        },
        "from-0": [250],
        "from-251": [500],
        "from-501": [750],
        "from-751": [1000]
    }
}

ANTICOLLISION_CONTINUOUS_WITH_MULTIPLE_VALUES = {
    "urn:Characteristic:7777": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 100
        },
        "from-1": [25, 30, 50],
        "from-26": [40],
        "from-31": [45],
        "from-51": [75],
        "from-76": [100]
    }
}

ANTICOLLISION_CONTINUOUS_WITH_DUPLICATES = {
    "urn:Characteristic:8888": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 50
        },
        "from-1": [10, 15],
        "from-11": [20],
        "from-16": [25],
        "from-21": [30],
        "from-26": [35],
        "from-31": [40],
        "from-36": [45],
        "from-41": [50],
        "from-46": [50]
    }
}

ANTICOLLISION_NON_CONTINUOUS_GAP = {
    "urn:Characteristic:9999": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 100
        },
        "from-1": [50],
        "from-60": [100]
    }
}

ANTICOLLISION_MULTIPLE_CHARS_ALL_CONTINUOUS = {
    "urn:Characteristic:1111": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 50
        },
        "from-1": [25],
        "from-26": [50]
    },
    "urn:Characteristic:2222": {
        "total_range": {
            "valueFrom": 100,
            "valueTo": 200
        },
        "from-100": [150],
        "from-151": [200]
    }
}

ANTICOLLISION_MULTIPLE_CHARS_ONE_NON_CONTINUOUS = {
    "urn:Characteristic:3333": {
        "total_range": {
            "valueFrom": 1,
            "valueTo": 50
        },
        "from-1": [25],
        "from-26": [50]
    },
    "urn:Characteristic:4444": {
        "total_range": {
            "valueFrom": 100,
            "valueTo": 200
        },
        "from-100": [150],
        "from-160": [200]
    }
}

ANTICOLLISION_EXACT_BOUNDARIES = {
    "urn:Characteristic:6666": {
        "total_range": {
            "valueFrom": 10,
            "valueTo": 20
        },
        "from-10": [20]
    }
}

ANTICOLLISION_COMPLEX_BRANCHES = {
    "urn:Characteristic:5555": {
        "total_range": {
            "valueFrom": 0,
            "valueTo": 100
        },
        "from-0": [20, 30, 40],
        "from-21": [35, 50],
        "from-31": [45],
        "from-36": [60],
        "from-41": [55],
        "from-46": [70],
        "from-51": [65],
        "from-56": [75],
        "from-61": [80],
        "from-66": [85],
        "from-71": [90],
        "from-76": [95],
        "from-81": [100],
        "from-86": [100],
        "from-91": [100],
        "from-96": [100]
    }
}