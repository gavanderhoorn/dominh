
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


from . constants import HLPR_SCALAR_VAR
from . exceptions import DominhException
from . helpers import exec_kcl
from . helpers import read_helper


def set_scalar_var(conx, name, val):
    """Update the value of variable 'name' to 'val'.

    NOTE: 'val' will always be sent as its 'str(..)'-i-fied representation.
    The controller will (attempt to) parse this back into its native data
    type.

    TODO: add basic error checking (none performed right now).

    :param name: Name of the variable to write to
    :type name: str
    :param val: Value to write to 'name'
    :type val: any (must have str() support)
    """
    exec_kcl(conx, cmd=f'set var {name}={val}')


def get_scalar_var(conx, name):
    """Retrieve the value of the variable named 'name'.

    NOTE: should only be used for scalar variables and individual array
    elements.

    TODO: see whether perhaps SHOW VAR could be used here instead.

    :param name: Name of the variable to write to
    :type name: str
    :returns: JSON value for key 'name'
    :rtype: str (to be parsed by caller)
    """
    ret = read_helper(conx, helper=HLPR_SCALAR_VAR, params={'_reqvar': name})
    ret = ret[name.upper()]
    if 'bad variable' in ret.lower():
        raise DominhException(f"Error reading variable: '{ret}'")
    if 'unknown variable' in ret.lower():
        raise DominhException(ret)
    return ret
