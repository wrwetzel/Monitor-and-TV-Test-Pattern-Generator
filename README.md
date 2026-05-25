# Monitor / TV Test Pattern Generator

The `mk-patterns.py` program generates images files containing test patterns (currently 206)
for assessing the performance of computer monitors, televisions, and other display devices.
The program includes built-in resolutions shown below and accepts command-line options
for user-specified resolutions. A companion shell script, `mk-patterns.sh`, runs `mk-patterns.py`
on all processors.

|Name|Resolution|
|---|---|
|Thumb | 160x100|
|FHD | 1920x1080|
|HD | 1280x720|
|HD+ | 1600x900|
|NTSC | 720x480|
|PAL | 720x576|
|QHD | 2560x1440|
|SXGA | 1280x1024|
|UHD | 3840x2160|
|UXGA | 1600x1200|
|WQXGA | 2560x1600|
|WSXGA+ | 1680x1050|
|WUXGA | 1920x1200|
|WXGA | 1280x800|
|WXGA+ | 1440x900|
|XGA | 1024x768|
|8k-UHD * | 7680x4320 |

This site includes only the generator program, no generated patterns. Those are available as zip
files at: [https://patterns.wrwetzel.com](https://patterns.wrwetzel.com) for all 206
patterns in each of the above resolutions. That site includes a brief description of all patterns.

\* Note that the 8k-UHD file is huge, 245.4 MBytes.

## Viewing Resolution
Pattern resolution is intended to match native resolution of the display.
At any other resolutions where the pattern size is scaled to the display
scaling artifacts will render many patterns useless.  If your viewing
program supports a scaling factor of 1:1, that is, one pixel in the image
maps to one pixel in the display, then patterns not matching the display
resolution will show without artifacts but intent of some of the patterns
will not be realized.

## Usage

*mk-patterns.py* generates one or more families of image files of format
determined by an internal list or given by the `-x` and `-y` options.  
See *Generated Files* below for information about the location and naming
of generated files.


```
mk-patterns.py [-t] [-v] [-V] [-h] [-o output_dir] [-c output_type] [-x user_width] [-y user_height]

-o output_dir
    Saves output images in output_dir, default "Output" in the home directory.

-c output_type
    Generate images in give output type, default "png". Supported types include:
        bmp eps gif im jpg msp palm pcx pdf png ppm spider tif xbm

-x user_width
-y user_height
    Generates one set of images of shape user_width x user_height (in
    pixels) and family name "User" when both options are given.  No text
    is included in images with a horizontal size smaller than 200 pixels
    for thumbnails.  Text in images between that size and common screen
    sizes may be sub-optimal.

-u user_text
    Includes "user_text" in the output directory and file names, default "User".

-v
    Verbose. Displays names of output files and more to stdout.

-V
    Displays version and names of default output shapes.

-h
    Help. This message.

-t test
    Generates a subset of all tests for development testing

-f first
-s step
    Start with shape identified by index "first" and advance to next shape by adding "step" to index.
    Used by mk-patterns.sh to distribute generation across all processors.
```

## Generated Files

The generated files are written to a directory tree rooted at `~/Output` or as specified by the
`-o output_dir` option.

The first level of the tree contains a directory for each of the
above resolutions. The directories are named with a
descriptive resolution identifier taken from a
[Wikipedia article](https://en.wikipedia.org/wiki/Computer_display_standard)
and the numeric resolution. Example: `UXGA-1600x1200`

The second level of the tree each contains 206 image files at the resolution
indicated by the directory name. The image file names start with the directory
name described above followed by a brief description of the file content.
Example: `UXGA-1600x1200-Check-Composite.png`, `UXGA-1600x1200-Geometry-Checkers-Log.png`,
and `UXGA-1600x1200-Wipe-Rgb-Fix-Blue-127-Var-Red-Green.png`.

The use of the term *checkers* in the image name is unrelated to the term *check*.
*Checkers* refers to an
alternating black/white pattern similar to a checkers board and is frequently used with gamma patterns. 
*Check* refers to assessment or evaluation.

The description part of the file name is usually self-evident. Here is an example of one that may not be self-evident.
The `UXGA-1600x1200-Wipe-Rgb-Fix-Blue-127-Var-Red-Green.png` image is a wipe generated with RGB color specification,
a constant B value of 127, with R and G varying over the full range of 0 to 255 on the X and Y axes respectively.
Other images are generated with HSL and HSV color specifications.


## Development History
Many years ago I posted some HDTV test patterns to Flickr.  They were
quite popular, received many hits, and were probably
linked from another site but I never found where.

December-2013 - Wrote a new generating program in Python, included
several composite images, many geometric and color images, and used
descriptive file names.  These were, and continue to be, some of my most
popular images on Flickr but at Flickr they are only in a resolution of
1920x1080.

March-2023 - Converted the generating program from Python2 to Python3,
corrected a bug causing vertical lines in one of the color images, changed
the name of the image files, updated the resolutions, and added many new
patterns including the inverse of several.

29-Dec-2023 - Replaced WUXGA-1900x1200 with WUXGA-1920x1200.  Original was
in error.  Thanks, Shawn, for pointing this out. 

May-2026 - Changed the implementation of the generation of the RGB, HSV, and HSL wipes to reduce
processing time. A computed comparison of results to prior images showed no perceptual differences.
Initial release at Github. Thanks, Ava, for motivating this.
