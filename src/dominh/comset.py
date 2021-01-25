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


import typing as t

from .helpers import exec_karel_prg


def _get_cmt_fc(cmt: str) -> int:
    return {
        'NUMREG': 1,
        'POSREG': 3,
        'UALARM': 4,
        'RDI': 6,
        'RDO': 7,
        'DIN': 8,
        'DOUT': 9,
        'GIN': 10,
        'GOUT': 11,
        'AIN': 12,
        'AOUT': 13,
        'STRREG': 14,
        'FLG': 19,
    }.get(cmt.upper())


def _get_val_fc(valt: str) -> int:
    return {
        'NUMREG': 2,
        'UALARM': 5,  # actually sets 'severity'
        'STRREG': 15,
    }.get(valt.upper())


def comset(
    conx,
    fc: str,
    idx: int,
    val: t.Optional[t.Union[int, float, str]] = None,
    comment: str = '',
) -> None:
    """Low-level wrapper around the 'karel/ComSet' program.

    This method uses the COMSET Karel program on the controller, which is
    normally used by the 'Comment Tool' (accessible via the controller's
    web server).

    Valid values for 'fc':

    When updating a comment:

        - AIN
        - AOUT
        - DIN
        - DOUT
        - FLG
        - GIN
        - GOUT
        - NUMREG
        - POSREG
        - RDI
        - RDO
        - STRREG
        - UALARM

    When updating a value:

        - NUMREG
        - STRREG
        - UALARM

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
        sfc = _get_val_fc(fc)
        real_flag = 1 if type(val) == float else -1
        params = {'sValue': val, 'sIndx': idx, 'sRealFlag': real_flag, 'sFc': sfc}

    if comment:
        sfc = _get_cmt_fc(fc)
        params = {'sComment': comment, 'sIndx': idx, 'sFc': sfc}

    # make sure to request 'return_raw', as 'ComSet' does not return JSON
    # TODO: check return value
    exec_karel_prg(conx, prg_name='ComSet', params=params, return_raw=True)
