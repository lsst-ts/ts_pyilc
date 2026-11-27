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

from typing import Iterator

__all__ = ["ILCModes"]


class ILCModes:
    MAJOR_FAULT = 0x0001
    MINOR_FAULT = 0x0002
    # 0x0004 is reserved
    FAULT_OVERRIDE = 0x0008
    CALIBRATION_MAIN = 0x0010  # Electromechanical, Pneumatic or Thermal ILC's only
    CALIBRATION_BACKUP = 0x0020  # Electromechanical, Pneumatic or Thermal ILC's only
    REFERENCE_RESISTOR = 0x0040  # Thermal ILC's only
    RTD = 0x0080  # Thermal ILC's only
    LIMIT_SWITCH_1 = 0x0100  # Electromechanical ILC's only
    LIMIT_SWITCH_2 = 0x0200  # Electromechanical ILC's only
    BREAKER_1_HEATER = 0x0400  # Thermal ILC's only
    BREAKER_2_FAN = 0x0800  # Thermal ILC's only
    MONITOR_INSTRUMENT_ERROR = 0x1000  # Monitoring ILC's only
    MEZZANINE_BOARD = 0x2000  # Pneumatic or Hardpoint Monitoring ILC's only
    MEZZANINE_BOARD_BOOTLOAD_MODE = 0x4000  # Pneumatic or Hardpoint Monitoring ILC's only
    # 0x8000 is reserved

    def __init__(self, modes: int):
        self.modes = modes

    def to_strings(self) -> Iterator[str]:
        str_modes = [
            "Major Fault",
            "Minor Fault",
            "Reserved (0x0008)",
            "Fault override",
            "Main Calibration",
            "Backup Calibration",
            "Reference Resistor",
            "RTD",
            "Limit Switch 1",
            "Limit Switch 2",
            "Breaker 1 Heater",
            "Breaker 2 Fan",
            "Monitor Instrument",
            "Mezzanine Board",
            "Mezzanine Board Bootload Mone",
            "Reserved (0x8000)",
        ]

        for i, name in enumerate(str_modes):
            if self.modes & (1 << i):
                yield name

    def __str__(self) -> str:
        return ", ".join(self.to_strings())
