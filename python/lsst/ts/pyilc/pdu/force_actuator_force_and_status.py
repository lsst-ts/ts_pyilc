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
    "ForceActuatorForceAndStatusRequest",
    "ForceActuatorForceAndStatusSAResponse",
    "ForceActuatorForceAndStatusDAResponse",
]


from .force_actuator_force_demand import (
    ForceActuatorForceDemandDAResponse,
    ForceActuatorForceDemandSAResponse,
)
from .utils import ILCFunction, ILCRequest


class ForceActuatorForceAndStatusRequest(ILCRequest):
    """Single axis force actuator force demand."""

    function_code = ILCFunction.FA_FORCE_AND_STATUS


class ForceActuatorForceAndStatusSAResponse(ForceActuatorForceDemandSAResponse):
    function_code = ILCFunction.FA_FORCE_AND_STATUS


class ForceActuatorForceAndStatusDAResponse(ForceActuatorForceDemandDAResponse):
    function_code = ILCFunction.FA_FORCE_AND_STATUS
