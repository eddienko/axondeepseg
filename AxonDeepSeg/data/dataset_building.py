import os
import shutil
from scipy.misc import imread, imsave
from sklearn import preprocessing
from skimage.transform import rescale
import random
from ..config import general_pixel_size, path_matlab, path_axonseg
import numpy as np
from patch_extraction import extract_patch


def build_dataset(path_data, trainingset_path, trainRatio = 0.80, thresh_indices = [0,0.8], random_seed = None):
    """
    :param path_data: folder including all images used for the training. Each image is represented by a a folder
    including image.png and mask.png (ground truth) and a .txt file named pixel_size_in_micrometer.
    :param trainingset_path: path of the resulting trainingset
    :param trainRatio: ratio of the training patches over the total . (High ratio : good learning but poor estimation of the performance)
    :param thresh_indices: list of float in [0,1[.

    WARNING with 3 classes, labels should be [0,0.1,0.8], it was designed for .jpeg
    :param random_seed: the random seed to use when generating the dataset. Enables to generate the same train and validation set if given the same raw dataset.
    
    :return: no return

    Every 256 by 256 patches are extracted from the images with a very low overlapping.
    They are regrouped by category folder : \Train and \Validation.
    Each data is represented by the patch, image_i.png, and its groundtruth, mask_i.png
    A rescaling is also added to set the pixel size at the value of the general_pixel_size
    """
    
    random.seed(random_seed) #Setting the random seed in order to get reproducible results.
    
    i = 0
    for root in os.listdir(path_data)[:]:

        if '.DS_Store' not in root :
            subpath_data = os.path.join(path_data, root)

            file = open(subpath_data+'/pixel_size_in_micrometer.txt', 'r')
            pixel_size = float(file.read())
            rescale_coeff = pixel_size/general_pixel_size # Used to set the resolution to the general_pixel_size

            for data in os.listdir(subpath_data):
                if 'image' in data:
                    img = imread(os.path.join(subpath_data, data), flatten=False, mode='L')
                    img = (rescale(img, rescale_coeff)*256).astype(int)
                elif 'mask' in data:
                    mask_init = imread(os.path.join(subpath_data, data), flatten=False, mode='L')
                    mask = (rescale(mask_init, rescale_coeff)*256)

                    # Set the mask values to the classes' values
                    for indice,value in enumerate(thresh_indices[:-1]):
                        if np.max(mask) > 1.001: # because of numerical values.
                            thresh_inf = np.int(255*value)
                            thresh_sup = np.int(255*thresh_indices[indice+1])
                        else:
                            thresh_inf = value
                            thresh_sup = thresh_indices[indice+1]   

                        mask[(mask >= thresh_inf) & (mask < thresh_sup)] = np.mean([value,thresh_indices[indice+1]])

                    mask[mask>=thresh_sup] = 1

            if i == 0:
                patches = extract_patch(img, mask, 256)
            else:
                patches += extract_patch(img, mask, 256)
            i+=1

    validationRatio = 1-trainRatio
    size_validation = int(validationRatio*len(patches))

    random.shuffle(patches)
    patches_train = patches[:-size_validation]
    patches_validation = patches[-size_validation:]

    if not os.path.exists(trainingset_path):
        os.makedirs(trainingset_path)
        os.makedirs(trainingset_path+'/raw/')
        os.makedirs(trainingset_path+'/testing/')
        

    folder_train = trainingset_path+'/training/Train'

    if os.path.exists(folder_train):
        shutil.rmtree(folder_train)
    if not os.path.exists(folder_train):
        os.makedirs(folder_train)

    folder_validation = trainingset_path+'/training/Validation' # change to Validation.

    if os.path.exists(folder_validation):
        shutil.rmtree(folder_validation)
    if not os.path.exists(folder_validation):
        os.makedirs(folder_validation)

    j = 0
    for patch in patches_train:
        imsave(folder_train+'/image_%s.png'%j, patch[0],'png')
        imsave(folder_train+'/mask_%s.png'%j, patch[1],'png')
        j += 1

    k=0
    for patch in patches_validation:
        imsave(folder_validation+'/image_%s.png'%k, patch[0], 'png')
        imsave(folder_validation+'/mask_%s.png'%k, patch[1], 'png')
        k += 1


