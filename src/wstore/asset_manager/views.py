# -*- coding: utf-8 -*-

# Copyright (c) 2013 - 2017 CoNWeT Lab., Universidad Politécnica de Madrid

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

import json

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import HttpResponse

from wstore.asset_manager.asset_manager import AssetManager
from wstore.asset_manager.errors import ProductError, ServiceError
from wstore.asset_manager.offering_validator import OfferingValidator
from wstore.asset_manager.product_validator import ProductValidator
from wstore.asset_manager.resource_plugins.plugin_error import PluginError
from wstore.models import UserProfile
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.resource import Resource
from wstore.store_commons.utils.http import (
    authentication_required,
    build_response,
    get_content_type,
    supported_request_mime_types,
)

##########################################
#from wstore.asset_manager import service_specification_manager
from wstore.asset_manager.service_validator import ServiceValidator
##########################################


class AssetCollection(Resource):
    def read(self, request):
        """
        Retrieves the existing digital assets associated with a given seller
        :param request:
        :return: JSON List containing the existing assets
        """

        user = request.GET.get("user", None)

        pagination = {
            "offset": request.GET.get("offset", None),
            "size": request.GET.get("size", None),
        }
        if pagination["offset"] is None or pagination["size"] is None:
            pagination = None

        if user is None:
            if request.user.is_anonymous:
                return build_response(request, 401, "Authentication required")
            user = request.user.userprofile
        else:
            try:
                user_search = User.objects.get(username=user)
                user = UserProfile.objects.get(user=user_search)
            except Exception as e:
                return build_response(
                    request,
                    404,
                    "User {} does not exist, error: {}".format(user, str(e)),
                )

        try:
            asset_manager = AssetManager()
            response = asset_manager.get_provider_assets_info(user, pagination=pagination)
        except Exception as e:
            return build_response(request, 400, str(e))

        return HttpResponse(
            json.dumps(response),
            status=200,
            content_type="application/json; charset=utf-8",
        )


class AssetEntry(Resource):
    def read(self, request, asset_id):
        """
        Retrieves the information associated to a given digital asset
        :param request:
        :param id:
        :return:
        """

        try:
            asset_manager = AssetManager()
            response = asset_manager.get_asset_info(asset_id)
        except ObjectDoesNotExist as e:
            return build_response(request, 404, str(e))
        except PermissionDenied as e:
            return build_response(request, 403, str(e))
        except:
            return build_response(request, 500, "An unexpected error occurred")

        return HttpResponse(
            json.dumps(response),
            status=200,
            content_type="application/json; charset=utf-8",
        )


class AssetEntryFromProduct(Resource):
    def read(self, request, product_id):
        """
        Retrieves the assets from a product
        :param request:
        :param id:
        :return:
        """

        try:
            asset_manager = AssetManager()
            response = asset_manager.get_product_assets(product_id)
        except PermissionDenied as e:
            return build_response(request, 403, str(e))
        except:
            return build_response(request, 500, "An unexpected error occurred")

        return HttpResponse(
            json.dumps(response),
            status=200,
            content_type="application/json; charset=utf-8",
        )


def _manage_digital_asset(request, manager):
    user = request.user
    profile = user.userprofile
    content_type = get_content_type(request)[0]

    if "provider" not in profile.get_current_roles() and not user.is_staff:
        return build_response(request, 403, "You don't have the seller role")

    try:
        resource, data = manager(request, user, content_type)
    except ValueError as e:
        return build_response(request, 422, str(e))
    except ConflictError as e:
        return build_response(request, 409, str(e))
    except ObjectDoesNotExist as e:
        return build_response(request, 404, str(e))
    except PermissionDenied as e:
        return build_response(request, 403, str(e))
    except Exception as e:
        return build_response(request, 400, str(e))

    location = resource.get_url()

    # Fill location header with the URL of the uploaded digital asset
    response = HttpResponse(
        json.dumps(
            {
                "content": location,
                "contentType": data["contentType"],
                "id": str(resource.pk),
                "href": resource.get_uri(),
            }
        ),
        status=200,
        content_type="application/json; charset=utf-8",
    )

    response["Location"] = location
    return response


class UploadCollection(Resource):
    @supported_request_mime_types(("application/json", "multipart/form-data"))
    @authentication_required
    def create(self, request):
        """
        Uploads a new downloadable digital asset
        :param request:
        :return: 200 Created, including the new URL of the asset in the location header
        """

        def upload_asset(req, user, content_type):
            asset_manager = AssetManager()

            ##########################
            # APIs TMForums
            # En el body de la request iría json con la info bien ordenada
            # Si falla xa tería que ir dar o error e parar a execución
            #mspecification = service_specification_manager.ServiceSpecificationManager()
            #mspecification.create_service_spec_cand(req.body)
            ##########################

            if content_type == "application/json":
                data = json.loads(req.body)
                resource = asset_manager.upload_asset(user, data)
            else:
                data = json.loads(req.POST["json"])
                f = req.FILES["file"]
                resource = asset_manager.upload_asset(user, data, file_=f)

            return resource, data

        return _manage_digital_asset(request, upload_asset)


class UpgradeCollection(Resource):
    @supported_request_mime_types(("application/json", "multipart/form-data"))
    @authentication_required
    def create(self, request, asset_id):
        """
        Upgrades an existing digital asset for creating new product versions
        :param request: User request
        :param asset_id: Id of the asset to be upgraded
        :return: Response 200 if the asset is correctly upgraded
        """
        print("upgrade")
        print(asset_id)
        def upgrade_asset(req, user, content_type):
            asset_manager = AssetManager()

            if content_type == "application/json":
                data = json.loads(req.body)
                resource = asset_manager.upgrade_asset(asset_id, user, data)
            else:
                data = json.loads(req.POST["json"])
                f = req.FILES["file"]
                resource = asset_manager.upgrade_asset(asset_id, user, data, file_=f)

            return resource, data

        return _manage_digital_asset(request, upgrade_asset)



#Vai dar problemas fijo polo tema do data, revisalo
def _validate_catalog_element(request, element, validator):

    print("Entra en _validate_catalog_element")

    # Validate user permissions
    user = request.user
    if "provider" not in user.userprofile.get_current_roles() and not user.is_staff:
        return build_response(request, 403, "You don't have the seller role")

    # Parse content
    try:
        data = json.loads(request.body)
    except:
        return build_response(request, 400, "The content is not a valid JSON document")

    if "action" not in data:
        return build_response(request, 400, "Missing required field: action")

    if element not in data:
        return build_response(request, 400, "Missing required field: product")

    try:
        response = validator.validate(data["action"], user.userprofile.current_organization, data[element])
    except ValueError as e:
        return build_response(request, 400, str(e))
    except ProductError as e:
        return build_response(request, 400, str(e))
    except ServiceError as e:
        return build_response(request, 400, str(e))
    except ConflictError as e:
        return build_response(request, 409, str(e))
    except PluginError as e:
        return build_response(request, 422, str(e))
    except PermissionDenied as e:
        return build_response(request, 403, str(e))
    except Exception as e:
        print(str(e))
        return build_response(request, 500, "An unexpected error has occurred")
    print("sale de _validate_catalog_element")
    return build_response(request, 200, "OK", extra_content=response)

class ValidateServiceCollection(Resource):
    @supported_request_mime_types(("application/json",))
    @authentication_required
    def create(self, request):
        """
        Validates the digital asset contained in a TMForum service Specification
        :param request:
        :return:
        """
        
        service_validator = ServiceValidator()
        return _validate_catalog_element(request, "service", service_validator)

class ValidateCollection(Resource):
    @supported_request_mime_types(("application/json",))
    @authentication_required
    def create(self, request):
        """
        Validates the digital assets contained in a TMForum service Specification assosiated to a product Specification
        :param request:
        :return:
        """

        product_validator = ProductValidator()
        return _validate_catalog_element(request, "product", product_validator)

class ValidateOfferingCollection(Resource):
    @supported_request_mime_types(("application/json",))
    @authentication_required
    def create(self, request):
        """
        Validates the TMForum product offering selling a product specification
        :param request:
        :return:
        """
        offering_validator = OfferingValidator()
        return _validate_catalog_element(request, "offering", offering_validator)
