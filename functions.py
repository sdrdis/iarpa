from params import *
import os
from os import listdir
from os.path import isfile, join
import subprocess
import numpy as np
import scipy.misc
from gdalconst import *
import cv2
import gdal
import pickle

import numpy as np

from skimage import exposure

import OpenEXR
import Imath

import pyproj

import struct
    
import scipy.ndimage

from sklearn import linear_model
import math

import skimage.restoration

import time

import resource

log_msgs = []
def log_msg(msg):
    print msg
    log_msgs.append(msg)
        
def open_gtiff(path, dtype=None):
    ds = gdal.Open(path)
    if dtype is None:
        im_np = np.array(ds.ReadAsArray())
        return im_np.copy()
    else:
        im_np = np.array(ds.ReadAsArray(), dtype=dtype)
        return im_np.copy()
        
def save_gtiff_3d(path, im_np):
    output_raster = gdal.GetDriverByName('GTiff').Create(path,im_np.shape[2], im_np.shape[1], im_np.shape[0] ,gdal.GDT_Float32)  # Open the file
    for i in xrange(im_np.shape[0]):
        #print i, im_np[i].shape, np.min(im_np[i]), np.max(im_np[i])
        band = output_raster.GetRasterBand(i + 1)
        #band.SetBlockSize(256, 256)]
        #band.SetColorTable(gdal
        band.WriteArray(im_np[i])   # Writes my array to the raster

        
    
    

def cartesian_to_spherical(xyz):
    wgs84 = pyproj.Proj('+proj=utm +zone=21 +datum=WGS84 +south')
    geocentric= pyproj.Proj('+proj=geocent +datum=WGS84 +units=m +no_defs')
    x, y ,z = pyproj.transform(geocentric, wgs84, xyz[:,0], xyz[:,1], xyz[:,2])
    
    ptsnew = np.zeros(xyz.shape, dtype=np.double)
    ptsnew[:,0] = z
    ptsnew[:,1] = x
    ptsnew[:,2] = y
    ptsnew[:,3:] = xyz[:,3:]
    return ptsnew

    
def get_center_coordinates(filepath):
    f = open(filepath, 'r')
    txt = f.read()
    f.close()

    center = txt.split(' ')[0:3]
    for i in xrange(len(center)):
        center[i] = float(center[i])
    return np.array(center,dtype=np.double)
    
def im_size_from_bounds(im_width, bounds):
    return (int(round((bounds[1][1] - bounds[1][0]) * im_width / (bounds[2][1] - bounds[2][0]))), im_width)
    
def get_height_map(spherical_c, bounds = None, im_size = None):
    if bounds is None:
        bounds = [[spherical_c[:,0].min(), spherical_c[:,0].max()], [spherical_c[:,1].min(), spherical_c[:,1].max()], [spherical_c[:,2].min(), spherical_c[:,2].max()]]
    if im_size is None:
        im_size = im_size_from_bounds(2048, bounds)
    im_np = -np.ones(im_size)
    z = (spherical_c[:,0] - bounds[0][0]) / (bounds[0][1] - bounds[0][0]) * 255
    x, y = spherical_to_image_positions(spherical_c, bounds, im_size)
    y[y < 0] = 0
    x[x < 0] = 0
    y = np.round(y).astype(int)
    x = np.round(x).astype(int)
    y[y >= im_size[0]] = im_size[0] - 1
    x[x >= im_size[1]] = im_size[1] - 1
    for i in xrange(z.shape[0]):
        cy = y[i]
        cx = x[i]
        im_np[cy,cx] = max(im_np[cy,cx], z[i])
    return im_np
    
def spherical_to_image_positions(spherical_c, bounds, im_size):
    y = (spherical_c[:,1] - bounds[1][0]) / (bounds[1][1] - bounds[1][0])
    x = (spherical_c[:,2] - bounds[2][0]) / (bounds[2][1] - bounds[2][0])
    y *= im_size[0]
    x *= im_size[1]
    return x, y
    
def image_to_spherical_positions(x, y, bounds, im_size):
    spherical_y = y / im_size[0]
    spherical_x = x / im_size[1]
    spherical_y *= (bounds[1][1] - bounds[1][0])
    spherical_x *= (bounds[2][1] - bounds[2][0])
    spherical_y += bounds[1][0]
    spherical_x += bounds[2][0]
    return spherical_x, spherical_y
    
def get_PC(image_filepath, center_filepath, color_filepath, consistency_filepath):
    center = get_center_coordinates(center_filepath)
    
    im_np = open_gtiff(image_filepath,np.double)
    
    data = np.load(consistency_filepath)
    
    lrc_init_np = data['lrc_init_np']
    lrc_1_np = data['lrc_1_np']
    lrc_2_np = data['lrc_2_np']
    
    color_np = standardize_im(open_gtiff(color_filepath))
    
    coordinates_len = im_np.shape[1] * im_np.shape[2]
    
    selected = np.logical_not(np.logical_and(np.logical_and(im_np[0,:,:] == 0, im_np[1,:,:] == 0), np.logical_and(im_np[2,:,:] == 0, im_np[3,:,:] == 0))).reshape(coordinates_len)
    
    coordinates = np.zeros((coordinates_len, 7), dtype=np.double)
    coordinates[:,0] = im_np[0,:,:].reshape(coordinates_len)
    coordinates[:,1] = im_np[1,:,:].reshape(coordinates_len)
    coordinates[:,2] = im_np[2,:,:].reshape(coordinates_len)
    coordinates[:,3] = color_np[:,:].reshape(coordinates_len)
    coordinates[:,4] = lrc_init_np[:,:].reshape(coordinates_len)
    coordinates[:,5] = lrc_1_np[:,:].reshape(coordinates_len)
    coordinates[:,6] = lrc_2_np[:,:].reshape(coordinates_len)
    
    image_positions = np.zeros((coordinates_len, 2), dtype=int)
    pos_range = np.arange(coordinates_len)
    image_positions[:,0] = pos_range / im_np.shape[2]
    image_positions[:,1] = pos_range % im_np.shape[2]
    
    coordinates = coordinates[selected]
    image_positions = image_positions[selected]


    coordinates[:,0] += center[0]
    coordinates[:,1] += center[1]
    coordinates[:,2] += center[2]

    spherical_c = cartesian_to_spherical(coordinates)
    
    return (image_positions, spherical_c)
    
def pair_filenames_to_pair(pair_filenames):
    return [tmp_cropped_images_path + pair_filenames[0] + '.tif', tmp_cropped_images_path + pair_filenames[1] + '.tif']
    
def get_pairs(selected_pairs_filenames):
    pairs = []
    for filenames in selected_pairs_filenames:
        pairs.append(pair_filenames_to_pair(filenames))
    return pairs

def generate_cropped(kml_path, image_path, image_to_path, image_type = 'GTiff', min_size = 1000):
    exec_path = get_crop_area_path + ' -k ' + kml_path + ' ' + image_path
    p = subprocess.Popen(exec_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    out = p.stdout.readlines()[0]
    if (out[0:5] == 'ERROR'):
        log_msg('ERROR WHEN CROPPING FILE!')
        return False, False
    
    crop_area = out.split(' ')[0:8]
    width_too_small = (int(crop_area[2]) - int(crop_area[0])) < min_size
    width_borders_cut = (int(crop_area[4]) == 0) or (int(crop_area[5]) == 0)
    height_too_small = (int(crop_area[3]) - int(crop_area[1])) < min_size
    height_borders_cut = (int(crop_area[6]) == 0) or (int(crop_area[7]) == 0)
    
    print crop_area
    print width_too_small, width_borders_cut, height_too_small, height_borders_cut
    
    if ((width_too_small and width_borders_cut) or (height_too_small and height_borders_cut)):
        log_msg('FILE TOO SMALL!')
        return False, False
    
    np.save(image_to_path, map(int, crop_area))
    
    crop_command = gdal_translate_path + ' -of ' + image_type + ' -srcwin ' + crop_area[0] + ' '  + crop_area[1] + ' ' + str(int(crop_area[2]) - int(crop_area[0])) + ' ' + str(int(crop_area[3]) - int(crop_area[1])) + ' ' + image_path + ' ' + image_to_path
        
    os.system(crop_command)
    
    return True, not(width_borders_cut or height_borders_cut)

def normalize_im(im_np):
    im_defined = im_np >= 0
    im_equalized = exposure.equalize_hist(im_np,mask=im_defined)
    im_equalized[np.logical_not(im_defined)] = -1
    return im_equalized

def standardize_im(im_np, nb=8):
    im_np = im_np.astype(float)
    im_defined = im_np >= 0
    median_value = np.median(im_np[im_defined])
    im_np -= median_value
    median_distance = np.median(np.abs(im_np[im_defined]))
    im_np /= median_distance * nb
    im_np[im_np < -1] = -1
    im_np[im_np > 1] = 1
    im_np += 1
    im_np /= 2
    im_np[np.logical_not(im_defined)] = -1
    return im_np

def compute_filtered_disp(left_matcher, left_np, right_np, ori_left_disp, ori_right_disp, left_invalid_np, right_invalid_np, max_disp, disc_radius = 3, lrc_threshold = 24):
    left_disp = ori_left_disp.copy()
    right_disp = ori_right_disp.copy()
    
    invalid_values = -np.ones(ori_left_disp.shape) * (max_disp + 10) * 16
    invalid_values[:,(invalid_values.shape[1] / 2):] = (max_disp + 20) * 16

    left_to_remove = left_invalid_np.copy()
    right_to_remove = right_invalid_np.copy()
    left_disp[left_to_remove] = invalid_values[left_to_remove]
    right_disp[right_to_remove] = invalid_values[right_to_remove]
    
    wls_filter = cv2.ximgproc.createDisparityWLSFilter(left_matcher)
    wls_filter.setLambda(wls_lambda)
    wls_filter.setSigmaColor(wls_sigma)
    wls_filter.setDepthDiscontinuityRadius(disc_radius) # Normal value = 7
    wls_filter.setLRCthresh(lrc_threshold)
    disparity = np.zeros(left_disp.shape)
    disparity = wls_filter.filter(left_disp,left_np, disparity,right_disp,(0, 0, left_disp.shape[1], left_disp.shape[0]),right_np)
    
    confidence_np = wls_filter.getConfidenceMap()

    return disparity, confidence_np

def post_process_undefined(undefined_np, max_disp):
    undefined_np[:,0] = True
    undefined_np[:,-1] = True
    undefined_np[0,:] = True
    undefined_np[-1,:] = True
    undefined_np = scipy.ndimage.binary_dilation(undefined_np, iterations = margin_undefined)
    return undefined_np

def get_M_from_exr(file_path):
    pt = Imath.PixelType(Imath.PixelType.FLOAT)
    exr = OpenEXR.InputFile(file_path)

    exr_str = exr.channel('Channel0',pt)

    return np.fromstring(exr_str, dtype=np.float32).reshape((3,3))

def warp_coordinates(Xfrom, Yfrom, mat, width, height):
    X = np.round(mat[0,0] * Xfrom + mat[0,1] * Yfrom + mat[0,2]).astype('int')
    Y = np.round(mat[1,0] * Xfrom + mat[1,1] * Yfrom + mat[1,2]).astype('int')
    
    coordinates_to_keep = np.ones(X.shape, dtype=bool)
    coordinates_to_keep[X < 0] = False
    coordinates_to_keep[Y < 0] = False
    coordinates_to_keep[X >= width] = False
    coordinates_to_keep[Y >= height] = False
    
    X = X[coordinates_to_keep]
    Y = Y[coordinates_to_keep]
    Xfrom = Xfrom[coordinates_to_keep]
    Yfrom = Yfrom[coordinates_to_keep]
    
    print Y.max()
    
    return X, Y, Xfrom, Yfrom


def save_pc(out_path, pc):
    out_f = np.zeros((pc.shape[0], 4))
    out_f[:,0] = pc[:,1]
    out_f[:,1] = pc[:,2]
    out_f[:,2] = pc[:,0]
    out_f[:,3] = pc[:,3]
    
    np.savetxt(out_path, out_f, fmt='%.3f')


def imsave(path, im_np):
    im_np_min = np.nanmin(im_np)
    im_np_max = np.nanmax(im_np)
    im_normalized_np = (im_np - im_np_min) * 255.0 / (im_np_max - im_np_min)
    im_normalized_np[im_normalized_np < 0] = 0
    im_normalized_np[im_normalized_np > 255] = 255

    im_color_np = np.zeros((im_np.shape[0], im_np.shape[1],3), dtype='uint8')
    im_color_np[:,:,0] = im_normalized_np
    im_color_np[:,:,1] = im_normalized_np
    im_color_np[:,:,2] = im_normalized_np
    im_np_nan = np.isnan(im_np)
    im_color_np[im_np_nan,0] = 255
    im_color_np[im_np_nan,1] = 0
    im_color_np[im_np_nan,2] = 0
    
    scipy.misc.imsave(path, im_color_np)

def final_heights_to_spherical_c(f_infos, bounds):
    f_heights = f_infos[:,:,1]
    f_colors = f_infos[:,:,2]
    
    if (is_debug_mode):
        np.save('tmp/f_infos.npy', f_infos)
    
    r_heights = scipy.misc.imresize(f_heights, 3.0, 'bilinear', 'F')
    r_colors = scipy.misc.imresize(f_colors, 3.0, 'bilinear', 'F')
    
    if (is_debug_mode):
        imsave('tmp/f_heights.png', f_heights)
        imsave('tmp/f_consensus.png', f_infos[:,:,0])
        imsave('tmp/f_r_heights.png', r_heights)
    
    
    im_size = r_heights.shape
    idx = np.arange(r_heights.shape[0] * r_heights.shape[1])
    x = idx % r_heights.shape[1]
    y = idx / r_heights.shape[1]
    heights = r_heights.reshape(r_heights.shape[0] * r_heights.shape[1])
    colors = r_colors.reshape(r_heights.shape[0] * r_heights.shape[1])
    defined = np.logical_not(np.isnan(heights))
    
    x = x[defined]
    y = y[defined]
    heights = heights[defined]
    colors = colors[defined]
    
    spherical_c = np.zeros((heights.shape[0], 4))
    
    spherical_c[:,0] = heights
    spherical_c[:,2], spherical_c[:,1] = image_to_spherical_positions(x.astype(float), y.astype(float), bounds, im_size)
    spherical_c[:,3] = colors
    
    if (is_debug_mode):
        re_im_np = get_height_map(spherical_c, bounds, im_size)
        imsave('tmp/f_re_heights.png', re_im_np)
    
    print 'NB POINTS:', spherical_c.shape[0]
    return spherical_c


    
def denoise_heights(f_infos):
    height_np = f_infos[:,:,1].copy()


    undefined_np = np.isnan(height_np)
    min_np = np.nanmin(height_np)
    height_np -= min_np

    max_height = np.nanmax(height_np)

    height_np[undefined_np] = max_height * 100 + 100

    height_np = skimage.restoration.denoise_bilateral(height_np, multichannel=False, sigma_color=1, sigma_spatial=1)

    height_np += min_np
    height_np[undefined_np] = np.nan

    f_infos[:,:,1] = height_np
    

def get_best_interval(list_height, data, height_variance = 2, min_items=1):
    lower = 0
    upper = 1
    need_add = True
    sums_np = data[:,0].copy()
    best_interval = None
    while(True):
        if upper >= list_height.shape[0] or np.isnan(list_height[upper]):
            break
        if (list_height[upper] - list_height[lower]) > height_variance:
            nb_items = upper - lower
            if need_add and nb_items >= min_items and (best_interval is None or nb_items > best_interval[3]):
                best_interval = (lower,upper,sums_np/nb_items,nb_items)
            need_add = False
            sums_np -= data[:, lower]
            lower += 1
        else:
            need_add = True
            sums_np += data[:, upper]
            upper += 1
    nb_items = upper - lower
    if need_add and nb_items >= min_items and (best_interval is None or nb_items > best_interval[3]):
        best_interval = (lower,upper,sums_np/nb_items,nb_items)
    return best_interval

def get_final_height_from_heights(item_heights, height_variance = 2):
    if (len(item_heights[0]) == 0):
        return None
    
    heights_order = np.argsort(item_heights[0])
    
    item_heights_np = np.array(item_heights)[:,heights_order]
    
    lrc_data = item_heights_np[2,:]
    item_heights_np = item_heights_np[0:2,:]
    
    groups = [np.ones(item_heights_np.shape[1], dtype=bool), lrc_data > 0.5, lrc_data > 1.5]
    
    overall_best_interval = None
    for i in [2, 1, 0]:
        group = groups[i]
        group_heights = item_heights_np[:,group]
        if (group_heights.shape[1] == 0):
            continue
            
            
        best_interval = get_best_interval(group_heights[0,:], group_heights, height_variance)
        
        # @todo: remove last condition, buggy...  and best_interval[3] > 2
        if (overall_best_interval is None or (best_interval[3] > overall_best_interval[3])):
            overall_best_interval = best_interval
            
    return overall_best_interval

def get_min_consensus(f_infos, min_definition):
    nb_existing_nan = np.sum(np.isnan(f_infos[:,:,1]))
    total_nb = f_infos.shape[0] * f_infos.shape[1]
    need_definition = total_nb * min_definition
    return np.nanpercentile(f_infos[:,:,0], 100 - (need_definition * 100.0 / (total_nb - nb_existing_nan)))
    

def optimize_precision(f_infos, consensus, min_definition = 0.6):
    margin = 30
    min_consensus = get_min_consensus(f_infos, min_definition)
    if (f_infos.shape[0] > margin * 2 and f_infos.shape[1] > margin * 2):
        min_consensus = min(min_consensus, get_min_consensus(f_infos[margin:-margin,margin:-margin,:], min_definition))
    print 'consensus before', consensus, min_consensus
    
    if (min_consensus <= consensus):
        consensus = int(min_consensus)
    
    print 'consensus after', consensus
    
    f_infos[f_infos[:,:,0] < consensus,:] = np.nan
    
def post_process_f_infos(f_infos, consensus, min_definition = 0.6):
    try:
        optimize_precision(f_infos, consensus, min_definition)
    except:
        log_msg('PRECISION OPTIMIZATION FAILED, skipping...')
    try:
        denoise_heights(f_infos)
    except:
        log_msg('HEIGHTS DENOISING FAILED, skipping...')
    
def generate_pc_from_pair(pair, pair_id):
    bundle_adjust_prefix = tmp_stereo_output_path + str(pair_id) + '/bundle_adjust/ba'
        
    pre_path = tmp_stereo_output_path + str(pair_id) + '/results/out'
        
    stereo_command = stereo_path + ' -t rpc -e 4 ' + ' '.join(pair) + ' ' + pre_path
    if (use_bundle_adjust):
        stereo_command += ' --bundle-adjust-prefix ' + bundle_adjust_prefix
    print '############## Executing:', stereo_command
    os.system(stereo_command)
    
    
def generate_rectified(pair, pair_id):
    if (use_bundle_adjust):
        bundle_adjust_prefix = tmp_stereo_output_path + str(pair_id) + '/bundle_adjust/ba'

        bundle_adjust_command = bundle_adjust_path + ' ' + ' '.join(pair) + ' -o ' + bundle_adjust_prefix
        print '############## Executing:', bundle_adjust_command
        os.system(bundle_adjust_command)
    
    pair_path = tmp_stereo_output_path + str(pair_id)
    out_path = pair_path + '/results/out'
    
    stereo_command = stereo_path + ' -t rpc --stop-point=1 ' + ' '.join(pair) + ' ' + out_path
    if (use_bundle_adjust):
        stereo_command += ' --bundle-adjust-prefix ' + bundle_adjust_prefix
    print '############## Executing:', stereo_command
    os.system(stereo_command)
    
    is_valid = os.path.exists(out_path + '-L.tif') and os.path.exists(out_path + '-R.tif')
    
    if (not is_valid):
        if (os.path.exists(pair_path)):
            shutil.rmtree(pair_path, True)
    
    return is_valid

def register_time(times):
    times.append(time.time())
    print len(times), times[-1] - times[-2]
    
def display_times(times):
    for i in range(1, len(times)):
        print i, times[i] - times[i-1]

def save_times(times, total_time, path):
    with open(path, 'w') as f:
        for i in range(1, len(times)):
            f.write(str(i))
            f.write(': ')
            f.write(str(times[i] - times[i-1]))
            f.write("\n")
        f.write("\nTotal time: ")
        f.write(str(total_time))
        f.write("\nMax memory used: ")
        f.write(str(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024))
        f.write('M')
        f.write("\n\nLogs:")
        i = 0
        for msg in log_msgs:
            f.write("\n" + str(i) + ': ' + msg)
            i += 1