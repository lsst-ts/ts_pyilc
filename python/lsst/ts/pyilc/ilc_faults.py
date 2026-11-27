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

__all__ = ["ILCFaults"]


class ILCFaults:
    UNIQUE_ID = 0x0001
    APPLICATION_TYPE = 0x0002
    NO_APPLICATION = 0x0004
    APPLICATION_CRC = 0x0008
    NO_TEDS = 0x0010
    TEDS_1 = 0x0020
    TEDS_2 = 0x0040
    # 0x0080 is reserved
    WATCHDOG_RESET = 0x0100
    BROWN_OUT = 0x0200
    EVENT_TRAP = 0x0400
    MOTOR_DRIVER = 0x0800
    SSR_POWER = 0x1000
    AUX_POWER = 0x2000
    SMC_POWER = 0x4000
    # 0x8000 is reserved

    def __init__(self, failures: int):
        self.failures = failures

    def to_strings(self) -> Iterator[str]:
        str_failures = [
            "Unique ID CRC",
            "Application type & Network type Node Match",
            "ILC Application",
            "Application CRC",
            "TEDs",
            "TEDS 1",
            "TEDS 2",
            "Reserved (0x0080)",
            "Watchdog Reset",
            "Brown Out",
            "Event Trap",
            "Motor Driver",
            "SSR Power",
            "Auxiliar Power",
            "SMC Power",
            "Reserved (0x8000)",
        ]

        for i, name in enumerate(str_failures):
            if self.failures & (1 << i):
                yield name

    def __str__(self) -> str:
        return ", ".join(self.to_strings())
