from pathlib import Path
import shutil

from skimage.io import imread
import numpy as np
from numpy.testing import (assert_array_almost_equal,
                           assert_array_equal, assert_equal)
from scipy.spatial.transform import Rotation

from tadataka.interpolation import interpolation
from tadataka.dataset.new_tsukuba import (
    NewTsukubaDataset, load_depth, generate_depth_cache, generate_image_cache)
from tadataka.warp import Warp2D

from tests.dataset.path import new_tsukuba


def test_generate_image_cache():
    image_dir = Path(new_tsukuba, "illumination", "daylight")
    cache_dir = Path(new_tsukuba, "illumination", "daylight_cache")

    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    def check(subdir):
        print(Path(image_dir, subdir))
        image_paths = list(Path(image_dir, subdir).glob("*.png"))
        assert(len(image_paths) == 5)

        for image_path in image_paths:
            filename = image_path.name.replace(".png", ".npy")
            cache_path = Path(cache_dir, subdir, filename)
            assert(cache_path.exists())

            image_map = imread(image_path)
            cache_map = np.load(cache_path)
            assert_array_equal(image_map, cache_map)

    generate_image_cache(image_dir, cache_dir)

    check("left")
    check("right")

    # cleanup
    shutil.rmtree(cache_dir)


def test_generate_depth_cache():
    depth_dir = Path(new_tsukuba, "groundtruth", "depth_maps")
    cache_dir = Path(new_tsukuba, "groundtruth", "depth_cache")

    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    def check(subdir):
        depth_paths = list(Path(depth_dir, subdir).glob("*.xml"))
        assert(len(depth_paths) == 5)

        for depth_path in depth_paths:
            filename = depth_path.name.replace(".xml", ".npy")
            cache_path = Path(cache_dir, subdir, filename)
            assert(cache_path.exists())

            depth_map = load_depth(depth_path)
            cache_map = np.load(cache_path)
            assert_array_equal(depth_map, cache_map)

    generate_depth_cache(depth_dir, cache_dir)

    check("left")
    check("right")

    # cleanup
    shutil.rmtree(cache_dir)


def test_new_tsukuba_stereo():
    dataset = NewTsukubaDataset(new_tsukuba)

    assert_equal(len(dataset), 5)

    L, R = dataset[0]
    image_shape = (480, 640, 3)
    assert_equal(L.image.shape, image_shape)
    assert_equal(R.image.shape, image_shape)
    assert_equal(L.depth_map.shape, image_shape[0:2])
    assert_equal(R.depth_map.shape, image_shape[0:2])

    L, R = dataset[4]
    translation_true = np.array([-51.802731, -4.731323, 105.171677])
    degrees_true = np.array([16.091024, 10.583960, -0.007110])
    rotation_true = Rotation.from_euler('xyz', degrees_true, degrees=True)

    pose_l = L.pose
    assert_array_almost_equal(
        pose_l.t,
        translation_true + np.dot(rotation_true.as_matrix(), [-5, 0, 0])
    )
    assert_array_almost_equal(
        pose_l.rotation.as_euler('xyz', degrees=True),
        degrees_true
    )

    pose_r = R.pose
    assert_array_almost_equal(
        pose_r.t,
        translation_true + np.dot(rotation_true.as_matrix(), [5, 0, 0])
    )
    assert_array_almost_equal(
        pose_r.rotation.as_euler('xyz', degrees=True),
        degrees_true
    )


def test_new_tsukuba_warp():
    def run(frame0, frame1, us0, threshold):
        warp = Warp2D(frame0.camera_model, frame1.camera_model,
                      frame0.pose, frame1.pose)

        depths0 = np.array([frame0.depth_map[y, x] for x, y in us0])

        us1, depths1 = warp(us0, depths0)

        d = depths1 - interpolation(frame1.depth_map, us1)
        assert((np.abs(d) < threshold).all())

    dataset = NewTsukubaDataset(new_tsukuba)

    frame0, _ = dataset[0]
    frame1, _ = dataset[4]

    run(frame0, frame1,
        np.array([
            [500, 300],
            [300, 140]
        ]),
        threshold=0.2)

    frame0, _ = dataset[0]
    _, frame1 = dataset[3]

    run(frame0, frame1,
        np.array([
            [100, 200],
            [300, 440]
        ]),
        threshold=0.1)
