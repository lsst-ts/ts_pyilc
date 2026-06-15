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

from .utils import ILCFunction

__all__ = [
    "WriteApplicationStatesRequest",
    "WriteApplicationStatesResponse",
    "EraseApplication",
    "WriteApplicationPageRequest",
    "WriteApplicationPageResponse",
    "WriteVerifyApplicationRequest",
    "WriteVerifyApplicationResponse",
]

import struct

from pymodbus.framer import FramerRTU
from pymodbus.pdu import ModbusPDU
from pymodbus.utilities import hexlify_packets

from .utils import ILCRequest, ILCResponse


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
        return FramerRTU.compute_CRC(data)

    def encode(self) -> bytes:
        data = struct.pack("<6H", self.data_crc, 0, self.start_address, 0, self.data_length, 0)
        parameter_CRC = FramerRTU.compute_CRC(data)

        return struct.pack("<4H", self.data_crc, self.start_address, self.data_length, parameter_CRC)

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

    def encode(self) -> bytes:
        return struct.pack(f">HH{self.length}B", self.start_address, self.length, self.data)

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

    status: int = 0

    def encode(self) -> bytes:
        return struct.pack(">H", self.status)

    def decode(self, data: bytes) -> None:
        self.status = struct.unpack(">H", data)[0]
