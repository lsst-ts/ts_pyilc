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
import logging

from pymodbus.datastore import ModbusServerContext
from pymodbus.pdu import ExceptionResponse, ModbusPDU
from pymodbus.server import StartAsyncTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

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
    WriteApplicationPageRequest,
    WriteApplicationPageResponse,
    WriteApplicationStatesRequest,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationRequest,
    WriteVerifyApplicationResponse,
)
from .pdu.utils import ILCException

# Global broadcast communication counter
communication_counter = 0


class SimulatedServerIDRequest(ServerIDRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = ServerIDResponse(dev_id=self.dev_id)

        pdu.unique_id = 0x020304050607
        pdu.ilc_app_type = 0xFA
        pdu.network_node_type = 0xFF
        pdu.ilc_selected_options = 0xFD
        pdu.network_node_options = 0xFC
        pdu.minor_rev = 255
        pdu.major_rev = 245
        pdu.firmware_name = "Simulated ILC (C) 4242 Sirius Cybernetics Corp."

        return pdu


class SimulatedServerStatusRequest(ServerStatusRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = ServerStatusResponse(dev_id=self.dev_id)

        pdu.mode = 0x04
        pdu.status = 0x0102
        pdu.faults = 0x0000

        return pdu


ilc_mode = int(ILCMode.STANDBY)


class SimulatedChangeILCMode(ChangeILCMode):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        global ilc_mode

        if self.mode == 0xFFFF:
            return ChangeILCMode(self.dev_id, ilc_mode)

        def exception(exception_code: int) -> ExceptionResponse:
            return ExceptionResponse(self.function_code, exception_code, self.dev_id)

        def change_mode(new_mode: int | None = None) -> ChangeILCMode:
            global ilc_mode

            ilc_mode = self.mode if new_mode is None else new_mode
            return ChangeILCMode(self.dev_id, ilc_mode)

        # test allowable transitions..
        if ilc_mode == ILCMode.FAULT:
            if self.mode != ILCMode.CLEAR_FAULTS:
                return exception(ILCException.ILLEGAL_FUNCTION)
            return change_mode(ILCMode.STANDBY)
        elif ilc_mode == ILCMode.BOOTLOADER:
            if self.mode != ILCMode.STANDBY:
                return exception(ILCException.ILLEGAL_FUNCTION)
            return change_mode()

        if self.mode in (ILCMode.STANDBY, ILCMode.DISABLED, ILCMode.ENABLED):
            if abs(ilc_mode - self.mode) != 1:
                return exception(ILCException.ILLEGAL_FUNCTION)
            return change_mode()
        elif self.mode == ILCMode.BOOTLOADER:
            if ilc_mode != ILCMode.STANDBY:
                return exception(self.ILCException.ILLEGAL_FUNCTION)
            return change_mode()
        elif self.mode == ILCMode.FAULT:
            return change_mode(ILCMode.FAULT)

        return exception(ILCException.ILLEGAL_DATA_VALUE)


class SimulatedHardpointStepMoveRequest(HardpointStepMotorMoveRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = HardpointStepMotorMoveResponse(dev_id=self.dev_id)

        pdu.ssi_encoder_position = -8
        pdu.load_cell_force = 42.42

        return pdu


class SimulatedHardpointForceAndStatusRequest(HardpointForceAndStatusRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = HardpointForceAndStatusResponse(dev_id=self.dev_id)

        global communication_counter

        pdu.ilc_fault = True
        pdu.limit_switch_cw = True
        pdu.limit_switch_ccw = True
        pdu.communication_counter = communication_counter & 0x0F
        communication_counter += 1

        pdu.ssi_encoder_position = -8
        pdu.load_cell_force = 43.42

        return pdu


class SimulatedSetILCTemporaryAddress(SetILCTemporaryAddress):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = SetILCTemporaryAddress(dev_id=self.dev_id, new_address=self.address)

        return pdu


class SimulatedForceActuatorSetBoosterValveDCAGainRequest(ForceActuatorSetBoosterValveDCAGainRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = ForceActuatorSetBoosterValveDCAGainResponse(dev_id=self.dev_id)

        return pdu


class SimulatedWriteApplicationStatesReques(WriteApplicationStatesRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = WriteApplicationStatesResponse(dev_id=self.dev_id)

        return pdu


class SimulatedEraseApplication(EraseApplication):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = EraseApplication(dev_id=self.dev_id)

        return pdu


class SimulatedWriteApplicationPageRequest(WriteApplicationPageRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = WriteApplicationPageResponse(dev_id=self.dev_id)

        return pdu


class SimulatedWriteVerifyApplicationRequest(WriteVerifyApplicationRequest):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        pdu = WriteVerifyApplicationResponse(dev_id=self.dev_id, status=0)

        return pdu


class SimulatedFreezeSensorValuesBroadcast(FreezeSensorValuesBroadcast):
    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> None:
        return None


async def main(host: str, port: int) -> None:
    print(f"Starting simulator on {host}:{port}.")

    server = asyncio.create_task(
        StartAsyncTcpServer(
            context=SimDevice(0, SimData(0, datatype=DataType.REGISTERS, values=[17] * 100)),
            address=(host, port),
            custom_pdu=[
                SimulatedServerIDRequest,
                SimulatedServerStatusRequest,
                SimulatedChangeILCMode,
                SimulatedHardpointStepMoveRequest,
                SimulatedHardpointForceAndStatusRequest,
                SimulatedSetILCTemporaryAddress,
                SimulatedForceActuatorSetBoosterValveDCAGainRequest,
                SimulatedWriteApplicationStatesReques,
                SimulatedEraseApplication,
                SimulatedWriteApplicationPageRequest,
                SimulatedWriteVerifyApplicationRequest,
                SimulatedFreezeSensorValuesBroadcast,
            ],
        )
    )

    await server


def run() -> None:
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="localhost",
        type=str,
        help="Simualtor hostname. Defaults to localhost.",
    )
    parser.add_argument("--port", default=5020, type=int, help="Simulator port. Defaults to 5020.")
    parser.add_argument("--debug", action="store_true", help="Enable pymodbus debugging.")

    args = parser.parse_args()

    if args.debug:
        log = logging.getLogger("pymodbus")
        log.setLevel(logging.DEBUG)

    asyncio.run(main(args.host, args.port))
