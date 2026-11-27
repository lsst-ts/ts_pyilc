# This file is part of ts_pyilc.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from typing import Callable

from intelhex import IntelHex
from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.pdu import ModbusPDU

from . import (
    ChangeILCMode,
    ForceActuatorForceAndStatusDAResponse,
    ForceActuatorForceDemandDAResponse,
    ForceActuatorReadBoosterValveDCAGainsResponse,
    ForceActuatorSetBoosterValveDCAGainsResponse,
    HardpointForceAndStatusResponse,
    HardpointStepMotorMoveResponse,
    ILCMode,
    ReadCalibrationDataResponse,
    ReadDACValuesResponse,
    ReadMezzanineIDResponse,
    ReadMezzanineLVDTResponse,
    ReadMezzaninePressureResponse,
    ReadMezzanineStatusResponse,
    ReadMonitorTemperatureSensorsResponse,
    ReadReheaterGainsResponse,
    Reset,
    ServerIDResponse,
    ServerStatusResponse,
    SetADCChannelOffsetAndSensitivityResponse,
    SetADCScanRate,
    SetILCTemporaryAddress,
    SetReheaterGainsResponse,
    ThermalDemandResponse,
    ThermalStatusResponse,
)
from .firmware import (
    CRC,
    EraseApplication,
    WriteApplicationPageRequest,
    WriteApplicationPageResponse,
    WriteApplicationStatesRequest,
    WriteApplicationStatesResponse,
    WriteVerifyApplicationRequest,
    WriteVerifyApplicationResponse,
)

__all__ = ["Context", "ILCModeChangeError"]


class ILCModeChangeError(RuntimeError):
    def __init__(self, current_mode: ILCMode, message: str):
        super().__init__(message)
        self.current_mode = current_mode


# We use a global context dictionary or a container to hold our active client,
# default address and connection name.
class Context:
    """Global context, to be used for command line as well as scripting.

    Arguments
    ---------
    client : `None | AsyncModbusSerialClient | AsyncModbusTcpClient`
        Modbus client to access ILC.
    name : `str`
        Named identified of the connection.
    """

    def __init__(self) -> None:
        self.client = None
        self.name: str = ""

    async def connect(self, client: AsyncModbusSerialClient | AsyncModbusTcpClient) -> None:
        """Connect to a device.

        Parameters
        ----------
        client : `AsyncModbusSerialClient | AsyncModbusTcpClient`
            New Modbus client.
        """
        await client.connect()
        client.register(ServerIDResponse)
        client.register(ServerStatusResponse)
        client.register(ChangeILCMode)
        client.register(HardpointStepMotorMoveResponse)
        client.register(HardpointForceAndStatusResponse)
        client.register(SetILCTemporaryAddress)
        client.register(ForceActuatorReadBoosterValveDCAGainsResponse)
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
        client.register(ReadCalibrationDataResponse)
        client.register(ReadMezzaninePressureResponse)
        client.register(ReadMezzanineIDResponse)
        client.register(ReadMezzanineStatusResponse)
        client.register(ReadMezzanineLVDTResponse)
        client.register(ReadMonitorTemperatureSensorsResponse)

        self.client = client
        self.name = str(client)

    async def execute(self, request: ModbusPDU) -> ModbusPDU:
        """Execute request. Returns request response.

        Parameters
        ----------
        request : `ModbusPDU`
            Request to execute on PDU.

        Returns
        -------
        response : `ModbusPDU`
            Request response. Usually same custom PDU object as request, with
            Response suffix (instead of Request for request).
        """
        if self.client is None:
            raise RuntimeError("Client not connected. Use 'serial' or 'tcp' commands to connect to client.")

        return await self.client.execute(False, request)

    async def change_mode(
        self,
        address: int,
        target_mode: ILCMode,
        callback: Callable[[int, ILCMode, str], None] = lambda progress, mode, message: None,
    ) -> None:
        """Change ILC with with given address to new state. Does its best to
        make sure the ILC ends in new mode. ILCModeChangeError on any problems.

        Parameters
        ----------
        address : `int`
            ILC address.
        target_mode : `ILCMode`
            New ILC mode.
        callback : `Callable[[int, ILCMode, str], None]`
            Callback as the state is changed. Receives progress (0-5, 5 means
            done) and current ILC mode and string explaining what is going on.
        """
        current_mode = await self.execute(ChangeILCMode(dev_id=address))
        if current_mode.isError():
            raise ILCModeChangeError(ILCMode.QUERY, f"Cannot query ILC {address} mode.")
        if current_mode.mode == target_mode:
            callback(5, target_mode, f"ILC {address} already in target mode {target_mode.name}.")
            return
        callback(0, current_mode.mode, f"Starting change to {target_mode.name}.")

        for progress in range(1, 5):
            if current_mode.mode == target_mode:
                callback(
                    6 - progress,
                    current_mode.mode,
                    f"Target mode reached for address {address} mode: {ILCMode(current_mode.mode).name}",
                )
                return
            next_mode = await self.execute(
                ChangeILCMode(dev_id=address, new_mode=target_mode, current_mode=current_mode.mode)
            )
            if next_mode.isError():
                raise ILCModeChangeError(
                    next_mode,
                    f"Cannot change mode from {ILCMode(current_mode.mode).name} towards {target_mode.name}",
                )

            if next_mode.mode == current_mode.mode:
                raise ILCModeChangeError(
                    next_mode, f"Cannot transition - stuck in {ILCMode(current_mode.mode).name}"
                )
            elif next_mode.mode != target_mode:
                callback(
                    1,
                    next_mode.mode,
                    f"ILC {address} mode changed from {ILCMode(current_mode.mode).name} "
                    f"to {ILCMode(next_mode.mode).name}",
                )

            current_mode = next_mode

        raise ILCModeChangeError(current_mode, f"ILC {address} cannot transition to mode {target_mode.name}")

    async def flash(
        self,
        address: int,
        intel_hex_file: IntelHex,
        callback: Callable[[int, str], None] = lambda progress, message: None,
    ) -> int:
        """Flash ILC. Operates at the following steps:
        1. Change ILC into bootloader (firmware update) mode.
        2. Erase ILC application.
        3. Write ILC application pages.
        4. Write ILC application statistics.
        5. Verify application.
        6. Change ILC into standby mode.
        7. Change ILC into disabled mode.

        Parameters
        ----------
        address: `int`
            ILC device address.
        intel_hex_file : `IntelHex`
            IntelHex class with data to load.
        callback : `Callable[[int, str], None]`, optional
            Optional callback. Called after an operation (ILC communication) is
            performed. The int argument is a number 0-1000, steps progressed.
            The string is a string describing current phase of the operation
            progress.

        Returns
        -------
        verify : `int`
            Returned verification status.
        """

        # maximal progress - 100 %, so 1000 per thousand
        MAX_PROGRESS = 1000

        # cost of a simple FCU query
        SIMPLE_STEP = 5

        # number 0-1000 for the current phase
        progress_phase = 0

        # 1. Change ILC to bootloader state.
        await self.change_mode(
            address, ILCMode.BOOTLOADER, lambda progress, mode, message: callback(progress, message)
        )

        progress_phase += SIMPLE_STEP
        callback(SIMPLE_STEP, "Erasing app")

        # 2. Command ILC to erase its firmware - made it available for writing.
        erase = await self.execute(EraseApplication(dev_id=address))
        if erase.isError():
            raise RuntimeError(f"Cannot erase ILC {address}: {erase}.")

        intel_hex_file.padding = 0xFF

        # use only 0x0000 - 0xFFFF segments; hexfiles usually contains some 00
        # well over 0xFFFF, we will ignore those
        segments = [s for s in intel_hex_file.segments() if s[1] < 0xFFFF]
        start_address = segments[0][0]
        end_address = segments[-1][1]

        mem_address = start_address

        # We are flashing 256 bytes chunks, but as every fourth byte is not
        # written, only 256 - (256 / 4) bytes are actually transferred
        PAGE_PADDED_LENGTH = 256
        APPLICATION_PAGE_LENGTH = PAGE_PADDED_LENGTH - (PAGE_PADDED_LENGTH // 4)

        # CRC is calculated from all data (including padding characters, which
        # aren't send to ILC). From the first send byte to the latest valid
        # byte - see length argument.
        crc = CRC()

        # progress step per byte written
        progress_step = float(end_address - start_address) / (
            MAX_PROGRESS - progress_phase - (5 * SIMPLE_STEP)
        )

        # 3. Write ILC pages.
        while mem_address < end_address:
            data_start = max(segments[0][0], mem_address)
            length = PAGE_PADDED_LENGTH

            data = []

            for i in range(PAGE_PADDED_LENGTH):
                data.append(intel_hex_file[mem_address + i])

            for i in range(3, PAGE_PADDED_LENGTH + 1, 4):
                data[i] = 0x00

            if len(segments) == 1:
                length = min(segments[0][1] - data_start, PAGE_PADDED_LENGTH)

            # Use all valid data for CRC calculation.
            crc.append(data[:length])

            # remove every 4th byte - that's how hexfile was compiled, as it is
            # storing 3 bytes of allowable MCU opcodes into 4 bytes
            del data[3::4]

            progress_phase += int(progress_step * PAGE_PADDED_LENGTH)
            callback(
                int(progress_step * PAGE_PADDED_LENGTH), f"Writing {progress_phase // PAGE_PADDED_LENGTH}"
            )

            page = await self.execute(
                WriteApplicationPageRequest(
                    dev_id=address,
                    start_address=mem_address,
                    length=APPLICATION_PAGE_LENGTH,
                    data=bytes(data),
                ),
            )
            if page.isError():
                raise RuntimeError(
                    f"Cannot write page starting with address {mem_address} to ILC {address}: {page}."
                )
            mem_address += PAGE_PADDED_LENGTH

            # handle segments
            if mem_address > segments[0][1]:
                del segments[0]
                if len(segments) and (mem_address) + 0xFF < segments[0][0]:
                    raise RuntimeError(
                        f"Big firmware chunk is empty between address {mem_address} and {segments[0][0]}, "
                        "aborting writing the file."
                    )

        progress_phase += SIMPLE_STEP
        callback(SIMPLE_STEP, "Confirming")

        # 4. Write application statistics. ILC verifies checksum, and if it
        # matches, it is ready to copy new firmware from staging are into main
        # memory and use it after rebooting.
        stat = await self.execute(
            WriteApplicationStatesRequest(
                dev_id=address,
                data_crc=crc.crc,
                start_address=start_address,
                data_length=end_address - start_address,
            ),
        )
        if stat.isError():
            raise RuntimeError(f"Cannot write end statistics to ILC {address}: {stat}.")

        progress_phase += 5
        callback(5, "quering status")

        # 5. Ask ILC for verification status. This also copy the firmware from
        # stagging memory buffer into main memory.
        verify = await self.execute(WriteVerifyApplicationRequest(dev_id=address))
        if verify.isError():
            raise RuntimeError(f"Cannot verify ILC {address} write: {verify}.")

        # 6. Transition ILC to DISABLED mode.
        await self.change_mode(address, ILCMode.DISABLED)

        callback(MAX_PROGRESS, "done")

        return verify.status

    def disconnect(self) -> None:
        """Closes connection to client."""
        pass
