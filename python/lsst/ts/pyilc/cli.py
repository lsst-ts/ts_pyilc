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
import os

import asyncclick as click
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.pdu import ModbusPDU

from . import ServerIDRequest, ServerIDResponse

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


# We use a global context dictionary or a container to hold our active client
class CLIContext:
    def __init__(self) -> None:
        self.client = None
        self.address: int = 255
        self.name: str = ""

    async def connect(self, client: AsyncModbusSerialClient | AsyncModbusTcpClient) -> None:
        await client.connect()
        client.register(ServerIDResponse)

        self.client = client
        self.name = str(client)

    def execute(self, pdu: ModbusPDU) -> ModbusPDU:
        if self.client is None:
            raise RuntimeError("Client not connected. Use 'serial' or 'tcp' commands to connect to client.")

        return self.client.execute(pdu)

    def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()
            click.echo("Disconnected current connection.")


pass_ctx = click.make_pass_decorator(CLIContext, ensure=True)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("port", type=str)
@pass_ctx
async def serial(ctx: CLIContext, port: str) -> None:
    ctx.disconnect()
    await ctx.connect(AsyncModbusSerialClient(port, baudrate=921600))

    click.echo(f"Connected to {port}. Type 'help' for commands, 'exit' or 'quit' to exit.\n")


@cli.command()
@click.argument("host", type=str)
@click.argument("port", type=int, default=502)
@pass_ctx
async def tcp(ctx: CLIContext, host: str, port: int) -> None:
    ctx.disconnect()
    await ctx.connect(AsyncModbusTcpClient(host, port=port))

    click.echo(f"Connected to {host}:{port}. Type 'help' for commands, 'exit' or 'quit' to exit.\n")


@cli.command()
@click.argument("address", type=int, default=None)
@pass_ctx
def report_server_id(ctx: CLIContext, address: None | int) -> None:
    """Read coils or registers from the server."""
    server_id = ctx.execute(ServerIDRequest(dev_id=ctx.address if address is None else address))
    if server_id.isError():
        click.echo("Error: {server_id}")
        return

    click.echo(f"Unique ID: {server_id.unique_id}")
    click.echo(f"ILC Application Type: {server_id.ilc_app_type}")
    click.echo(f"Firmware Version: {server_id.major_rev}.{server_id.minor_rev}")
    click.echo(f"Firmware Name: {server_id.firmware_name}")


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
    asyncio.run(main())
