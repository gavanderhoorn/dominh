
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


def set_scalar_var(self, varname, val):
    """Update the value of variable 'varname' to 'val'.

    NOTE: 'val' will always be sent as its 'str(..)'-i-fied representation.
    The controller will (attempt to) parse this back into its native data
    type.

    TODO: add basic error checking (none performed right now).

    :param varname: Name of the variable to write to
    :type varname: str
    :param val: Value to write to 'varname'
    :type val: any (must have str() support)
    """
    self._exec_kcl(cmd=f'set var {varname}={val}')


def get_scalar_var(self, varname):
    """Retrieve the value of the variable named 'varname'.

    NOTE: should only be used for scalar variables and individual array
    elements.

    TODO: see whether perhaps SHOW VAR could be used here instead.

    :param varname: Name of the variable to write to
    :type varname: str
    :returns: JSON value for key 'varname'
    :rtype: str (to be parsed by caller)
    """
    ret = self._read_helper(
        helper=HLPR_SCALAR_VAR, params={'_reqvar': varname})
    return ret[varname.upper()]
