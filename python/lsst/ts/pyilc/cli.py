# This file is part of ts_pyilc.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
import os

import asyncclick as click
from intelhex import IntelHex
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ModbusPDU

from .pdu import (
    ADCScanRate,
    ChangeILCMode,
    ForceActuatorForceAndStatusDAResponse,
    ForceActuatorForceAndStatusRequest,
    ForceActuatorForceDemandDARequest,
    ForceActuatorForceDemandDAResponse,
    ForceActuatorForceDemandSARequest,
    ForceActuatorReadBoosterValveDCAGainsRequest,
    ForceActuatorSetBoosterValveDCAGainsRequest,
    ForceActuatorSetBoosterValveDCAGainsResponse,
    FreezeSensorValuesBroadcast,
    HardpointForceAndStatusRequest,
    HardpointForceAndStatusResponse,
    HardpointStepMotorMoveRequest,
    HardpointStepMotorMoveResponse,
    ILCMode,
    ReadDACValuesRequest,
    ReadDACValuesResponse,
    ReadReheaterGainsRequest,
    ReadReheaterGainsResponse,
    Reset,
    ServerIDRequest,
    ServerIDResponse,
    ServerStatusRequest,
    ServerStatusResponse,
    SetADCChannelOffsetAndSensitivityRequest,
    SetADCChannelOffsetAndSensitivityResponse,
    SetADCScanRate,
    SetILCTemporaryAddress,
    SetReheaterGainsRequest,
    SetReheaterGainsResponse,
    ThermalDemandRequest,
    ThermalDemandResponse,
    ThermalStatusRequest,
    ThermalStatusResponse,
)
from .pdu.firmware import (
    EraseApplication,
    WriteApplicationPageResponse,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationResponse,
)
from .pdu.firmware import flash as flash_ilc
from .pdu.utils import ELECTROMECHANICAL_BROADCAST_ADDRESS, PNEUMATIC_BROADCAST_ADDRESS

# Setup history file tracking via standard readline
HISTORY_FILE = os.path.expanduser("~/.ilccli_history")

try:
    import readline
except ImportError:
    print("Readline not supported.")
    readline = None  # type: ignore

if readline and hasattr(readline, "read_history_file"):
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass


# We use a global context dictionary or a container to hold our active client,
# default address and connection name.
class CLIContext:
    def __init__(self) -> None:
        self.client = None
        self.address: int = 255
        self.name: str = ""
        self.debug = False

    def dev_id(self, dev_id: int | None) -> int:
        """Returns either provided address or default address."""
        return self.address if dev_id is None else dev_id

    async def connect(self, client: AsyncModbusSerialClient | AsyncModbusTcpClient) -> None:
        await client.connect()
        client.register(ServerIDResponse)
        client.register(ServerStatusResponse)
        client.register(ChangeILCMode)
        client.register(HardpointStepMotorMoveResponse)
        client.register(HardpointForceAndStatusResponse)
        client.register(SetILCTemporaryAddress)
        client.register(ForceActuatorSetBoosterValveDCAGainsResponse)
        client.register(WriteApplicationStatesResponse)
        client.register(EraseApplication)
        client.register(WriteApplicationPageResponse)
        client.register(WriteVerifyApplicationResponse)
        client.register(ForceActuatorForceDemandDAResponse)
        client.register(ForceActuatorForceAndStatusDAResponse)
        client.register(SetADCScanRate)
        client.register(SetADCChannelOffsetAndSensitivityResponse)
        client.register(ReadDACValuesResponse)
        client.register(ThermalDemandResponse)
        client.register(ThermalStatusResponse)
        client.register(SetReheaterGainsResponse)
        client.register(ReadReheaterGainsResponse)
        client.register(Reset)

        self.client = client
        self.name = str(client)

    async def execute(self, request: ModbusPDU) -> ModbusPDU:
        if self.client is None:
            raise RuntimeError("Client not connected. Use 'serial' or 'tcp' commands to connect to client.")

        return await self.client.execute(False, request)

    def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
            click.echo("Disconnected current connection.")


pass_ctx = click.make_pass_decorator(CLIContext, ensure=True)


# Group for all ILC commands.
@click.group()
def cli() -> None:
    pass


# Commands defined click-way.


@cli.command()
@pass_ctx
def debug(ctx: CLIContext) -> None:
    """Log every command."""
    ctx.debug = True
    log = logging.getLogger("pymodbus")
    log.setLevel(logging.DEBUG)


@cli.command()
@click.argument("port", type=str)
@pass_ctx
async def serial(ctx: CLIContext, port: str) -> None:
    """Open connection to serial port."""
    ctx.disconnect()
    await ctx.connect(AsyncModbusSerialClient(port, baudrate=921600))

    click.echo(f"Connected to {port}. Type 'help' for commands, 'exit' or 'quit' to exit.\n")


@cli.command()
@click.argument("host", type=str)
@click.argument("port", type=int, default=502)
@pass_ctx
async def tcp(ctx: CLIContext, host: str, port: int) -> None:
    """Connect to TCP/IP bridge."""
    ctx.disconnect()
    await ctx.connect(AsyncModbusTcpClient(host, port=port))

    click.echo(f"Connected to {host}:{port}. Type 'help' for commands, 'exit' or 'quit' to exit.\n")


@cli.command()
@click.argument("address", type=int)
@pass_ctx
def address(ctx: CLIContext, address: int) -> None:
    """Change default address."""
    ctx.address = address


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def report_server_id(ctx: CLIContext, address: None | int) -> None:
    """Read coils or registers from the server."""
    dev_id = ctx.dev_id(address)
    server_id = await ctx.execute(ServerIDRequest(dev_id=dev_id))
    if server_id.isError():
        click.echo(f"Error: {server_id}")
        return

    click.echo(f"Unique ID: {server_id.unique_id} (0x{server_id.unique_id:012X})")
    click.echo(f"ILC Application Type: {server_id.ilc_app_type}")
    click.echo(f"Network Node Type: 0x{server_id.network_node_type:02X}")
    click.echo(f"ILC Selected Options: 0x{server_id.ilc_selected_options:02X}")
    click.echo(f"Network Node Options: {server_id.network_node_options:02X}")
    click.echo(f"Firmware Version: {server_id.major_rev}.{server_id.minor_rev}")
    click.echo(f"Firmware Name: {server_id.firmware_name}")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def report_server_status(ctx: CLIContext, address: None | int) -> None:
    """Report ILC status - mode, status and faults."""
    dev_id = ctx.dev_id(address)
    server_status = await ctx.execute(ServerStatusRequest(dev_id=dev_id))
    if server_status.isError():
        click.echo(f"Error: {server_status}")
        return

    click.echo(f"Mode: {server_status.mode}")
    click.echo(f"Status: {server_status.status} (0x{server_status.status:04X})")
    click.echo(f"Faults: {server_status.faults} (0x{server_status.faults:04X})")


@cli.command()
@click.argument("mode", type=int, default=0xFFFF)
@click.argument("address", type=int, default=None)
@pass_ctx
async def change_ilc_mode(ctx: CLIContext, mode: int, address: None | int) -> None:
    """Command ILC to change its mode. Reads ILC mode if new mode is not
    provided."""
    dev_id = ctx.dev_id(address)
    ilc_mode = await ctx.execute(ChangeILCMode(dev_id=dev_id, new_mode=mode))

    if ilc_mode.isError():
        click.echo(f"Error: {ilc_mode}")
        return

    click.echo(f"Mode: {ilc_mode.mode}")


async def __state_transition(ctx: CLIContext, dev_id: int, target_mode: int) -> None:
    current_mode = await ctx.execute(ChangeILCMode(dev_id=dev_id))
    if current_mode.isError():
        click.echo("Error: {current_mode}")
        return

    with click.progressbar(length=4, show_eta=True, show_percent=True, item_show_func=str, width=0) as bar:
        if current_mode.mode == target_mode:
            bar.update(4, f"New ILC {dev_id} mode: {ILCMode(current_mode.mode).name}")
            return
        next_mode = await ctx.execute(
            ChangeILCMode(dev_id=dev_id, new_mode=target_mode, current_mode=current_mode.mode)
        )
        if next_mode.isError():
            click.echo("Error: {next_mode}")
            return
        bar.update(
            1,
            f"current: {ILCMode(next_mode.mode).name}"
            if next_mode.mode in ILCMode
            else f"current: {next_mode.mode}",
        )
        if next_mode.mode == current_mode.mode:
            if current_mode.mode in ILCMode:
                click.echo(f"Cannot transition - stuck in {ILCMode(current_mode.mode).name}")
            else:
                click.echo(f"Cannot transition - stuck in {current_mode.mode}")
            return
        current_mode = next_mode

    click.echo(f"ILC {dev_id} cannot transition to mode {target_mode}")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def standby(ctx: CLIContext, address: None | int) -> None:
    """Switch ILC to standby mode."""
    await __state_transition(ctx, ctx.dev_id(address), ILCMode.STANDBY)


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def disable(ctx: CLIContext, address: None | int) -> None:
    """Switch ilc to disabled mode."""
    await __state_transition(ctx, ctx.dev_id(address), ILCMode.DISABLED)


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def enable(ctx: CLIContext, address: None | int) -> None:
    """Switch ILC to enabled mode."""
    await __state_transition(ctx, ctx.dev_id(address), ILCMode.ENABLED)


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def bootloader(ctx: CLIContext, address: None | int) -> None:
    """Switch ILC to bootloader mode."""
    await __state_transition(ctx, ctx.dev_id(address), ILCMode.BOOTLOADER)


@cli.command()
@click.argument("steps", type=int, default=0)
@click.argument("address", type=int, default=None)
@pass_ctx
async def hardpoint_step_motor_move(ctx: CLIContext, steps: int, address: None | int) -> None:
    """Command ILC to move hardpoint step motor."""
    dev_id = ctx.dev_id(address)
    hp_status = await ctx.execute(HardpointStepMotorMoveRequest(dev_id=dev_id, step_motor_command=steps))

    if hp_status.isError():
        click.echo(f"Error: {hp_status}")
        return

    click.echo(f"Encoder position: {hp_status.ssi_encoder_position}")
    click.echo(f"Force: {hp_status.load_cell_force:0.3f}")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def hardpoint_force_and_status(ctx: CLIContext, address: None | int) -> None:
    """Command ILC to move hardpoint step motor."""
    dev_id = ctx.dev_id(address)
    hp_status = await ctx.execute(HardpointForceAndStatusRequest(dev_id=dev_id))

    if hp_status.isError():
        click.echo(f"Error: {hp_status}")
        return

    click.echo(f"ILC Fault: {hp_status.ilc_fault}")
    click.echo(f"Limit switch CW: {hp_status.limit_switch_cw}")
    click.echo(f"Limit switch CCW: {hp_status.limit_switch_ccw}")
    click.echo(f"Communication countre: {hp_status.communication_counter}")
    click.echo(f"Encoder position: {hp_status.ssi_encoder_position}")
    click.echo(f"Force: {hp_status.load_cell_force:0.3f}")


@cli.command()
@click.argument("new_address", type=int)
@click.argument("address", type=int, default=None)
@pass_ctx
async def set_ilc_temporary_address(ctx: CLIContext, new_address: int, address: None | int) -> None:
    "Set ILC temporary address. Sets default address to the new address."
    dev_id = ctx.dev_id(address)
    address_status = await ctx.execute(SetILCTemporaryAddress(dev_id=dev_id, new_address=new_address))

    if address_status.isError():
        click.echo(f"Error: {address_status}")
        return

    click.echo(f"New address: {address_status.address}")
    ctx.address = address_status.address


@cli.command()
@click.argument("axial-gain", type=float)
@click.argument("lateral-gain", type=float)
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_set_booster_valve_dca_gains(
    ctx: CLIContext, axial_gain: float, lateral_gain: float, address: None | int
) -> None:
    "Set booster valves DCA gains."
    dev_id = ctx.dev_id(address)
    set_gains = await ctx.execute(
        ForceActuatorSetBoosterValveDCAGainsRequest(
            dev_id=dev_id, axial_gain=axial_gain, lateral_gain=lateral_gain
        )
    )

    if set_gains.isError():
        click.echo(f"Error: {set_gains}")
        return

    click.echo(
        f"ILC {dev_id} Booster Valve DCA Gains set to axial: {axial_gain:.4f} lateral: {lateral_gain:.4f}"
    )


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_read_booster_valve_dca_gains(ctx: CLIContext, address: None | int) -> None:
    "Set booster valves DCA gains."
    dev_id = ctx.dev_id(address)
    read_gains = await ctx.execute(ForceActuatorReadBoosterValveDCAGainsRequest(dev_id=dev_id))

    if read_gains.isError():
        click.echo(f"Error: {read_gains}")
        return

    click.echo(f"Axial gain: {read_gains.axial_gain:.4f}")
    click.echo(f"Lateral gain: {read_gains.lateral_gain:.4f}")


@cli.command()
@click.argument("intel-hex", type=click.Path())
@click.argument("address", type=int, default=None)
@pass_ctx
async def flash(ctx: CLIContext, intel_hex: click.Path, address: None | int) -> None:
    """Flash new ILC firmware."""
    dev_id = ctx.dev_id(address)
    if ctx.debug:
        await flash_ilc(ctx.client, dev_id, IntelHex(intel_hex))
        return

    with click.progressbar(length=1000, show_eta=True, show_percent=True, item_show_func=str, width=0) as bar:
        await flash_ilc(ctx.client, dev_id, IntelHex(intel_hex), bar.update)


@cli.command()
@click.argument("communication-counter", type=int)
@click.argument("broadcast", type=int, default=None)
@pass_ctx
async def freeze_sensor_values(ctx: CLIContext, communication_counter: int, broadcast: int) -> None:
    if broadcast not in (ELECTROMECHANICAL_BROADCAST_ADDRESS, PNEUMATIC_BROADCAST_ADDRESS):
        click.echo(
            "Freeze sensor broadcast must be either"
            f"{ELECTROMECHANICAL_BROADCAST_ADDRESS} or"
            f"{PNEUMATIC_BROADCAST_ADDRESS} broadcast address."
        )
        return
    freeze_sensor = await ctx.execute(FreezeSensorValuesBroadcast(address, communication_counter))

    if freeze_sensor.isError():
        click.echo(f"Error: {freeze_sensor}")
        return

    click.echo("Sensor values freezed.")


@cli.command()
@click.argument("force-setpoint", type=float)
@click.argument("slew-flag", type=int, default=0)
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_force_demand_sa(
    ctx: CLIContext,
    force_setpoint: float,
    slew_flag: int,
    address: None | int,
) -> None:
    dev_id = ctx.dev_id(address)
    sa_demand = await ctx.execute(
        ForceActuatorForceDemandSARequest(dev_id, slew_flag, int(force_setpoint * 1000))
    )

    if sa_demand.isError():
        click.echo("Error: {sa_demand}")
        return

    click.echo(f"ILC Fault: {sa_demand.ilc_fault}")
    click.echo(f"DCA Fault: {sa_demand.dca_fault}")
    click.echo(f"Communication counter: {sa_demand.communication_counter}")

    click.echo("")

    click.echo(f"Axial measured force: {sa_demand.axial_cell_force:.4f}")
    click.echo(f"Lateral measured force: {sa_demand.lateral_cell_force:.4f}")


@cli.command()
@click.argument("axial-force-setpoint", type=float)
@click.argument("lateral-force-setpoint", type=float)
@click.argument("slew-flag", type=int, default=0)
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_force_demand_da(
    ctx: CLIContext,
    axial_force_setpoint: float,
    lateral_force_setpoint: float,
    slew_flag: int,
    address: None | int,
) -> None:
    dev_id = ctx.dev_id(address)
    da_demand = await ctx.execute(
        ForceActuatorForceDemandDARequest(
            dev_id, slew_flag, int(axial_force_setpoint * 1000), int(lateral_force_setpoint * 1000)
        )
    )

    if da_demand.isError():
        click.echo("Error: {da_demand}")
        return

    click.echo(f"ILC Fault: {da_demand.ilc_fault}")
    click.echo(f"DCA Fault: {da_demand.dca_fault}")
    click.echo(f"Communication counter: {da_demand.communication_counter}")

    click.echo("")

    click.echo(f"Axial measured force: {da_demand.axial_cell_force:.4f}")
    click.echo(f"Lateral measured force: {da_demand.lateral_cell_force:.4f}")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_force_and_status_da(ctx: CLIContext, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    da_force = await ctx.execute(ForceActuatorForceAndStatusRequest(dev_id))

    if da_force.isError():
        click.echo("Error: {da_force}")
        return

    click.echo(f"ILC Fault: {da_force.ilc_fault}")
    click.echo(f"DCA Fault: {da_force.dca_fault}")
    click.echo(f"Communication counter: {da_force.communication_counter}")

    click.echo("")

    click.echo(f"Axial measured force: {da_force.axial_cell_force:.4f}")
    click.echo(f"Lateral measured force: {da_force.lateral_cell_force:.4f}")


@cli.command()
@click.argument("scan-rate", type=int, default=ADCScanRate.NO_CHANGE)
@click.argument("address", type=int, default=None)
@pass_ctx
async def set_adc_scan_rate(ctx: CLIContext, scan_rate: int, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    rate = await ctx.execute(SetADCScanRate(dev_id, ADCScanRate(scan_rate)))

    if rate.isError():
        click.echo(f"Error: {rate}")
        return

    click.echo(f"Scan Rate: {rate.scan_rate.name}")


@cli.command()
@click.argument("sensor_channel", type=int)
@click.argument("offset", type=float)
@click.argument("sensitivity", type=float)
@click.argument("address", type=int, default=None)
@pass_ctx
async def set_adc_channel_offset_and_sensitivity(
    ctx: CLIContext, sensor_channel: int, offset: float, sensitivity: float, address: None | int
) -> None:
    dev_id = ctx.dev_id(address)
    channel = await ctx.execute(
        SetADCChannelOffsetAndSensitivityRequest(dev_id, sensor_channel, offset, sensitivity)
    )

    if channel.isError():
        click.echo(f"Error: {channel}")
        return

    click.echo(f"Set ILC {address} ADC channel {sensor_channel}: {offset=:.3f} {sensitivity=:.3f}.")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def read_dac_values(ctx: CLIContext, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    dac_values = await ctx.execute(ReadDACValuesRequest(dev_id))

    if dac_values.isError():
        click.echo("Error: {dac_values}")
        return

    click.echo(f"DAC 1 (axial push): {dac_values.dac1_axial_push}")
    click.echo(f"DAC 2 (axial pull): {dac_values.dac2_axial_pull}")
    click.echo(f"DAC 3 (lateral push): {dac_values.dac3_lateral_push}")
    click.echo(f"DAC 4 (lateral pull): {dac_values.dac4_lateral_pull}")


@cli.command()
@click.argument("heater-pwm", type=int)
@click.argument("fan-pwm", type=int)
@click.argument("address", type=int, default=None)
@pass_ctx
async def thermal_demand(ctx: CLIContext, heater_pwm: int, fan_pwm: int, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    thermal = await ctx.execute(ThermalDemandRequest(dev_id, heater_pwm // 10, fan_pwm // 10))

    if thermal.isError():
        click.echo(f"Error: {thermal}")
        return

    click.echo(f"Differential temperature: {thermal.differential_temperature:.2f} °C")
    click.echo(f"Fan RPM: {thermal.fan_rpm * 10} rpm")
    click.echo(f"Absolute temperature: {thermal.absolute_temperature:.2f} °C")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def thermal_status(ctx: CLIContext, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    thermal = await ctx.execute(ThermalStatusRequest(dev_id))

    if thermal.isError():
        click.echo(f"Error: {thermal}")
        return

    click.echo(f"Differential temperature: {thermal.differential_temperature:.2f} °C")
    click.echo(f"Fan RPM: {thermal.fan_rpm * 10} rpm")
    click.echo(f"Absolute temperature: {thermal.absolute_temperature:.2f} °C")


@cli.command()
@click.argument("proportional-gain", type=float)
@click.argument("integral-gain", type=float)
@click.argument("address", type=int, default=None)
@pass_ctx
async def set_reheater_gains(
    ctx: CLIContext, proportional_gain: float, integral_gain: float, address: None | int
) -> None:
    dev_id = ctx.dev_id(address)
    reheater = await ctx.execute(SetReheaterGainsRequest(dev_id, proportional_gain, integral_gain))

    if reheater.isError():
        click.echo(f"Error: {reheater}")
        return

    click.echo(f"Set ILC {dev_id} to: {integral_gain=:.6f} {proportional_gain=:.6f}.")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def read_reheater_gains(ctx: CLIContext, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    reheater = await ctx.execute(ReadReheaterGainsRequest(dev_id))

    if reheater.isError():
        click.echo(f"Error: {reheater}")
        return

    click.echo(f"Reheater Gains P (proportional): {reheater.p:.6f}")
    click.echo(f"Reheater Gains I (intergral): {reheater.i:.6f}")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
async def reset(ctx: CLIContext, address: None | int) -> None:
    dev_id = ctx.dev_id(address)
    reset_response = await ctx.execute(Reset(dev_id))

    if reset_response.isError():
        click.echo(f"Error: {reset_response}")
        return

    click.echo(f"ILC {dev_id} reseted.")


async def main() -> None:
    # Initialize our custom click context container
    ctx_obj = CLIContext()

    while True:
        try:
            # Read input using standard prompt line
            user_input = input(f"{ctx_obj.name}> ").strip()

            if not user_input:
                continue

            # Handle manual exit commands
            if user_input.lower() in ["exit", "quit"]:
                break

            # Intercept standard 'help' string to align with Click's '--help'
            if user_input.lower() == "help":
                user_input = "--help"

            args = user_input.split(" ")

            # Run the command through the click parser pipeline
            await cli.main(args=args, prog_name="", standalone_mode=False, obj=ctx_obj)
        except click.NoSuchOption as e:
            click.echo(f"{e.message}")
        except RuntimeError as e:
            click.echo(f"RuntimeError: {str(e)}")
        except ModbusIOException as e:
            click.echo(f"ModbusIOException: {str(e)}")
        except click.UsageError as e:
            e.show()
        except click.BadArgumentUsage as e:
            e.show()
        except (KeyboardInterrupt, EOFError):
            click.echo("\nExiting...")
            break
        finally:
            if readline and hasattr(readline, "write_history_file"):
                readline.write_history_file(HISTORY_FILE)

    ctx_obj.disconnect()


def run() -> None:
    logging.basicConfig()

    asyncio.run(main())
