#!/usr/bin/python
# ------------------------------------------------------------------------------
#   compare-versions.py - Compare two versions of output files after
#       changing the generating algorithm. Change affected only the wipe functions with a fixed parameter.
# ------------------------------------------------------------------------------

import sys
import numpy as np
from PIL import Image
from pathlib import Path

# ------------------------------------------------------------------------------

old_dir = "~/Original-Output/User-600x400"
new_dir = "~/Output/User-600x400"

for ofile in Path( old_dir ).expanduser().glob( '*Wipe*Fix*' ):
    print( ofile )

    nfile = Path( Path( new_dir ).expanduser(), ofile.name )

    img1 = Image.open( ofile )
    img2 = Image.open( nfile )

    a1 = np.array(img1)
    a2 = np.array(img2)

    diff = np.abs(a1.astype(int) - a2.astype(int))
    print( f"  Max diff: {diff.max()}" )
    print( f"  Pixels differing: {np.count_nonzero(diff)},  {100 * np.count_nonzero(diff) / a1.size:.4f}%" )
    print( '' )


# ------------------------------------------------------------------------------
