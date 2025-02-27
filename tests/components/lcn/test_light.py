"""Test for the LCN light platform."""
from unittest.mock import patch

from pypck.inputs import ModStatusOutput, ModStatusRelays
from pypck.lcn_addr import LcnAddr
from pypck.lcn_defs import RelayStateModifier

from homeassistant.components.lcn.helpers import get_device_connection
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_TRANSITION,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
    DOMAIN as DOMAIN_LIGHT,
    SUPPORT_TRANSITION,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)

from .conftest import MockModuleConnection


async def test_setup_lcn_light(hass, lcn_connection):
    """Test the setup of light."""
    for entity_id in (
        "light.light_output1",
        "light.light_output2",
        "light.light_relay1",
    ):
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == STATE_OFF


async def test_entity_state(hass, lcn_connection):
    """Test state of entity."""
    state = hass.states.get("light.light_output1")
    assert state
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_TRANSITION
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [COLOR_MODE_BRIGHTNESS]

    state = hass.states.get("light.light_output2")
    assert state
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_TRANSITION
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [COLOR_MODE_ONOFF]


async def test_entity_attributes(hass, entry, lcn_connection):
    """Test the attributes of an entity."""
    entity_registry = await hass.helpers.entity_registry.async_get_registry()

    entity_output = entity_registry.async_get("light.light_output1")

    assert entity_output
    assert entity_output.unique_id == f"{entry.entry_id}-m000007-output1"
    assert entity_output.original_name == "Light_Output1"

    entity_relay = entity_registry.async_get("light.light_relay1")

    assert entity_relay
    assert entity_relay.unique_id == f"{entry.entry_id}-m000007-relay1"
    assert entity_relay.original_name == "Light_Relay1"


@patch.object(MockModuleConnection, "dim_output")
async def test_output_turn_on(dim_output, hass, lcn_connection):
    """Test the output light turns on."""
    # command failed
    dim_output.return_value = False

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_output1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 100, 9)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state != STATE_ON

    # command success
    dim_output.reset_mock(return_value=True)
    dim_output.return_value = True

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_output1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 100, 9)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_ON


@patch.object(MockModuleConnection, "dim_output")
async def test_output_turn_on_with_attributes(dim_output, hass, lcn_connection):
    """Test the output light turns on."""
    dim_output.return_value = True

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.light_output1",
            ATTR_BRIGHTNESS: 50,
            ATTR_TRANSITION: 2,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 19, 6)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_ON


@patch.object(MockModuleConnection, "dim_output")
async def test_output_turn_off(dim_output, hass, lcn_connection):
    """Test the output light turns off."""
    state = hass.states.get("light.light_output1")
    state.state = STATE_ON

    # command failed
    dim_output.return_value = False

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.light_output1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 0, 9)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state != STATE_OFF

    # command success
    dim_output.reset_mock(return_value=True)
    dim_output.return_value = True

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.light_output1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 0, 9)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_OFF


@patch.object(MockModuleConnection, "dim_output")
async def test_output_turn_off_with_attributes(dim_output, hass, lcn_connection):
    """Test the output light turns off."""
    dim_output.return_value = True

    state = hass.states.get("light.light_output1")
    state.state = STATE_ON

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "light.light_output1",
            ATTR_TRANSITION: 2,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    dim_output.assert_awaited_with(0, 0, 6)

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_OFF


@patch.object(MockModuleConnection, "control_relays")
async def test_relay_turn_on(control_relays, hass, lcn_connection):
    """Test the relay light turns on."""
    states = [RelayStateModifier.NOCHANGE] * 8
    states[0] = RelayStateModifier.ON

    # command failed
    control_relays.return_value = False

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_relay1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    control_relays.assert_awaited_with(states)

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state != STATE_ON

    # command success
    control_relays.reset_mock(return_value=True)
    control_relays.return_value = True

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.light_relay1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    control_relays.assert_awaited_with(states)

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state == STATE_ON


@patch.object(MockModuleConnection, "control_relays")
async def test_relay_turn_off(control_relays, hass, lcn_connection):
    """Test the relay light turns off."""
    states = [RelayStateModifier.NOCHANGE] * 8
    states[0] = RelayStateModifier.OFF

    state = hass.states.get("light.light_relay1")
    state.state = STATE_ON

    # command failed
    control_relays.return_value = False

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.light_relay1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    control_relays.assert_awaited_with(states)

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state != STATE_OFF

    # command success
    control_relays.reset_mock(return_value=True)
    control_relays.return_value = True

    await hass.services.async_call(
        DOMAIN_LIGHT,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.light_relay1"},
        blocking=True,
    )
    await hass.async_block_till_done()
    control_relays.assert_awaited_with(states)

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state == STATE_OFF


async def test_pushed_output_status_change(hass, entry, lcn_connection):
    """Test the output light changes its state on status received."""
    device_connection = get_device_connection(hass, (0, 7, False), entry)
    address = LcnAddr(0, 7, False)

    # push status "on"
    inp = ModStatusOutput(address, 0, 50)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_BRIGHTNESS] == 127

    # push status "off"
    inp = ModStatusOutput(address, 0, 0)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get("light.light_output1")
    assert state is not None
    assert state.state == STATE_OFF


async def test_pushed_relay_status_change(hass, entry, lcn_connection):
    """Test the relay light changes its state on status received."""
    device_connection = get_device_connection(hass, (0, 7, False), entry)
    address = LcnAddr(0, 7, False)
    states = [False] * 8

    # push status "on"
    states[0] = True
    inp = ModStatusRelays(address, states)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state == STATE_ON

    # push status "off"
    states[0] = False
    inp = ModStatusRelays(address, states)
    await device_connection.async_process_input(inp)
    await hass.async_block_till_done()

    state = hass.states.get("light.light_relay1")
    assert state is not None
    assert state.state == STATE_OFF


async def test_unload_config_entry(hass, entry, lcn_connection):
    """Test the light is removed when the config entry is unloaded."""
    await hass.config_entries.async_unload(entry.entry_id)
    assert hass.states.get("light.light_output1").state == STATE_UNAVAILABLE
