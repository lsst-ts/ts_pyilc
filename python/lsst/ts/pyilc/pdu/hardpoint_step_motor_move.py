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

__all__ = ["HardpointStepMotorMoveRequest", "HardpointStepMotorMoveResponse"]

import math as m
import struct

from pymodbus.pdu import ModbusPDU

from .utils import ILCFunction


class HardpointStepMotorMoveRequest(ModbusPDU):
    """Request Hardpoint Step Motor to move."""

    function_code = ILCFunction.HP_STEP_MOTOR_MOVE
    rtu_frame_size = 1

    def __init__(self, dev_id: int = 255, step_motor_command: int = 0):
        super().__init__(dev_id=dev_id)
        self.step_motor_command = step_motor_command

    def encode(self) -> bytes:
        return struct.pack(">B", self.step_motor_command)

    def decode(self, data: bytes) -> None:
        self.step_motor_command = int.from_bytes(data, byteorder="big")


class HardpointStepMotorMoveResponse(ModbusPDU):
    """Report Hardpoint Forces and Encoder Position."""

    function_code = ILCFunction.HP_STEP_MOTOR_MOVE
    rtu_frame_size = 8

    def __init__(self, dev_id: int = 255):
        super().__init__(dev_id=dev_id)

        self.ssi_encoder_position: int = 0
        self.load_cell_force: float = m.nan

    def encode(self) -> bytes:
        return struct.pack(">if", self.ssi_encoder_position, self.load_cell_force)

    def decode(self, data: bytes) -> None:
        (self.ssi_encoder_position, self.load_cell_force) = struct.unpack(">if", data)
