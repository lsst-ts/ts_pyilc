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

__all__ = ["ThermalDemandRequest", "ThermalDemandResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction


class ThermalDemandRequest(ModbusPDU):
    """Sets thermal (FCU) heater and fan demand.

    Parameters
    ----------
    dev_id : `int`
        ILC address.
    heater_pwm : `int`
        Heater PWM demand.
    fan_pwm : `int`
        Fan PWM demand.
    """

    function_code = ILCFunction.TS_DEMAND
    rtu_frame_size = 2

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS, heater_pwm: int = 0, fan_pwm: int = 0):
        super().__init__(dev_id=dev_id)

        self.heater_pwm = heater_pwm
        self.fan_pwm = fan_pwm

    def encode(self) -> bytes:
        return struct.pack(">BB", self.heater_pwm, self.fan_pwm)

    def decode(self, data: bytes) -> None:
        (self.heater, self.fan_pwm) = struct.unpack(">BB", data)


class ThermalDemandResponse(ModbusPDU):
    function_code = ILCFunction.TS_DEMAND
    rtu_frame_size = 10

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__()

        self.ilc_fault: bool = False
        self.heater_disabled: bool = False
        self.breaker_1: bool = False
        self.breaker_2: bool = False

        self.communication_counter: int = 0

        self.differential_temperature: float = m.nan
        self.fan_rpm: int = 0
        self.absolute_temperature: float = m.nan

    def encode(self) -> bytes:
        status = (
            (self.ilc_fault)
            | (self.heater_disabled << 1)
            | (self.breaker_1 << 2)
            | (self.breaker_2 << 3)
            | ((self.communication_counter << 4) & 0xF0)
        )
        return struct.pack(
            ">BfBf", status, self.differential_temperature, self.fan_rpm, self.absolute_temperature
        )

    def decode(self, data: bytes) -> None:
        (status, self.differential_temperature, self.fan_rpm, self.absolute_temperature) = struct.unpack(
            ">BfBf", data
        )

        self.ilc_fault = bool(status & 0x01)
        self.heater_disabled = bool(status & 0x02)
        self.breaker_1 = bool(status & 0x03)
        self.breaker_2 = bool(status & 0x04)

        self.communication_counter = (status >> 4) & 0x0F
