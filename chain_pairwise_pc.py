'''
This is the first part of our chain: it generates a point cloud for each pair.
'''

from functions import *
from params import *
import shutil
import functions_disparity_map
import time

# It starts here...
def run(kml_path, images_path):
    start_time = time.time()
    
    shutil.rmtree(tmp_cropped_images_path, True)
    os.mkdir(tmp_cropped_images_path)
    shutil.rmtree(tmp_stereo_output_path, True)
    shutil.rmtree(tmp_disparity_debug_path, True)
    os.mkdir(tmp_disparity_debug_path)

    # First, reference all the images we might have to process...
    images = set()
    for pair in pairs_filenames:
        images.add(pair[0])
        images.add(pair[1])

    full_images = {}
    correct_images = {}
    
    # For each image, crop them according to the kml area.
    # Save if the crop was succesful and if the full kml area was acquired.
    for image in images:
        image_path = images_path + image
        
        try:
            is_correct, is_full = generate_cropped(kml_path, image_path, tmp_cropped_images_path + image + '.tif')
        except:
            is_correct = False
            is_full = False
        
        correct_images[image] = is_correct
        full_images[image] = is_full
        
    # Reference all the pairs where the full kml area was acquired and those where it was not the case.
    full_pairs = []
    not_full_pairs = []
    for pair_filenames in pairs_filenames:
        is_correct = correct_images[pair_filenames[0]] and correct_images[pair_filenames[1]]
        if (is_correct):
            is_full = full_images[pair_filenames[0]] and full_images[pair_filenames[1]]
            if (is_full):
                full_pairs.append(pair_filenames)
            else:
                not_full_pairs.append(pair_filenames)
    
        
    # Evaluate 3d for each pair where full kml area was acquired (until time limit is reached.)
    pair_id = 0
    for pair_filenames in full_pairs:
        pair_id, can_continue = process_pair(pair_filenames, pair_id, start_time)
        if (not can_continue):
            break
        
    # If there wasn't enough pair with full kml area, try on pairs with only part of the kml area (recue mode...)
    if (pair_id < min_enough_pairs):
        log_msg('NOT ENOUGH PAIRS, TAKING NOT FULL PAIRS')
        for pair_filenames in not_full_pairs:
            pair_id, can_continue = process_pair(pair_filenames, not_full_pairs, start_time)
            if (not can_continue):
                break
                
# Pairwise processing
def process_pair_inside(pair_filenames, pair_id):
    pair = pair_filenames_to_pair(pair_filenames)
    if (os.path.exists(pair[0]) and os.path.exists(pair[1])):
        try:
            # Rectify the pair
            is_valid = generate_rectified(pair, pair_id)
        except:
            log_msg('Error during rectification, skipping...')
            is_valid = False
        if (is_valid):
            try:
                # Apply stereo algorithm on the pair to generate disparity map.
                functions_disparity_map.generate_disparity_map_from_pair(pair_filenames, pair_id)
            except:
                log_msg('Error during disparity calculation, skipping...')
                return False
            try:
                # Generated point cloud from disparity map.
                generate_pc_from_pair(pair, pair_id)
            except:
                log_msg('Error during PC calculation, skipping...')
                return False
            return True
    return False

# Container of process_pair_inside with time checking...
def process_pair(pair_filenames, pair_id, start_time):
    
    elapsed_time = time.time() - start_time
    current_pair_id = pair_id
    print 'ELAPSED TIME:', elapsed_time
    print 'PAIR ID:', pair_id
    pair_start_time = time.time()
    
    # If we have enough 3d from pairs, or if too much time has passed, return and proceed...
    if (pair_id >= max_enough_pairs or (pair_id > 0 and ((elapsed_time > chain_pairwise_pc_allocated_time_not_enough) or (elapsed_time > chain_pairwise_pc_allocated_time and pair_id >= min_enough_pairs)))):
        return pair_id, False
    
    is_generated = process_pair_inside(pair_filenames, pair_id)
    if (is_generated):
        pair_id += 1
    else:
        pair_path = tmp_stereo_output_path + str(pair_id)
        if (os.path.exists(pair_path)):
            shutil.rmtree(pair_path, True)
    log_msg('PAIR ' + str(current_pair_id) + ' PROCESSING TIME: ' + str(time.time() - pair_start_time))
    return pair_id, True
    

if __name__ == "__main__":
    nb_args = len(sys.argv)

    if (nb_args < 3):
        print 'Correct format: python chain_pairwise_pc.py [Input KML file] [Path to NITF image folder]'
    else:
        kml_path = sys.argv[1]
        images_path = sys.argv[2]

        if (images_path[-1] != '/'):
            images_path += '/'

        run(kml_path, images_path)
