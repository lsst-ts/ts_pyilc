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

import argparse
import asyncio

from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.pdu import ModbusPDU
from pymodbus.server import StartAsyncTcpServer

from .pdu import (
    ForceActuatorSetBoosterValveDCAGainRequest,
    ForceActuatorSetBoosterValveDCAGainResponse,
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
    WriteApplicationPageRequest,
    WriteApplicationPageResponse,
    WriteApplicationStatesRequest,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationRequest,
    WriteVerifyApplicationResponse,
)


class SimulatedServerIDRequest(ServerIDRequest):
    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        pdu = ServerIDResponse(dev_id=self.dev_id)

        pdu.unique_id = 0x020304050607
        pdu.ilc_app_type = 0xFA
        pdu.network_node_type = 0xFF
        pdu.ilc_selected_options = 0xFD
        pdu.network_node_options = 0xFC
        pdu.minor_rev = 255
        pdu.major_rev = 245
        pdu.firmware_name = "Simulated ILC!"

        return pdu


class SimulatedServerStatusRequest(ServerStatusRequest):
    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        pdu = ServerStatusResponse(dev_id=self.dev_id)

        pdu.mode = 0x04
        pdu.status = 0x0102
        pdu.faults = 0x0000

        return pdu


ilc_mode = ILCMode.STANDBY


class SimulatedILCMode(ILCMode):
    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        global ilc_mode

        if self.mode != 0xFFFF:
            ilc_mode = self.mode
        pdu = ILCMode(dev_id=self.dev_id, new_mode=ilc_mode)

        return pdu


class SimulatedHardpointStepMoveRequest(HardpointStepMotorMoveRequest):
    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        pdu = HardpointStepMotorMoveResponse(dev_id=self.dev_id)

        pdu.ssi_encoder_position = -8
        pdu.load_cell_force = 42.42

        return pdu


class SimulatedHardpointForceAndStatusRequest(HardpointForceAndStatusRequest):
    async def update_datastore(self, context: ModbusDeviceContext) -> ModbusPDU:
        pdu = HardpointForceAndStatusResponse(dev_id=self.dev_id)

        pdu.status = 42
        pdu.ssi_encoder_position = -8
        pdu.load_cell_force = 43.42

        return pdu


class SimulatedSetILCTemporaryAddress(SetILCTemporaryAddress):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = SetILCTemporaryAddress(dev_id=self.dev_id, new_address=self.address)

        return pdu


class SimulatedForceActuatorSetBoosterValveDCAGainRequest(ForceActuatorSetBoosterValveDCAGainRequest):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = ForceActuatorSetBoosterValveDCAGainResponse(dev_id=self.dev_id)

        return pdu


class SimulatedWriteApplicationStatesReques(WriteApplicationStatesRequest):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = WriteApplicationStatesResponse(dev_id=self.dev_id)

        return pdu


class SimulatedEraseApplication(EraseApplication):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = EraseApplication(dev_id=self.dev_id)

        return pdu


class SimulatedWriteApplicationPageRequest(WriteApplicationPageRequest):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = WriteApplicationPageResponse(dev_id=self.dev_id)

        return pdu


class SimulatedWriteVerifyApplicationRequest(WriteVerifyApplicationRequest):
    async def update_datastore(self, context: ModbusServerContext) -> ModbusPDU:
        pdu = WriteVerifyApplicationResponse(dev_id=self.dev_id, status=0)

        return pdu


async def main(host: str, port: int) -> None:
    store = ModbusServerContext(single=True)

    print(f"Starting simulator on {host}:{port}.")

    server = asyncio.create_task(
        StartAsyncTcpServer(
            context=store,
            address=(host, port),
            custom_pdu=[
                SimulatedServerIDRequest,
                SimulatedServerStatusRequest,
                SimulatedILCMode,
                SimulatedHardpointStepMoveRequest,
                SimulatedHardpointForceAndStatusRequest,
                SimulatedSetILCTemporaryAddress,
                SimulatedForceActuatorSetBoosterValveDCAGainRequest,
                SimulatedWriteApplicationStatesReques,
                SimulatedEraseApplication,
                SimulatedWriteApplicationPageRequest,
                SimulatedWriteVerifyApplicationRequest,
            ],
        )
    )

    await server


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="localhost",
        type=str,
        help="Simualtor hostname. Defaults to localhost.",
    )
    parser.add_argument("--port", default=5020, type=int, help="Simulator port. Defaults to 5020")

    args = parser.parse_args()

    asyncio.run(main(args.host, args.port))
