# tyler
A leaflet utility that generates map tiles from a single hi-res image. A "tiler", if you will.

## Getting started

```
 main.py:
  --[no]debug: Whether or not to output debug tiles showing Leaflet x/y/z reference example.
    (default: 'false')
  --input: Input image file to use for the outermost zoom level of the map.
  --max_zoom: Maximum zoom level to generate
    (default: '3')
    (an integer)
  --min_zoom: Minimum zoom level to generate
    (default: '0')
    (an integer)
  --output: Output folder, relative to local execution path
    (default: 'output')
  --[no]output_tiles: Whether or not to output tile images in output_dir/tiles/
    (default: 'true')
```

### 1. Install requirements

```
pip install -r requirements.txt
```

### 1. Generate tiles

Example invocation, point to a single high-quality image and it will generate tiles in output/tiles that can be used with Leaflet and other map tiling servers. Start with max_zoom 5-7, anything beyond 10x becomes exponentially difficult / millions
of tiles!

```
python main.py --input ~/Downloads/night_city_map_hq.png --max_zoom 7
```