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
    ChangeILCMode,
    ForceActuatorSetBoosterValveDCAGainRequest,
    ForceActuatorSetBoosterValveDCAGainResponse,
    FreezeSensorValuesBroadcast,
    HardpointForceAndStatusRequest,
    HardpointForceAndStatusResponse,
    HardpointStepMotorMoveRequest,
    HardpointStepMotorMoveResponse,
    ILCMode,
    ServerIDRequest,
    ServerIDResponse,
    ServerStatusRequest,
    ServerStatusResponse,
    SetILCTemporaryAddress,
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
        client.register(ForceActuatorSetBoosterValveDCAGainResponse)
        client.register(WriteApplicationStatesResponse)
        client.register(EraseApplication)
        client.register(WriteApplicationPageResponse)
        client.register(WriteVerifyApplicationResponse)

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
    server_id = await ctx.execute(ServerIDRequest(dev_id=ctx.dev_id(address)))
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
    server_status = await ctx.execute(ServerStatusRequest(dev_id=ctx.dev_id(address)))
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
    ilc_mode = await ctx.execute(ChangeILCMode(dev_id=ctx.dev_id(address), new_mode=mode))

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
    hp_status = await ctx.execute(
        HardpointStepMotorMoveRequest(dev_id=ctx.dev_id(address), step_motor_command=steps)
    )

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
    hp_status = await ctx.execute(HardpointForceAndStatusRequest(dev_id=ctx.dev_id(address)))

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
    address_status = await ctx.execute(
        SetILCTemporaryAddress(dev_id=ctx.dev_id(address), new_address=new_address)
    )

    if address_status.isError():
        click.echo(f"Error: {address_status}")
        return

    click.echo(f"New address: {address_status.address}")
    ctx.address = address_status.address


@cli.command()
@click.argument("axial_gain", type=float)
@click.argument("lateral_gain", type=float)
@click.argument("address", type=int, default=None)
@pass_ctx
async def force_actuator_set_booster_valve_dca_gain(
    ctx: CLIContext, axial_gain: float, lateral_gain: float, address: None | int
) -> None:
    "Set booster valves DCA gains."
    set_gains = await ctx.execute(
        ForceActuatorSetBoosterValveDCAGainRequest(
            dev_id=ctx.dev_id(address),
            axial_gain=axial_gain,
            lateral_gain=lateral_gain,
        )
    )

    if set_gains.isError():
        click.echo(f"Error: {set_gains}")
        return

    click.echo(f"Booster Valve DCA Gains set to axial: {axial_gain:.4f} lateral: {lateral_gain:.4f}")


@cli.command()
@click.argument("intel-hex", type=click.Path())
@click.argument("address", type=int, default=None)
@pass_ctx
async def flash(ctx: CLIContext, intel_hex: click.Path, address: None | int) -> None:
    """Flash new ILC firmware."""
    if ctx.debug:
        await flash_ilc(ctx.client, ctx.dev_id(address), IntelHex(intel_hex))
        return

    with click.progressbar(length=1000, show_eta=True, show_percent=True, item_show_func=str, width=0) as bar:
        await flash_ilc(ctx.client, ctx.dev_id(address), IntelHex(intel_hex), bar.update)


@cli.command()
@click.argument("communication_counter", type=int)
@click.argument("broadcast", type=int, default=None)
@pass_ctx
async def freeze_sensor_values(ctx: CLIContext, communication_counter: int, broadcast: None | int) -> None:
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
