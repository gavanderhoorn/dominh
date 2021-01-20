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


from .comset import comset


def cmt_numreg(conx, idx, comment):
    """Update the comment on numerical register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset(conx, 'NUMREG', idx, comment=comment)


def cmt_posreg(conx, idx, comment):
    """Update the comment on position register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset(conx, 'POSREG', idx, comment=comment)


def cmt_strreg(conx, idx, comment):
    """Update the comment on string register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset(conx, 'STRREG', idx, comment=comment)


def cmt_din(conx, idx, comment):
    """Update the comment on 'DIN[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset(conx, 'DIN', idx, comment=comment)


def cmt_dout(conx, idx, comment):
    """Update the comment on 'DOUT[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    comset(conx, 'DOUT', idx, comment=comment)
