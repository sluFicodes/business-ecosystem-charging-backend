from logging import getLogger
from bson import ObjectId
from django.conf import settings
from django.core.exceptions import PermissionDenied

from wstore.asset_manager.catalog_validator import CatalogValidator
from wstore.asset_manager.errors import ServiceError
from wstore.asset_manager.inventory_upgrader import InventoryUpgrader
from wstore.asset_manager.models import Resource, ResourcePlugin
from wstore.asset_manager.resource_plugins.decorators import (
    on_service_spec_attachment,
    on_service_spec_validation,
)
from wstore.store_commons.database import DocumentLock
from wstore.store_commons.errors import ConflictError
from wstore.store_commons.rollback import downgrade_asset, downgrade_asset_pa, rollback
from wstore.store_commons.utils.url import is_valid_url
from wstore.store_commons.utils.version import is_lower_version, is_valid_version
from bson.errors import InvalidId
logger = getLogger("wstore.service_validator")
class ServiceValidator(CatalogValidator):

    def _get_asset_resouces(self, asset_t, asset_id):
        try:
            # Search the asset type
            resource_asset_type = ResourcePlugin.objects.get(name=asset_t)
            # Use the asset_id to retrieve the asset linked in service spec characteristic
            resource_asset = Resource.objects.get(pk=ObjectId(asset_id)) if asset_id else None
        except Resource.DoesNotExist:
             raise ServiceError("The asset or asset type characteristic included in the service specification is not valid")
        except InvalidId:
            raise ServiceError("Invalid asset id")      
        except Exception as e:
            print(type(e).__name__)
            logger.error(f"_get_asset_resources:{e}")
            #For security we cannot pass all error messages to the user 
            raise ServiceError(f"Error retrieving the asset or the asset type, check charging backend for further details.")

        return resource_asset_type, resource_asset

    def _validate_service_characteristics(self, asset, provider, asset_t, media_type):
        print("_validate_spec_characteristic")
        if asset.provider != provider:
            raise PermissionDenied(
                "You are not authorized to use the digital asset specified in the location characteristic"
            )

        if asset.resource_type != asset_t:
            raise ServiceError("The specified asset type is different from the asset one")

        if asset.content_type.lower() != media_type.lower():
            raise ServiceError("The provided media type characteristic is different from the asset one")

        if asset.is_public:
            raise ServiceError("It is not allowed to create services with public assets")

    @on_service_spec_validation
    def _validate_service(self, provider, asset_t, media_type, url, asset_id):
        print("Entra en _validate_service 2")
        
        # Validate location format
        if not is_valid_url(url):
            raise ServiceError("The location characteristic included in the service specification is not a valid URL")
        resource_asset_type, resource_asset = self._get_asset_resouces(asset_t, asset_id)
        if asset_id is not None and resource_asset:
            # Check if the asset is already registered
            print("asset dentro de mongo")
            asset = resource_asset
            if asset.service_id is not None:
                raise ServiceError(
                    "There is already an existing service specification defined for the given digital asset"
                )
            print("validate spec characteristic")
            self._validate_service_characteristics(asset, provider, asset_t, media_type)
            print("start save")
            asset.has_terms = self._has_terms
            asset.save()
            print("end save")
        else:
            print("asset no incluido aún")
            # The asset is not yet included, this option is only valid for URL assets without metadata
            site = settings.SITE
            if "FILE" in resource_asset_type.formats and (
                ("URL" not in resource_asset_type.formats) or 
                ("URL" in resource_asset_type.formats and url.startswith(site))
            ):
                raise ServiceError(
                    "The URL specified in the location characteristic does not point to a valid digital asset"
                )
            # URL must be included in asset type for direct asset creation
            if "URL" not in resource_asset_type.formats:
                raise ServiceError("The asset doesn't support URL format")
            
            if resource_asset_type.form:
                raise ServiceError("Automatic creation of digital assets with expected metadata is not supported")

            # Validate media type
            if len(resource_asset_type.media_types) and media_type.lower() not in [
                media.lower() for media in resource_asset_type.media_types
            ]:
                raise ServiceError(
                    "The media type characteristic included in the service specification is not valid for the given asset type"
                )

            # Create the new asset model
            asset = Resource.objects.create(
                has_terms=self._has_terms,
                resource_path="",
                download_link=url,
                provider=provider,
                content_type=media_type,
            )
        # The asset model is included to the rollback list so if an exception is raised in the plugin post validation
        # the asset model would be deleted
        print("start rollback")
        self.rollback_logger["models"].append(asset) # type: ignore
        print("return _validate_service")
        return asset

    @on_service_spec_attachment
    def _attach_service_info(self, asset, asset_t, service_spec):
        # Complete asset information
        asset.service_id = service_spec["id"]
        asset.version = service_spec["version"]
        asset.resource_type = asset_t
        asset.state = "attached"
        asset.save()
        print("saved")


    def _extract_digital_assets(self, bundled_specs):
        assets = []
        for bundled_info in bundled_specs:
            digital_asset = Resource.objects.filter(service_id=bundled_info["id"])
            if len(digital_asset):
                assets.append(digital_asset[0].pk)

        return assets
    @rollback()
    def attach_info(self, provider, service_spec):
        print("attach_info")
        print(service_spec)
        print("-----------------------")
        # Get the digital asset
        asset_t, media_type, url, asset_id = self.parse_spec_characteristics(service_spec)
        print(asset_t)
        print(media_type)
        print(url)
        print(asset_id)
        is_digital = asset_t is not None and media_type is not None and url is not None
        print("digital check")
        if is_digital:
            try:
                print("get asset id")
                asset = Resource.objects.get(pk=ObjectId(asset_id))
                # TODO: Drop the service object from the catalog in case of error
                self.rollback_logger["models"].append(asset) # type: ignore

                # The asset is a digital service or a bundle containing a digital service
                self._attach_service_info(asset, asset_t, service_spec)
            except Resource.DoesNotExist:
                raise ServiceError("The asset included doesn't exist")
            except InvalidId:
                raise ServiceError("invalid asset id")
        else: 
            raise ServiceError("The asset included doesn't exist")
        print("return attach_info")
        return service_spec

    """
    @on_service_spec_upgrade
    def _notify_service_upgrade(self, asset, asset_t, service_spec):
        # Update existing inventory services to include new version asset info
        upgrader = InventoryUpgrader(asset)
        upgrader.start()

        # Set the asset status to attached
        asset.state = "attached"
        asset.save()
    """

    def _get_upgrading_asset(self, asset_t, asset_id, service_id):
        asset_type, asset = self._get_asset_resouces(asset_t, asset_id)

        if not asset:
            raise ServiceError(
                "Invalid asset_id"
            )
        # Lock the access to the asset
        lock = DocumentLock("wstore_resource", asset.pk, "asset")
        lock.wait_document()

        asset = Resource.objects.get(pk=asset.pk)

        # Check that the asset is in upgrading state
        if asset.state != "upgrading":
            raise ServiceError("There is not a new version of the specified digital asset")

        if asset.service_id != service_id:
            raise ServiceError("The specified digital asset is included in other service spec")

        return asset, lock

    """
    def attach_upgrade(self, provider, service_spec):
        asset_t, media_type, url, asset_id = self.parse_characteristics(service_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        if is_digital:
            asset, lock = self._get_upgrading_asset(asset_t, url, service_spec["id"])
            self._notify_service_upgrade(asset, asset_t, service_spec)

            # Release asset lock
            lock.unlock_document()
        return service_spec
    """

    @rollback(downgrade_asset_pa)
    def validate_upgrade(self, provider, service_spec):
        if "version" in service_spec and "serviceSpecCharacteristic" in service_spec:
            # Extract service needed characteristics
            asset_t, media_type, url, asset_id = self.parse_characteristics(service_spec)
            is_digital = asset_t is not None and media_type is not None and url is not None

            if is_digital:
                asset, lock = self._get_upgrading_asset(asset_t, asset_id, service_spec["id"])

                self._to_downgrade = asset

                self._validate_service_characteristics(asset, provider, asset_t, media_type)

                # Check service version
                if not is_valid_version(service_spec["version"]):
                    raise ServiceError("The field version does not have a valid format")

                if not is_lower_version(asset.old_versions[-1].version, service_spec["version"]):
                    raise ServiceError("The provided version is not higher that the previous one")

                # Attach new info
                asset.version = service_spec["version"]
                asset.save()

                # Release asset lock
                lock.unlock_document()
        return service_spec

    def _rollback_handler(self, provider, service_spec, rollback_method):
        asset_t, media_type, url, asset_id = self.parse_characteristics(service_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None

        if is_digital:
            _, resource_asset = self._get_asset_resouces(asset_t, asset_id)
            if resource_asset:
                self._validate_service_characteristics(resource_asset, provider, asset_t, media_type)
                rollback_method(resource_asset)
            else:
                raise ServiceError("Cannot rollback an asset with invalid id")

    def rollback_create(self, provider, service_spec):
        def rollback_method(asset):
            if asset.service_id is None:
                asset.delete()

        self._rollback_handler(provider, service_spec, rollback_method)
        return service_spec

    def rollback_upgrade(self, provider, service_spec):
        def rollback_method(asset):
            if asset.service_id == service_spec["id"] and asset.state == "upgrading":
                downgrade_asset(asset)

        self._rollback_handler(provider, service_spec, rollback_method)
        return service_spec

    # Detalles a tener en cuenta:
    # Esto es para los serviceos, no para los service specification
    # Eso significa que pueden tener varios service specification y que hay que hacer el parse para todos

    #@rollback()
    #def validate_creation(self, provider, service_spec):
        # Extract service needed characteristics
    #    asset_t, media_type, url, asset_id = self.parse_characteristics(service_spec)
    #    is_digital = asset_t is not None and media_type is not None and url is not None

        # Service spec bundles are intended for creating composed services, it cannot contain its own asset
    #    if service_spec["isBundle"] and is_digital:
    #        raise ServiceError("Service spec bundles cannot define digital assets")

    #    if not service_spec["isBundle"] and is_digital:
    #        # Process the new digital service
    #        self._validate_service(provider, asset_t, media_type, url, asset_id)

    #    elif service_spec["isBundle"] and not is_digital:
    #        # The service bundle may contain digital services already registered
    #        self._build_bundle(provider, service_spec)
    
    
    @rollback()
    def validate_creation(self, provider, service_spec):
        print("Entra en validate_creation")
        # Extract service needed characteristics
        asset_t, media_type, url, asset_id = self.parse_spec_characteristics(service_spec)
        is_digital = asset_t is not None and media_type is not None and url is not None
        print(asset_t)
        print(media_type)
        print(url)
        print(asset_id)
        
        # Service spec bundles does not exist
        if service_spec["isBundle"]:
            print("ValidateCreation Service Error")
            raise ServiceError("Service spec bundles are not supported")
        if is_digital:
            print("Entra en _validate_service 1")
            asset = self._validate_service(provider, asset_t, media_type, url, asset_id)
            print(f"asset id validate creation: {str(asset._id)}")
            if asset_id is None:
                return {"id": str(asset._id)}
        
            