# Copyright (c) 2021, G.A. vd. Hoorn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# author: G.A. vd. Hoorn


from enum import IntEnum
import typing as t

from .connection import Connection
from .helpers import exec_karel_prg


class CommentFuncCode(IntEnum):
    NUMREG = 1
    POSREG = 3
    UALARM = 4
    RDI = 6
    RDO = 7
    DIN = 8
    DOUT = 9
    GIN = 10
    GOUT = 11
    AIN = 12
    AOUT = 13
    STRREG = 14
    FLG = 19


class ValueFuncCode(IntEnum):
    NUMREG = 2
    UALARM = 5  # actually sets 'severity'
    STRREG = 15


def comset(
    conx: Connection,
    fc: int,
    idx: int,
    val: t.Optional[t.Union[int, float, str]] = None,
    comment: str = '',
) -> None:
    """Low-level wrapper around the 'karel/ComSet' program.

    This method uses the COMSET Karel program on the controller, which is
    normally used by the 'Comment Tool' (accessible via the controller's
    web server).

    Valid values for 'fc' should be taken from CommentFuncCode when updating a
    comment, or from ValueFuncCode when writing to a register.

    In general, prefer to use the wrappers comset_val and comset_cmt instead of
    this low-level function.

    Note: if both 'val' and 'comment' are set, only the comment will be
    updated on the controller.

    :param fc: Type name of commentable
    :type fc: str
    :param idx: Numeric ID of register/alarm/IO element
    :type idx: int
    :param val: Value to write to register
    :type val: int/float/str
    :param comment: Comment to set on commentable
    :type comment: str
    """
    if not val and not comment:
        raise ValueError("Need either val or comment")

    if val:
        real_flag = 1 if type(val) == float else -1
        params = {'sValue': val, 'sIndx': idx, 'sRealFlag': real_flag, 'sFc': fc}

    if comment:
        params = {'sComment': comment, 'sIndx': idx, 'sFc': fc}

    # make sure to request 'return_raw', as 'ComSet' does not return JSON
    # TODO: check return value
    exec_karel_prg(conx, prg_name='ComSet', params=params, return_raw=True)


def comset_val(
    conx: Connection, fc: ValueFuncCode, idx: int, val: t.Union[int, float, str]
) -> None:
    """Update the value of the element at 'idx'.

    This method uses the COMSET Karel program on the controller, which is
    normally used by the 'Comment Tool' (accessible via the controller's
    web server).

    :param fc: function code (ie: the ComSet 'sFc' value)
    :type fc: ValueFuncCode
    :param idx: Numeric ID of NumReg/StrReg/UAlarm
    :type idx: int
    :param val: Value to write to register
    :type val: int/float/str
    """
    comset(conx, fc.value, idx, val=val)


def comset_cmt(conx: Connection, fc: CommentFuncCode, idx: int, comment: str) -> None:
    """Update the comment of the element at 'idx'.

    This method uses the COMSET Karel program on the controller, which is
    normally used by the 'Comment Tool' (accessible via the controller's
    web server).

    :param fc: function code (ie: the ComSet 'sFc' value)
    :type fc: CommentFuncCode
    :param idx: Numeric ID of the element (fi: register or IO port index)
    :type idx: int
    :param comment: Comment to set on element
    :type comment: int/float/str
    """
    comset(conx, fc.value, idx, comment=comment)
