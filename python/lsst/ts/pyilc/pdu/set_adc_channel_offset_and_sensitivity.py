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

__all__ = ["SetADCChannelOffsetAndSensitivityRequest", "SetADCChannelOffsetAndSensitivityResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction, ILCResponse


class SetADCChannelOffsetAndSensitivityRequest(ModbusPDU):
    """Sets the offset and load cell sensitivity values of a sensor attached to
    one of the four ILC analog input channels.

    Parameters
    ----------
    dev_id : `int`
        ILC address.
    sensor_channel : `int`
        Offset channel (load cell). 1-4.
    offset : `float`
        Load cell offset.
    sensitivity : `float`
        Load cell sensitivity.
    """

    function_code = ILCFunction.SET_ADC_CHANNEL_OFFSET
    rtu_frame_size = 9

    def __init__(
        self,
        dev_id: int = DEFAULT_ILC_ADDRESS,
        sensor_channel: int = 0,
        offset: float = m.nan,
        sensitivity: float = m.nan,
    ):
        super().__init__(dev_id=dev_id)

        self.sensor_channel = sensor_channel
        self.offset = offset
        self.sensitivity = sensitivity

    def encode(self) -> bytes:
        return struct.pack(">Bff", self.sensor_channel, self.offset, self.sensitivity)

    def decode(self, data: bytes) -> None:
        (self.sensor_channel, self.offset, self.sensitivity) = struct.unpack(">Bff", data)


class SetADCChannelOffsetAndSensitivityResponse(ILCResponse):
    function_code = ILCFunction.SET_ADC_CHANNEL_OFFSET
