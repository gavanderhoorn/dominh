
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


def cmt_numreg(self, idx, comment):
    """Update the comment on numerical register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    self._comset('NUMREG', idx, comment=comment)


def cmt_posreg(self, idx, comment):
    """Update the comment on position register at 'idx'.

    :param idx: Numeric ID of register
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    self._comset('POSREG', idx, comment=comment)


def cmt_din(self, idx, comment):
    """Update the comment on 'DIN[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    self._comset('DIN', idx, comment=comment)


def cmt_dout(self, idx, comment):
    """Update the comment on 'DOUT[idx]'.

    :param idx: Numeric ID of port
    :type idx: int
    :param comment: Comment to set
    :type comment: str
    """
    self._comset('DOUT', idx, comment=comment)
