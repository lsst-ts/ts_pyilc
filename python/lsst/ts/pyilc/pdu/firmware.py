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

from .ilc_mode import ILCMode
from .utils import ILCFunction, ILCRequest, ILCResponse

__all__ = ["flash"]

import struct
from collections.abc import Callable

from intelhex import IntelHex
from pymodbus.client import ModbusBaseClient
from pymodbus.framer import FramerRTU
from pymodbus.pdu import ModbusPDU
from pymodbus.utilities import hexlify_packets


class CRC:
    crc = 0xFFFF

    def __init__(self, data: bytes = b""):
        self.append(list(data))

    def append(self, data: list[int]) -> None:
        for data_byte in data:
            idx = FramerRTU.crc16_table[(self.crc ^ int(data_byte)) & 0xFF]
            self.crc = ((self.crc >> 8) & 0xFF) ^ idx


class WriteApplicationStatesRequest(ModbusPDU):
    """Request ILC to record newly programmed application statistics and CRCs.
    Calculates fourth argument - Modbus 16bit CRC from input arguments."""

    function_code = ILCFunction.WRITE_APPLICATION_STATES
    rtu_frame_size = 8

    def __init__(self, dev_id: int = 255, data_crc: int = 0, start_address: int = 0, data_length: int = 0):
        super().__init__(dev_id=dev_id)
        self.data_crc = data_crc
        self.start_address = start_address
        self.data_length = data_length

    def compute_parameters_CRC(self) -> int:
        data = struct.pack("<6H", self.data_crc, 0, self.start_address, 0, self.data_length, 0)
        return CRC(data).crc

    def encode(self) -> bytes:
        return struct.pack(
            ">4H", self.data_crc, self.start_address, self.data_length, self.compute_parameters_CRC()
        )

    def decode(self, data: bytes) -> None:
        (self.data_crc, self.start_address, self.data_length, parameter_CRC) = struct.unpack(">4H", data)

        computed_parameters_CRC = self.compute_parameters_CRC()

        if parameter_CRC != computed_parameters_CRC:
            raise RuntimeError(
                "Invalid parameter CRC in response: "
                f"data: {hexlify_packets(data)} "
                f"CRC: {parameter_CRC} "
                f"expected CRC: {computed_parameters_CRC}."
            )


class WriteApplicationStatesResponse(ILCResponse):
    """Response to APLICATION_STATES requets."""

    function_code = ILCFunction.WRITE_APPLICATION_STATES


class EraseApplication(ILCRequest):
    """Erases ILC applcation. Must be called before a new application can be
    flashed."""

    function_code = ILCFunction.ERASE_APPLICATION


class WriteApplicationPageRequest(ModbusPDU):
    """Write page of the newly flashed firmware."""

    function_code = ILCFunction.WRITE_APPLICATION_PAGE
    rtu_byte_count_pos = 5

    start_addres: int = 0
    length: int = 0
    data: bytes = b""

    def __init__(self, dev_id: int = 255, start_address: int = 0, length: int = 0, data: bytes = b""):
        super().__init__(dev_id=dev_id)
        self.start_address = start_address
        self.length = length
        self.data = data

    def encode(self) -> bytes:
        return struct.pack(f">HH{self.length}s", self.start_address, self.length, self.data)

    def decode(self, data: bytes) -> None:
        (self.start_address, self.length) = struct.unpack(">2H", data)

        self.data = data[4:]

        assert len(self.data) == self.length


class WriteApplicationPageResponse(ILCResponse):
    """ILC response to new page written with WRITE_APPLICATION_PAGE
    function."""

    function_code = ILCFunction.WRITE_APPLICATION_PAGE


class WriteVerifyApplicationRequest(ILCRequest):
    """Request application verification from the ILC."""

    function_code = ILCFunction.WRITE_VERIFY_APPLICATION


class WriteVerifyApplicationResponse(ModbusPDU):
    """Data with application verification received from ILC."""

    function_code = ILCFunction.WRITE_VERIFY_APPLICATION
    rtu_frame_size = 2

    def __init__(self, dev_id: int = 255, status: int = 0):
        super().__init__(dev_id=dev_id)

        self.status = status

    def encode(self) -> bytes:
        return struct.pack(">H", self.status)

    def decode(self, data: bytes) -> None:
        self.status = struct.unpack(">H", data)[0]


async def flash(
    client: ModbusBaseClient,
    dev_id: int,
    intel_hex_file: IntelHex,
    page_callback: None | Callable[[int], None] = None,
) -> int:
    """Flash ILC. Operates at the following steps:
    1. Change ILC into standby mode.
    2. Change ILC into firmware update mode.
    3. Clear ILC faults.
    4. Erase ILC application.
    5. Write ILC application pages.
    6. Write ILC application statistics.
    7. Verify application.
    8. Change ILC into standby mode.
    9. Change ILC into disabled mode.

    Parameters
    ----------
    client : `ModbusBaseClient`
        Async Modbus client to ILC bus.
    dev_id: `int`
        ILC device address.
    intel_hex_file : `IntelHex`
        IntelHex class with data to load.
    page_callback : `Callable[[int], None]`, optional
        Optional callback. Called after a page is sucessfully loaded into.
        Passes last written address.

    Returns
    -------
    verify : `int`
        Returned verification status.
    """
    status = await client.execute(ILCMode(dev_id=dev_id))

    for attempts in range(4):
        if status.isError():
            raise RuntimeError(f"Cannot query ILC {dev_id} mode: {status}.")

        new_mode = 0xFFFF

        if status.mode == ILCMode.BOOTLOADER:
            break
        elif status.mode == ILCMode.ENABLED:
            new_mode = ILCMode.DISABLED
        elif status.mode == ILCMode.DISABLED:
            new_mode = ILCMode.STANDBY
        elif status.mode == ILCMode.STANDBY:
            new_mode = ILCMode.BOOTLOADER
        elif status.mode == ILCMode.FAULT:
            new_mode = ILCMode.CLEAR_FAULTS
        else:
            raise RuntimeError(
                f"ILC is in {status.mode} mode during transition to bootloade"
                "mode, for which transition isn't defined."
            )

        status = await client.execute(ILCMode(dev_id=dev_id, new_mode=new_mode))

    if status.isError():
        raise RuntimeError(f"ILC {dev_id} in error while transitioning to bootloader mode: {status}.")

    if status.mode != ILCMode.BOOTLOADER:
        raise RuntimeError(f"ILC {dev_id} transitioned to {status.mode} instead to BOOTLOADER (3).")

    erase = await client.execute(EraseApplication(dev_id=dev_id))
    if erase.isError():
        raise RuntimeError(f"Cannot erase ILC {dev_id}: {erase}.")

    intel_hex_file.padding = 0xFF

    # use only 0x0000 - 0xFFFF segments; hexfiles usually contains some 00 well
    # over 0xFFFF, we will ignore those
    segments = [s for s in intel_hex_file.segments() if s[1] < 0xFFFF]
    start_address = segments[0][0]
    end_address = segments[-1][1]

    mem_address = start_address

    # We are flashing 256 bytes chunks, but as every fourth byte is not
    # written, only 256 - (256 / 4) bytes are actually transferred
    APPLICATION_PAGE_LENGTH = 192

    crc = CRC()

    while mem_address < end_address:
        data_start = max(segments[0][0], mem_address)
        length = 256

        data = []

        for i in range(256):
            data.append(intel_hex_file[mem_address + i])

        for i in range(3, 257, 4):
            data[i] = 0x00

        if len(segments) == 1:
            length = min(segments[0][1] - data_start, 256)

        crc.append(data[:length])

        # remove every 4th element - that's how hexfile was compiled, as it is
        # storing 3 bytes of opcodes into 4 bytes
        del data[3::4]

        page = await client.execute(
            WriteApplicationPageRequest(
                dev_id=dev_id, start_address=mem_address, length=APPLICATION_PAGE_LENGTH, data=bytes(data)
            )
        )
        if page.isError():
            raise RuntimeError(
                f"Cannot write page starting with address {mem_address} to ILC {dev_id}: {page}."
            )
        mem_address += 256

        # handle segments..
        if mem_address > segments[0][1]:
            del segments[0]
            if len(segments) and (mem_address) + 0xFF < segments[0][0]:
                raise RuntimeError(
                    f"Big firmware chunk is empty between address {mem_address} and {segments[0][0]}, "
                    "aborting writing the file."
                )

    stat = await client.execute(
        WriteApplicationStatesRequest(
            dev_id=dev_id,
            data_crc=crc.crc,
            start_address=start_address,
            data_length=end_address - start_address,
        )
    )
    if stat.isError():
        raise RuntimeError(f"Cannot write end statistics to ILC {dev_id}: {stat}.")

    verify = await client.execute(WriteVerifyApplicationRequest(dev_id=dev_id))
    if verify.isError():
        raise RuntimeError(f"Cannot verify ILC {dev_id} write: {verify}.")

    status = await client.execute(ILCMode(dev_id=dev_id, new_mode=ILCMode.STANDBY))
    if status.isError():
        raise RuntimeError(
            f"Cannot transition ILC {dev_id} to standby after verifying the flashed code: {status}."
        )

    status = await client.execute(ILCMode(dev_id=dev_id, new_mode=ILCMode.DISABLED))
    if status.isError():
        raise RuntimeError(
            f"Cannot transition ILC {dev_id} to disabled mode after verifying the flashed code: {status}."
        )

    return verify.status
