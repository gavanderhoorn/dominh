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


from .connection import Connection
from .exceptions import DominhException

# TODO(gavanderhoorn): refactor frames._match_position
from .frames import _match_position
from .helpers import exec_kcl
from .types import Config_t, Plst_Grp_t, Position_t
from .utils import format_sysvar
from .variables import get_scalar_var


def was_jogged(conx: Connection, group: int = 1) -> bool:
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    ret = get_scalar_var(conx, name=f'$MOR_GRP[{group}].$JOGGED')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret.lower() == 'true'


def get_robot_id(conx: Connection, group: int = 1) -> str:
    ret = get_scalar_var(conx, name=f'$SCR_GRP[{group}].$ROBOT_ID')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_robot_model(conx: Connection, group: int = 1) -> str:
    ret = get_scalar_var(conx, name=f'$SCR_GRP[{group}].$ROBOT_MODEL')
    if 'bad variable' in ret.lower():
        raise DominhException(f"Could not read sysvar: '{ret}'")
    return ret


def get_payload(conx: Connection, idx: int, grp: int = 1) -> Plst_Grp_t:
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
    if grp < 1 or grp > 5:
        raise ValueError(f"Group ID must be between 1 and 5 (got: {grp})")
    if idx < 1 or idx > 10:
        raise ValueError(f"Payload ID must be between 1 and 10 (got: {idx})")

    # TODO: retrieve struct in one read and parse result instead
    base_vname = f'plst_grp{grp}[{idx}]'
    cmt = get_scalar_var(conx, format_sysvar([base_vname, 'comment']))
    return Plst_Grp_t(
        comment=None if cmt == 'Uninitialized' else cmt,
        payload=float(get_scalar_var(conx, format_sysvar([base_vname, 'payload']))),
        payload_x=float(get_scalar_var(conx, format_sysvar([base_vname, 'payload_x']))),
        payload_y=float(get_scalar_var(conx, format_sysvar([base_vname, 'payload_y']))),
        payload_z=float(get_scalar_var(conx, format_sysvar([base_vname, 'payload_z']))),
        payload_ix=float(
            get_scalar_var(conx, format_sysvar([base_vname, 'payload_ix']))
        ),
        payload_iy=float(
            get_scalar_var(conx, format_sysvar([base_vname, 'payload_iy']))
        ),
        payload_iz=float(
            get_scalar_var(conx, format_sysvar([base_vname, 'payload_iz']))
        ),
    )


def get_current_pose(
    conx: Connection, group: int = 1, restore_grp: bool = False
) -> Position_t:
    """Return the position of the TCP relative to the current user frame.

    x, y, and z are in millimeters.
    w, p, and r are in degrees.

    NOTE: this method can be slow if 'restore_grp' is True, as in that case
    multiple KCL commands have to be used.

    :param group: The motion group to retrieve the payload for
    :type group: int
    :param restore_grp: Whether or not the currently default KCL group should
    be restored after retrieving the pose of group 'group'
    :type restore_grp: bool
    :returns: The current Cartesian pose of the motion group with id 'group'
    :rtype: Position_t
    """
    # user could request us to restore the current 'default group'. This is
    # only really important if other KCL commands which are group-specific will
    # be used in the future.
    saved_grp = None
    if restore_grp:
        resp = exec_kcl(conx, cmd='show group', wait_for_response=True)
        if "Default group number" not in resp:
            raise DominhException("Unexpected response for 'show group'")
        # TODO(gavanderhoorn): could've used a regex
        resp = resp.strip()
        saved_grp = int(resp[resp.index('=') + 1 :])

    # select grp first, then execute command
    cmds = [f'set group {group}', 'show curpos']
    # see if we need to restore the default KCL group
    if saved_grp:
        cmds.append(f'set group {saved_grp}')

    # run the cmds
    # TODO(gavanderhoorn): add proper support for "multi-line" KCL cmds
    resp = exec_kcl(conx, cmd="\n".join(cmds), wait_for_response=True)

    # user could have specified an invalid group
    if "Group number is not in valid range" in resp:
        raise DominhException(f"No such group on controller: {group}")

    # try to match returned position
    match = _match_position(resp.strip())
    if not match:
        raise DominhException("Could not match value returned by 'show curpos'")

    # some nasty fiddling
    # TODO: this won't work for non-6-axis systems
    f = match[2] == 'F'  # N
    u = match[3] == 'U'  # D
    t = match[4] == 'T'  # B
    turn_nos = list(map(int, match[5:8]))
    xyzwpr = list(map(float, match[8:14]))
    curr_pose = Position_t(Config_t(f, u, t, *turn_nos), *xyzwpr)

    # done
    return curr_pose
