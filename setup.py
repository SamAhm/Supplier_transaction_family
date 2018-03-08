# Copyright 2017-2018 Wind River
# Copyright 2017 Intel Corporation
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
# ------------------------------------------------------------------------------

from __future__ import print_function

import os
import subprocess

from setuptools import setup, find_packages

data_files = []

if os.path.exists("/etc/default"):
    data_files.append(
        ('/etc/default', ['packaging/systemd/sparts-supplier-tp-python']))

if os.path.exists("/lib/systemd/system"):
    data_files.append(('/lib/systemd/system',
                       ['packaging/systemd/sparts-supplier-tp-python.service']))

setup(
    name='sparts-supplier',
    version=subprocess.check_output(
        ['../../../bin/get_version']).decode('utf-8').strip(),
    description='Sparts Supplier',
    author='Wind River Systems',
    url='https://github.com/Wind-River/sparts',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
        'sawtooth-signing',
        'PyYAML',
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'supplier = sparts_supplier.supplier_cli:main_wrapper',
            'supplier_tp_python = sparts_supplier.processor.main:main',
        ]
    })
