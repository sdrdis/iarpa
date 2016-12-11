import cv2
import numpy as np
from functions import *
import scipy.ndimage
from params import *
import os
import shutil
import scipy.signal
import time

#http://docs.opencv.org/3.1.0/d3/d14/tutorial_ximgproc_disparity_filtering.html#gsc.tab=0

def generate_disparity_map_from_pair(pair_filenames, pair_id):
    generate_disparity_map(tmp_stereo_output_path + str(pair_id) + '/results/', pair_id, pair_filenames, max_disp)


def generate_disparity_map(path, pair_id, pair_filenames, max_disp):
    left_np = open_gtiff(path + 'out-L.tif')
    right_np = open_gtiff(path + 'out-R.tif')
    
    left_infos_np = np.load(tmp_cropped_images_path + pair_filenames[0] + '.tif.npy')
    left_M = get_M_from_exr(path + 'out-align-L.exr')
    
    if (is_debug_mode):
        common_max = max(left_np.max(), right_np.max())
        
        raw_left_np = left_np.copy()
        raw_right_np = right_np.copy()
        
        raw_left_np[raw_left_np < 0] = 0
        raw_right_np[raw_right_np < 0] = 0

        raw_left_np *= 255.0 / common_max
        raw_right_np *= 255.0 / common_max
        
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-L-raw.png', raw_left_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-R-raw.png', raw_right_np)
    
    standardized_left_np = standardize_im(left_np)
    standardized_right_np = standardize_im(right_np)
    
    left_np = standardized_left_np.copy() # normalize_im(left_np)
    right_np = standardized_right_np.copy() # normalize_im(right_np)
    
    left_undefined_np = left_np < 0
    right_undefined_np = right_np < 0
    
    left_invalid_np = post_process_undefined(left_undefined_np, max_disp)
    right_invalid_np = post_process_undefined(right_undefined_np, max_disp)

    left_np[left_np < 0] = 0
    right_np[right_np < 0] = 0
    standardized_left_np[left_np < 0] = 0
    standardized_right_np[right_np < 0] = 0

    left_np *= 255
    right_np *= 255
    
    standardized_left_np *= 255
    standardized_right_np *= 255

    left_np = left_np.astype('uint8')
    right_np = right_np.astype('uint8')
    
    standardized_left_np = standardized_left_np.astype('uint8')
    standardized_right_np = standardized_right_np.astype('uint8')
    
    left_np = filter_im(left_np)
    right_np = filter_im(right_np)
    
    margin = max_disp
    
    is_rotated = get_is_rotated(left_np, right_np, left_invalid_np)
    
    if (is_rotated):
        left_np = np.rot90(left_np)
        right_np = np.rot90(right_np)
        left_undefined_np = np.rot90(left_undefined_np)
        right_undefined_np = np.rot90(right_undefined_np)
        left_invalid_np = np.rot90(left_invalid_np)
        right_invalid_np = np.rot90(right_invalid_np)
        standardized_left_np = np.rot90(standardized_left_np)
        standardized_right_np = np.rot90(standardized_right_np)
    
    left_np = add_margin(left_np, margin)
    right_np = add_margin(right_np, margin)
    standardized_left_np = add_margin(standardized_left_np, margin)
    standardized_right_np = add_margin(standardized_right_np, margin)
    left_undefined_np = add_margin(left_undefined_np, margin, True)
    right_undefined_np = add_margin(right_undefined_np, margin, True)
    left_invalid_np = add_margin(left_invalid_np, margin, True)
    right_invalid_np = add_margin(right_invalid_np, margin, True)
    
    if (is_debug_mode):
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-L.png', left_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-R.png', right_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-L-std.png', standardized_left_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-R-std.png', standardized_right_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-L-invalid.png', left_invalid_np)
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-R-invalid.png', right_invalid_np)
    
    

    left_disp, right_disp, left_matcher, right_matcher = get_multiscale_disps(left_np, right_np)
    
    if (is_debug_mode):
        save_disparity(left_disp, tmp_disparity_debug_path + str(pair_id) + '-left_disparity.png')
        save_disparity(right_disp, tmp_disparity_debug_path + str(pair_id) + '-right_disparity.png')
        consistency_np = get_left_right_consistency_map(left_disp / 16.0, right_disp / 16.0, -(max_disp/2)) < 1.5
        save_disparity(consistency_np, tmp_disparity_debug_path + str(pair_id) + '-consistency.png')
    
    
    def remove_unselected(left_disp, right_disp, left_to_remove):
        positions = np.where(left_to_remove)
        ys = positions[0]
        xs = positions[1]
        for i in xrange(xs.shape[0]):
            x = xs[i]
            y = ys[i]
            disp = left_disp[y,x] / 16.0
            new_x = int(round(x + disp))
            if not(new_x < 0 or new_x >= left_disp.shape[1]):
                right_disp[y,new_x] = left_disp.shape[1] * 160
    


    pre_left_filtered_disp, pre_left_confidence_np = compute_filtered_disp(left_matcher, standardized_left_np, standardized_right_np, left_disp, right_disp, left_invalid_np, right_invalid_np, max_disp)
    pre_right_filtered_disp, pre_right_confidence_np = compute_filtered_disp(left_matcher, standardized_right_np, standardized_left_np, right_disp, left_disp, right_invalid_np, left_invalid_np, max_disp)



    if (is_debug_mode):
        save_disparity(pre_left_confidence_np, tmp_disparity_debug_path + str(pair_id) + '-left_confidence.png',1)
        save_disparity(pre_right_confidence_np, tmp_disparity_debug_path + str(pair_id) + '-right_confidence.png',1)

        save_disparity(pre_left_filtered_disp, tmp_disparity_debug_path + str(pair_id) + '-left_filtered_disparity.png')
        save_disparity(pre_right_filtered_disp, tmp_disparity_debug_path + str(pair_id) + '-right_filtered_disparity.png')
    
    
    left_filtered_disp, left_confidence_np = compute_filtered_disp(left_matcher, standardized_left_np, standardized_right_np, pre_left_filtered_disp, pre_right_filtered_disp, left_invalid_np, right_invalid_np, max_disp)
    
    right_filtered_disp, right_confidence_np = compute_filtered_disp(left_matcher, standardized_right_np, standardized_left_np, pre_right_filtered_disp, pre_left_filtered_disp, right_invalid_np, left_invalid_np, max_disp)
    
    lrc_init_np = get_left_right_consistency_map(left_disp / 16.0, right_disp / 16.0, -(max_disp/2)) < 3
    lrc_1_np = get_left_right_consistency_map(pre_left_filtered_disp / 16.0, pre_right_filtered_disp / 16.0, -(max_disp/2)) < 3
    lrc_2_np = get_left_right_consistency_map(left_filtered_disp / 16.0, right_filtered_disp / 16.0, -(max_disp/2)) < 3
    
    photoconsistency_np = get_photoconsistency_map(left_np, right_np, left_filtered_disp / 16.0, -(max_disp/2))
    
    if is_debug_mode:
        save_disparity(lrc_init_np, tmp_disparity_debug_path + str(pair_id) + '-f-consistency-init.png')
        save_disparity(lrc_1_np, tmp_disparity_debug_path + str(pair_id) + '-f-consistency-1.png')
        save_disparity(lrc_2_np, tmp_disparity_debug_path + str(pair_id) + '-f-consistency-2.png')
        
        save_disparity(left_confidence_np, tmp_disparity_debug_path + str(pair_id) + '-left_confidence_post.png')
        save_disparity(left_filtered_disp, tmp_disparity_debug_path + str(pair_id) + '-left_filtered_disparity_post.png')
        
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-photoconsistency.png', photoconsistency_np)
    
    disparity = left_filtered_disp
    
    disparity = remove_margin(disparity, margin)
    left_undefined_np = remove_margin(left_undefined_np, margin)
    photoconsistency_np = remove_margin(photoconsistency_np, margin)
    lrc_init_np = remove_margin(lrc_init_np, margin)
    lrc_1_np = remove_margin(lrc_1_np, margin)
    lrc_2_np = remove_margin(lrc_2_np, margin)
    

    if (is_rotated):
        disparity = np.rot90(disparity, 3)
        left_undefined_np = np.rot90(left_undefined_np, 3)
        photoconsistency_np = np.rot90(photoconsistency_np, 3)
        lrc_init_np = np.rot90(lrc_init_np, 3)
        lrc_1_np = np.rot90(lrc_1_np, 3)
        lrc_2_np = np.rot90(lrc_2_np, 3)
    
    left_defined_np = np.logical_not(left_undefined_np)
    
    original_width = left_infos_np[2] - left_infos_np[0]
    original_height = left_infos_np[3] - left_infos_np[1]
        
    (Yfrom, Xfrom) = np.where(left_defined_np)
    Xto, Yto, Xfrom, Yfrom = warp_coordinates(Xfrom, Yfrom, np.linalg.inv(left_M), original_width, original_height)
    
    final_defined_positions = np.logical_and(np.logical_and(Xto >= left_infos_np[4], Xto <= original_width - left_infos_np[5]), np.logical_and(Yto >= left_infos_np[6], Yto <= original_height - left_infos_np[7]))

    Xdefined = Xfrom[final_defined_positions]
    Ydefined = Yfrom[final_defined_positions]
    
    final_defined_np = np.zeros(left_defined_np.shape, dtype=bool)
    final_defined_np[Ydefined, Xdefined] = True
    
    if (is_debug_mode):
        scipy.misc.imsave(tmp_disparity_debug_path + str(pair_id) + '-final_defined.png', final_defined_np)
        final_disparity = disparity.copy()
        save_equalized_disparity(final_disparity, tmp_disparity_debug_path + str(pair_id) + '-left_filtered_disparity_final.png', final_defined_np)

    outf = np.zeros((3, disparity.shape[0], disparity.shape[1]))
    main_channel = 0
    if (is_rotated):
        main_channel = 1
    
    outf[main_channel,:,:] = -disparity
    outf[main_channel,:,:] /= 16.0
    outf[2,:,:] = final_defined_np

    np.savez_compressed(path + 'consistency', photoconsistency_np = photoconsistency_np, lrc_1_np = lrc_1_np, lrc_2_np = lrc_2_np, lrc_init_np = lrc_init_np)
    save_gtiff_3d(path + 'out-F.tif', outf)



def save_disparity(disparity, path, mult=1, equalize=False, defined=None):
    disparity = mult*disparity
    disparity_min = np.min(disparity)
    disparity_max = np.max(disparity)
    disparity_normalized = ((disparity.astype(float) - disparity_min) * 255 / (disparity_max- disparity_min)).astype('uint8')
    cv2.imwrite(path, disparity_normalized)
    
def save_equalized_disparity(disparity, path, defined):
    disp = exposure.equalize_hist(disparity,mask=defined)
    disp[np.logical_not(defined)] = np.nan
    imsave(path, disp)
    
def get_left_right_consistency_map(left_disp, right_disp, min_disp, max_disp = 80):
    consistency_mat = np.zeros(left_disp.shape)
    nb_positions = left_disp.shape[0] * left_disp.shape[1]
    positions = np.arange(nb_positions)
    xs = (positions % left_disp.shape[1]).astype(int)
    ys = (positions / left_disp.shape[1]).astype(int)
    
    reshaped_left_disp_np = left_disp.reshape(nb_positions)
    disp_xs = np.round(xs - reshaped_left_disp_np).astype(int)
    undefined_values = np.logical_or(np.logical_or(np.logical_or(np.isnan(reshaped_left_disp_np), disp_xs < 0), disp_xs >= left_disp.shape[1]), reshaped_left_disp_np < min_disp)
    disp_xs[undefined_values] = xs[undefined_values]
    
    diff = np.abs(right_disp[ys, disp_xs] + left_disp[ys, xs])
    diff[undefined_values] = max_disp
    
    consistency_mat[ys, xs] = diff
    
    return consistency_mat

def get_photoconsistency_map(left_np, right_np, left_disp, min_disp):
    consistency_mat = np.zeros(left_disp.shape)
    nb_positions = left_disp.shape[0] * left_disp.shape[1]
    positions = np.arange(nb_positions)
    xs = (positions % left_disp.shape[1]).astype(int)
    ys = (positions / left_disp.shape[1]).astype(int)
    
    reshaped_left_disp_np = left_disp.reshape(nb_positions)
    disp_xs = np.round(xs - reshaped_left_disp_np).astype(int)
    undefined_values = np.logical_or(np.logical_or(np.logical_or(np.isnan(reshaped_left_disp_np), disp_xs < 0), disp_xs >= left_disp.shape[1]), reshaped_left_disp_np < min_disp)
    disp_xs[undefined_values] = xs[undefined_values]
    
    diff = np.abs(right_np[ys, disp_xs].astype(float) - left_np[ys, xs].astype(float)) / 255.0
    diff[undefined_values] = 0
    
    consistency_mat[ys, xs] = diff
    
    return consistency_mat


    
def filter_im(im_np):
    #im_np = cv2.medianBlur(im_np, 3)
    #im_np = cv2.bilateralFilter(im_np, -1, 5, 3)
    return im_np
    

    
def gross_match(left_np, right_np):
    left_matcher = cv2.StereoBM_create(max_disp, 31)
    left_matcher.setMinDisparity(-(max_disp / 2 - 1))
    left_matcher.setUniquenessRatio(30)
    left_matcher.setSpeckleRange(1)
    left_matcher.setSpeckleWindowSize(50)
    return left_matcher.compute(left_np, right_np)
    
def get_is_rotated(ori_left_np, ori_right_np, left_invalid_np):
    left_np = ori_left_np
    right_np = ori_right_np
    
    disp_np = gross_match(left_np, right_np)
    
    left_np = np.rot90(ori_left_np)
    right_np = np.rot90(ori_right_np)
    
    rotated_disp_np = gross_match(left_np, right_np)
    
    selected_disp = disp_np[np.logical_not(left_invalid_np)]
    selected_disp = selected_disp[selected_disp > -(max_disp / 2) * 16 + 15]
    
    selected_rotated_disp = rotated_disp_np[np.rot90(np.logical_not(left_invalid_np))]
    selected_rotated_disp = selected_rotated_disp[selected_rotated_disp > -(max_disp / 2) * 16 + 15]
    
    range_disp = np.percentile(selected_disp, 80) - np.percentile(selected_disp, 20)
    range_rotated_disp = np.percentile(selected_rotated_disp, 80) - np.percentile(selected_rotated_disp, 20)
    
    disp_ratio = range_disp / max(range_rotated_disp, 1)
    nb_points_ratio = selected_disp.shape[0] * 1.0 / max(selected_rotated_disp.shape[0], 1)
    nb_points_max = max(selected_disp.shape[0], selected_rotated_disp.shape[0])
    
    if (nb_points_max < 50000):
        return False
        
    if (disp_ratio < 2.0/3.0 and nb_points_ratio < 2.0/3.0):
        return True
        
    return False
    
def get_disps(left_np, right_np, scale, uniqueness_ratio):
    left_matcher = cv2.StereoSGBM_create(minDisparity=-(max_disp / 2), numDisparities=max_disp, blockSize=scale)
    P1 = int(round(8 * scale * scale))
    P2 = int(round(32 * scale * scale))

    
    left_matcher.setMode(0)
    left_matcher.setP1(P1)
    left_matcher.setP2(P2)
    left_matcher.setUniquenessRatio(uniqueness_ratio)
    left_matcher.setSpeckleWindowSize(0)
    
    right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

    left_disp = left_matcher.compute(left_np, right_np)
    right_disp = right_matcher.compute(right_np,left_np)
    
    return left_disp, right_disp, left_matcher, right_matcher
    
def get_multiscale_disps(left_np, right_np):
    big_left_disp, big_right_disp, big_left_matcher, big_right_matcher = get_disps(left_np, right_np, block_size_disp, 0)
    return big_left_disp, big_right_disp, big_left_matcher, big_right_matcher

def add_margin(im_np, margin, val = 0):
    t_im_np = np.zeros((im_np.shape[0], im_np.shape[1] + margin * 2), dtype=im_np.dtype)
    t_im_np[:,:] = val
    t_im_np[:,margin:-margin] = im_np
    return t_im_np

def remove_margin(im_np, margin):
    return im_np[:,margin:-margin]

