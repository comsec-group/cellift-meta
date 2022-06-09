# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script manages the translation between
#  - the intermediate representation as a list of pairs (addr, byte_taint).
#  - taint lines in taint files.

import sys

DEFAULT_TAINT_ID = 0

# Transforms a taintbits iterable into a taint file content and returns this content.
# @param taintfile the path to the taintfile to write.
# @param taintbits an iterable of pairs (addr, byte_taint).
# @return the taint file content.
def gen_taintlines(taintfile, taintbits):
    tt = TaintTuples()
    for tb in taintbits:
        assert len(tb) == 2
        addr, taintbyte = tb
        assert taintbyte >= 0 and taintbyte <= 255 # byte mask
        tt.add_tuple(tainttuple = tb)
    return tt.gen_taintlines()

# Transforms a taintbits iterable into a taint file.
# @param taintfile the path to the taintfile to write.
# @param taintbits an iterable of pairs (addr, byte_taint).
# @return None
def write_taintfile(taintfile, taintbits):
    content = gen_taintlines(taintfile, taintbits)
    with open(taintfile, 'w') as f:
        f.write(content)

# Parses a taintfile into taintbytes.
def parse_taintfile(taintfile_path):
    taintbits = []
    tt=TaintTuples()
    # A file not found error here may indicate that the benchmark files were not generated.
    with open(taintfile_path) as fp:
        lines = fp.readlines()
    for line in lines:
        tt.add_taintline(taintline=line)
    return tt.asbytes()

# TaintTuples stores the taint data.
class TaintTuples:
    # design_name is only used for the alignment bits.
    def __init__(self):
        # Alignment.
        self.alignment = 32
        # Taint list: dict[addr: Int] = taints: 
        self.taintlist = dict()

    def add_taintline(self, taintline):
        # Hex string to bytes object.
        def parse_taintbytes(bytestr):
            if len(bytestr) % 2 != 0:
                raise ValueError('can not parse hex taint bytes')
            return bytes.fromhex(bytestr)

        fields=taintline.split()
        taint_id, address, nbytes, taintbytes_mask = int(fields[0]), int(fields[1],16), int(fields[2]), parse_taintbytes(fields[3])

        # Adjust taint mask to given length if possible.
        if len(taintbytes_mask) > nbytes:
            raise Exception('length too small to cover taint bytes. length: {}. Bytes: {}.'.format(nbytes, taintbytes_mask))
        while len(taintbytes_mask) < nbytes:
            taintbytes_mask += bytes([0])
            print('WARNING: short taint bytes, appending zero. len: {}. Bytes: {}'.format(len(taintbytes_mask), nbytes))

        self.private_add(taint_id, address, nbytes, taintbytes_mask)

    # Add tuple 
    def add_tuple(self, tainttuple):
        taint_id = DEFAULT_TAINT_ID
        address = tainttuple[0]
        taintbytes_mask = bytes([tainttuple[1]])
        nbytes = 1
        self.private_add(taint_id, address, nbytes, taintbytes_mask)

    # Private method, do not call externally.
    def private_add(self, taint_id, address, nbytes, taintbytes_mask):
        assert len(taintbytes_mask) == nbytes

        # Align the taint data correctly.
        while address % self.alignment > 0:
            address -= 1
            nbytes += 1
            taintbytes_mask = bytes([0]) + taintbytes_mask

        if len(taintbytes_mask) > self.alignment:
            raise ValueErrror('do not support multi-word taint strings yet')
        while len(taintbytes_mask) < self.alignment:
            taintbytes_mask += bytes([0])

        assert len(taintbytes_mask) == self.alignment
        self.taint_id = taint_id
        if address in self.taintlist:
            prev = self.taintlist[address]
            assert len(prev) == self.alignment
            assert len(prev) == len(taintbytes_mask)
            updated = [a | b for a,b in zip(prev,taintbytes_mask)]
#            print('from: %s and: %s to: %s' % (self.encode_bytes(prev), self.encode_bytes(taintbytes_mask), self.encode_bytes(updated)))
            assert len(updated) == self.alignment
            self.taintlist[address] = updated
        else:
            self.taintlist[address] = taintbytes_mask

    def clamptaint(self, nbytes):
        assert nbytes > 0
        for x in self.taintlist:
            self.taintlist[x] = self.taintlist[x][0:nbytes]

    def asbytes(self):
      for a in self.taintlist:
        l=[]
        for b in self.taintlist[a]:
            if b != 0:
                if b != 0xff:
                    raise Exception('returning %s asbytes, saw %s: can only handle bytes for now' % (self.taintbytes_mask, b))
                l.append((a, b))
            a += 1
        return l

    def aswords(self):
      wl = []
      for a in self.taintlist:
        # addr, taintbits = tt.asword()
        assert a % self.alignment == 0
        wl.append(a, self.taintlist[a])
      return wl

    def encode_bytes(self, b):
        return ''.join('%02X' % x for x in b)

    def gen_taintlines(self):
        ret = []
        for a in self.taintlist:
            assert a % self.alignment == 0
            b=self.taintlist[a]
            ret.append('0 %08x %d %s' % (a, len(b), self.encode_bytes(b)))
        return '\n'.join(ret)
