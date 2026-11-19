"""Seeded generator for the synthetic JPEG image set.

Each image is a colour gradient with random shapes drawn on it and a layer of
noise blended in. No downloaded photos are used. The same seed and the same
Pillow version give byte-identical files.

Layout: <out>/<size class>/<size class>-<NN>.jpg, for example
local/images/medium/medium-00.jpg. The file name without ".jpg" is the image id.

    python -m plb.images --config config/dev.toml --out local/images
"""

from __future__ import annotations

import argparse
import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from plb.config import ImagesConfig, load_config

SIZE_CLASSES = ("small", "medium", "large")

# Quality of the generated source files. The worker always re-encodes at 80.
SOURCE_QUALITY = 90
NOISE_SHARE = 0.15


def write_image_set(images: ImagesConfig, seed: int, out_dir: str | Path) -> list[Path]:
    """Write per_class images for each size class and return their paths."""
    out_dir = Path(out_dir)
    paths = []
    for size_class in SIZE_CLASSES:
        width, height = getattr(images.resolutions, size_class)
        class_dir = out_dir / size_class
        class_dir.mkdir(parents=True, exist_ok=True)
        for index in range(images.per_class):
            image_id = f"{size_class}-{index:02d}"
            # A string seed is hashed with SHA-512, so it gives the same
            # stream on every machine and every run.
            rng = random.Random(f"{seed}:{image_id}")
            path = class_dir / f"{image_id}.jpg"
            path.write_bytes(_draw_jpeg(rng, width, height))
            paths.append(path)
    return paths


def _draw_jpeg(rng: random.Random, width: int, height: int) -> bytes:
    image = _gradient(rng, width, height)

    draw = ImageDraw.Draw(image)
    for _ in range(rng.randint(8, 20)):
        _draw_shape(draw, rng, width, height)

    noise = Image.frombytes("RGB", (width, height), rng.randbytes(width * height * 3))
    image = Image.blend(image, noise, NOISE_SHARE)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=SOURCE_QUALITY)
    return buffer.getvalue()


def _gradient(rng: random.Random, width: int, height: int) -> Image.Image:
    ramp = Image.linear_gradient("L").rotate(rng.uniform(0, 360), fillcolor=128)
    ramp = ramp.resize((width, height))
    return ImageOps.colorize(ramp, black=_colour(rng), white=_colour(rng))


def _draw_shape(draw: ImageDraw.ImageDraw, rng: random.Random, width: int, height: int) -> None:
    x0, x1 = sorted(rng.randrange(width) for _ in range(2))
    y0, y1 = sorted(rng.randrange(height) for _ in range(2))
    kind = rng.choice(("ellipse", "rectangle", "polygon"))
    if kind == "ellipse":
        draw.ellipse((x0, y0, x1, y1), fill=_colour(rng))
    elif kind == "rectangle":
        draw.rectangle((x0, y0, x1, y1), fill=_colour(rng))
    else:
        points = [(rng.randrange(width), rng.randrange(height)) for _ in range(rng.randint(3, 6))]
        draw.polygon(points, fill=_colour(rng))


def _colour(rng: random.Random) -> tuple[int, int, int]:
    return (rng.randrange(256), rng.randrange(256), rng.randrange(256))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate the seeded synthetic image set.")
    parser.add_argument("--config", required=True, help="config TOML file")
    parser.add_argument("--out", required=True, help="output folder")
    parser.add_argument("--seed", type=int, help="override seeds.image_set from the config")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    seed = args.seed if args.seed is not None else config.seeds.image_set
    if seed is None:
        parser.error("seeds.image_set is unset in the config; pass --seed")
    paths = write_image_set(config.images, seed, args.out)
    print(f"wrote {len(paths)} images to {args.out} (seed {seed})")


if __name__ == "__main__":
    main()
