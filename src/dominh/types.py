# Copyright (c) 2020, G.A. vd. Hoorn
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


from collections import namedtuple


Plst_Grp_t = namedtuple(
    'Plst_Grp_t',
    [
        'comment',
        'payload',
        'payload_x',
        'payload_y',
        'payload_z',
        'payload_ix',
        'payload_iy',
        'payload_iz',
    ],
)

Config_t = namedtuple(
    'Config_t',
    [
        'flip',
        'up',
        'top',
        'turn_no1',
        'turn_no2',
        'turn_no3',
    ],
)

Position_t = namedtuple(
    'Position_t',
    [
        'config',
        'x',
        'y',
        'z',
        'w',
        'p',
        'r',
    ],
)

JointPos_t = namedtuple(
    'JointPos_t',
    [
        'j1',
        'j2',
        'j3',
        'j4',
        'j5',
        'j6',
    ],
)
