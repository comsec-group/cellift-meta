# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import zlib

# Generate the string associated with a taint bit tuple.
# @param taintbits: iterable of 2-tuples representing the taint assignment.
def taintstr(taintbits):
    for x in taintbits:
        assert isinstance(x, tuple)
        assert len(x) == 2
    if taintbits == []:
        return 'NoTaintSet'
    retstr='-'.join([('{}_{}'.format(*x)) for x in taintbits])
    return retstr

# Add CRC to binary name.
def binarycrc(binary):
        crc = zlib.crc32(open(binary, 'rb').read())
        return 'bin{}'.format(crc)
