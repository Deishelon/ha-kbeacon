"""The kbeacon integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.bluetooth.active_update_processor import (ActiveBluetoothProcessorCoordinator,
                                                                        BluetoothScanningMode)

from .const import DOMAIN, K_ADDR
from .decoder import parse_adv_packet, KBluetoothDeviceData

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up kbeacon from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    k_addr = entry.data[K_ADDR]
    _LOGGER.debug(f"Setting up KBeacon for address: {k_addr}")

    k_data = KBluetoothDeviceData()

    coordinator = ActiveBluetoothProcessorCoordinator(
        hass=hass,
        logger=_LOGGER,
        address=k_addr,
        mode=BluetoothScanningMode.ACTIVE,
        update_method=lambda service_info: k_data.update(service_info),
        needs_poll_method=lambda service_info, last_poll: False,
    )

    coordinator.async_start()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
