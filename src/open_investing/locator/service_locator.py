#!/usr/bin/env python3

from open_library.collections.dict import hashable_json
from pydantic import BaseModel


class ServiceKey(BaseModel):
    service_type: str  # e.g., 'database_manager', 'exchange_api'
    service_name: str  # e.g., 'binance', 'order'
    params: dict = {}  # Additional parameters

    class Config:
        # To allow the model to be hashable, even if it includes a mutable type like a dictionary
        frozen = True

    def __hash__(self):
        # Create a hash from a tuple representation of the data
        # Convert the dict to a tuple of items to ensure it's hashable
        params_items = tuple(sorted(self.params.items())) if self.params else None
        return hash((self.service_type, self.service_name, params_items))

    def __eq__(self, other):
        if isinstance(other, ServiceKey):
            # Ensure all corresponding properties are equal
            return (
                self.service_type == other.service_type
                and self.service_name == other.service_name
                and self.params == other.params
            )
        return False


class ServiceLocator:
    def __init__(self):
        self._services = {}

    def register_service(self, service_key, service):
        if service_key in self._services:
            raise Exception(f"service already registered: {service_key}")

        self._services[service_key] = service

    def get_service(self, service_key):
        if service_key not in self._services:
            raise Exception(f"service not registered: {service_key}")

        return self._services[service_key]
