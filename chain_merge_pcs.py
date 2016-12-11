'''
This is the second part of our chain: it merges the 3d from all the pairs...
'''
import numpy as np
from params import *
from functions import *
import scipy.spatial
import scipy.misc
from scipy import ndimage
from sklearn import linear_model
import scipy.stats
import time
import cv2
from fastkml import kml
import struct

# It starts here...
def run(kml_path, out_path):
    definition = 0.6
    
    # First, extract the bounds from the kml file...
    bounds, final_bounds, im_size, final_im_size, decal = get_bounds_and_imsize_from_kml(kml_path, definition)
    
    # Loading all 3d from pairs
    print '####### Loading PCs'
    pcs = load_PCs(bounds, im_size)

    # Aligning all the 3d using correlation
    print '####### Correcting long lats'
    try:
        reference_pair_id = correct_all_long_lat(pcs, bounds, im_size)
    except:
        log_msg('WARNING: CORRECT ALL LONG LAT FAILED...')
        reference_pair_id = 0

    # Merging all 3d...
    print '####### Get all heights'
    f_infos = get_all_heights(pcs, reference_pair_id, im_size, final_im_size, decal)
    
    if (is_debug_mode):
        start_save_time = time.time()
        np.savez_compressed('tmp/f_infos', f_infos=f_infos, bounds=final_bounds)
        print 'save time:', time.time() - start_save_time
    
    concensus_needed = int(len(pcs) * relative_consensus)
    
    print 'Consensus needed:', concensus_needed, f_infos.shape
    
    if height_map_post_process_enabled:
        post_process_f_infos(f_infos, concensus_needed)
    
    
    if (out_path[-4:] == '.npz'):
        np.savez_compressed(out_path[:-4], f_infos=f_infos, bounds=final_bounds)
    else:
        # Converting height map back to 3d positions
        spherical_c = final_heights_to_spherical_c(f_infos, final_bounds)
        save_pc(out_path, spherical_c)

def get_correlation_score(im_1_np, im_2_np):
    try:
        defined_np = np.logical_not(np.logical_or(np.isnan(im_1_np), np.isnan(im_2_np)))

        im_1_np = im_1_np[defined_np]
        im_2_np = im_2_np[defined_np]
        divider = np.sqrt(np.sum(im_1_np*im_1_np)*np.sum(im_2_np*im_2_np))
        if (divider == 0):
            return 0
        return np.sum(im_1_np * im_2_np) / divider
    except:
        return 0


def find_D(r_im_np, im_np, init_D, area_size = 20):
    w = r_im_np.shape[1]
    h = r_im_np.shape[0]
    
    scores = np.zeros((area_size * 2 + 1, area_size * 2 + 1))
    
    for x in range(-area_size, +area_size + 1):
        for y in range(-area_size, +area_size + 1):
            r_from_x = max(-x-init_D[0], 0)
            r_from_y = max(-y-init_D[1], 0)
            r_to_x = min(w-x-init_D[0],w)
            r_to_y = min(h-y-init_D[1],h)
            
            from_x = max(x+init_D[0], 0)
            from_y = max(y+init_D[1], 0)
            to_x = min(w+x+init_D[0],w)
            to_y = min(h+y+init_D[1],h)
            
            r_extract_np = r_im_np[r_from_y:r_to_y, r_from_x:r_to_x]
            extract_np = im_np[from_y:to_y, from_x:to_x]
            
            score = get_correlation_score(r_extract_np, extract_np)
            
            scores[y + area_size, x + area_size] = score
    
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(scores)
    
    Dx = maxLoc[0] + init_D[0]
    Dy = maxLoc[1] + init_D[1]
    Dx -= area_size
    Dy -= area_size
    D = [Dx, Dy]
    return D
    

def get_correlation_between_pairs(pcs, type_im = 1):
    min_scales = []
    scores = []
    
    for pair_id in xrange(len(pcs)):
        im_np = pcs[pair_id][:,:,type_im]
        min_scales.append(scipy.misc.imresize(im_np, 1.0 / 2.0, 'bilinear', 'F'))
        scores.append(0)
        if (is_debug_mode):
            imsave('tmp/mini-' + str(pair_id) + '.png', min_scales[pair_id])
    
    for pair_id in xrange(len(scores)):
        im_1_np = min_scales[pair_id]
        for second_pair_id in xrange(pair_id + 1, len(scores)):
            if (second_pair_id != pair_id):
                im_2_np = min_scales[second_pair_id]
                score = get_correlation_score(im_1_np, im_2_np)
                scores[pair_id] += score
                scores[second_pair_id] += score
     
    return scores
                
def find_Ds(ims, reference_image_id, margin):
    pyramid_scales = [4, 2, 1]
    
    r_im_np = ims[reference_image_id]
    r_pyr_ims = []
    for i in xrange(len(pyramid_scales)):
        r_pyr_ims.append(scipy.misc.imresize(r_im_np, 1.0 / pyramid_scales[i], 'bilinear', 'F'))
    
    
    Ds = []
    start_time = time.time()
    for pair_id in xrange(len(ims)):
        if (pair_id != reference_image_id):
            im_np = ims[pair_id]
            
            D = [0, 0]
            search_area = 20
            for i in xrange(len(pyramid_scales)):
                scale = pyramid_scales[i]
                pyr_im_np = scipy.misc.imresize(im_np, 1.0 / pyramid_scales[i], 'bilinear', 'F')
                init_D = [D[0] / scale, D[1] / scale]
                D = find_D(r_pyr_ims[i], pyr_im_np, init_D, search_area)
                D[0] *= scale
                D[1] *= scale
                search_area = 5
            
            Ds.append(D)
        else:
            Ds.append((0, 0))
    log_msg('Recaling time: ' + str(time.time() - start_time))
    return Ds

def save_color_map(path, color_map):
    c_map = color_map.copy()
    c_map[np.isnan(c_map)] = 0
    scipy.misc.imsave(path, c_map)
    

def decal_pc(dx, dy, pc):
    height_map = pc
    
    new_height_map = np.roll(height_map, dy, 0)
    new_height_map = np.roll(new_height_map, dx, 1)
    if (dy < 0):
        new_height_map[dy:,:,:] = np.nan
    else:
        new_height_map[:dy,:,:] = np.nan
    if (dx < 0):
        new_height_map[:,dx:,:] = np.nan
    else:
        new_height_map[:,:dx,:] = np.nan
    
    return new_height_map

def get_reference_pair(pcs, Ds):
    scores = get_correlation_between_pairs(pcs)
    
    if (len(scores) > 5):
        from_id = int(round(len(scores) / 3)) #todo: add 2.0 * 
    else:
        from_id = 0
    best_ids = np.argsort(scores)[from_id:]
    
    
    d_scores = np.zeros(best_ids.shape[0])
    i = 0
    for pair_id in best_ids:
        r_D = Ds[pair_id]
        for second_pair_id in xrange(len(pcs)):
            D = Ds[second_pair_id]
            d_scores[i] += abs(r_D[0] - D[0]) + abs(r_D[1] - D[1])
        i += 1
    reference_pair_id = best_ids[np.argmin(d_scores)]
    return reference_pair_id
    
    return reference_pair_id
    
def correct_all_long_lat(pcs, bounds, im_size):
    ims = []
    for pair_id in xrange(len(pcs)):
        color_map = pcs[pair_id][:,:,1]
        ims.append(color_map)
        if (is_debug_mode):
            save_color_map(tmp_path + str(pair_id) + '-color.png', color_map)
    margin = min(im_size[0] / 20, im_size[1] / 20)
    
    r_im_np = ims[0]
    
    print 'Computing Ds'
    
    scores = get_correlation_between_pairs(pcs)
    
    tmp_reference_pair_id = np.argmax(scores)
    
    Ds = find_Ds(ims, tmp_reference_pair_id, margin)
    
    print 'Matching all images'
    
    for pair_id in xrange(len(pcs)):
        if pair_id != tmp_reference_pair_id:
            pcs[pair_id] = decal_pc(-Ds[pair_id][0], -Ds[pair_id][1], pcs[pair_id])
    
    
    
    print 'Computing reference pair'
    reference_pair_id = get_reference_pair(pcs, Ds)
        
    
    print 'Recalling according to reference pair'
    r_D = Ds[reference_pair_id]
    for pair_id in xrange(len(pcs)):
        pcs[pair_id] = decal_pc(r_D[0], r_D[1], pcs[pair_id])
        if (is_debug_mode):
            save_color_map(tmp_path + 'D-' + str(pair_id) + '.png', pcs[pair_id][:,:,1])
    
    return reference_pair_id


def get_CPC(image_filepath, center_filepath, color_filepath, consistency_filepath, bounds, im_size):
    pc = get_PC(image_filepath, center_filepath, color_filepath, consistency_filepath)
    pair_heights = get_pair_heights(pc[1], bounds, im_size)
    
    return pair_heights
    
def load_PCs(bounds, im_size):
    start_time = time.time()
    pc_dirs = [f for f in os.listdir(tmp_stereo_output_path) if os.path.isdir(join(tmp_stereo_output_path, f))]
    
    pcs = []
    pc_i = 0
    for pc_dir in pc_dirs:
        elapsed_time = time.time() - start_time
        if (elapsed_time > merge_pcs_allocated_time):
            log_msg('TAKING TOO MUCH TIME WHEN REFERENCING PCs, skipping...')
            break
        print pc_i, '/', len(pc_dirs), '-- Elapsed time:', elapsed_time
        pc_i += 1
        pair_path = join(tmp_stereo_output_path, pc_dir)
        pc_file = pair_path + '/results/out-PC.tif'
        print 'LOADING:', pc_file
        if (os.path.isfile(pc_file)):
            try:
                pc = get_CPC(pc_file, pair_path + '/results/out-PC-center.txt', pair_path + '/results/out-L.tif', pair_path + '/results/consistency.npz', bounds, im_size)
                pcs.append(pc)
            except:
                log_msg('ERROR WHILE READING PC FILE: ' + pc_file)
        else:
            log_msg('ERROR SINCE NO PC FILE: ' + pc_file)
    
    log_msg('NB PCS: ' + str(len(pcs)))
    return pcs

    
def get_pair_heights(spherical_c, bounds, im_size):
    heights = [[[[], [], [], [], []] for j in xrange(im_size[1])] for i in xrange(im_size[0])]
    x, y = spherical_to_image_positions(spherical_c, bounds, im_size)
    x = np.round(x).astype(int)
    y = np.round(y).astype(int)
    selected = np.logical_and(np.logical_and(x >= 0, y >= 0), np.logical_and(x < im_size[1], y < im_size[0]))
    x = x[selected]
    y = y[selected]
    sel_spherical_c = spherical_c[selected]
    sel_heights = sel_spherical_c[:,0]
    sel_grays = sel_spherical_c[:,3]
    sel_lrc_init = sel_spherical_c[:,4]
    sel_lrc_1 = sel_spherical_c[:,5]
    sel_lrc_2 = sel_spherical_c[:,6]
    
    
    print '-> Listing view heights'
    for i in xrange(sel_heights.shape[0]):
        heights[y[i]][x[i]][0].append(sel_heights[i])
        heights[y[i]][x[i]][1].append(sel_grays[i])
        heights[y[i]][x[i]][2].append(sel_lrc_init[i])
        heights[y[i]][x[i]][3].append(sel_lrc_1[i])
        heights[y[i]][x[i]][4].append(sel_lrc_2[i])
        
        
    print '-> Merging view heights'
    f_heights = np.zeros((im_size[0], im_size[1], 3))
    f_heights[:] = np.nan
    for y in xrange(len(heights)):
        for x in xrange(len(heights[0])):
            height_infos = heights[y][x]
            if (len(height_infos[0]) == 0):
                continue
            
            infos = np.array(height_infos)
            max_height = np.max(infos[0,:])
            selected = infos[0,:] >= (max_height - acceptable_height_deviation)
            
            mean_infos = np.mean(infos[:,selected], 1)
            
            in_lrc_init = mean_infos[2] > 0.0001
            in_lrc_1 = mean_infos[3] > 0.0001
            in_lrc_2 = mean_infos[4] > 0.0001
    
            in_both = in_lrc_1 and in_lrc_2
            in_three = in_both and in_lrc_init
            
            lrc_val = 0
            if (in_both):
                lrc_val = 1
            if (in_three):
                lrc_val = 2
            
            f_heights[y,x,0] = float(mean_infos[0])
            f_heights[y,x,1] = float(mean_infos[1])
            f_heights[y,x,2] = lrc_val
            
    print '-> View heights merged'
    return f_heights

def correct_heights(pc, reference_pc):
    height_np = pc[:,:,0]
    r_height_np = reference_pc[:,:,0]
    
    selected = np.logical_not(np.logical_or(np.isnan(height_np), np.isnan(r_height_np)))
    
    if (np.sum(selected) > 0):
        diff = np.median(r_height_np[selected] - height_np[selected])

        pc[:,:,0] += diff
    

def get_all_heights(pcs, reference_pair_id, im_size, final_im_size, decal):
    
    (dy, dx) = decal
    
    for pair_id in xrange(len(pcs)):
        print pair_id, '/', len(pcs)
        if pair_id != reference_pair_id:
            correct_heights(pcs[pair_id], pcs[reference_pair_id])
        
        if (is_debug_mode):
            pair_heights = pcs[pair_id]
            imsave('tmp/F-' + str(pair_id) + '.png', pair_heights[:,:,0])
            np.save('tmp/FF-' + str(pair_id), pair_heights[:,:,0])

    print '-> Merging'
    f_infos = np.zeros((final_im_size[0], final_im_size[1], 3))
    f_infos[:] = np.nan
    progression = 0
    nb_total = final_im_size[0] * final_im_size[1]
    for y in xrange(final_im_size[0]):
        from_y = y + dy
        for x in xrange(final_im_size[1]):
            from_x = x + dx
            if (progression % (nb_total / 40) == 0):
                print progression * 100.0 / nb_total, '%'
                
            item_heights = [[],[],[]]
            for pair_id in xrange(len(pcs)):
                pair_heights = pcs[pair_id]
                if (np.isnan(pair_heights[from_y,from_x,0])):
                    continue
                
                for i in xrange(3):
                    item_heights[i].append(struct.unpack('f', struct.pack('f', pair_heights[from_y,from_x,i]))[0])
            try:
                best_interval = get_final_height_from_heights(item_heights)
            except:
                log_msg('Error when getting interval for (' + str(y) + ', ' + str(x) + ')')
                best_interval = None
            if (best_interval is not None):
                f_infos[y,x,0] = best_interval[3]
                f_infos[y,x,1] = best_interval[2][0]
                f_infos[y,x,2] = best_interval[2][1]
            progression += 1
                    
    
    
    
    return f_infos

def get_bounds_and_imsize_from_kml(kml_file, definition = 0.6, margin = 100, final_margin = 22):
    with open(kml_file, 'r') as content_file:
        content = content_file.read()
    k = kml.KML()
    k.from_string(content)
    f = list(list(k.features())[0].features())[0].geometry.bounds
    
    wgs84 = pyproj.Proj('+proj=utm +zone=21 +datum=WGS84 +south')
    lon, lat = wgs84([f[0], f[2]], [f[1], f[3]])
    
    bounds = [[0, 0], [lon[0] - margin, lon[1] + margin], [lat[0] - margin, lat[1] + margin]]
    final_bounds = [[0, 0], [lon[0] - final_margin, lon[1] + final_margin], [lat[0] - final_margin, lat[1] + final_margin]]
    
    height = int(round((bounds[1][1] - bounds[1][0]) / definition))
    width = int(round((bounds[2][1] - bounds[2][0]) / definition))
    
    final_height = int(round((final_bounds[1][1] - final_bounds[1][0]) / definition))
    final_width = int(round((final_bounds[2][1] - final_bounds[2][0]) / definition))
    
    dx = int((width - final_width) / 2)
    dy = int((height - final_height) / 2)
    
    return bounds, final_bounds, (height, width), (final_height, final_width), (dy, dx)



if __name__ == "__main__":
    nb_args = len(sys.argv)
    
    if (nb_args < 3):
        print 'Correct format: python chain_merge_pcs.py [Input KML file] [Output file]'
    else:
        kml_path = sys.argv[1]
        out_path = sys.argv[2]

        run(kml_path, out_path)


