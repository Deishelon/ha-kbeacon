"""Platform for sensor integration."""
from __future__ import annotations

import logging

from sensor_state_data import SensorUpdate, DeviceKey, Units

from . import DOMAIN
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info
from homeassistant.components.bluetooth.active_update_processor import ActiveBluetoothProcessorCoordinator
from homeassistant.components.bluetooth.passive_update_processor import PassiveBluetoothDataProcessor, \
    PassiveBluetoothProcessorEntity, \
    PassiveBluetoothDataUpdate, PassiveBluetoothEntityKey

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = {
    (SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS): SensorEntityDescription(
        key=f"{SensorDeviceClass.TEMPERATURE}_{UnitOfTemperature.CELSIUS}",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (SensorDeviceClass.HUMIDITY, Units.PERCENTAGE): SensorEntityDescription(
        key=f"{SensorDeviceClass.HUMIDITY}_{Units.PERCENTAGE}",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=Units.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (SensorDeviceClass.VOLTAGE, Units.ELECTRIC_POTENTIAL_VOLT): SensorEntityDescription(
        key=f"{SensorDeviceClass.VOLTAGE}_{Units.ELECTRIC_POTENTIAL_VOLT}",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=Units.ELECTRIC_POTENTIAL_VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


def device_key_to_bluetooth_entity_key(
        device_key: DeviceKey,
) -> PassiveBluetoothEntityKey:
    """Convert a device key to an entity key."""
    return PassiveBluetoothEntityKey(device_key.key, device_key.device_id)


def sensor_update_to_bluetooth_data_update(
        sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a bluetooth data update."""
    return PassiveBluetoothDataUpdate(
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        entity_descriptions={
            device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
                (description.device_class, description.native_unit_of_measurement)
            ]
            for device_key, description in sensor_update.entity_descriptions.items()
            if description.device_class
        },
        entity_data={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
        entity_names={
            device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
    )


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the KBeacon sensor devices."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    processor = KPassiveBluetoothDataProcessor(
        sensor_update_to_bluetooth_data_update
    )
    config_entry.async_on_unload(
        processor.async_add_entities_listener(KBluetoothSensorEntity, async_add_entities)
    )
    config_entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class KPassiveBluetoothDataProcessor(PassiveBluetoothDataProcessor):
    """Define a Bluetooth Passive Update Data Processor."""

    coordinator: ActiveBluetoothProcessorCoordinator


class KBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[KPassiveBluetoothDataProcessor],
    SensorEntity,
):
    """Representation of a KBeacon ble sensor."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
