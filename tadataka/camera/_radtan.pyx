import numpy as np
cimport numpy as cnp


cdef extern from "_radtan_distort_jacobian.h":
    void distort_jacobian(double *dist_coeffs, double *keypoint, double *out)


cdef extern from "_radtan_distort.h":
    void distort(double *dist_coeffs, double *keypoint, double *out)


def radtan_distort_jacobian(cnp.ndarray[cnp.double_t, ndim=1] keypoint,
                            cnp.ndarray[cnp.double_t, ndim=1] dist_coeffs):
    cdef cnp.ndarray[cnp.float64_t, ndim=1] out = np.empty(4, dtype=np.float64)

    distort_jacobian(&dist_coeffs[0], &keypoint[0], &out[0])
    return out.reshape((2, 2))


def distort_(cnp.ndarray[cnp.double_t, ndim=1] keypoint,
             cnp.ndarray[cnp.double_t, ndim=1] dist_coeffs):
    cdef cnp.ndarray[cnp.float64_t, ndim=1] out = np.empty(2, dtype=np.float64)

    distort(&dist_coeffs[0], &keypoint[0], &out[0])
    return out


def radtan_distort(cnp.ndarray[cnp.double_t, ndim=2] keypoints,
                   cnp.ndarray[cnp.double_t, ndim=1] dist_coeffs):

    keypoints = np.ascontiguousarray(keypoints, dtype=np.float64)

    for i in range(keypoints.shape[0]):
        keypoints[i] = distort_(keypoints[i], dist_coeffs)
    return keypoints


def inv2x2(cnp.ndarray[cnp.double_t, ndim=2] X):
    cdef cnp.ndarray[cnp.float64_t, ndim=2] out
    out = np.empty((2, 2), dtype=np.float64)

    a, b, c, d = X[0, 0], X[0, 1], X[1, 0], X[1, 1]
    det = a * d - b * c
    out[0, 0] = d
    out[0, 1] = -b
    out[1, 0] = -c
    out[1, 1] = a
    out = out / det
    return out


def dot(cnp.ndarray[cnp.double_t, ndim=2] A,
        cnp.ndarray[cnp.double_t, ndim=1] b,
        cnp.ndarray[cnp.double_t, ndim=1] out):
    out[0] = A[0, 0] * b[0] + A[0, 1] * b[1]
    out[1] = A[1, 0] * b[0] + A[1, 1] * b[1]
    return  # void


def error(cnp.ndarray[cnp.float64_t, ndim=1] d):
    return d[0] * d[0] + d[1] * d[1]


def undistort_(cnp.ndarray[cnp.double_t, ndim=1] keypoint,
               cnp.ndarray[cnp.double_t, ndim=1] dist_coeffs,
               int max_iter, float threshold):
    cdef cnp.ndarray[cnp.float64_t, ndim=2] J
    cdef cnp.ndarray[cnp.float64_t, ndim=1] r
    cdef cnp.ndarray[cnp.float64_t, ndim=1] d = np.empty(2)
    cdef cnp.ndarray[cnp.float64_t, ndim=1] p = np.copy(keypoint)

    for i in range(max_iter):
        J = radtan_distort_jacobian(p, dist_coeffs)
        r = keypoint - distort_(p, dist_coeffs)
        # d = inv(J.T * J) * J.T * r
        # J.T * J * d = J.T * r
        # J * d = r
        # if J is a square matrix
        # d = inv(J) * r
        dot(inv2x2(J), r, d)

        if error(d) < threshold:
            break

        p = p + d
    return p


def radtan_undistort(cnp.ndarray[cnp.double_t, ndim=2] keypoints,
                     cnp.ndarray[cnp.double_t, ndim=1] dist_coeffs,
                     int max_iter, float threshold):

    keypoints = np.ascontiguousarray(keypoints, dtype=np.float64)

    for i in range(keypoints.shape[0]):
        keypoints[i] = undistort_(keypoints[i], dist_coeffs, max_iter, threshold)
    return keypoints
