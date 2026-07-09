# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid
# Copyright (c) 2026 Future Internet Consulting and Development Solutions S.L.

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
import re


def to_utc_z(dt):
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    if isinstance(dt, datetime.date):
        dt = datetime.datetime(dt.year, dt.month, dt.day, tzinfo=datetime.timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    raise TypeError(f"Expected datetime or date, got {type(dt).__name__}")


def utc_z_to_dt(dt_str: str) -> datetime.datetime:
    normalized = re.sub(r'(\.\d{6})\d+', r'\1', dt_str.replace("Z", "+00:00"))
    return datetime.datetime.fromisoformat(normalized)
