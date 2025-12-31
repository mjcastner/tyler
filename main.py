import os
import sys
import logging

from absl import app, flags, logging
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from tqdm import tqdm

FLAGS = flags.FLAGS
flags.DEFINE_bool(
    "debug",
    False,
    "Whether or not to output debug tiles showing Leaflet x/y/z reference example.",
)
flags.DEFINE_string(
    "input", None, "Input image file to use for the outermost zoom level of the map."
)
flags.DEFINE_string(
    "output", "output", "Output folder, relative to local execution path"
)
flags.DEFINE_bool(
    "output_tiles",
    True,
    "Whether or not to output tile images in output_dir/tiles/",
)
flags.DEFINE_integer("min_zoom", 0, "Minimum zoom level to generate")
flags.DEFINE_integer("max_zoom", 3, "Maximum zoom level to generate")


def _save_tile_worker(args):
    segment, z, x, y, save_path, is_debug_mode = args

    if is_debug_mode:
        img = Image.new("RGB", (256, 256), color=(40, 40, 40))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 255, 255], outline="cyan", width=2)
        d.text((10, 10), f"Zoom: {z}", fill="white")
        d.text((10, 30), f"X: {x}  Y: {y}", fill="white")
        d.line([0, 0, 256, 256], fill="gray", width=1)
    else:
        img = segment.resize((256, 256), Image.Resampling.LANCZOS)

    if save_path:
        img.save(save_path)

    return (z, x, y)


def generate_tiles(root_image, min_z, max_z, is_debug=False):
    if not is_debug:
        if not root_image or not os.path.exists(root_image):
            raise ValueError(f"File not found: {root_image}")
        logging.info(f"Loading High-Res Base: {root_image}")
        Image.MAX_IMAGE_PIXELS = None  # Disable decompression bomb check for large maps
    else:
        logging.info("Running in DEBUG mode (Synthesizing tiles)")

    from contextlib import nullcontext

    source_context = Image.open(root_image) if not is_debug else nullcontext()

    with source_context as root_img_source:
        src_w, src_h = 0, 0
        if not is_debug:
            root_img_source = root_img_source.convert("RGB")
            src_w, src_h = root_img_source.size
            logging.info(f"Source Dimensions: {src_w}x{src_h} px")

        total_tiles = sum(4**z for z in range(min_z, max_z + 1))
        max_workers = min(32, (os.cpu_count() or 1) + 4)

        def tile_task_generator():
            for z in range(min_z, max_z + 1):
                dim = 2**z
                step_w = (src_w / dim) if not is_debug else 0
                step_h = (src_h / dim) if not is_debug else 0
                z_path = os.path.join(FLAGS.output, "tiles", str(z))
                if FLAGS.output_tiles:
                    os.makedirs(z_path, exist_ok=True)

                for x in range(dim):
                    if FLAGS.output_tiles:
                        x_path = os.path.join(z_path, str(x))
                        os.makedirs(x_path, exist_ok=True)

                    for y in range(dim):
                        save_path = None
                        if FLAGS.output_tiles:
                            save_path = os.path.join(x_path, f"{y}.png")

                        segment = None

                        if not is_debug:
                            left = int(x * step_w)
                            upper = int(y * step_h)
                            right = int((x + 1) * step_w)
                            lower = int((y + 1) * step_h)
                            if right - left < 1 or lower - upper < 1:
                                continue

                            segment = root_img_source.crop(
                                (left, upper, right, lower)
                            ).copy()

                        yield (segment, z, x, y, save_path, is_debug)

        logging.info(f"Starting generation on {max_workers} threads...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results_iterator = executor.map(_save_tile_worker, tile_task_generator())
            for _ in tqdm(
                results_iterator, total=total_tiles, unit="tile", desc="Generating"
            ):
                pass

    logging.info("Processing Complete.")


def main(argv):
    del argv
    try:
        os.makedirs(FLAGS.output, exist_ok=True)
        if FLAGS.output_tiles:
            os.makedirs(os.path.join(FLAGS.output, "tiles"), exist_ok=True)
    except Exception as e:
        raise ValueError(f"Unable to create output directory: {e}")

    if FLAGS.debug:
        generate_tiles(
            root_image=None, min_z=FLAGS.min_zoom, max_z=FLAGS.max_zoom, is_debug=True
        )
    else:
        if not FLAGS.input:
            raise ValueError("Flag --input is required unless --debug is set.")

        generate_tiles(
            root_image=FLAGS.input,
            min_z=FLAGS.min_zoom,
            max_z=FLAGS.max_zoom,
            is_debug=False,
        )


if __name__ == "__main__":
    app.run(main)
