import numpy as np
from skimage import data
from skimage.color import rgb2gray

from tadataka.gradient import grad_x, grad_y


# it is very hard to test 'compute_image_curvature'
# so separate the grad computation from it
def compute_curvature(fx, fy, fxx, fxy, fyx, fyy):
    f2y = fy * fy
    f2x = fx * fx
    return f2y * fxx - fx * fy * fxy - fy * fx * fyx + f2x * fyy


def compute_image_curvature(image):
    assert(np.ndim(image) == 2)

    gx = grad_x(image)
    gy = grad_y(image)

    gxx = grad_x(gx)
    gxy = grad_y(gx)
    gyx = grad_x(gy)
    gyy = grad_y(gy)

    return compute_curvature(gx, gy, gxx, gxy, gyx, gyy)


def extract_curvature_extrema(image, percentile=95):
    curvature = compute_image_curvature(rgb2gray(image))
    threshold = np.percentile(curvature, percentile)
    ys, xs = np.where(curvature > threshold)
    return np.vstack((xs, ys)).T
