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

__all__ = [
    "ForceActuatorForceDemandSARequest",
    "ForceActuatorForceDemandSAResponse",
    "ForceActuatorForceDemandDARequest",
    "ForceActuatorForceDemandDAResponse",
]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import DEFAULT_ILC_ADDRESS, ILCFunction


class ForceActuatorForceDemandSARequest(ModbusPDU):
    """Single axis force actuator force demand.

    Parameters
    ----------
    dev_id : `int`
        ILC address.
    slew_flag : `int`
        Force actuator slew flag. 0xFF to activate booster valves.
    force_setpoint : `int`
        Primary axis requested force in mN.
    """

    function_code = ILCFunction.FA_FORCE_DEMAND
    rtu_frame_size = 4

    def __init__(
        self,
        dev_id: int = DEFAULT_ILC_ADDRESS,
        slew_flag: int = 0,
        force_setpoint: int = 0,
    ):
        super().__init__(dev_id=dev_id)

        self.slew_flag = slew_flag
        self.force_setpoint = force_setpoint

    def encode(self) -> bytes:
        return struct.pack(">B", self.slew_flag) + self.force_setpoint.to_bytes(
            3, byteorder="big", signed=True
        )

    def decode(self, data: bytes) -> None:
        self.slew_flag = data[0]
        self.force_setpoint = int.from_bytes(data[1:4], byteorder="big", signed=True)


class ForceActuatorForceDemandSAResponse(ModbusPDU):
    function_code = ILCFunction.FA_FORCE_DEMAND
    rtu_frame_size = 5

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id)

        self.ilc_fault: bool = False
        self.dca_fault: bool = False
        self.communication_counter: int = 0

        self.load_cell_force: float = m.nan

    def encode(self) -> bytes:
        status = (self.ilc_fault) | (self.dca_fault << 1) | ((self.communication_counter << 4) & 0xF0)
        return struct.pack(">Bf", status, self.load_cell_force)

    def decode(self, data: bytes) -> None:
        (status, self.load_cell_force) = struct.unpack(">Bf", data)

        self.ilc_fault = bool(status & 0x01)
        self.dca_fault = bool(status & 0x02)
        self.communication_counter = (status >> 4) & 0x0F


class ForceActuatorForceDemandDARequest(ModbusPDU):
    function_code = ILCFunction.FA_FORCE_DEMAND
    rtu_frame_size = 7

    def __init__(
        self,
        dev_id: int = DEFAULT_ILC_ADDRESS,
        slew_flag: int = 0,
        axial_force_setpoint: int = 0,
        lateral_force_setpoint: int = 0,
    ):
        super().__init__(dev_id=dev_id)

        self.slew_flag = slew_flag
        self.axial_force_setpoint = axial_force_setpoint
        self.lateral_force_setpoint = lateral_force_setpoint

    def encode(self) -> bytes:
        return (
            struct.pack(">B", self.slew_flag)
            + self.axial_force_setpoint.to_bytes(3, byteorder="big", signed=True)
            + self.lateral_force_setpoint.to_bytes(3, byteorder="big", signed=True)
        )

    def decode(self, data: bytes) -> None:
        self.slew_flag = data[0]
        self.axial_force_setpoint = int.from_bytes(data[1:4], byteorder="big", signed=True)
        self.lateral_force_setpoint = int.from_bytes(data[4:7], byteorder="big", signed=True)


class ForceActuatorForceDemandDAResponse(ModbusPDU):
    function_code = ILCFunction.FA_FORCE_DEMAND
    rtu_frame_size = 9

    def __init__(self, dev_id: int = DEFAULT_ILC_ADDRESS):
        super().__init__(dev_id)

        self.ilc_fault: bool = False
        self.dca_fault: bool = False
        self.communication_counter: int = 0

        self.axial_cell_force: float = m.nan
        self.lateral_cell_force: float = m.nan

    def encode(self) -> bytes:
        status = (self.ilc_fault) | (self.dca_fault << 1) | ((self.communication_counter << 4) & 0xF0)
        return struct.pack(">Bff", status, self.axial_cell_force, self.lateral_cell_force)

    def decode(self, data: bytes) -> None:
        (status, self.axial_cell_force, self.lateral_cell_force) = struct.unpack(">Bff", data)

        self.ilc_fault = bool(status & 0x01)
        self.dca_fault = bool(status & 0x02)
        self.communication_counter = (status >> 4) & 0x0F
