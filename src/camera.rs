use ndarray::{arr1, arr2, Array, Array1, Array2, ArrayBase, Data, Ix1, Ix2};

#[derive(Clone)]
pub struct CameraParameters {
     pub focal_length: Array1<f64>,
     pub offset: Array1<f64>
}

impl CameraParameters {
    pub fn new(focal_length: (f64, f64), offset: (f64, f64)) -> Self {
        let (fx, fy) = focal_length;
        let (ox, oy) = offset;
        CameraParameters { focal_length: arr1(&[fx, fy]), offset: arr1(&[ox, oy]) }
    }

    fn matrix(&self) -> Array2<f64> {
        let fx = self.focal_length[0];
        let fy = self.focal_length[1];
        let ox = self.offset[0];
        let oy = self.offset[1];
        arr2(&[[fx, 0., ox],
               [0., fy, oy],
               [0., 0., 1.]])
    }
}

pub trait Normalizer<A, D, K> {
    fn normalize(&self, keypoints: &K) -> Array<A, D>;
    fn unnormalize(&self, keypoints: &K) -> Array<A, D>;
}

impl<S> Normalizer<f64, Ix2, ArrayBase<S, Ix2>> for CameraParameters
where
    S: Data<Elem = f64>,
{
    fn normalize(&self, keypoints: &ArrayBase<S, Ix2>) -> Array<f64, Ix2> {
        let n = keypoints.shape()[0];
        let focal_length = self.focal_length.broadcast((n, 2)).unwrap();
        let offset = self.offset.broadcast((n, 2)).unwrap();
        (keypoints - &offset) / focal_length
    }

    fn unnormalize(&self, keypoints: &ArrayBase<S, Ix2>) -> Array<f64, Ix2> {
        let n = keypoints.shape()[0];
        let focal_length = self.focal_length.broadcast((n, 2)).unwrap();
        let offset = self.offset.broadcast((n, 2)).unwrap();
        keypoints * &focal_length + &offset
    }
}

impl<S> Normalizer<f64, Ix1, ArrayBase<S, Ix1>> for CameraParameters
where
    S: Data<Elem = f64>,
{
    fn normalize(&self, keypoints: &ArrayBase<S, Ix1>) -> Array<f64, Ix1> {
        (keypoints - &self.offset) / &self.focal_length
    }

    fn unnormalize(&self, keypoints: &ArrayBase<S, Ix1>) -> Array<f64, Ix1> {
        keypoints * &self.focal_length + &self.offset
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalizer() {
        let camera_params = CameraParameters::new((10., 20.), (2., 4.));

        let normalized = arr2(&[
            [1.0, 1.0],
            [-0.2, -0.2],
            [0.6, 0.3]
        ]);

        let unnormalized = arr2(&[
            [12., 24.],
            [0., 0.],
            [8., 10.]
        ]);

        assert_eq!(camera_params.normalize(&unnormalized), normalized);
        assert_eq!(camera_params.unnormalize(&normalized), unnormalized);

        let normalized = arr1(&[1.0, 1.0]);
        let unnormalized = arr1(&[12., 24.]);

        assert_eq!(camera_params.normalize(&unnormalized), normalized);
        assert_eq!(camera_params.unnormalize(&normalized), unnormalized);

        let normalized = arr1(&[-0.2, -0.2]);
        let unnormalized = arr1(&[0., 0.]);

        assert_eq!(camera_params.normalize(&unnormalized), normalized);
        assert_eq!(camera_params.unnormalize(&normalized), unnormalized);
    }

    #[test]
    fn test_camera() {
        let c = CameraParameters::new((1.0, 1.2), (0.8, 0.2));
        let expected = arr2(
            &[[1.0, 0.0, 0.8],
              [0.0, 1.2, 0.2],
              [0.0, 0.0, 1.0]]
        );

        assert_eq!(c.matrix(), expected);
    }
}
