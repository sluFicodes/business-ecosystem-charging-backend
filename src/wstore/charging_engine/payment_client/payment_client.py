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


class PaymentClient:
    _purchase = None

    def __init__(self, purchase):
        self._purchase = purchase

    def start_redirection_payment(self, price, currency):
        pass

    def end_redirection_payment(self, token, payer_id):
        pass

    def direct_payment(self, currency, price, credit_card):
        pass

    def refund(self):
        pass

    def get_checkout_url(self):
        pass
