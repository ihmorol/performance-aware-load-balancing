from PIL import Image

from plb.config import ImagesConfig, MixConfig, ResolutionsConfig
from plb.images import write_image_set

# Small resolutions keep the tests fast; the classes still differ in size.
IMAGES = ImagesConfig(
    per_class=2,
    resolutions=ResolutionsConfig(small=(64, 48), medium=(160, 90), large=(320, 180)),
    mix=MixConfig(small=0.4, medium=0.4, large=0.2),
)


def file_bytes(paths):
    return {p.relative_to(p.parents[1]).as_posix(): p.read_bytes() for p in paths}


def test_same_seed_gives_byte_identical_files(tmp_path):
    first = write_image_set(IMAGES, seed=7, out_dir=tmp_path / "a")
    second = write_image_set(IMAGES, seed=7, out_dir=tmp_path / "b")

    assert len(first) == 6
    assert file_bytes(first) == file_bytes(second)


def test_different_seed_gives_different_files(tmp_path):
    first = file_bytes(write_image_set(IMAGES, seed=7, out_dir=tmp_path / "a"))
    second = file_bytes(write_image_set(IMAGES, seed=8, out_dir=tmp_path / "b"))

    assert first.keys() == second.keys()
    assert all(first[name] != second[name] for name in first)


def test_each_file_has_the_resolution_of_its_class(tmp_path):
    paths = write_image_set(IMAGES, seed=7, out_dir=tmp_path)

    expected = {"small": (64, 48), "medium": (160, 90), "large": (320, 180)}
    for path in paths:
        with Image.open(path) as image:
            assert image.format == "JPEG"
            assert image.size == expected[path.parent.name], path
