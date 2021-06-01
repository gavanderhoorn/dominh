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


from .comset import comset_cmt
from .comset import CommentFuncCode


def cmt_numreg(conx, idx: int, comment: str) -> None:
    """Update the comment on numerical register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.NUMREG, idx, comment=comment)


def cmt_posreg(conx, idx: int, comment: str) -> None:
    """Update the comment on position register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.POSREG, idx, comment=comment)


def cmt_rdi(conx, idx: int, comment: str) -> None:
    """Update the comment on 'RDI[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.RDI, idx, comment=comment)


def cmt_rdo(conx, idx: int, comment: str) -> None:
    """Update the comment on 'RDO[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.RDO, idx, comment=comment)


def cmt_din(conx, idx: int, comment: str) -> None:
    """Update the comment on 'DIN[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.DIN, idx, comment=comment)


def cmt_dout(conx, idx: int, comment: str) -> None:
    """Update the comment on 'DOUT[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.DOUT, idx, comment=comment)


def cmt_flag(conx, idx: int, comment: str) -> None:
    """Update the comment on 'FLG[idx]'.

    :param idx: Numeric ID of the flag
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.FLG, idx, comment=comment)


def cmt_gin(conx, idx: int, comment: str) -> None:
    """Update the comment on 'GIN[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.GIN, idx, comment=comment)


def cmt_gout(conx, idx: int, comment: str) -> None:
    """Update the comment on 'GOUT[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.GOUT, idx, comment=comment)


def cmt_ain(conx, idx: int, comment: str) -> None:
    """Update the comment on 'AIN[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.AIN, idx, comment=comment)


def cmt_aout(conx, idx: int, comment: str) -> None:
    """Update the comment on 'AOUT[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.AOUT, idx, comment=comment)


def cmt_strreg(conx, idx: int, comment: str) -> None:
    """Update the comment on string register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.STRREG, idx, comment=comment)


def cmt_ualarm(conx, idx: int, comment: str) -> None:
    """Update the comment on 'UALARM[idx]'.

    :param idx: Numeric ID of the user alarm
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.UALARM, idx, comment=comment)


def cmt_flg(conx, idx: int, comment: str) -> None:
    """Update the comment on 'FLG[idx]'.

    :param idx: Numeric ID of flag
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset_cmt(conx, CommentFuncCode.FLG, idx, comment=comment)
