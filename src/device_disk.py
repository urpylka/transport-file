#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:set ts=4 sw=4 et:

# Copyright 2018 Artem Smirnov

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from device_abstract import Device
from bash_commands import *

import os, time

class DISK(Device):
    def _connect(self):
        self.is_remote_available.clear()
        self.kwargs["logger"].info("SOURCE: Раздел недоступен, все операции заблокированы")
        while True:
            time.sleep(1)
            code = None
            output = None
            code, output, error = bash_command("/bin/lsblk -o MOUNTPOINT \"/dev/disk/by-uuid/" + self.kwargs["uuid"] + "\"", self.kwargs["logger"])
            if code == 0:
                #if output.find((self.kwargs["mount_point"]) > -1:
                if self.kwargs["mount_point"] in str(output):
                    if not self.is_remote_available.is_set():
                        self.is_remote_available.set()
                        self.kwargs["logger"].info("SOURCE: Раздел доступен, все операции разблокированы")
                else:
                    self.kwargs["logger"].debug("SOURCE: Try to mount partition")
                    a, b, c = bash_command("/bin/mount /dev/disk/by-uuid/" + self.kwargs["uuid"] + " " + self.kwargs["mount_point"], self.kwargs["logger"])
                    continue
            else:
                if self.is_remote_available.is_set():
                    self.is_remote_available.clear()
                    self.kwargs["logger"].info("SOURCE: Раздел недоступен, все операции заблокированы")

                    if code == 32:
                        self.kwargs["logger"].debug("SOURCE: The partition was ejected")
                    else: self.kwargs["logger"].debug("SOURCE: lsblk returned code: " + str(code))


    def get_list(self):
        """
        Get list of files
        """
        self.is_remote_available.wait()
        my_list = []
        for rootdir, dirs, files in os.walk(self.kwargs["mount_point"]):
            for file in files:
                my_list.append(os.path.join(rootdir.replace(self.kwargs["mount_point"], '', 1), file))
        return my_list


    def download2(self, remote_path, local_path):
        self.is_remote_available.wait()
        return copy(remote_path, local_path, self.kwargs["logger"])


    def download(self, device_path, target_stream, chunk_size=1024):
        """

        from device_disk import DISK
        from logger import get_logger
        logger = get_logger("filesync", "/home/pi/flir/filesync.log")
        source = DISK("66F8-E5D9", "/mnt", logger)
        with open("20181106_163024_949.JPG", 'wb') as target_stream:
            source.download("/20181106_163024/20181106_163024_949.JPG", target_stream)
        print("OK")

        https://docs.python.org/3/library/io.html
        https://docs.python.org/3/library/asyncio-stream.html
        https://python-scripts.com/threading
        """
        self.is_remote_available.wait()
        self.kwargs["logger"].debug("Downloading from " + str(device_path))

        with open(self.kwargs["mount_point"] + device_path, 'rb') as stream:
            while True:
                # print(stream.tell())
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                target_stream.write(chunk)


    def upload(self, source_stream, device_path, chunk_size=1024):
        """

        with open("file_name", 'rb') as source_stream:
            target.upload(source_stream, "device_path")

        """
        self.is_remote_available.wait()
        self.kwargs["logger"].debug("Upload to " + str(device_path))

        with open(self.kwargs["mount_point"] + device_path, 'wb') as stream:
            while True:
                chunk = source_stream.read(chunk_size)
                if not chunk:
                    break
                stream.write(chunk)
