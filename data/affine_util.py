# zyx add
from __future__ import print_function
import torch
import numpy as np
from PIL import Image
import inspect
import re
import numpy as np
import os
import collections

import cv2

# Converts a Tensor into a Numpy array
# |imtype|: the desired type of the converted numpy array


def tensor2im(image_tensor, img_type='regular', imtype=np.uint8):
    image_numpy = image_tensor[0].cpu().float().numpy()
    if image_numpy.shape[0] == 1:
        image_numpy = np.tile(image_numpy, (3, 1, 1))
    if img_type == 'regular':
        image_numpy = (np.transpose(image_numpy, (1, 2, 0)) + 1) / 2.0 * 255.0
    else:
        image_numpy = (np.transpose(image_numpy, (1, 2, 0))) * 255.0
    return image_numpy.astype(imtype)


def diagnose_network(net, name='network'):
    mean = 0.0
    count = 0
    for param in net.parameters():
        if param.grad is not None:
            mean += torch.mean(torch.abs(param.grad.data))
            count += 1
    if count > 0:
        mean = mean / count
    print(name)
    print(mean)


def save_image(image_numpy, image_path):
    image_pil = Image.fromarray(image_numpy)
    image_pil.save(image_path)


def info(object, spacing=10, collapse=1):
    """Print methods and doc strings.
    Takes module, class, list, dictionary, or string."""
    methodList = [e for e in dir(object) if isinstance(
        getattr(object, e), collections.Callable)]
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    print("\n".join(["%s %s" %
                     (method.ljust(spacing),
                      processFunc(str(getattr(object, method).__doc__)))
                     for method in methodList]))


def varname(p):
    for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
        m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
        if m:
            return m.group(1)


def print_numpy(x, val=True, shp=False):
    x = x.astype(np.float64)
    if shp:
        print('shape,', x.shape)
    if val:
        x = x.flatten()
        print('mean = %3.3f, min = %3.3f, max = %3.3f, median = %3.3f, std=%3.3f' % (
            np.mean(x), np.min(x), np.max(x), np.median(x), np.std(x)))


def mkdirs(paths):
    if isinstance(paths, list) and not isinstance(paths, str):
        for path in paths:
            mkdir(path)
    else:
        mkdir(paths)


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def th_affine2d(x, matrix, output_img_width, output_img_height, center=True, is_landmarks=False):
    """
    2D Affine image transform on torch.Tensor

    """
    assert(matrix.dim() == 2)
    matrix = matrix[:2, :]
    transform_matrix = matrix.numpy()
    print(is_landmarks,"pp")
    if is_landmarks:
        x = x.squeeze()
        src = x.numpy()

        dst = np.empty((src.shape[0], 2), dtype=np.float32)
        for i in range(src.shape[0]):
            dst[i, :] = AffinePoint(np.expand_dims(
                src[i, :], axis=0), transform_matrix)

        dst = torch.from_numpy(dst).float().unsqueeze(0)

    else:

        src = x.transpose((1, 2, 0)).astype(np.uint8)
        # cols, rows, channels = src.shape
        dst = cv2.warpAffine(src, transform_matrix, (output_img_width, output_img_height),
                             cv2.INTER_LINEAR, cv2.BORDER_CONSTANT, borderValue=(127, 127, 127))
        # for gray image
        if len(dst.shape) == 2:
            dst = np.expand_dims(np.asarray(dst), axis=2)

        dst = dst.transpose((2, 0, 1))
        #dst = torch.from_numpy(dst).float()

    return dst


def th_perspect2d(x, matrix, output_img_width, output_img_height, center=True, is_landmarks=False):
    """
    2D Affine image transform on torch.Tensor

    """
    assert(matrix.dim() == 2)
    #matrix = matrix[:2,:]
    transform_matrix = matrix.numpy()

    if is_landmarks:
        x = x.squeeze()
        src = x.numpy()

        dst = np.empty((src.shape[0], 2), dtype=np.float32)
        for i in range(src.shape[0]):
            dst[i, :] = PerspectPoint(np.expand_dims(
                src[i, :], axis=0), transform_matrix)

        dst = torch.from_numpy(dst).float().unsqueeze(0)

    else:

        src = x.numpy().transpose((1, 2, 0)).astype(np.uint8)
        # cols, rows, channels = src.shape
        dst = cv2.warpPerspective(src, transform_matrix, (output_img_width, output_img_height),
                                  cv2.INTER_LINEAR, cv2.BORDER_CONSTANT, borderValue=(127, 127, 127))

        # for gray image
        if len(dst.shape) == 2:
            dst = np.expand_dims(np.asarray(dst), axis=2)

        dst = dst.transpose((2, 0, 1))
        dst = torch.from_numpy(dst).float()

    return dst


def normalize_image(input_tf, normalisation_type):
    img_normalise = np.empty(
        (input_tf.shape[0], input_tf.shape[1], input_tf.shape[2]), dtype=np.float32)
    num_channels = input_tf.shape[0]
    print(num_channels,"0000")
    print(input_tf.shape)
    #img = input_tf.numpy()
    img = input_tf

    if normalisation_type == 'channel-wise':
        for i in range(num_channels):
            mean = np.mean(img[i])
            std = np.std(img[i])
            if std < 1E-6:
                std = 1.0
            img_normalise[i] = (img[i] - mean) / std
    elif normalisation_type == 'regular':
        for i in range(num_channels):
            mean = 0.5
            std = 0.5
            img_normalise[i] = (img[i]/255. - mean) / std
    elif normalisation_type == 'heatmap':
        assert(num_channels == 1)
        for i in range(num_channels):
            img_normalise[i] = img[i]/255.

    dst = torch.from_numpy(img_normalise).float()

    return dst


def AffinePoint(point, affine_mat):
    """
    Affine 2d point
    """
    assert(affine_mat.shape[0] == 2)
    assert(affine_mat.shape[1] == 3)
    assert(point.shape[1] == 2)

    point_x = point[0, 0]
    point_y = point[0, 1]
    result = np.empty((1, 2), dtype=np.float32)
    result[0, 0] = affine_mat[0, 0] * point_x + \
        affine_mat[0, 1] * point_y + \
        affine_mat[0, 2]
    result[0, 1] = affine_mat[1, 0] * point_x + \
        affine_mat[1, 1] * point_y + \
        affine_mat[1, 2]

    return result


def PerspectPoint(point, affine_mat):
    """
    Affine 2d point
    """
    #print(point, point.shape)
    assert(affine_mat.shape[0] == 3)
    assert(affine_mat.shape[1] == 3)
    assert(point.shape[1] == 2)

    point_x = point[0, 0]
    point_y = point[0, 1]
    result = np.empty((1, 2), dtype=np.float32)
    tmp = affine_mat[2, 0] * point_x + affine_mat[2, 1] * \
        point_y + affine_mat[2, 2] + 1e-4

    result[0, 0] = (affine_mat[0, 0] * point_x +
                    affine_mat[0, 1] * point_y +
                    affine_mat[0, 2]) / tmp
    result[0, 1] = (affine_mat[1, 0] * point_x +
                    affine_mat[1, 1] * point_y +
                    affine_mat[1, 2]) / tmp

    return result


def exchange_landmarks(input_tf, corr_list):
    """
    Exchange value of pair of landmarks
    """
    for i in range(corr_list.shape[0]):
        temp = input_tf[0, corr_list[i][0], :].clone()
        input_tf[0, corr_list[i][0], :] = input_tf[0, corr_list[i][1], :]
        input_tf[0, corr_list[i][1], :] = temp

    return input_tf
