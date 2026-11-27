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

import linecache
import os
import sys
import tokenize
from pathlib import Path
from types import FrameType
from typing import Any, Callable

from .pdu import Context

__all__ = ["Script"]


class Script:
    """
    Creates, compiles and run a script from filename. Script is passed context
    variable, which is the axcual lsst.ts.pyilc.pdu.Context object.

    Parameters
    ----------
    filename: `str`
        Script to execute.
    """

    def __init__(self, filename: str):
        self.filepath = Path(filename)

    async def run(
        self,
        ctx: Context,
        address: int,
        line_callback: Callable[[str, int, str], bool] = lambda filename, lineno, line: True,
    ) -> None:
        """
        Run script from a file. Throws compile errors (mainly SyntaxError) if
        the code cannot be executed.

        Parameters
        ----------
        ctx: `Context`
            Context to run in. Contains execute function to execute *Requests
            and returning responses. Passed to the script.
        address: `int`
            Default ILC address. Passed to the script.
        line_callback: Callable[[str, int, str], bool]`, optional
            Callback after every executed line. Can be used to print tracking
            etc. If callback returns False, execution will be stopped.
        """
        stat = self.filepath.stat()

        filename = str(self.filepath.resolve())

        with tokenize.open(self.filepath) as f:
            lines = f.readlines()

        linecache.cache[filename] = (stat.st_size, stat.st_mtime, lines, os.path.abspath(self.filepath))

        # wrap code in async coroutine, so it can be awaited
        source_code = "async def _coro() -> None:\n    " + "    ".join(lines)

        byte_code = compile(source_code, filename, "exec")

        def trace_lines(
            frame: FrameType, event: str, arg: Any
        ) -> Callable[[FrameType, str, Any], Any] | None:
            if event == "line" and frame.f_code.co_filename == filename:
                lineno = frame.f_lineno - 1

                # call callback only on non-wrapped lines
                if lineno >= 0:
                    shall_continue = line_callback(
                        filename, lineno, linecache.getline(filename, lineno).rstrip()
                    )
                    if not (shall_continue):
                        return None
            return trace_lines

        sys.settrace(trace_lines)
        try:
            namespace: dict[str, Any] = {}
            exec(byte_code, {"context": ctx, "address": address}, namespace)

            await namespace["_coro"]()
        finally:
            # Remove any settrace
            sys.settrace(None)
