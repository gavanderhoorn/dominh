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


import re
import typing as t

from .exceptions import DominhException
from .helpers import get_var_raw
from .variables import get_scalar_var
from .types import Config_t
from .types import Position_t


def _match_position(text: str) -> t.Tuple[str, ...]:
    """Try to extract elements of a FANUC POSITION from 'text'.

    :param text: Textual representation of a POSITION variable.
    :type text: str
    :returns: A tuple with all the matched fields.
    :rtype: tuple(str, str, ..)
    """
    # use Jay's regex (thanks!)
    matches = re.findall(
        r"(?m)"
        r"("
        r"  Group: (\d)   Config: (F|N) (U|D) (T|B), (\d), (\d), (\d)\r?\n"
        r"  X:\s*(-?\d*.\d+|[*]+)   Y:\s+(-?\d*.\d+|[*]+)   Z:\s+(-?\d*.\d+|[*]+)\r?\n"  # noqa
        r"  W:\s*(-?\d*.\d+|[*]+)   P:\s*(-?\d*.\d+|[*]+)   R:\s*(-?\d*.\d+|[*]+)"  # noqa
        r"|"
        r"  Group: (\d)\r?\n"
        r"  (J1) =\s*(-?\d*.\d+|[*]+) deg   J2 =\s*(-?\d*.\d+|[*]+) deg   J3 =\s*(-?\d*.\d+|[*]+) deg \r?\n"  # noqa
        r"  J4 =\s*(-?\d*.\d+|[*]+) deg   J5 =\s*(-?\d*.\d+|[*]+) deg   J6 =\s*(-?\d*.\d+|[*]+) deg"  # noqa
        r")",
        text,
    )
    return matches[0] if matches else None


def _get_frame_var(conx, varname: str) -> Position_t:
    """Retrieve the POSITION variable 'varname'.

    :param varname: Name of the variable to retrieve.
    :type varname: str
    :returns: Position_t instance populated with values retrieved from the
    'varname' variable.
    :rtype: Position_t
    """
    # NOTE: assuming here that get_var_raw(..) returns something we can
    # actually parse
    ret = get_var_raw(conx, varname)
    # remove the first line as it's empty
    match = _match_position(ret.replace('\r\n', '', 1))

    if not match:
        raise DominhException(f"Could not match value returned for '{varname}'")

    # some nasty fiddling
    # TODO: this won't work for non-6-axis systems
    f = match[2] == 'F'  # N
    u = match[3] == 'U'  # D
    t = match[4] == 'T'  # B
    turn_nos = list(map(int, match[5:8]))
    xyzwpr = list(map(float, match[8:14]))
    return Position_t(Config_t(f, u, t, *turn_nos), *xyzwpr)


def _get_frame_comment(conx, frame_type: int, group: int, idx: int) -> str:
    """Return the comment for the jog/tool/user frame 'idx'.

    :param frame_type: Type of frame the comment is associated with (
    jog:2, tool:1, user:3).
    :type frame_type: int
    :param group: Numeric ID of the motion group the frame is associated
    with.
    :type group: int
    :param idx: Numeric ID of the frame.
    :type idx: int
    :returns: The comment of the frame in group 'group', with ID 'idx'
    :rtype: str
    """
    varname = f'[TPFDEF]SETUP_DATA[{group},{frame_type},{idx}].$COMMENT'
    return get_scalar_var(conx, name=varname)


def get_jogframe(
    conx, idx: int, group: int = 1, include_comment: bool = False
) -> t.Tuple[Position_t, t.Optional[str]]:
    """Return the jog frame at index 'idx'.

    :param idx: Numeric ID of the jog frame.
    :type idx: int
    :param group: Numeric ID of the motion group the jog frame is
    associated with.
    :type group: int
    :returns: A tuple containing the user frame and associated comment (if
    requested)
    :rtype: tuple(Position_t, str)
    """
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    if idx < 1 or idx > 5:
        raise ValueError(
            f"Requested jog frame idx invalid (must be between 1 and 5, got: {idx})"
        )
    varname = f'[TPFDEF]JOGFRAMES[{group},{idx}]'
    frame = _get_frame_var(conx, varname)
    cmt = None
    if include_comment:
        JOGFRAME = 2
        cmt = _get_frame_comment(conx, frame_type=JOGFRAME, group=group, idx=idx)
    return (frame, cmt)


def get_toolframe(
    conx, idx: int, group: int = 1, include_comment: bool = False
) -> t.Tuple[Position_t, t.Optional[str]]:
    """Return the tool frame at index 'idx'.

    :param idx: Numeric ID of the tool frame.
    :type idx: int
    :param group: Numeric ID of the motion group the tool frame is
    associated with.
    :type group: int
    :returns: A tuple containing the tool frame and associated comment (if
    requested)
    :rtype: tuple(Position_t, str)
    """
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    if idx < 1 or idx > 10:
        raise ValueError(
            "Requested tool frame idx invalid (must be "
            f"between 1 and 10, got: {idx})"
        )
    varname = f'[*SYSTEM*]$MNUTOOL[{group},{idx}]'
    frame = _get_frame_var(conx, varname)
    cmt = None
    if include_comment:
        TOOLFRAME = 1
        cmt = _get_frame_comment(conx, frame_type=TOOLFRAME, group=group, idx=idx)
    return (frame, cmt)


def get_userframe(
    conx, idx: int, group: int = 1, include_comment: bool = False
) -> t.Tuple[Position_t, t.Optional[str]]:
    """Return the user frame at index 'idx'.

    :param idx: Numeric ID of the user frame.
    :type idx: int
    :param group: Numeric ID of the motion group the user frame is
    associated with.
    :type group: int
    :returns: A tuple containing the user frame and associated comment (if
    requested)
    :rtype: tuple(Position_t, str)
    """
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    if idx < 1 or idx > 10:
        raise ValueError(
            "Requested user frame idx invalid (must be "
            f"between 1 and 10, got: {idx})"
        )
    varname = f'[*SYSTEM*]$MNUFRAME[{group},{idx}]'
    frame = _get_frame_var(conx, varname)
    cmt = None
    if include_comment:
        USERFRAME = 3
        cmt = _get_frame_comment(conx, frame_type=USERFRAME, group=group, idx=idx)
    return (frame, cmt)


def get_active_jogframe(conx, group: int = 1) -> int:
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    return int(get_scalar_var(conx, name=f'[TPFDEF]JOGFRAMNUM[{group}]'))


def get_active_toolframe(conx, group: int = 1) -> int:
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    return int(get_scalar_var(conx, name=f'[*SYSTEM*]$MNUTOOLNUM[{group}]'))


def get_active_userframe(conx, group: int = 1) -> int:
    if group < 1 or group > 8:
        raise ValueError(
            f"Requested group id invalid (must be between 1 and 8, got: {group})"
        )
    return int(get_scalar_var(conx, name=f'[*SYSTEM*]$MNUFRAMENUM[{group}]'))
