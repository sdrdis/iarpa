import numpy as np
from params import *
from functions import *
import scipy.ndimage
import math
import sys
import scipy.misc

fire_palette = scipy.misc.imread('palettes/fire_palette.png')[0][:, 0:3]
confidence_palette = scipy.misc.imread('palettes/confidence_palette.png')[0][:, 0:3]
    
def getImageMinMax(im_np):
    return np.nanpercentile(im_np, 10), np.nanpercentile(im_np, 90)

def getColorMapFromPalette(im_np, palette, im_min = None, im_max = None):
    if (im_min is None):
        im_min, im_max = getImageMinMax(im_np)
    print 'min:', im_min, 'max:', im_max
    normalized = ((im_np - im_min) / (im_max - im_min))
    normalized[normalized < 0] = 0
    normalized[normalized > 1] = 1
    normalized_nan = np.isnan(normalized)
    normalized_not_nan = np.logical_not(normalized_nan)

    color_indexes = np.round(normalized * (palette.shape[0] - 2) + 1).astype('uint32')
    color_indexes[normalized_nan] = 0

    color_map = palette[color_indexes]

    return color_map



print 'Loading intervals...'

nb_args = len(sys.argv)
if (nb_args < 3):
    print 'Correct format: python vizualize_result.py [Input KML file] [Path to NITF image folder]'
    sys.exit()

data_path = sys.argv[1]
out_path = sys.argv[2]

data = np.load(data_path)
f_infos = data['f_infos']
bounds = data['bounds']

palettes = [confidence_palette, fire_palette, None]
names = ['confidence', 'height_map', 'color_map']

for i in xrange(f_infos.shape[2]):
    palette = palettes[i]
    path = out_path+str(names[i])+'.png'
    if (palette is None):
        imsave(path, f_infos[:,:,i])
    else:
        scipy.misc.imsave(path, getColorMapFromPalette(f_infos[:,:,i], palette))


