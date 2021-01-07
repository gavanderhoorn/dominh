#!/usr/bin/env python3

# flake8: noqa

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
Usage: print_controller_info.py [(--user=<user> --pw=<pw>)] <host>

"""

from docopt import docopt

from dominh import Client


if __name__ == '__main__':
    args = docopt(__doc__, version='dominh 0.2.2')
    host = args['<host>']
    user = args['--user']
    pw = args['--pw']

    print(f'Attempting to connect to: {host}')

    auth = None
    if user:
        print("Assuming KCL and Karel resources share credentials.")
        auth = (user, pw)
    c = Client(host, kcl_auth=auth, karel_auth=auth)
    c.initialise()

    print('\nController info:')
    print(f'  Time                  : {c.get_clock()}')
    print(f'  Series                : {c.get_controller_series()}')
    print(f'  Application           : {c.get_application()}')
    print(f'  Software version      : {c.get_system_software_version()}')
    print(f'  $FNO                  : {c.get_scalar_var("$fno")}')

    print('\nRobot info:')

    num_groups = c.get_num_groups()
    print(f'  Number of groups      : {num_groups}')

    for grp in range(1, num_groups+1):
        print(f'  Group {grp}:')
        print(f'    ID                  : {c.get_robot_id(group=grp)}')
        print(f'    Model               : {c.get_robot_model(group=grp)}')

    print(f'\nGeneral override        : {c.get_general_override()}%')

    print('\nController status:')
    print(f'  TP enabled            : {c.tp_enabled()}')
    print(f'  In AUTO               : {c.in_auto_mode()}')
    print(f'  In error              : {c.is_faulted()}')
    print(f'  E-stopped             : {c.is_e_stopped()}')
    print(f'  Remote mode           : {c.in_remote_mode()}')
    print(f'  Program running       : {c.is_program_running()}')
    print(f'  Program paused        : {c.is_program_paused()}')

    numregs = ', '.join([str(c.get_numreg(i)) for i in range(1, 6)])
    print(f'\nFirst 5 numregs         : {numregs}')

    pld = c.get_payload(idx=1)
    pld_frame = f'({pld.payload_x}, {pld.payload_y}, {pld.payload_z})'
    pld_inertia = f'{pld.payload_ix}, {pld.payload_iy}, {pld.payload_iz}'
    print(f'\nPayload 1 in group 1    : {pld.payload} Kg at {pld_frame} (inertia: {pld_inertia})')

    prgs = '; '.join([f"{nam}.{ext}" for nam, ext in c.list_programs()[:5]])
    print(f'\nFirst five programs     : {prgs}')

    errs = '\n  '.join([f'{stamp:15s} {lvl:7s} {msg}' for _, stamp, msg, _, lvl, _ in c.list_errors()[:5]])
    print(f'\nFive most recent errors:\n  {errs}')
