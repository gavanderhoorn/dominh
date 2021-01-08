
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


from . exceptions import DominhException
from . variables import get_scalar_var
from . types import Plst_Grp_t
from . utils import format_sysvar


def was_jogged(conx, group=1):
    if group < 1 or group > 8:
        raise ValueError("Requested group id invalid (must be "
                         f"between 1 and 8, got: {group})")
    ret = get_scalar_var(conx, name=f'$MOR_GRP[{group}].$JOGGED')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret.lower() == 'true'


def get_robot_id(conx, group=1):
    ret = get_scalar_var(conx, name=f'$SCR_GRP[{group}].$ROBOT_ID')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_robot_model(conx, group=1):
    ret = get_scalar_var(conx, name=f'$SCR_GRP[{group}].$ROBOT_MODEL')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_payload(conx, idx, grp=1):
    """Retrieve payload nr 'idx' for group 'grp'.

    NOTE: this method is expensive and slow, as it retrieves the individual
    fields of the payload variable separately, instead of a single struct.

    :param idx: The number of the payload schedule to retrieve
    :type idx: int
    :param grp: The motion group to retrieve the payload for
    :type grp: int
    :returns: A named tuple matching the structure of a PLST_GRP_T. The
    'ICONDISP' field is not included.
    :rtype: plst_grp_t
    """
    if (grp < 1 or grp > 5):
        raise ValueError(f"Group ID must be between 1 and 5 (got: {grp})")
    if (idx < 1 or idx > 10):
        raise ValueError(
            f"Payload ID must be between 1 and 10 (got: {idx})")

    # TODO: retrieve struct in one read and parse result instead
    base_vname = f'plst_grp{grp}[{idx}]'
    cmt = get_scalar_var(conx, format_sysvar([base_vname, 'comment']))
    return Plst_Grp_t(
        comment=None if cmt == 'Uninitialized' else cmt,
        payload=float(get_scalar_var(conx,
                      format_sysvar([base_vname, 'payload']))),
        payload_x=float(get_scalar_var(conx,
                        format_sysvar([base_vname, 'payload_x']))),
        payload_y=float(get_scalar_var(conx,
                        format_sysvar([base_vname, 'payload_y']))),
        payload_z=float(get_scalar_var(conx,
                        format_sysvar([base_vname, 'payload_z']))),
        payload_ix=float(get_scalar_var(conx,
                         format_sysvar([base_vname, 'payload_ix']))),
        payload_iy=float(get_scalar_var(conx,
                         format_sysvar([base_vname, 'payload_iy']))),
        payload_iz=float(get_scalar_var(conx,
                         format_sysvar([base_vname, 'payload_iz']))),
    )
