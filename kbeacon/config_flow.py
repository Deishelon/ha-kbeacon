"""Config flow for kbeacon integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, K_ADDR

_LOGGER = logging.getLogger(__name__)

INPUT_SCHEMA = vol.Schema(
    {
        vol.Required(K_ADDR): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for kbeacon."""

    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Asks user to input the device mac address (i.e. BC:57:29:02:45:47) """
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input[K_ADDR], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=INPUT_SCHEMA, errors=errors
        )
