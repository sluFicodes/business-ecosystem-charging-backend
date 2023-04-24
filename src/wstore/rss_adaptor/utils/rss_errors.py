# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

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


ERROR_CODES = {
    "SVC1006": "The current instance of WStore is not registered in the Revenue Sharing System, so it is not possible to access RSS APIs. Please contact with the administrator of the RSS."
}


def get_error_message(code):
    result = "An error occurs when accessing the RSS"
    if code in ERROR_CODES:
        result = ERROR_CODES[code]
    return result
