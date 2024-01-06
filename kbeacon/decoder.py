import logging

from bluetooth_sensor_state_data import BluetoothData

from sensor_state_data import SensorLibrary

from homeassistant.components.bluetooth import BluetoothServiceInfo

from .model import KInfo

_LOGGER = logging.getLogger(__name__)

SERVICE_KBEACON = "0000feaa-0000-1000-8000-00805f9b34fb"


def parse_adv_packet(beacon_data) -> KInfo | None:
    n_srv_index = 1  # skip adv type

    sensor_mask_high = (beacon_data[n_srv_index] & 0xFF) << 8
    n_sensor_mask = sensor_mask_high + (beacon_data[n_srv_index + 1] & 0xFF)
    n_srv_index += 2

    if (n_sensor_mask & 0x1) > 0:
        if n_srv_index > (len(beacon_data) - 2):
            return None
        n_battery_lvs = (beacon_data[n_srv_index] & 0xFF) << 8
        n_battery_lvs += (beacon_data[n_srv_index + 1] & 0xFF)
        m_voltage = n_battery_lvs
        n_srv_index += 2
    else:
        m_voltage = None

    if (n_sensor_mask & 0x2) > 0:
        if n_srv_index > (len(beacon_data) - 2):
            return None
        temp_high = beacon_data[n_srv_index]
        temp_low = beacon_data[n_srv_index + 1]
        temperature = _signed_bytes_to_float(temp_high, temp_low)
        n_srv_index += 2
    else:
        temperature = None

    if (n_sensor_mask & 0x4) > 0:
        if n_srv_index > (len(beacon_data) - 2):
            return None
        hum_high = beacon_data[n_srv_index]
        hum_low = beacon_data[n_srv_index + 1]
        humidity = _signed_bytes_to_float(hum_high, hum_low)
        n_srv_index += 2
    else:
        humidity = None

    return KInfo(
        temperature=temperature,
        humidity=humidity,
        m_voltage=m_voltage
    )


def _signed_bytes_to_float(hi, lo):
    combine = ((hi & 0xFF) << 8) + (lo & 0xFF)
    if combine >= 0x8000:
        combine = combine - 0x10000

    f_result = combine / 256.0
    return round(f_result, 2)


class KBluetoothDeviceData(BluetoothData):
    """Data for KBeacon BLE sensors."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        for uuid, data in service_info.service_data.items():
            if uuid == SERVICE_KBEACON:
                if self._parse_k_beacon(service_info, data):
                    self.last_service_info = service_info

    def _parse_k_beacon(
            self, service_info: BluetoothServiceInfo, data: bytes
    ) -> bool:
        """Parser for KBeacon sensors"""
        self.device_id = service_info.address

        self.set_title(f"{service_info.name} {service_info.address}")
        self.set_device_name(f"{service_info.name} {service_info.address}")

        decoded = parse_adv_packet(data)

        if decoded is not None:
            self.update_predefined_sensor(SensorLibrary.TEMPERATURE__CELSIUS, decoded.temperature)
            self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, decoded.humidity)
            self.update_predefined_sensor(SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, decoded.m_voltage / 1000)

        return True
