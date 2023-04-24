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

CURRENCIES = {
    "EUR": "1",
    "GBP": "2",
    "BRL": "3",
    "ARS": "4",
    "MXN": "5",
    "CLP": "6",
    "PEN": "7",
    "VEF": "8",
    "COP": "9",
    "USD": "10",
    "NIO": "11",
    "GTQ": "12",
    "SVC": "13",
    "PAB": "14",
    "UYU": "15",
    "MYR": "16",
    "NOK": "17",
    "HUF": "18",
}

COUNTRIES = {
    "ES": "1",
    "GB": "2",
    "DE": "3",
    "MX": "4",
    "CL": "5",
    "AR": "6",
    "PE": "7",
    "VE": "8",
    "CO": "9",
    "EC": "10",
    "NI": "11",
    "GT": "12",
    "SV": "13",
    "PA": "14",
    "UY": "15",
    "BR": "16",
    "MY": "17",
    "NO": "18",
    "HU": "19",
}


def get_currency_code(curr):
    try:
        code = CURRENCIES[curr]
    except:
        raise Exception("Invalid currency code")

    return code


def get_country_code(country):
    try:
        code = COUNTRIES[country]
    except:
        raise Exception("Invalid country code")

    return code
