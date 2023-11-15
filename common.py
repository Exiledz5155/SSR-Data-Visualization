import argparse
import ctypes
import gzip
import os
import pickle
import shutil
import glob
import pandas as pd
import numpy as np

# Nominal HaFX data class from C++ implemented in Python
# to make loading/decoding easier
# NB THIS IS 123 BINS NOT 122
NUM_HG_BINS = 123
HafxHistogramArray = NUM_HG_BINS * ctypes.c_uint32
class NominalHafx(ctypes.Structure):
    # Do not pad the struct
    _pack_ = 1
    _fields_ = [
        ('ch', ctypes.c_uint8),
        ('buffer_number', ctypes.c_uint16),
        ('num_evts', ctypes.c_uint32),
        ('num_triggers', ctypes.c_uint32),
        ('dead_time', ctypes.c_uint32),
        ('anode_current', ctypes.c_uint32),
        ('histogram', HafxHistogramArray),
        ('time_anchor', ctypes.c_int32),
        ('missed_pps', ctypes.c_bool)
    ]

def read_time_slices(fn: str) -> list[NominalHafx]:
    ret = []
    sz = ctypes.sizeof(NominalHafx)
    i = 0
    with gzip.open(fn, 'rb') as f:
        while True:
            nh = NominalHafx()
            eof = f.readinto(nh) != sz
            if eof: break

            ret.append(nh)
            i += 1
    return ret


def gZip(fn: str):
    dat_dir = 'test_data'
    os.makedirs(dat_dir, exist_ok=True)

    base_fn = os.path.basename(fn)

    file_in = open(fn, "rb")

    file_out = gzip.open(f"{dat_dir}/{base_fn}.gz", "wb")

    shutil.copyfileobj(file_in, file_out)

    file_out.close()
    file_in.close()

def gZipFiles(f_dir: str):
    os.makedirs(f_dir, exist_ok=True)
    filepaths = glob.glob(f"{f_dir}/*.bin")
    #print(filepaths)

    for filepath in filepaths:
        gZip(filepath)

def read_multiple_slices(f_dir: str) -> list[list[NominalHafx]]:
    os.makedirs(f_dir, exist_ok=True)
    filepaths = glob.glob(f"{f_dir}/*.gz")
    # print(filepaths)
    slices = []

    for filepath in filepaths:
        slices.append(read_time_slices(filepath))

    return slices


def processSlices(slices: list[slice: list[NominalHafx]]) -> dict:
    data_dict = []
    # Iterate through list of slices
    for slice in slices:
        # Iterate through each NominalHafx object
        for fields in slice:
            time_anchor = 0
            if fields.time_anchor > 971979211: # only convert reasonable time anchors after the year 2000
                time_anchor = pd.to_datetime(fields.time_anchor, unit='s')
            fields_dict = {
                'buffer_number': fields.buffer_number,
                'num_evts': fields.num_evts,
                'num_triggers': fields.num_triggers,
                'dead_time': (fields.dead_time * 25.0) / 1e3,
                'anode_current': fields.anode_current,
                'time_anchor': time_anchor,
                'missed_pps': fields.missed_pps,
            }
            data_dict.append(fields_dict)
    return data_dict

