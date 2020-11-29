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
Write to a controller IO port.

Usage: dominh [--no-upload] write [options] <host> <port_type> <index> <val>

Options:
  -h --help     Show this screen.
  --check       Verify the write was successful. Exit status
                reflects success of operation.

"""

import sys

from docopt import docopt
from requests import exceptions

from dominh import Client, DominhException


def main(argv, skip_upload=False):
    args = docopt(__doc__, argv=argv)

    port_type = args['<port_type>']
    index = int(args['<index>'])
    val = int(args['<val>'])

    check = args['--check']

    try:
        c = Client(args['<host>'], skip_helper_upload=skip_upload)
        c.initialise()
        val = c.io_write(port_type, index, val, check=check)

    except (exceptions.ConnectionError, OSError) as e:
        sys.stderr.write(f"Error trying to connect to the controller: {e}\n")
    except DominhException as e:
        sys.stderr.write(f"Error during write: {e}\n")
