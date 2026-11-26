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

import struct

from pymodbus.framer import FramerRTU
from pymodbus.pdu import ModbusPDU
from pymodbus.utilities import hexlify_packets

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCRequest, ILCResponse, pdu_stringify

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

    def x_encode(self) -> bytes:
        return struct.pack(
            ">4H", self.data_crc, self.start_address, self.data_length, self.compute_parameters_CRC()
        )

    def x_decode(self, data: bytes) -> None:
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

    start_address: int = 0
    length: int = 0
    data: bytes = b""

    def __init__(
        self, dev_id: int = DEFAULT_ILC_ADDRESS, start_address: int = 0, length: int = 0, data: bytes = b""
    ):
        super().__init__(dev_id=dev_id)
        self.start_address = start_address
        self.length = length
        self.data = data

    def x_encode(self) -> bytes:
        return struct.pack(f">HH{self.length}s", self.start_address, self.length, self.data)

    def x_decode(self, data: bytes) -> None:
        (self.start_address, self.length) = struct.unpack(">2H", data[:4])
        self.data = data[4:]

        assert len(self.data) == self.length

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        assert len(data) > 7, "Write application page request must contain len bytes at position 3."
        return struct.unpack(">H", data[4:5])[0] + 8


class WriteApplicationPageResponse(ILCResponse):
    """ILC response to new page written with WRITE_APPLICATION_PAGE
    function."""

    function_code = ILCFunction.WRITE_APPLICATION_PAGE


class WriteVerifyApplicationRequest(ILCRequest):
    """Request application verification from the ILC."""

    function_code = ILCFunction.WRITE_VERIFY_APPLICATION


@pdu_stringify("status")
class WriteVerifyApplicationResponse(ModbusPDU):
    """Data with application verification received from ILC."""

    function_code = ILCFunction.WRITE_VERIFY_APPLICATION

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, status: int = 0):
        super().__init__(dev_id=dev_id)

        self.status = status

    def x_encode(self) -> bytes:
        return struct.pack(">H", self.status)

    def x_decode(self, data: bytes) -> None:
        self.status = struct.unpack(">H", data)[0]

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        return 6
