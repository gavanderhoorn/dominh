
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


from setuptools import setup

setup(
    name='dominh',
    version='0.1.1',
    packages=['dominh', 'dominh.tool'],
    package_dir={'': 'src'},
    scripts=['bin/dominh'],
    author='G.A. vd. Hoorn',
    author_email='g.a.vanderhoorn@tudelft.nl',
    maintainer='G.A. vd. Hoorn',
    maintainer_email='g.a.vanderhoorn@tudelft.nl',
    description=("A poor man's implementation of an RPC interface to Fanuc "
                 "R-30iA and R-30iB(+) controllers"),
    license='Apache-2.0',
    python_requires='>=3.6',
    install_requires=['docopt', 'requests'],
)
