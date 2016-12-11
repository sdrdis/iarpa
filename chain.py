'''
This the main code for running the chain.
It is quite straightforward: it runs chain_pairwise_pc and chain_merge_pcs (with a few additional logs...)
'''

import chain_pairwise_pc
import chain_merge_pcs
import time
from params import *
import sys
import os
import os.path
import shutil
import numpy as np
import resource
from functions import *

nb_args = len(sys.argv)
if (nb_args < 4):
    print 'Correct format: python chain.py [Input KML file] [Path to NITF image folder] [Output file]'
else:
    kml_path = sys.argv[1]
    images_paths = sys.argv[2]
        
    if (images_paths[-1] != '/'):
        images_paths += '/'
        
    out_path = sys.argv[3]
    
    
    skip_align = False
    for arg in sys.argv:
        if (arg == 'skip_align'):
            skip_align = True
            
    
    start_time = time.time()
    times = [start_time]

    if not is_debug_mode:
        shutil.rmtree(tmp_path, True)

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    

    chain_pairwise_pc.run(kml_path, images_paths)
    register_time(times)
    chain_merge_pcs.run(kml_path, out_path)
    register_time(times)
    display_times(times)
    
    total_time = time.time() - start_time
    
    
    save_times(times, total_time, tmp_path + 'durations.txt')
    
    print 'Total time:', total_time
