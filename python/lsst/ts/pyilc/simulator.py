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
import argparse

from pymodbus.datastore import ModbusServerContext
from pymodbus.server import StartAsyncTcpServer

from . import ServerIDRequest


async def main(host: str, port: int) -> None:
    store = ModbusServerContext(single=True)

    server = asyncio.create_task(
        StartAsyncTcpServer(
            context=store, address=(host, port), custom_pdu=[ServerIDRequest]
        )
    )

    await server


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="localhost",
        type=str,
        help="Simualtor hostname. Defaults to localhost.",
    )
    parser.add_argument(
        "--port", default=5020, type=int, help="Simulator port. Defaults to 5020"
    )

    args = parser.parse_args()

    asyncio.run(main(args.host, args.port))
