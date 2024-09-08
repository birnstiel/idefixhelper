import os
import sys
import struct
from pathlib import Path
import numpy as np

# try to import the IDEFIX_DIR from the environment
if not 'IDEFIX_DIR' in os.environ:
    os.environ['IDEFIX_DIR'] = str(Path('~/CODES/idefix').expanduser())

if os.environ['IDEFIX_DIR'] not in sys.path:
    sys.path.insert(1, os.environ['IDEFIX_DIR'])

from pytools.dump_io import DumpDataset
from pytools.dump_io import HEADER_SIZE
from pytools.dump_io import NAME_SIZE
from pytools.dump_io import DOUBLE_SIZE
from pytools.dump_io import FLOAT_SIZE
from pytools.dump_io import INT_SIZE
from pytools.dump_io import BOOL_SIZE


class WritableDumpDataset(DumpDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _write_field(self, fh, field, arr, byteorder="little"):

        # determine the data type and sizes
        dtype = arr.dtype.name

        if dtype == "float64":
            mysize = DOUBLE_SIZE
            stringchar = "d"
            ntype = 0
        elif dtype == "float32":
            mysize = FLOAT_SIZE
            stringchar = "f"
            ntype = 1
        elif dtype == "int32":
            mysize = INT_SIZE
            stringchar = "i"
            ntype = 2
        elif dtype == 'bool':
            mysize = BOOL_SIZE
            stringchar = "?"
            ntype = 3
        else:
            raise RuntimeError(
                f"Found unknown data type {dtype} for field {field}")

        # write a NAME_SIZES binary string with the field name
        name = field.encode() + b"\x00"
        name += ((NAME_SIZE - len(name)) * ' ').encode()
        fh.write(name)

        # write the data type
        fh.write(ntype.to_bytes(length=INT_SIZE, byteorder=byteorder))

        # write the number of dimensions
        fh.write(arr.ndim.to_bytes(length=INT_SIZE, byteorder=byteorder))

        # write the length of all dimensions
        for n in arr.shape[::-1]:
            fh.write(n.to_bytes(length=INT_SIZE, byteorder=byteorder))

        # pack the struct & write it
        ntot = np.prod(arr.shape)
        raw = struct.pack(str(ntot) + stringchar,
                          *arr.T.ravel(order='C'))
        fh.write(raw)

    def write_dump(self, fname):

        # get original header
        with open(self.filename, 'rb') as fh:
            binary_header = fh.read(HEADER_SIZE)

        # open the output file
        with open(fname, 'wb') as fh:

            # write the same header
            fh.write(binary_header)

            # write the coordinates
            fields = ['x1', 'x1l', 'x1r', 'x2',
                      'x2l', 'x2r', 'x3', 'x3l', 'x3r']

            for field in fields:
                arr = getattr(self, field)
                self._write_field(fh, field, arr)

            # write out all the fields in data

            for key, value in self.data.items():
                self._write_field(fh, key, value)

            # write the eof field
            self._write_field(fh, 'eof', np.array([0], dtype=np.int32))
