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

__all__ = ["ILCFunction", "ILCException", "ILCRequest", "ILCResponse", "DEFAULT_ILC_ADDRESS"]

from enum import IntEnum
from typing import Any, Callable

from pymodbus.pdu import ModbusPDU

ELECTROMECHANICAL_BROADCAST_ADDRESS = 248
"""Broadcast address for electromechanical ILCs."""

PNEUMATIC_BROADCAST_ADDRESS = 249
"""Broadcast address for pneumatic ILCs."""

DEFAULT_ILC_ADDRESS = 255
"""Address ILC uses in case TEDS is not connected."""


def pdu_stringify[T](*fields: str, **formatted_fields: str) -> Callable[[type[T]], type[T]]:
    """
    Decorator creating a custom __str__, returning prinout of selected
    attributes.

    Usage
    -----

    @pdu_stringify("name", "my_value")
    class Test:
        def __init__(self):
            self.name = "This is test"
            self.my_value = 32.432

    Parameters
    ----------
    fields: `list[str]`
        List of decorator strings.
    formatted_fields: `dict[str, str]
        Formated fields.
    """

    def decorator(cls: type[T]) -> type[T]:
        def stringify(self: Any) -> str:
            parts: list[str] = []

            # 1. Standard fields (uses repr formatting)
            for field in fields:
                parts.append(f"{field}={getattr(self, field, None)!r}")

            # 2. Custom-formatted fields (uses format(val, spec))
            for field, spec in formatted_fields.items():
                val = getattr(self, field, None)
                formatted_val = "None" if val is None else format(val, spec)
                parts.append(f"{field}={formatted_val}")

            return f"{cls.__name__}({', '.join(parts)})"

        # Attach the method
        setattr(cls, "__str__", stringify)
        return cls

    return decorator


class ILCFunction(IntEnum):
    """Modbus Function Codes for M1M3 ILCs based on LTS-646."""

    # ID, status and mode functions
    REPORT_SERVER_ID = 0x11  # 17
    REPORT_SERVER_STATUS = 0x12  # 18
    CHANGE_ILC_MODE = 0x41  # 65

    # Common commands
    FREEZE_SENSOR_VALUES = 0x44  # 68
    SET_TEMP_ILC_ADDR = 0x48  # 72
    SET_ADC_SCANRATE = 0x50  # 80
    SET_ADC_CHANNEL_OFFSET = 0x51  # 81
    READ_DAC_VALUES = 0x52  # 82
    RESET_SERVER = 0x6B  # 107
    READ_CALIBRATION_DATA = 0x6E  # 110

    READ_MEZZANINE_PRESSURE = 0x77  # 119
    READ_MEZZANINE_ID = 0x78  # 120
    READ_MEZZANINE_STATUS = 0x79  # 121

    # Firmware / memory commands
    WRITE_APPLICATION_STATES = 0x64  # 100
    ERASE_APPLICATION = 0x65  # 101
    WRITE_APPLICATION_PAGE = 0x66  # 102
    WRITE_VERIFY_APPLICATION = 0x67  # 103

    # FA - Pneumatic ILC
    FA_SET_BOOSTER_VALVE_DCA_GAINS = 0x49  # 73
    FA_READ_BOOSTER_VALVE_DCA_GAINS = 0x4A  # 74
    FA_FORCE_DEMAND = 0x4B  # 75
    FA_FORCE_AND_STATUS = 0x4C  # 76

    # HP - Electromechanical (Hardpoint) and M2 ILC
    HP_STEP_MOTOR_MOVE = 0x42  # 66
    HP_FORCE_AND_STATUS = 0x43  # 67

    # HM - Harpoint Monitoring ILC
    HM_READ_MEZZANINE_LVDT = 0x7A  # 122

    # TS - Thermal ILC
    TS_DEMAND = 0x58  # 88
    TS_STATUS = 0x59  # 89
    SET_REHEATER_GAINS = 0x5C
    READ_REHEATER_GAINS = 0x5D

    # M2 - M2 Support System ILC
    READ_MONITOR_SENSORS = 0x54  # 84


@pdu_stringify()
class ILCRequest(ModbusPDU):
    """Generic class providing empty encode function - for parameter-less
    requests."""

    def x_encode(self) -> bytes:
        return b""

    def x_decode(self, data: bytes) -> None:
        return

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        return 4


@pdu_stringify()
class ILCResponse(ModbusPDU):
    """Generic class for processing empty response - for Requests calls when
    response is enough to signal sucessfull completion."""

    def x_encode(self) -> bytes:
        return b""

    def x_decode(self, data: bytes) -> None:
        return

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        return 4


class ILCException(IntEnum):
    """ILC Exceptions codes."""

    ILLEGAL_FUNCTION = 0x01
    ILLEGAL_DATA_VALUE = 0x03
    SERVER_DEVICE_FAULT = 0x04
