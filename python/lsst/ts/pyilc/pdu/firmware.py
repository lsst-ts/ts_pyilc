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

from .change_ilc_mode import ChangeILCMode, ILCMode
from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest, ILCResponse

__all__ = ["flash"]

import struct
from collections.abc import Callable

from intelhex import IntelHex
from pymodbus.client import ModbusBaseClient
from pymodbus.framer import FramerRTU
from pymodbus.pdu import ModbusPDU
from pymodbus.utilities import hexlify_packets

"""
This module handles communication during ILC firmware update. Beware this
isn't well documented in the available documentation - the code actually
provides the documentation (see flash function). Based on C++ code, which was
based on LabVIEW code, and reverse engineering of the ILC bootloader.
"""


class CRC:
    """
    Streaming Modbus 16-but CRC calculations. Allows continuous update as new
    data are available. Does not swap CRC bytes at the end for correct endian
    order - but works with big ending (>H for struct.pack) encoding.

    Parameters
    ----------
    data : `bytes`, optional
        Starting byte sequence.

    Attributes
    ----------
    crc : `int`
        Calculated CRC.
    """

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

    def __init__(
        self,
        dev_id: int = DEFAULT_ILC_ADDRESS,
        data_crc: int = 0,
        start_address: int = 0,
        data_length: int = 0,
    ):
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
    """Response to APLICATION_STATES request."""

    function_code = ILCFunction.WRITE_APPLICATION_STATES


class EraseApplication(ILCRequest):
    """Erases ILC applcation. Must be called before a new application can be
    flashed."""

    function_code = ILCFunction.ERASE_APPLICATION


class WriteApplicationPageRequest(ModbusPDU):
    """Write page of the newly flashed firmware."""

    function_code = ILCFunction.WRITE_APPLICATION_PAGE
    rtu_byte_count_pos = 5

    length: int = 0
    data: bytes = b""

    def __init__(
        self, dev_id: int = DEFAULT_ILC_ADDRESS, start_address: int = 0, length: int = 0, data: bytes = b""
    ):
        super().__init__(dev_id=dev_id)
        self.start_address = start_address
        self.length = length
        self.data = data

    def encode(self) -> bytes:
        return struct.pack(f">HH{self.length}s", self.start_address, self.length, self.data)

    def decode(self, data: bytes) -> None:
        (self.start_address, self.length) = struct.unpack(">2H", data[:4])
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

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, status: int = 0):
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
    callback: None | Callable[[int, str], None] = None,
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
    client : `ModbusBaseClient`
        Async Modbus client to ILC bus.
    dev_id: `int`
        ILC device address.
    intel_hex_file : `IntelHex`
        IntelHex class with data to load.
    callback : `Callable[[int, str], None]`, optional
        Optional callback. Called after an operation (ILC communication) is
        performed. The int argument is a number 0-1000, steps progressed.  The
        string is a string describing current phase of the operation progress.

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

    async def change_state(new_mode: int) -> None:
        status = await client.execute(False, ChangeILCMode(dev_id=dev_id))
        if status.isError():
            raise RuntimeError(f"ILC {dev_id} in error while transitioning to bootloader mode: {status}.")

        if status.isError():
            raise RuntimeError(f"Cannot query ILC {dev_id} mode: {status}.")

        for attempts in range(4):
            nonlocal progress_phase
            progress_phase += SIMPLE_STEP
            if callback:
                callback(SIMPLE_STEP, f"configuring ({status.status})")

            new_status = await client.execute(False, ChangeILCMode(dev_id, new_mode, status.mode))
            if new_status.isError():
                raise RuntimeError(
                    f"ILC {dev_id} in error while transitioning to bootloader mode: {new_status}."
                )

            if new_status.mode == new_mode:
                return

            if new_status.mode == status.mode:
                raise RuntimeError(f"Cannot transition ILC {dev_id} to {new_mode}")

            status = new_status

    # 1. Change ILC to bootloader state.
    await change_state(ILCMode.BOOTLOADER)

    progress_phase += SIMPLE_STEP
    if callback:
        callback(SIMPLE_STEP, "erasing app")

    # 2. Command ILC to erase its firmware - made it available for writing.
    erase = await client.execute(False, EraseApplication(dev_id=dev_id))
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
    PAGE_PADDED_LENGTH = 256
    APPLICATION_PAGE_LENGTH = PAGE_PADDED_LENGTH - (PAGE_PADDED_LENGTH // 4)

    # CRC is calculated from all data (including padding characters, which
    # aren't send to ILC). From the first send byte to the latest valid byte -
    # see length argument.
    crc = CRC()

    # progress step per byte written
    progress_step = float(end_address - start_address) / (MAX_PROGRESS - progress_phase - (5 * SIMPLE_STEP))

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
        if callback:
            callback(
                int(progress_step * PAGE_PADDED_LENGTH), f"writing {progress_phase // PAGE_PADDED_LENGTH}"
            )

        page = await client.execute(
            False,
            WriteApplicationPageRequest(
                dev_id=dev_id, start_address=mem_address, length=APPLICATION_PAGE_LENGTH, data=bytes(data)
            ),
        )
        if page.isError():
            raise RuntimeError(
                f"Cannot write page starting with address {mem_address} to ILC {dev_id}: {page}."
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

    progress_phase += 5
    if callback:
        callback(5, "confirming")

    # 4. Write application statistics. ILC verifies checksum, and if it
    # matches, it is ready to copy new firmware from staging are into main
    # memory and use it after rebooting.
    stat = await client.execute(
        False,
        WriteApplicationStatesRequest(
            dev_id=dev_id,
            data_crc=crc.crc,
            start_address=start_address,
            data_length=end_address - start_address,
        ),
    )
    if stat.isError():
        raise RuntimeError(f"Cannot write end statistics to ILC {dev_id}: {stat}.")

    progress_phase += 5
    if callback:
        callback(5, "quering status")

    # 5. Ask ILC for verification status. This also copy the firmware from
    # stagging memory buffer into main memory.
    verify = await client.execute(False, WriteVerifyApplicationRequest(dev_id=dev_id))
    if verify.isError():
        raise RuntimeError(f"Cannot verify ILC {dev_id} write: {verify}.")

    # 6. Transition ILC to DISABLED mode.
    await change_state(ILCMode.DISABLED)

    if callback:
        callback(MAX_PROGRESS, "done")

    return verify.status
