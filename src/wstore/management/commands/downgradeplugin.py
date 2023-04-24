# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 CoNWeT Lab., Universidad Politécnica de Madrid
# Copyright (c) 2022 Future Internet Consulting and Development Solutions S.L.

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


from django.core.management.base import BaseCommand, CommandError
from wstore.asset_manager.resource_plugins.plugin_loader import PluginLoader


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("args", nargs="*")

    def handle(self, *args, **options):
        """
        Downgrades a resource plugin to an older version
        """

        # Check arguments
        if len(args) < 1:
            raise CommandError("Error: Please specify the plugin to be deleted")
        elif len(args) > 2:
            raise CommandError(
                "Error: Number of arguments is too high, " "specify only one plugin and optionally a version number."
            )

        try:
            name = args[0]
            version = args[1] if len(args) == 2 else None
            # Load plugin
            plugin_loader = PluginLoader()
            plugin_loader.downgrade_plugin(name, version)
        except Exception as e:
            raise CommandError(str(e))

        self.stdout.write("The plugin has been downgraded\n")
