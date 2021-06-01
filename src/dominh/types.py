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


from dataclasses import dataclass


@dataclass
class Plst_Grp_t:
    comment: str
    payload: float
    payload_x: float
    payload_y: float
    payload_z: float
    payload_ix: float
    payload_iy: float
    payload_iz: float


@dataclass
class Config_t:
    flip: bool
    up: bool
    top: bool
    turn_no1: int
    turn_no2: int
    turn_no3: int

    def __repr__(self):
        f = "F" if self.flip else "N"
        u = "U" if self.up else "D"
        t = "T" if self.top else "B"
        return f"{f} {u} {t}, {self.turn_no1}, {self.turn_no2}, {self.turn_no3}"


@dataclass
class Position_t:
    config: Config_t
    x: float
    y: float
    z: float
    w: float
    p: float
    r: float

    def __repr__(self):
        return (
            f"[{self.x}, {self.y}, {self.z}, {self.w}, {self.p}, {self.r} | "
            f"{self.config}]"
        )


@dataclass
class JointPos_t:
    j1: float
    j2: float
    j3: float
    j4: float
    j5: float
    j6: float
