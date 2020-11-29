#!/usr/bin/env python3

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


"""
Retrieve value of a (system) variable.

Usage: dominh [--no-upload] get [options] <host> <variable>

Options:
  -h --help     Show this screen.

"""

import sys

from docopt import docopt
from requests import exceptions

from dominh import Client, DominhException


def main(argv, skip_upload=False):
    args = docopt(__doc__, argv=argv)

    varname = args['<variable>']

    try:
        c = Client(args['<host>'], skip_helper_upload=skip_upload)
        c.initialise()
        print(c.get_scalar_var(varname))

    except (exceptions.ConnectionError, OSError) as e:
        sys.stderr.write(f"Error trying to connect to the controller: {e}\n")
    except DominhException as e:
        sys.stderr.write(f"Error during read: {e}\n")
