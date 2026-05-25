#!/usr/bin/python
# -----------------------------------------------------------------------------------
#   mk-patterns.py

#   Make display test patterns using the Python Image library
#   WRW 21 Dec 2013

#   WRW 12 Mar 2023
#       Convert to python3 with 2to3 -1
#           Almost all changes were xrange() -> range()
#           A few map() to comprehensions
#                - color = map( lambda x: int( x * 255 ), colorsys.hsv_to_rgb(h, s, v))
#                + color = [int( x * 255 ) for x in colorsys.hsv_to_rgb(h, s, v)]
#           And, of course, print -> print()

#       Changed names of output files for TV resolutions.
#       Added monitor resolution, removed couple of TV resolution.

#       Added int() to a few divisions that were producing floats with type conflicts.
#       Changed PIL textsize() to textlength(). No.
#           textsize() returned (width, height), textlength() return width.
#           Instead, added my_textsize() to deal with this using textbox()

#       Fixed old bug with gaps in continuous vertical bar pattern.
#       Cleaned up code, remove most globals.
#       Added fill= to several d.point() calls for consistency when only fill tuple was given. Probably unnecessary.
#       Added inverse images for several images for black against white, possible blooming.

#   WRW 29 Dec 2023
#       Changed WUXGA-1900x1200 to WUXGA-1920x1200 per suggestion from user 'Shawn'.
#       Ran only the above and uploaded to site, deleted WUXGA-1920x1200.

#   WRW 24-May-2026
#       Following query by user who found the patterns online: I re-tested the code to be sure
#       compatibility with current Python 3.14.4 - all OK. I decided to ask Claude for help
#       with the wipe-generating functions using d.point(). Claude made a significant
#       improvement in execution time of these functions. The output of the original
#       and improved functions differed by at most one pixel value at positions in the image
#       most likely related to accumulation error boundaries in the old algorithm.

#       On 12-core laptop:
#       ________________________________________________________
#       Executed in  158.05 secs    fish           external
#          usr time  797.96 secs  749.00 micros  797.96 secs
#          sys time   14.39 secs  198.00 micros   14.39 secs

# -----------------------------------------------------------------------------------

import os
import sys
import getopt
import random
import math
import colorsys
import time
import numpy as np
from datetime import date
from pathlib import Path
from PIL import Image               # WRW 12 Mar 2023 - Added 'from PIL'
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

# -----------------------------------------------------------------------------------
#   A couple of global variables. Remainder below are constants.
#   writer, text_flag have to be a global because I'm too lazy to add an extra argument to
#       all of the mk_*() functions.

version_str = "1.0"         # WRW 12 Mar 2023 - from Beta 0.3
version_str = "1.0.1"       # WRW 29 Dec 2023 - for change 1900x1200 -> 1920x1200
version_str = "1.0.2"       # WRW 24-May-2026 - for update wipe generation algorithm

writer = None               # Class object for output.
text_flag = False           # True if image size big enough for text annotation.

# -----------------------------------------------------------------------------------
#   Return the inversion of a tuple

def invert( pat ):
    return [ ~b & 0xff for b in pat ]

# -----------------------------------------------------------------------------------

#   8x8 patterns. Bits of byte are horizontal, each byte is a line.
#       ( "ff", "ff", "ff", "ff", "ff", "ff", "ff", "ff" ),     # Solid, not interesting
#       A couple of patterns are duplicates with unique names for consistent naming.
#       Omit them from the list of patterns
#   WRW 13 Mar 2023 - Using tuple of bytes instead of strings as in example above.

pat_hlines_2 = ( 0xff, 0x00, 0xff, 0x00, 0xff, 0x00, 0xff, 0x00 )     # Hlines pitch 2
pat_hlines_4 = ( 0xff, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00 )     # Hlines pitch 4
pat_hlines_8 = ( 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 )     # Hlines pitch 8

pat_vlines_2 = ( 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa )     # Vlines pitch 2
pat_vlines_4 = ( 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88 )     # Vlines pitch 4
pat_vlines_8 = ( 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80 )     # Vlines pitch 8

pat_hlines_solid_4 = ( 0xff, 0xff, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00 )     # Hlines solid pitch 4
pat_hlines_solid_8 = ( 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00 )     # Hlines solid pitch 8

pat_vlines_solid_4 = ( 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc )     # Vlines solid pitch 4
pat_vlines_solid_8 = ( 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0 )     # Vlines solid pitch 8

pat_points_2 = ( 0xaa, 0x00, 0xaa, 0x00, 0xaa, 0x00, 0xaa, 0x00 )     # Points/squares pitch 2
pat_points_4 = ( 0x88, 0x00, 0x00, 0x00, 0x88, 0x00, 0x00, 0x00 )     # Points pitch 4
pat_points_8 = ( 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 )     # Points pitch 8

pat_squares_2 = ( 0xaa, 0x00, 0xaa, 0x00, 0xaa, 0x00, 0xaa, 0x00 )     # Points/squares pitch 2
pat_squares_4 = ( 0xcc, 0xcc, 0x00, 0x00, 0xcc, 0xcc, 0x00, 0x00 )     # Squares pitch 4
pat_squares_8 = ( 0xf0, 0xf0, 0xf0, 0xf0, 0x00, 0x00, 0x00, 0x00 )     # Squares pitch 8

pat_checker_square_2 = ( 0xaa, 0x55, 0xaa, 0x55, 0xaa, 0x55, 0xaa, 0x55 )     # Checker square/point pitch 2
pat_checker_square_4 = ( 0xcc, 0xcc, 0x33, 0x33, 0xcc, 0xcc, 0x33, 0x33 )     # Checker square pitch 4
pat_checker_square_8 = ( 0xf0, 0xf0, 0xf0, 0xf0, 0x0f, 0x0f, 0x0f, 0x0f )     # Checker square pitch 8

pat_checker_point_2 = ( 0xaa, 0x55, 0xaa, 0x55, 0xaa, 0x55, 0xaa, 0x55 )     # Checker square/point pitch 2
pat_checker_point_4 = ( 0x88, 0x00, 0x22, 0x00, 0x88, 0x00, 0x22, 0x00 )     # Checker point pitch 4
pat_checker_point_8 = ( 0x80, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00 )     # Checker point pitch 8

pat_hlines_4_inv =         invert( pat_hlines_4 )
pat_hlines_8_inv =         invert( pat_hlines_8 )
pat_vlines_4_inv =         invert( pat_vlines_4 )
pat_vlines_8_inv =         invert( pat_vlines_8 )
pat_points_4_inv =         invert( pat_points_4 )
pat_points_8_inv =         invert( pat_points_8 )
pat_checker_point_4_inv =  invert( pat_checker_point_4 )
pat_checker_point_8_inv =  invert( pat_checker_point_8 )

# -----------------------------------------------------------------------------------

# pat_squares_2,          # duplicate of pat_points_2
# pat_checker_point_2,    # duplicate of pat_checker_square_2

#   Count of pats should agree with layout in mk_patterns() and mk_patterns_with_background()

background_pats = (
    pat_hlines_2, pat_hlines_4, pat_hlines_4_inv, pat_hlines_8, pat_hlines_8_inv,
    pat_vlines_2, pat_vlines_4, pat_vlines_4_inv, pat_vlines_8, pat_vlines_8_inv,

    pat_hlines_solid_4, pat_hlines_solid_8,
    pat_vlines_solid_4, pat_vlines_solid_8,

    pat_points_2, pat_points_4, pat_points_4_inv, pat_points_8, pat_points_8_inv,

    pat_squares_4, pat_squares_8,

    pat_checker_square_2, pat_checker_square_4, pat_checker_square_8,
    pat_checker_point_4, pat_checker_point_4_inv, pat_checker_point_8, pat_checker_point_8_inv,
)

composite_pats = (
    pat_hlines_2, pat_hlines_4, pat_hlines_8,
    pat_vlines_2, pat_vlines_4, pat_vlines_8,
    pat_squares_2, pat_squares_4, pat_squares_8,
    pat_checker_square_2, pat_checker_square_4, pat_checker_square_8,
)

# -----------------------------------------------------------------------------------
#   Color masks.

colors_6 = (
    ("red",      (1, 0, 0 )),
    ("green",    (0, 1, 0 )),
    ("blue",     (0, 0, 1 )),
    ("yellow",   (1, 1, 0 )),
    ("magenta",  (1, 0, 1 )),
    ("cyan",     (0, 1, 1 )),
)

colors_3 = (
    ("red",      (1, 0, 0 )),
    ("green",    (0, 1, 0 )),
    ("blue",     (0, 0, 1 )),
)

colors_6g = colors_6 + (("gray", (1, 1, 1)),)
colors_3g = colors_3 + (("gray", (1, 1, 1)),)

# -----------------------------------------------------------------------------------
#   Utility functions
# -----------------------------------------------------------------------------------
#   .png format produced many colors, not just 256 as suggested in PIL documentation
#      bits=24 made no difference, omit it. quality=80 only applies to .jpg.

#   WRW 13 Mar 2023 - Add Writer() class to encapsulate most of image output.
#   WRW 13 Mar 2023 - Use sub-directories named for pattern

class Writer():
    def __init__( self, ):
        pass

    # -------------------------------------------
    def set_output_dir( self, dir ):
        self.output_dir = dir

    # -------------------------------------------
    def set_output_type( self, type ):
        self.output_type = type

    # -------------------------------------------
    def new_shape( self, shape, verbose ):
        self.ofile_list = []
        self.res_name = shape[0]        # "HD", "XGA", etc.
        self.res_x = shape[1]
        self.res_y = shape[2]
        self.verbose = verbose
        self.res_id = "%s-%dx%d" % ( self.res_name, self.res_x, self.res_y )

        if self.verbose:
            print("Family:", self.res_id )

    # -------------------------------------------

    def get_ofile_list_len( self ):
        return len( self.ofile_list )

    def get_res_id( self ):
        return self.res_id

    # -------------------------------------------
    # Example ofile: SXGA-1280x1024-Check-Contrast-Lines.png
    # Example opath: /home/wrw/Output/XGA-1024x768/XGA-1024x768-Color-Bars-Hori-03.png

    def write( self, img, pattern_name ):
        pattern = '-'.join( [ word.title() for word in pattern_name.split( '-' )] )     # Clean up pattern name

        ofile = "%s-%s.%s" % ( self.res_id, pattern, self.output_type )     
        self.ofile_list.append( ofile )
        res_opath = Path( self.output_dir, self.res_id ).expanduser()

        if not res_opath.exists():
            res_opath.mkdir()

        opath = Path( res_opath, ofile ).as_posix()

        if self.verbose:
            print( ofile )

        try:
            if self.output_type == "jpg":
                img.save( opath, quality=80 )
            else:
                img.save( opath )

        except KeyError:
            print("Output file type not recognized:", self.output_type )
            sys.exit( 1 )

# -----------------------------------------------------------------------------------
#   Yes, I know a hack. See comment about "lazy" above.

def save_img( img, pattern_name ):
    writer.write( img, pattern_name )

# -----------------------------------------------------------------------------------
#   Convert RGB to luminance to determine when to reverse text color.
#   luma3() takes three args, luma() takes np.array arg

def luma3( r, g, b ):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def luma( a ):
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

# -----------------------------------------------------------------------------------
#   Compute bit density of pattern

def density( data ):        # data is tuple of bytes
    bitcnt = 0
    bytecnt = 0

    for b in data:
        bitcnt += b.bit_count()
        bytecnt += 1

    d = bitcnt / (8.*bytecnt)
    return d

# -----------------------------------------------------------------------------------
#   Get one cell of pattern as bitmap image.
#   At this point all patterns / cells are 8x8 pixels
#   Image.frombytes(data, decoder_name='raw', *args)[source]
#   In hindsight pat should not have been strings but bytes as 0xff.
#       pat: pat_hlines_2 = ( "ff", "00", "ff", "00", "ff", "00", "ff", "00" )     # Hlines pitch 2
#   WRW 12 Mar 2023 - A little tweaking to get to work with python3.
#   WRW 13 Mar 2023 - Converted to use tuple of bytes instead of strings.
#       i.e. pat: pat_hlines_2 = ( 0xff, 0x00, 0xff, 0x00, 0xff, 0x00, 0xff, 0x00 )     # Hlines pitch 2
#   Image.frombytes() mode of '1': 1-bit pixels, black and white, stored with one pixel per byte

def get_image_from_pattern_one( size, pat ):
    return Image.frombytes( "1", (int(size[0]), int(size[1])), bytes( pat ) )     # WRW 12 Mar 2023

# -----------------------------------------------------------------------------------
#   Get cell of given size from pattern as RGB image.

def get_image_from_pattern( size, pat, color ):
    img =  Image.new( "RGB", (int(size[0]), int(size[1])) )

    ti = get_image_from_pattern_one( (8,8), pat )

    for y in range( 0, img.size[1], ti.size[1] ):
        for x in range( 0, img.size[0], ti.size[0] ):
            img.paste( tuple(color), (x, y), ti )     # Will clip if ti not integral to size

    return img

# -----------------------------------------------------------------------------------

def get_image_from_pattern_with_bg( size, pat, color, color_bg ):

    img =  Image.new( "RGB", (int(size[0]), int(size[1])), color_bg )
    ti = get_image_from_pattern_one( (8,8), pat )

    for y in range( 0, img.size[1], ti.size[1] ):
        for x in range( 0, img.size[0], ti.size[0] ):
            img.paste( tuple(color), (x, y), ti )     # Will clip if ti not integral to size

    return img

# -----------------------------------------------------------------------------------
#   WRW 12 Mar 2023 - Change from textsize() to textlength() caused a problem.
#       textsize() returned (width, height)
#       textlength() return width
#       Have to use textbox() instead.

#   Too many places to change. Instead use this funciton.

def my_textsize( d, text, **kwargs ):

    bb = d.textbbox((0,0), text, kwargs['font'])        # returns: (left, top, right, bottom) bounding box

    width = bb[2] - bb[0]
    height = bb[3] - bb[1]

    return( width, height )

# -----------------------------------------------------------------------------------
#   Image generation functions
# -----------------------------------------------------------------------------------

def mk_solids( size ):

    solids = (("red",     "#ff0000" ),
              ("green",   "#00ff00" ),
              ("blue",    "#0000ff" ),
              ("yellow",  "#ffff00" ),
              ("magenta", "#ff00ff" ),
              ("cyan",    "#00ffff" ),
              ("black",   "#000000" ),
              ("gray",    "#808080" ),
              ("white",   "#ffffff" ) )

    for solid in solids:
        img = Image.new( "RGB", size )
        mk_solid( img, solid[1] )
        save_img( img, "color-one-" + solid[0] )

# -----------------------------------------------------------------------------------

def mk_solid( img, color ):
    d = ImageDraw.Draw( img )
    d.rectangle( ((0,0), (img.size[0]-1, img.size[1]-1) ), fill=color )

# -----------------------------------------------------------------------------------

def mk_overscan( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xmax = size[0]-1
    ymax = size[1]-1

    for tt in range( 0, 20, 2 ):
        d.rectangle( ((tt,tt), (xmax-tt, ymax-tt)), outline="#ffffff")

    d.line( ((tt, tt ), (xmax-tt, ymax-tt)), fill="#ffffff")
    d.line( ((tt, ymax-tt ), (xmax-tt, tt)), fill="#ffffff")

    save_img( img, "check-overscan" )

# -----------------------------------------------------------------------------------

def mk_points( size ):
    points = (2, 4, 8, 16, 32)

    for point in points:
        mk_point( size, point )

# -----------------------------------------------------------------------------------

def mk_point( size, offset ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    for x in range( 0, size[0], offset ):
        for y in range( 0, size[1], offset ):
            d.point( (x, y), fill="#ffffff" )

    save_img( img, "geometry-points-" + "%02d" % offset )
    if offset > 2:
        save_img( ImageOps.invert( img ), "geometry-points-" + ("%02d" % offset) + "-inv" )

# -----------------------------------------------------------------------------------

def mk_star( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xcen = (size[0]-1)/2.
    ycen = (size[1]-1)/2.

    spacing = 10

    for x in range( 0, size[0], spacing ):
        d.line( ((xcen, ycen), ( x, 0 )), fill="#ffffff" )
        d.line( ((xcen, ycen), ( x, size[1]-1 )), fill="#ffffff" )

    for y in range( 0, size[1], spacing ):
        d.line( ((xcen, ycen), ( 0, y )), fill="#ffffff" )
        d.line( ((xcen, ycen), ( size[0]-1, y )), fill="#ffffff" )

    save_img( img, "check-resolution-star" )
    save_img( ImageOps.invert( img ), "check-resolution-star" )

# -----------------------------------------------------------------------------------

def mk_resolutions( size ):
    mk_resolution_hori( size )
    mk_resolution_vert( size )

# -----------------------------------------------------------------------------------

def mk_resolution_hori( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    ycen = size[1]/2.
    spacing = 10
    font = ImageFont.load( "pilfonts/helvR12.pil" )

    if text_flag:
        d.text( (10, size[1] * .96), "Line Pitch", fill="#ffffff", font=font )

    for y in range( 0, size[1], spacing ):
        d.line( ((0, ycen), ( size[0]-1, y )), fill="#ffffff" )

    for x in range(1, spacing):
        xpos = (1.* x/spacing ) * size[0]

        d.line( ((xpos, size[1] * .5 ), ( xpos, size[1] * .95 )), fill="#ffffff" )
        if text_flag:
            text = "%d" % x
            fsize = my_textsize( d,  text, font=font )
            d.text( (xpos - fsize[0]/2, size[1] * .96 ), text, fill="#ffffff", font=font )

    save_img( img, "check-resolution-hori-wedge" )
    save_img( ImageOps.invert( img ), "check-resolution-hori-wedge-inv" )

# -----------------------------------------------------------------------------------

def mk_resolution_vert( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xcen = size[0]/2
    spacing = 10
    font = ImageFont.load( "pilfonts/helvR12.pil" )

    if text_flag:
        d.text( (size[0] * .9, 10), "Line Pitch", fill="#ffffff", font=font )

    for x in range( 0, size[0], spacing ):
        d.line( ((xcen, 0), ( x, size[1]-1 )), fill="#ffffff" )

    for y in range(1, spacing):
        ypos = (1.* y/spacing ) * size[1]

        d.line( ((size[0] * .5, ypos ), ( size[0] * .95, ypos )), fill="#ffffff" )
        if text_flag:
            text = "%d" % y
            fsize = my_textsize( d,  text, font=font )
            d.text( (size[0] * .96, ypos - fsize[1]/2), text, fill="#ffffff", font=font )

    save_img( img, "check-resolution-vert-wedge" )
    save_img( ImageOps.invert( img ), "check-resolution-vert-wedge-inv" )

# -----------------------------------------------------------------------------------

def mk_wipes( size ):
    for (name, color) in colors_6:
        mk_wipe_full( size, name, color )

    for (name, color) in colors_6g:
        mk_wipe_half( size, name, color )

# -----------------------------------------------------------------------------------
#   color is np.array()
#       Remember xor: ( 0, 1, 0 ) ^ 1 ==> ( 1, 0, 1 )

def mk_wipe_full( size, name, color ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    color = np.array( color )

    for x in range( int(size[0]/2 )):        # Black to saturated in 1/2 width, WRW 12 Mar 2023 - added int()
        gray = int(255. * x/(size[0]/2 - 1))
        d.line( ((x,0), (x,size[1]-1)), fill=tuple(color*gray))

    for x in range( int( size[0]/2), size[0] ):  # Saturated to white in 1/2 width, WRW 12 Mar 2023 - added int()
        gray = int(255. * (x-size[0]/2)/(size[0]/2 - 1))
        fill = color * 255 + (color ^ 1) * gray
        d.line( ((x,0), (x,size[1]-1)), fill=tuple(fill) )

    save_img( img, "color-wipe-full-" + name )

# -----------------------------------------------------------------------------------

def mk_wipe_half( size, name, color ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    color = np.array( color )

    for x in range( size[0]):        # Black to saturated
        gray = int(255. * x/size[0])
        d.line( ((x,0), (x,size[1]-1)), fill=tuple( color * gray ) )

    save_img( img, "color-wipe-half-" + name )

# -----------------------------------------------------------------------------------

def mk_wedges( size ):
    for (name, color) in colors_6g:
        mk_wedge( size, "lin-" + name, color, 0 )

# -----------------------------------------------------------------------------------
#   This doesn't look very interesting

def mk_wedges_log( size ):
    for (name, color) in colors_6g:
        mk_wedge( size, "log-" + name, color, 1 )

# -----------------------------------------------------------------------------------

def mk_wedge( size, name, color, log ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    wedges = ( 8, 16, 32, 64, 128 )
    color = np.array( color )

    gap = size[0] * .01
    ysize = (1.*size[1] - gap * (len(wedges)-1))/len(wedges)

    for (y, xcnt ) in enumerate( wedges ):
        xsize = 1. * size[0] / (xcnt)
        yoff = y * (ysize + gap)

        if not log:
            gray = 0.
            gray_delta = 255./(xcnt-1)      # -1 to get full white
        else:
            gray = 1.
            gray_delta = 255. ** (1./(xcnt-1))

        for x in range( xcnt ):
            xoff = x * xsize
            igray = int( round( gray ))    # round() needed as had some very small differences from 255
            d.rectangle( ((xoff,yoff), (xoff+xsize-1, yoff+ysize-1)), fill=tuple( igray * color ))

            if text_flag:
                text = "%d" % igray
                font = ImageFont.load( "pilfonts/helvR08.pil" )
                fsize = my_textsize( d,  text, font=font )

                if my_textsize( d,  "000", font=font )[0] < xsize:
                    xtext = xoff + xsize/2 - fsize[0]/2
                    ytext = yoff + ysize - fsize[1] - 2

                    if luma( igray * color ) < 128:
                        d.text( (xtext, ytext), text, fill="#ffffff", font=font )
                    else:
                        d.text( (xtext, ytext), text, fill="#000000", font=font )

            if not log:
                gray += gray_delta
            else:
                gray *= gray_delta

    save_img( img, "color-step-" + name )

# -----------------------------------------------------------------------------------

def mk_wipes_all_colors( size ):
    mk_wipes_all_colors_half( size )
    mk_wipes_all_colors_full( size )

# -----------------------------------------------------------------------------------

def mk_wipes_all_colors_half( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    gap = size[0] * .01
    ysize = (1.* size[1] - gap * (len(colors_6g) - 1))/len(colors_6g)
    yoff = 0

    for __, color in colors_6g:
        color = np.array( color )
        for xoff in range( size[0] ):  # 0 to size[0]-1
            gray = int(255. * xoff/(size[0] - 1))
            d.line( ((xoff,yoff), (xoff, yoff+ysize-1)), fill=( tuple(color * gray) ))
        yoff += ysize + gap

    save_img( img, "check-color-wipe-half" )

# -----------------------------------------------------------------------------------

def mk_wipes_all_colors_full( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    gap = size[0] * .01
    ysize = (1.* size[1] - gap * (len(colors_6) - 1))/len(colors_6)
    yoff = 0

    for __, color in colors_6:
        color = np.array( color )
        xoff = 0
        gray = 0

        for x in range( int(size[0]/2) ):        # Black to saturated in 1/2 width. WRW 12 Mar 2023 - added int()
            gray = int(255. * x/(size[0]/2 - 1))
            d.line( ( (x,yoff), (x,yoff+ysize-1) ), fill=tuple(color*gray) )

        for x in range( int( size[0]/2), size[0] ):  # Saturated to white in 1/2 width, WRW 12 Mar 2023 - added int()
            gray = int(255. * (x-size[0]/2)/(size[0]/2 - 1))
            fill = color * 255 + (color ^ 1) * gray
            d.line( ((x,yoff), (x,yoff+ysize-1)), fill=tuple(fill) )

        yoff += ysize + gap

    save_img( img, "check-color-wipe-full" )

# -----------------------------------------------------------------------------------
#   WRW 13 Mar 2023 - had bar_cnt reversed for the continuous ones resulting in empty vertical 
#       gaps in continuous vertical bar pattern.

def mk_color_bars_all( size ):
    mk_color_bars( size, 0, 3 )
    mk_color_bars( size, 1, 3 )
    mk_color_bars( size, 0, 6 )
    mk_color_bars( size, 1, 6 )
    mk_color_bars( size, 0, 12 )
    mk_color_bars( size, 1, 12 )
    mk_color_bars( size, 0, size[1] )       # Continuous
    mk_color_bars( size, 1, size[0] )

# -----------------------------------------------------------------------------------
#   Easier to do this in hsv space than with array of specific rgb color values.
#   size: (x, y)

def mk_color_bars( size, vert, bar_cnt ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    bsize = 1. * size[0] / bar_cnt if vert else 1. * size[1] / bar_cnt
    s = v = 1

    for i in range( bar_cnt ):
        off = i * bsize
        h = i * 1./bar_cnt
        color = [int( x * 255 ) for x in colorsys.hsv_to_rgb(h, s, v)]

        if vert:
            d.rectangle( ((off, 0), (off+bsize-1, size[1]-1)), fill=tuple(color) )
        else:
            d.rectangle( ((0, off), (size[0]-1, off+bsize-1)), fill=tuple(color) )

    name = "vert" if vert else "hori"
    bar_name = "cont" if bar_cnt > 12 else ("%02d" % bar_cnt)   # Little hack
    save_img( img, "color-bars-%s-%s" % (name, bar_name))

# -----------------------------------------------------------------------------------
#   Studio swing: 16-235

def mk_targets_all( size ):
    step = 255 * .05        # 5% steps

    mk_targets( size, "full",      ( 0, step, step * 2 ), ( 255, 255-step, 255-(step * 2) ))
    mk_targets( size, "broadcast", ( 16, 16+step, 26+(step *2) ), ( 235, 235-step, 235-(step*2) ))

# -----------------------------------------------------------------------------------

def mk_targets( size, name, lower, upper ):
    dia = min( size[0]/2, size[1] ) * .8
    gap = (size[0] - 2.*dia)/3

    x1 = gap + dia/2
    x2 = 2*gap + dia + dia/2
    y = size[1]/2        

    gray = int(255 * .5)    # I used 18% in original patterns, this is better
    img = Image.new( "RGB", size, (gray, gray, gray) )
    d = ImageDraw.Draw( img )

    mk_target( d, (x1, y), dia, lower[0] )
    mk_target( d, (x1, y), 2*dia/3, lower[1] )
    mk_target( d, (x1, y), dia/3, lower[2] )

    mk_target( d, (x2, y), dia, upper[0] )
    mk_target( d, (x2, y), 2*dia/3, upper[1] )
    mk_target( d, (x2, y), dia/3, upper[2] )

    save_img( img, "check-clipping-target-" + name )

# -----------------------------------------------------------------------------------

def mk_target( d, center, dia, gray ):

    gray = int( gray )
    d.ellipse( (center[0] - dia/2, center[1] - dia/2, center[0] + dia/2, center[1]+dia/2), fill=(gray,)*3 )

    if text_flag:
        text = "%d" % gray
        font = ImageFont.load( "pilfonts/helvR10.pil" )
        fsize = my_textsize( d,  text, font=font )

        xtext = center[0] - fsize[0]/2
        ytext = center[1] + dia/2 - fsize[1] - 8

        if gray < 128:
            d.text( (xtext, ytext), text, fill="#ffffff", font=font )
        else:
            d.text( (xtext, ytext), text, fill="#000000", font=font )

# -----------------------------------------------------------------------------------

def mk_clippings( size ):
    mk_clipping( size, "clipping-low", 0, 0, 1, (1, 1, 1) )
    mk_clipping( size, "clipping-high", 255, 255, -1, (1, 1, 1) )

    mk_clipping( size, "clipping-low-red", 0, 0, 1, (1, 0, 0) )
    mk_clipping( size, "clipping-high-red", 255, 255, -1, (1, 0, 0) )

    mk_clipping( size, "clipping-low-green", 0, 0, 1, (0, 1, 0) )
    mk_clipping( size, "clipping-high-green", 255, 255, -1, (0, 1, 0) )

    mk_clipping( size, "clipping-low-blue", 0, 0, 1, (0, 0, 1) )
    mk_clipping( size, "clipping-high-blue", 255, 255, -1, (0, 0, 1) )

# -----------------------------------------------------------------------------------
#   ITU-R Recommendation BT.709
#       Studio swing: 16-235
#       Sync: 0, 255
#       Footroom: 1-15, 236-254

def mk_clipping( size, fname, bg, start, increment, color ):
    img = Image.new( "RGB", size, (bg * color[0], bg * color[1], bg * color[2]) )
    d = ImageDraw.Draw( img )

    color = np.array( color )

    rows = 4        # /// layout approach?
    cols = 8

    xsize = size[0]/cols * .7
    xgap = (size[0] - xsize * cols)/(cols+1)

    ysize = size[1]/rows * .7
    ygap = (size[1] - ysize * rows)/(rows+1)

    gray = start

    for y in range( rows ):
        yoff = ygap + y * ( ysize + ygap )

        for x in range( cols ):
            xoff = xgap + x * ( xsize + xgap )

            d.rectangle( ((xoff,yoff), (xoff+xsize, yoff+ysize)), fill=tuple( gray * color ))

            if text_flag:
                text = "%d" % gray
                textb = "studio swing"

                if gray < 128:
                    tcolor = tcolorb = "#ffffff"
                else:
                    tcolor = tcolorb = "#000000"

                if gray == 0 or gray == 255:
                    textb = "sync"
                    tcolorb = "#ff0000"

                if 0 < gray < 16:
                    textb = "footroom"
                    tcolorb = "#00ff00"

                if 235 < gray < 255:
                    textb = "headroom"
                    tcolorb = "#00ff00"

                font = ImageFont.load( "pilfonts/helvR10.pil" )
                fsize = my_textsize( d,  text, font=font )

                xtext = xoff + xsize/2 - fsize[0]/2
                ytext = yoff + ysize  - fsize[1] * 2 - 4
                d.text( (xtext, ytext), text, fill=tcolor, font=font )

                font = ImageFont.load( "pilfonts/helvR08.pil" )
                fsize = my_textsize( d,  textb, font=font )

                xtext = xoff + xsize/2 - fsize[0]/2
                ytext = yoff + ysize  - fsize[1] - 4
                d.text( (xtext, ytext), textb, fill=tcolorb, font=font )

            gray += increment

    save_img( img, fname )

# -----------------------------------------------------------------------------------

def mk_random_rgb( size ):
    pxsizes = (1, 2, 4, 8, 16 )

    for pxsize in pxsizes:
        img = Image.new( "RGB", size )
        d = ImageDraw.Draw( img )
        for yoff in range( 0, size[1], pxsize ):
            for xoff in range( 0, size[0], pxsize ):

                color = [random.randint( 0, 255 ) for __ in range(3)]
                d.rectangle( ((xoff,yoff), (xoff+pxsize-1, yoff+pxsize-1)), fill=tuple(color))

        save_img( img, "color-random-%02d" % pxsize )

# -----------------------------------------------------------------------------------

def mk_random_gray( size ):
    pxsizes = (1, 2, 4, 8, 16 )

    for pxsize in pxsizes:
        img = Image.new( "RGB", size )
        d = ImageDraw.Draw( img )
        for yoff in range( 0, size[1], pxsize ):
            for xoff in range( 0, size[0], pxsize ):
                gray = random.randint( 0, 255 )
                d.rectangle( ((xoff,yoff), (xoff+pxsize-1, yoff+pxsize-1)), fill=(gray,)*3 )

        save_img( img, "color-random-gray-%02d" % pxsize )

# -----------------------------------------------------------------------------------
#   Arg mask is r, g, b

def mk_colors_rgb( size ):
    for fixed_val in ( 0, 127, 255 ):
        mk_color_rgb( size, fixed_val, (1,0,0), (0,1,0), (0,0,1), "red",  "green", "blue" )
        mk_color_rgb( size, fixed_val, (0,1,0), (0,0,1), (1,0,0), "green", "blue", "red" )
        mk_color_rgb( size, fixed_val, (0,0,1), (1,0,0), (0,1,0), "blue", "red", "green" )

# -----------------------------------------------------------------------------------
#   Make colors varying just two of three values
#       Remember, ^ is xor, complements mask in color1, color2
#       This is faster with numpy.
#   WRW 13 Mar 2023 - This and the other mk_color_*() functions are very slow.
#       /// RESUME - do profiling, see if can speed up, I suspect bottleneck is d.point()

def OLD_mk_color_rgb( size, fixed_val, fixed, color1, color2, fixed_name, name1, name2 ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xci = 255./(size[0]-1)
    yci = 255./(size[1]-1)

    color1 = np.array( color1 )
    color2 = np.array( color2 )
    fixed  = np.array( fixed )

    color = fixed * fixed_val

    for y in range( size[1] ):
        color = color * (color1 ^ 1)        # ^ is XOR

        for x in range( size[0] ):
            d.point( (x,y), fill=tuple(color.astype(int)))
            color = color + xci * color1
        color = color + yci * color2

    save_img( img, "wipe-rgb-fix-%s-%03d-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   WRW 24-May-2026 - Numpy approach from Claude.

def mk_color_rgb( size, fixed_val, fixed, color1, color2, fixed_name, name1, name2 ):

    color1 = np.array( color1 )
    color2 = np.array( color2 )
    fixed  = np.array( fixed )

    x_vals = np.linspace( 0, 255, size[0] )   # shape (W,)
    y_vals = np.linspace( 0, 255, size[1] )   # shape (H,)

    # Each contributes to (H, W, 3) via broadcasting
    fixed_contrib = fixed * fixed_val                          # (3,)
    x_contrib     = np.outer( x_vals, color1 )                # (W, 3)
    y_contrib     = np.outer( y_vals, color2 )                # (H, 3)

    arr = fixed_contrib + x_contrib[np.newaxis, :, :] + y_contrib[:, np.newaxis, :]
    arr = np.clip( arr, 0, 255 ).astype( np.uint8 )

    img = Image.fromarray( arr, 'RGB' )
    save_img( img, "wipe-rgb-fix-%s-%03d-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   WRW 24-May-2026 - from Claude.
#   H, S, V are (rows, cols) arrays in [0,1]. Returns (rows, cols, 3) uint8.

def _hsv_to_rgb_array( H, S, V ):
    h6 = H * 6.0
    i  = np.floor( h6 ).astype( np.int32 ) % 6
    f  = h6 - np.floor( h6 )
    p  = V * ( 1.0 - S )
    q  = V * ( 1.0 - S * f )
    t  = V * ( 1.0 - S * ( 1.0 - f ) )
    r  = np.choose( i, [V, q, p, p, t, V] )
    g  = np.choose( i, [t, V, V, q, p, p] )
    b  = np.choose( i, [p, p, t, V, V, q] )
    return ( np.stack( [r, g, b], axis=-1 ) * 255 ).astype( np.uint8 )

# -----------------------------------------------------------------------------------
#   WRW 24-May-2026 - from Claude.
#   Matches colorsys.hls_to_rgb(h, l, s) exactly. Returns (rows, cols, 3) uint8.   

def _hls_to_rgb_array( H, L, S ):
    def _v( m1, m2, hue ):
        hue = hue % 1.0
        return np.where( hue < 1/6, m1 + ( m2 - m1 ) * hue * 6,
               np.where( hue < 1/2, m2,
               np.where( hue < 2/3, m1 + ( m2 - m1 ) * ( 2/3 - hue ) * 6,
                         m1 )))
    m2 = np.where( L <= 0.5, L * ( 1.0 + S ), L + S - L * S )
    m1 = 2.0 * L - m2
    r  = _v( m1, m2, H + 1/3 )
    g  = _v( m1, m2, H )
    b  = _v( m1, m2, H - 1/3 )
    return ( np.stack( [r, g, b], axis=-1 ) * 255 ).astype( np.uint8 )

# -----------------------------------------------------------------------------------
#   Arg mask is h, s, v

def mk_colors_hsv( size ):
    mk_color_hsv( size, 0.0, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "val" )
    mk_color_hsv( size, .33, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "val" )
    mk_color_hsv( size, .66, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "val" )

    mk_color_hsv( size, 0.0, (0,0,1), (1,0,0), (0,1,0), "val", "hue", "sat" )
    mk_color_hsv( size, .5,  (0,0,1), (1,0,0), (0,1,0), "val", "hue", "sat" )
    mk_color_hsv( size, 1.0, (0,0,1), (1,0,0), (0,1,0), "val", "hue", "sat" )

    mk_color_hsv( size, 0.0, (0,1,0), (0,0,1), (1,0,0), "sat", "val", "hue" )
    mk_color_hsv( size, .5,  (0,1,0), (0,0,1), (1,0,0), "sat", "val", "hue" )
    mk_color_hsv( size, 1.0, (0,1,0), (0,0,1), (1,0,0), "sat", "val", "hue" )

# -----------------------------------------------------------------------------------
#   Vary two of hsv holding the third constant.

def OLD_mk_color_hsv( size, fixed_val, fixed, var1, var2, fixed_name, name1, name2 ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xci = 1./(size[0]-1)
    yci = 1./(size[1]-1)

    var1 = np.array( var1 )
    var2 = np.array( var2 )
    fixed = np.array( fixed )

    color = fixed * fixed_val

    for y in range( size[1] ):
        color = color * (var1 ^ 1)

        for x in range( size[0] ):
            crgb = [int( x * 255. ) for x in colorsys.hsv_to_rgb( *color)]   # *color to unpack it into three values
            d.point( (x,y), fill=tuple(crgb))
            color = color + xci * var1

        color = color + yci * var2

    save_img( img, "wipe-hsv-fix-%s-%.2f-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   Vary two of hsv holding the third constant.
#   WRW 24-May-2026 - from Claude.

def mk_color_hsv( size, fixed_val, fixed, var1, var2, fixed_name, name1, name2 ):
    var1  = np.array( var1,  dtype=float )
    var2  = np.array( var2,  dtype=float )
    fixed = np.array( fixed, dtype=float )

    x_vals    = np.linspace( 0, 1, size[0] )
    y_vals    = np.linspace( 0, 1, size[1] )
    x_contrib = np.outer( x_vals, var1 )             # (W, 3)
    y_contrib = np.outer( y_vals, var2 )             # (H, 3)

    hsv = ( fixed * fixed_val
            + x_contrib[np.newaxis, :, :]
            + y_contrib[:, np.newaxis, :] )          # (H, W, 3)

    arr = _hsv_to_rgb_array( hsv[:,:,0], hsv[:,:,1], hsv[:,:,2] )
    save_img( Image.fromarray( arr, 'RGB' ),
              "wipe-hsv-fix-%s-%.2f-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   Arg mask is h, s, l

def mk_colors_hsl( size ):
    mk_color_hsl( size, 0.0, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "lev" )
    mk_color_hsl( size, .33, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "lev" )
    mk_color_hsl( size, .66, (1,0,0), (0,1,0), (0,0,1), "hue", "sat", "lev" )

    mk_color_hsl( size, .25, (0,0,1), (1,0,0), (0,1,0), "lev", "hue", "sat" )
    mk_color_hsl( size, .5,  (0,0,1), (1,0,0), (0,1,0), "lev", "hue", "sat" )
    mk_color_hsl( size, .75, (0,0,1), (1,0,0), (0,1,0), "lev", "hue", "sat" )

    mk_color_hsl( size, 0.0, (0,1,0), (0,0,1), (1,0,0), "sat", "lev", "hue" )
    mk_color_hsl( size, .5,  (0,1,0), (0,0,1), (1,0,0), "sat", "lev", "hue" )
    mk_color_hsl( size, 1.0, (0,1,0), (0,0,1), (1,0,0), "sat", "lev", "hue" )

# -----------------------------------------------------------------------------------
#   Vary two of hsv holding the third constant.
#   Remember, arg to colorsys.hls_to_rgb() is hls, not hsl as the mk_ function is named.
#   Use explicit unpack as a reminder.

def OLD_mk_color_hsl( size, fixed_val, fixed, var1, var2, fixed_name, name1, name2 ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xci = 1./(size[0]-1)
    yci = 1./(size[1]-1)

    var1 = np.array( var1 )
    var2 = np.array( var2 )
    fixed = np.array( fixed )

    color = fixed * fixed_val

    for y in range( size[1] ):
        color = color * (var1 ^ 1)

        for x in range( size[0] ):

            ( h, s, l ) = color
            crgb = [int( x * 255. ) for x in colorsys.hls_to_rgb( h, l, s )]                                          
            d.point( (x,y), fill=tuple(crgb))
            color = color + xci * var1

        color = color + yci * var2

    save_img( img, "wipe-hsl-fix-%s-%.2f-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   Vary two of hsv holding the third constant.
#   WRW 24-May-2026 - from Claude.

def mk_color_hsl( size, fixed_val, fixed, var1, var2, fixed_name, name1, name2 ):
    var1  = np.array( var1,  dtype=float )
    var2  = np.array( var2,  dtype=float )
    fixed = np.array( fixed, dtype=float )

    x_vals    = np.linspace( 0, 1, size[0] )
    y_vals    = np.linspace( 0, 1, size[1] )
    x_contrib = np.outer( x_vals, var1 )             # (W, 3)
    y_contrib = np.outer( y_vals, var2 )             # (H, 3)

    hsl = ( fixed * fixed_val
            + x_contrib[np.newaxis, :, :]
            + y_contrib[:, np.newaxis, :] )          # (H, W, 3)

    # Original unpacks (h, s, l) = color then calls hls_to_rgb( h, l, s ) note l/s swap in function name

    H, S, L = hsl[:,:,0], hsl[:,:,1], hsl[:,:,2]
    arr = _hls_to_rgb_array( H, L, S )
    save_img( Image.fromarray( arr, 'RGB' ),
              "wipe-hsl-fix-%s-%.2f-var-%s-%s" % ( fixed_name, fixed_val, name1, name2 ) )

# -----------------------------------------------------------------------------------
#   Fixed count of 16 steps in each color, 64 hori, 16 vert.
#   Blue varies in Y, Green slow in X, Red fast in X
#   /// Not really interesting. Omit now. Perhaps change later.

def mk_colors_all_a( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    rsteps = gsteps = bsteps = 16
    rci, gci, bci = 255./rsteps, 255./gsteps, 255./bsteps

    xsize = 1. * size[0]/(bsteps * gsteps)
    ysize = 1. * size[1]/rsteps

    adjust = 1 if not text_flag else 2      # Solid for small shapes, border for larger ones

    for bi in range( rsteps ):         # Red varies along Y
        yoff = bi * ysize
        for gi in range( gsteps ):     # Green varies slow along X
            for ri in range( bsteps ): # Blue varies fast along X
                xoff = xsize * ( gi * gsteps + ri )
                d.rectangle( ((xoff,yoff), (xoff+xsize-adjust, yoff+ysize-adjust)), fill=(int(ri * rci ), int(gi * gci), int(bi * bci)))

    save_img( img, "color-patch-4096-rgb-a" )

# -----------------------------------------------------------------------------------
#   Fixed count of 64 steps in x and y, 4096 colors total. Step each color by 16.
#   16^3 = 4096.                               
#   4 cycles of red horizontally, 4 lines for 1 cycle of green, 16 cycles of red, blue increments every 4 lines, 1 cycle total
#   WRW 13 Mar 2023 - Issue after convert to python3. Change yoff division to //.

def mk_colors_all_b( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    ci = 16

    xsize = 1.* size[0]/64           
    ysize = 1.* size[1]/64

    adjust = 1 if not text_flag else 2      # Solid for small shapes, border for larger ones

    for bi in range( 16 ):                 # Blue goes vertically every 4 rows
        for gi in range( 16 ):             # Green goes vertically every row and horizontally every 16 cells, 4 lines / cycle
            for ri in range( 16 ):         # Red horizontally each cell, 4 cycles per line
                xoff = xsize * ((gi % 4) * 16 + ri)
              # yoff = ysize * (bi * 4 + gi / 4 )
                yoff = ysize * (bi * 4 + gi // 4 )      # WRW 13 Mar 2023 
                d.rectangle( ((xoff,yoff), (xoff+xsize-adjust, yoff+ysize-adjust)), fill=(int(ri * ci ), int(gi * ci ), int(bi * ci)))

    save_img( img, "color-patch-4096-rgb-b" )

# -----------------------------------------------------------------------------------

def mk_hlines( size ):
    mk_hline( size, 2 )
    mk_hline( size, 4 )
    mk_hline( size, 8 )

# -----------------------------------------------------------------------------------

def mk_hline( size, pitch ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    for y in range( 0, size[1], pitch ):
        d.line( ((0,y), (size[0]-1,y)), fill="#ffffff" )

    save_img( img, "geometry-lines-hori-" + "%d" % pitch )
    if pitch > 2:
        save_img( ImageOps.invert( img ), "geometry-lines-hori-" + ("%d" % pitch) + "-inv" )

# -----------------------------------------------------------------------------------

def mk_vlines( size ):
    mk_vline( size, 2 )
    mk_vline( size, 4 )
    mk_vline( size, 8 )

# -----------------------------------------------------------------------------------

def mk_vline( size, pitch ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    for x in range( 0, size[0], pitch ):
        d.line( ((x,0), (x, size[1]-1)), fill="#ffffff" )

    save_img( img, "geometry-lines-vert-" + "%d" % pitch )
    if pitch > 2:
        save_img( ImageOps.invert( img ), "geometry-lines-vert-" + ("%d" % pitch) + "-inv" )

# -----------------------------------------------------------------------------------

def mk_loghlines( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    y = 1
    while y < size[1]:
        d.line( ((0,y), (size[0]-1,y)), fill="#ffffff" )
        y *= 1.05

    save_img( img, "geometry-lines-hori-log" )
    save_img( ImageOps.invert( img ), "geometry-lines-hori-log-inv" )

# -----------------------------------------------------------------------------------

def mk_logvlines( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    x = 1
    while x < size[0]:
        d.line( ((x,0), (x, size[1]-1)), fill="#ffffff" )
        x *= 1.05

    save_img( img, "geometry-lines-vert-log" )
    save_img( ImageOps.invert( img ), "geometry-lines-vert-log" )

# -----------------------------------------------------------------------------------

def mk_many_circles( size ):
    cols = 8
    rows = int( cols * 1. * size[1]/size[0] )

    xsize = size[0]/cols * .8
    xgap = (size[0] - xsize * cols)/(cols+1)

    ysize = size[1]/rows * .8
    ygap = (size[1] - ysize * rows)/(rows+1)

    csize = min( xsize, ysize )

    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    for y in range( rows ):
        yoff = ygap + y * ( ysize + ygap )                                 
        for x in range( cols ):
            xoff = xgap + x * ( xsize + xgap )
            d.ellipse( ((xoff,yoff), (xoff+csize-1, yoff+csize-1)), outline="#ffffff" )

    save_img( img, "geometry-distortion-circle-many" )
    save_img( ImageOps.invert( img ), "geometry-distortion-circle-many-inv" )

# -----------------------------------------------------------------------------------

def mk_many_squares( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    cols = 8
    rows = int( cols * 1. * size[1]/size[0] )

    xsize = size[0]/cols * .8
    xgap = (size[0] - xsize * cols)/(cols+1)

    ysize = size[1]/rows * .8
    ygap = (size[1] - ysize * rows)/(rows+1)

    csize = min( xsize, ysize )

    for y in range( rows ):
        yoff = ygap + y * ( ysize + ygap )                                 
        for x in range( cols ):
            xoff = xgap + x * ( xsize + xgap )
            d.rectangle( ((xoff,yoff), (xoff+csize-1, yoff+csize-1)), outline="#ffffff" )

    save_img( img, "geometry-distortion-square-many" )
    save_img( ImageOps.invert( img ), "geometry-distortion-square-many-inv" )

# -----------------------------------------------------------------------------------

def mk_color_step_wipes_composite( size ):
    for color in colors_3g:
        mk_color_step_wipes_one( size, color[0], color[1] )

# -----------------------------------------------------------------------------------
#   Composite figure - bi-directional wipes with bi-directional step wedges

def mk_color_step_wipes_one( size, name, color ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    color = np.array( color )
    xsize = size[0]
    ysize = size[1] / 4. 

    ypos_forward_step = 0
    ypos_forward_wipe = ypos_forward_step + ysize      
    ypos_reverse_wipe = ypos_forward_wipe + ysize      
    ypos_reverse_step = ypos_reverse_wipe + ysize      

    # ------------------------------------------------------------------
    #   +ysize-1 to get to bottom of current cell. +ysize gets to top of next

    y0 = ypos_forward_wipe
    for x in range( xsize ):
        gray = int(255. * x/(xsize-1))  # -1 to get to full 255
        d.line( ((x, y0), (x, y0 + ysize -1)), fill=tuple(gray*color) )

    # ------------------------------------------------------------------
    y0 = ypos_reverse_wipe
    for x in range( xsize ):
        gray = int(255. * (xsize - x)/(xsize-1))
        d.line( ((x, y0), (x,y0 + ysize -1)), fill=tuple(gray*color) )

    # ------------------------------------------------------------------

    wedges = 16
    wsize = 1. * xsize / wedges
    gray_step = 255./(wedges-1)     # -1 to get to full 255

    # ------------------------------------------------------------------

    y0 = ypos_forward_step
    for x in range( wedges ):
        mk_color_step( d, (x * wsize, y0), (x * wsize + wsize-1, y0 + ysize-1), x * gray_step, color )

    # ------------------------------------------------------------------

    y0 = ypos_reverse_step
    for x in range( wedges ):
        mk_color_step( d, (x * wsize, y0), (x * wsize + wsize-1, y0 + ysize-1), (wedges-x-1) * gray_step, color )

    # ------------------------------------------------------------------

    save_img( img, "color-composite-step-wipe-" + name )

# -----------------------------------------------------------------------------------
#   Do subtraction of 1 for final coordinate of d.rectangle in calling routine.

def mk_color_step( d, c1, c2, gray, color ):
    gray = int( round( gray ) )     # round() to reach full 255
    d.rectangle( ((c1[0],c1[1]), (c2[0], c2[1])), fill=tuple( gray*color))

    if text_flag:
        text = "%d" % gray
        font = ImageFont.load( "pilfonts/helvR08.pil" )
        fsize = my_textsize( d,  text, font=font )

        xsize = c2[0] - c1[0]
        xtext = c1[0] + xsize/2 - fsize[0]/2
        ytext = c2[1] - fsize[1] - 4

        if luma( gray*color ) > 128:
            d.text( (xtext, ytext), text, fill="#000000", font=font )
        else:
            d.text( (xtext, ytext), text, fill="#ffffff", font=font )

# -----------------------------------------------------------------------------------
#   Use line and checker. Lines preferred by some on web, probably from CRT days.
#   I think checker is smoother.

def mk_gammas( size ):
    mk_gamma( size, "lines-gray",       pat_hlines_2, ( 1, 1, 1 ))
    mk_gamma( size, "lines-gray-red",   pat_hlines_2, ( 1, 0, 0 ))
    mk_gamma( size, "lines-gray-green", pat_hlines_2, ( 0, 1, 0 ))
    mk_gamma( size, "lines-gray-blue",  pat_hlines_2, ( 0, 0, 1 ))
    mk_gamma( size, "checker-gray",     pat_checker_point_2, ( 1, 1, 1 ))
    mk_gamma( size, "checker-red",      pat_checker_point_2, ( 1, 0, 0 ))
    mk_gamma( size, "checker-green",    pat_checker_point_2, ( 0, 1, 0 ))
    mk_gamma( size, "checker-blue",     pat_checker_point_2, ( 0, 0, 1 ))

# -----------------------------------------------------------------------------------
#   Values from Ezio page:
#     Note: difference only for 1.2 and 1.6, all else match
#       1.0: 80, 1.2: 94, 1.4: 9c, 1.6: a6, 1.8: ae, 2.0: b5, 2.2: ba, 2.4: bf, 2.6: c4

#   Values I compute when using 256 as max:
#       1.0: 80, 1.2: 8f, 1.4: 9c, 1.6: a5, 1.8: ae, 2.0: b5, 2.2: ba, 2.4: bf, 2.6: c4

#   Values I compute when using 255 as max:
#       1.0: 7f, 1.2: 8f, 1.4: 9b, 1.6: a5, 1.8: ad, 2.0: b4, 2.2: ba, 2.4: bf, 2.6: c3

# -----------------------------------------------------------------------------------

def mk_gamma( size, name, pat, color ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    gammas = ( 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6 )
    xcnt = 3            # xcnt * ycnt must agree with gammas length
    ycnt = 3

    color = np.array( color )

    xcell = (size[0]/xcnt) * .65
    ycell = (size[1]/ycnt) * .65

    xgap = (size[0]-xcnt*xcell)/4
    ygap = (size[1]-ycnt*ycell)/4

    full_ti = get_image_from_pattern( size, pat, 255 * color  )
    img.paste( full_ti, (0, 0) )

    center_ti = get_image_from_pattern( (xcell/2, ycell/2), pat, 255 * color )

    xpos = xgap
    ypos = ygap

    cellcnt = 0
    for gamma in gammas:
        val = (.5 ** (1./gamma)) * 255.
        gray = int( val ) * color                                                  

        # print "%1.1f, %x" % (gamma, val )

        d.rectangle( ((xpos,ypos), xpos+xcell-1, ypos+ycell-1) , fill=tuple(gray))
        img.paste( center_ti, (int(xpos + xcell/4), int(ypos + ycell/4)) )

        if text_flag:
            text = "%.1f" % gamma
            font = ImageFont.load( "pilfonts/helvR14.pil" )
            fsize = my_textsize( d,  text, font=font )

            xtext = xpos + xcell/2 - fsize[0]/2
            ytext = ypos + ycell - ycell/8 - fsize[1]/2

            if luma3( gray[0], gray[1], gray[2] ) > 128:
                d.text( (xtext, ytext), text, fill="#000000", font=font )
            else:
                d.text( (xtext, ytext), text, fill="#ffffff", font=font )

        xpos += xcell + xgap
        cellcnt += 1
        if cellcnt % xcnt == 0:
            xpos = xgap
            ypos += ycell + ygap

    save_img( img, "gamma-" + name )

# -----------------------------------------------------------------------------------

def mk_one_circle( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    dia = min( size[0], size[1] ) * .8

    x1 = (size[0] - dia )/2
    y1 = (size[1] - dia )/2
    x2 = x1 + dia -1
    y2 = y1 + dia -1

    d.ellipse( (x1, y1, x2, y2), outline = "#ffffff" )

    save_img( img, "geometry-distortion-circle-one" )
    save_img( ImageOps.invert( img ), "geometry-distortion-circle-one-inv" )

# -----------------------------------------------------------------------------------
#   Remember addresses run to xsize-1, ysize-1
#   Had a problem with lines extending very slightly to right/bottom of outside edge.
#   Resolved with int( round( xpos )). int() would probably be enough.

def mk_grid( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    xsize = size[0]
    ysize = size[1]

    xstep = (xsize-1)/25.       # -1 to reach address exact edge, i.e. 0 to size-1
    ystep = (ysize-1)/25.       # xstep, ystep not integers, can't use xrange() to generate xpos, ypos

    xpos = ypos = 0.
    while xpos < xsize:
        ixpos = int( round( xpos ))
        d.line( ((ixpos,0), (ixpos, ysize-1)), fill="#ffffff" )
        xpos += xstep

    while ypos < ysize:
        iypos = int( round( ypos ))
        d.line( ((0, iypos), (xsize-1, iypos)), fill="#ffffff" )
        ypos += ystep

    save_img( img, "geometry-grid" )
    save_img( ImageOps.invert( img ), "geometry-grid-inv" )

# -----------------------------------------------------------------------------------

def mk_hconverge( size ):
    lines = 5
    segs = 10
    segsize = 1.* size[0]/segs
    ygap = 1.* size[1]/(lines + 1)

    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    color = [255, 0, 0]

    for y in range( lines ):
        ypos = ygap * ( y + 1 )
        for x in range( segs ):
            xpos = x * segsize
            d.line( ((xpos, ypos), (xpos + segsize, ypos)), fill=tuple(color) )
            color.append( color.pop(0) )        # Rotate color

    save_img( img, "check-convergence-hori" )

# -----------------------------------------------------------------------------------

def mk_vconverge( size ):
    lines = 5
    segs = 10
    segsize = 1.* size[1]/segs
    xgap = 1.* size[0]/(lines + 1)

    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    color = [255, 0, 0]

    for x in range( lines ):
        xpos = xgap * ( x + 1 )
        for y in range( segs ):
            ypos = y * segsize
            d.line( ((xpos, ypos), (xpos, ypos + segsize)), fill=tuple(color) )
            color.append( color.pop(0) )

    save_img( img, "check-convergence-vert" )

# -----------------------------------------------------------------------------------
#   Make a color triangle. Experimental.

def mk_color_triangle( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )
    (xsize, ysize) = size

    # ------------------------------------------------------------------
    #   Pick three cordinates for vertices

    xr = xsize * .1
    yr = ysize * .05

    xg = xsize * .9
    yg = ysize * .05

    xb = xsize * .5
    yb = ysize * .95

    # ------------------------------------------------------------------
    #   Traverse each line, drawing lines from opposite vertex to be
    #     sure I understand the geometry.

    if False:
        def do_fan( vertex, to_start, to_end ):
            lcnt = 10
            for i in range( 1, lcnt ):
                li = 1.* i/lcnt
                d.line( (( vertex[0], vertex[1] ), (to_start[0] + li * (to_end[0] - to_start[0]), to_start[1] + li * (to_end[1] - to_start[1]) )), fill="#ffffff" )

        do_fan( (xr, yr), (xg, yg), (xb, yb) )
        do_fan( (xg, yg), (xb, yb), (xr, yr) )
        do_fan( (xb, yb), (xr, yr), (xg, yg) )

    # ------------------------------------------------------------------
    #   Make a fan from vertex to points along the the destination line (dest_start, dest_end) with
    #     colors starting at color_vertex to the interpolation of color_start, color_end along
    #     the destination line.

    def do_fan_points( vertex, dest_start, dest_end, color_vertex, color_start, color_end ):

        line_cnt = 20

        color_vertex = np.array( color_vertex )
        color_start = np.array( color_start )
        color_end = np.array( color_end )

        # Draw a series of line_cnt lines from the vertex to (dest_x, dest_y)

        for i in range( 0, line_cnt + 1 ):         # +1 for end of line

            li =  1. * i/line_cnt                                          # Index along destination line

            dest_x = dest_start[0] + li * (dest_end[0] - dest_start[0])    # Points along the destination line
            dest_y = dest_start[1] + li * (dest_end[1] - dest_start[1])
            len = int( math.sqrt( (vertex[0] - dest_x)**2 + (vertex[1] - dest_y)**2 ))
            color_dest = (color_start * (1 - li ) + color_end * li).astype( int )

            # Draw a series of len points from vertex to one point on dest line

            for j in range( 0, len ):                                                         
                pi = 1.*j/len       # Point index along line from vertex to dest point.
                color = ( color_vertex * (1 - pi) + color_dest * pi ).astype( int )
                ptx = vertex[0] + pi * (dest_x - vertex[0])
                pty = vertex[1] + pi * (dest_y - vertex[1])

                #   Note: Tried adding new to existing pixel value but got many overflows.
                #     New pixel values were equal/almost equal to existing value.

                d.point( ( ptx, pty ), fill=tuple(color) )

    # ------------------------------------------------------------------

    do_fan_points( (xr, yr), (xg, yg), (xb, yb), (255, 0, 0), (0, 255, 0), (0, 0, 255) )
    do_fan_points( (xg, yg), (xb, yb), (xr, yr), (0, 255, 0), (0, 0, 255), (255, 0, 0) )
    do_fan_points( (xb, yb), (xr, yr), (xg, yg), (0, 0, 255), (255, 0, 0), (0, 255, 0) )

    # ------------------------------------------------------------------

    save_img( img, "color-triangle-wireframe" )

# -----------------------------------------------------------------------------------
#   This was a bit of work.
#   /// I would still like to avoid traversing entire image, just work within triangle. Think some more.

def mk_color_triangle_solid( size ):

    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )
    (xsize, ysize) = size

    # ------------------------------------------------------------------
    #   Pick three cordinates for vertices

    xr = xsize * .1
    yr = ysize * .05

    xg = xsize * .9
    yg = ysize * .05

    xb = xsize * .5
    yb = ysize * .95

    if False:   #   Useful for testing
        xr = random.randint( 100, xsize )
        yr = random.randint( 100, ysize )

        xg = random.randint( 100, xsize )
        yg = random.randint( 100, ysize )

        xb = random.randint( 100, xsize )
        yb = random.randint( 100, ysize )

    lrg = math.sqrt( (xg - xr)**2 + (yg - yr)**2 )  # len of each edge
    lgb = math.sqrt( (xb - xg)**2 + (yb - yg)**2 )
    lbr = math.sqrt( (xr - xb)**2 + (yr - yb)**2 )

    # ------------------------------------------------------------------
    #   Cross Product
    #   (x1, y1) x (x2, y2) = (x1*y2 - x2*y1)
    #       a          b
    #    a[0] a[1]  b[0] b[1]

    def x_prod( a, b ):
        return a[0] * b[1] - b[0] * a[1]

    # ------------------------------------------------------------------
    #   Decide if point is within triangle. Inside if cross products of
    #     line from point to vertex and line between vertices have same sign.

    for x in range( xsize ):
        for y in range( ysize ):

            xp1 = x_prod( (xr - xg, yr - yg ), ( x - xg, y - yg )  )
            xp2 = x_prod( (xg - xb, yg - yb ), ( x - xb, y - yb )  )
            xp3 = x_prod( (xb - xr, yb - yr ), ( x - xr, y - yr )  )

            if(  ((xp1 < 0) and (xp2 < 0) and (xp3 < 0) ) or
                 ((xp1 > 0) and (xp2 > 0) and (xp3 > 0) ) ):

                # --------------------------------------------------
                # If point (x, y) is inside the triangle, compute color.
                #   Color is ( 1 - ratio of len from vertex to point            
                #     to average len of adjacent sides ) * 255

                dr = math.sqrt( (xr - x)**2 + (yr - y)**2 )     # len from each vertex to point
                dg = math.sqrt( (xg - x)**2 + (yg - y)**2 )
                db = math.sqrt( (xb - x)**2 + (yb - y)**2 )

                rgb_flag = 1
                if rgb_flag:
                    r = int( (1 - (dr*2.)/( lrg + lbr ) ) * 255 )
                    g = int( (1 - (dg*2.)/( lrg + lgb ) ) * 255 )
                    b = int( (1 - (db*2.)/( lgb + lbr ) ) * 255 )
                    d.point( (x, y ), fill=(r, g, b) )

                # --------------- /// testing ------------------------
                else:   # Not very interesting.
                # (h, s, v) = colorsys.rgb_to_hsv(r, g, b)
                # (r, g, b) = colorsys.hsv_to_rgb(h, s, v)

                    h = (1 - (dr*2.)/( lrg + lbr ) )
                    s = (1 - (dg*2.)/( lrg + lgb ) )
                    v = (1 - (db*2.)/( lgb + lbr ) )
                    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
                    d.point( (x, y ), fill=(int(r*255), int(g*255), int(b*255)) )

                # --------------- /// testing ------------------------

    save_img( img, "color-triangle-solid" )

# -----------------------------------------------------------------------------------
#   Draw series of lines labeled with specific length in pixels

def mk_len_cali_hori( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )
    font = ImageFont.load( "pilfonts/helvR10.pil" )

    if text_flag:
        length = 100
    else:
        length = 10

    (xsize, ysize) = size
    gap = .1 * min( xsize, ysize )
    xmax = .95 * xsize
    ymax = .95 * ysize
    ypos = .05 * ysize
    xpos = .05 * xsize

    len = length

    while ypos <= ymax and (xpos + len) <= xmax:
        d.line( ((xpos, ypos), (xpos + len-1, ypos)), fill="#ffffff" )

        if text_flag:
            text = "%d" % len
            fsize = my_textsize( d,  text, font=font )
            xtext = xpos - fsize[0] - 8
            ytext = ypos - fsize[1]/2
            d.text( (xtext, ytext), text, fill="#ffffff", font=font )

        ypos += gap
        len += length

    save_img( img, "check-length-hori" )

# -----------------------------------------------------------------------------------

def mk_len_cali_vert( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    if text_flag:
        length = 100
    else:
        length = 10

    (xsize, ysize) = size
    gap = .1 * min( xsize, ysize )
    xmax = .95 * xsize
    ymax = .95 * ysize

    # Draw series of horizontal lines

    ypos = .05 * ysize
    xpos = .05 * xsize
    len = length

    while xpos <= xmax and (ypos + len) <= ymax:
        d.line( ((xpos, ypos), (xpos, ypos + len-1)), fill="#ffffff" )

        if text_flag:
            text = "%d" % len
            font = ImageFont.load( "pilfonts/helvR10.pil" )
            fsize = my_textsize( d,  text, font=font )
            xtext = xpos - fsize[0]/2
            ytext = ypos - fsize[1] - 8
            d.text( (xtext, ytext), text, fill="#ffffff", font=font )

        xpos += gap
        len += length

    save_img( img, "check-length-vert" )

# -----------------------------------------------------------------------------------

def mk_len_cali_both( size ):
    mk_len_cali_hori( size )
    mk_len_cali_vert( size )

# -----------------------------------------------------------------------------------

def mk_squares_log( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    pitch = 1

    xstart = 0
    ystart = 0

    while xstart < size[0] and ystart < size[1]:
        x = xstart
        y = ystart

        while x < size[0]:
            d.rectangle( ((x, y), (x+pitch-1, y+pitch-1)), fill="#ffffff" )
            x += 2*pitch

        x = xstart
        y = ystart
        while y < size[1]:
            d.rectangle( ((x, y), (x+pitch-1, y+pitch-1)), fill="#ffffff" )
            y += 2*pitch

        npitch = pitch * math.sqrt( 2 )     # Double pitch every two iterations

        ystart += (pitch + npitch)          # Average old and new pitch for increment
        xstart += (pitch + npitch)

        pitch = npitch

    save_img( img, "geometry-checkers-log" )
    save_img( ImageOps.invert( img ), "geometry-checkers-log-inv" )

# -----------------------------------------------------------------------------------
#   pitch of 1 would make a point, already did that

def mk_squares_all( size ):
    pitches = ( 2, 4, 8, 16, 32 )
    for pitch in pitches:
        mk_squares_one( size, pitch )

# -----------------------------------------------------------------------------------

def mk_squares_one( size, pitch ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    for x in range( 0, size[0], 2 * pitch):
        for y in range( 0, size[1], 2 * pitch):
            d.rectangle( ((x, y), (x+pitch-1, y+pitch-1)), fill="#ffffff" )

    save_img( img, "geometry-squares-" + "%02d" % pitch )

# -----------------------------------------------------------------------------------

def mk_checkers_all( size ):
    pitches = ( 2, 4, 8, 16, 32 )
    for pitch in pitches:
        mk_checkers_one( size, pitch )

# -----------------------------------------------------------------------------------

def mk_checkers_one( size, pitch ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    toggle = 0
    for y in range( 0, size[1], pitch):

        shift = pitch if toggle % 2 else 0
        toggle += 1

        for x in range( 0, size[0], 2 * pitch):
            d.rectangle( ((x + shift, y), (x + pitch-1 + shift, y + pitch-1)), fill="#ffffff" )

    save_img( img, "geometry-checkers-" + "%02d" % pitch )

# -----------------------------------------------------------------------------------
#   Leave extra gap at right/bottom for part of last bar

def mk_bars_bw_vert( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    pitches = ( 2, 4, 8, 16 )
    groups = len( pitches )

    width = .9 * size[0]/groups
    gap = (size[0] - groups * width)/ (groups-1)
    xstart = 0

    for pitch in pitches:
        mk_bars_bw_vert_one( d, size, xstart, width, pitch )
        xstart += width + gap

    save_img( img, "geometry-bars-vert" )

# -----------------------------------------------------------------------------------

def mk_bars_bw_vert_one( d, size, xstart, width, pitch ):
    x = xstart

    while x < xstart + width:
        d.rectangle( ((x, 0), (x + pitch - 1, size[1]-1)), fill="#ffffff" )
        x += 2 * pitch

# -----------------------------------------------------------------------------------

def mk_bars_bw_hori( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    pitches = ( 2, 4, 8, 16 )
    groups = len( pitches )

    height = .9 * size[1]/groups
    gap = (size[1] - groups * height)/ (groups-1)
    ystart = 0

    for pitch in pitches:
        mk_bars_bw_hori_one( d, size, ystart, height, pitch )
        ystart += height + gap

    save_img( img, "geometry-bars-hori" )

# -----------------------------------------------------------------------------------

def mk_bars_bw_hori_one( d, size, ystart, height, pitch ):
    y = ystart

    while y < ystart + height:
        d.rectangle( ((0, y), (size[0]-1, y + pitch - 1)), fill="#ffffff" )
        y += 2 * pitch

# -----------------------------------------------------------------------------------
#   Composite of colored and gray squares with more colors than in other patterns
#   Fixed at 12 boxes horizontally

def mk_composite( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    # ----------------------------------------------------------------------------------

    xcnt = 12
    layout = ( xcnt, 6 )
    gap = int( size[0] * .005 )
    bgap = 0 * gap

    cell = ((size[0] - 1.* gap * ( layout[0] -1 ) - bgap * 2) / layout[0],
            (size[1] - 1.* gap * ( layout[1] -1 ) - bgap * 2) / layout[1] )

    p_color_wipe = 0
    p_color_boxes = 1
    p_patterns = 2
    p_gamma = 3
    p_gray_boxes = 4
    p_gray_wipe = 5

    # ----------------------------------------------------------------------------------
    #   Colors boxes. Now generating in hsv instead of fixed array of colors

    ypos = bgap + (cell[1] + gap) * p_color_boxes
    s = v = 1

    for i in range( xcnt ):
        h = i * 1./xcnt
        color = [int( x * 255 ) for x in colorsys.hsv_to_rgb(h, s, v)]
        xpos = bgap + i * ( cell[0] + gap )
        d.rectangle( (( xpos, ypos ), (xpos + cell[0]-1, ypos + cell[1]-1)), tuple(color) )

        if text_flag:
            do_text_label( d, color, xpos, ypos, cell )

    # ----------------------------------------------------------------------------------
    #   Gray boxes

    ypos = bgap + (cell[1] + gap) * p_gray_boxes
    gray_step = 255./(xcnt-1)

    for x in range( xcnt ):
        xpos = bgap + x * (cell[0] + gap )
        igray = int( x * gray_step )
        d.rectangle( (( xpos, ypos ), (xpos + cell[0]-1, ypos + cell[1]-1)), ( igray,)*3  )

        if text_flag:
            do_text_label( d, (igray,)*3, xpos, ypos, cell )

    # ----------------------------------------------------------------------------------
    #   Gray Wipe

    ypos = bgap + (cell[1] + gap) * p_gray_wipe

    steps = (cell[0] * xcnt + gap * ( xcnt - 1))
    gray_step = 255./steps

    for x in range( int( steps )):
        xpos = x + bgap
        igray = int( gray_step * x )
        d.line( ((xpos,ypos), (xpos, ypos+cell[1]-1)), fill=(igray,)*3 )

    # ----------------------------------------------------------------------------------
    #   Color wipes

    ypos = bgap + (cell[1] + gap) * p_color_wipe

    steps = (cell[0] * xcnt + gap * (xcnt - 1))
    gray_step = 255./steps
    ystep = cell[1]/3

    for x in range( int( steps ) ):
        igray = int( x * gray_step )
        xpos = bgap + x

        for (y, color) in enumerate( ((1,0,0), (0,1,0), (0,0,1))):
            color = np.array( color )
            yoff = y * ystep
            d.line( ((xpos,ypos+yoff), (xpos, ypos + yoff + ystep-1 )), fill=tuple(igray*color) )

    # ----------------------------------------------------------------------------------
    #   Patterns. Exactly xcnt.

    ypos = bgap + (cell[1] + gap) * p_patterns
    xpos = bgap

    for pat in composite_pats:
        ti = get_image_from_pattern( cell, pat, (255,)*3 )
        img.paste( ti, (int(xpos), int(ypos)) )
        xpos += cell[0] + gap

    # ----------------------------------------------------------------------------------
    #   Gamma strip

    ypos = bgap + (cell[1] + gap) * p_gamma      
    xpos = bgap

    gammas = ( 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0 )     # need exactly xcnt

    for (x, gamma) in enumerate( gammas ):

        val = (.5 ** (1./gamma)) * 255.
        gray = int( val )      

        background_ti = get_image_from_pattern( (cell[0]-1, cell[1]-1), pat_hlines_2, (255,)*3 )
        img.paste( background_ti, (int(xpos), int(ypos)) )
        d.rectangle( (int(xpos + cell[0]/4), int(ypos + cell[1]/4), (int(xpos + cell[0]*3/4 -1), int(ypos + cell[1]*3/4-1)) ), fill=(gray, gray, gray))

        # ----------------------------
        if text_flag:
            text = "%.1f" % gamma
            font = ImageFont.load( "pilfonts/helvR08.pil" )
            fsize = my_textsize( d,  text, font=font )

            xtext = xpos + cell[0]/2  - fsize[0]/2
            ytext = ypos + cell[1]*3/4 - fsize[1] - 4

            if gray > 128:
                d.text( (xtext, ytext), text, fill="#000000", font=font )
            else:
                d.text( (xtext, ytext), text, fill="#ffffff", font=font )

        # ----------------------------

        xpos += cell[0] + gap

    # ----------------------------------------------------------------------------------

    save_img( img, "check-composite" )

# -----------------------------------------------------------------------------------

def mk_patterns_with_background( size ):
    img =  Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    # layout = (5, 4)
    layout = (7, 4)
    gap = size[0] * .005
    
    gray_cell = ((size[0] - gap * (layout[0]+1)) / layout[0],
                 (size[1] - gap * (layout[1]+1)) / layout[1] )
    
    pat_cell = ( gray_cell[0]/2, gray_cell[1]/2 )
    
    patoffx = (gray_cell[0]-pat_cell[0])/2
    patoffy = (gray_cell[1]-pat_cell[1])/2
    
    for i, pat in enumerate( background_pats ):

        xpos = int(i % layout[0]) * (gray_cell[0] + gap) + gap
        ypos = int(i / layout[0]) * (gray_cell[1] + gap) + gap

        ti = get_image_from_pattern( pat_cell, pat, (255, 255, 255) )
        gray = int( density( pat ) * 255)
    
        d.rectangle( (xpos, ypos, xpos + gray_cell[0] - 1, ypos + gray_cell[1] - 1), fill=(gray, gray, gray) )
        img.paste( ti, (int(xpos + patoffx), int(ypos + patoffy )) )

        if text_flag:
            text = "%d" %  gray
            font = ImageFont.load( "pilfonts/helvR10.pil" )
            fsize = my_textsize( d,  text, font=font )
            xtext = xpos + gray_cell[0]/2 - fsize[0]/2
            ytext = ypos + gray_cell[1] - fsize[1] - 8

            if gray > 128:
                d.text( (xtext, ytext), text, fill="#000000", font=font )
            else:
                d.text( (xtext, ytext), text, fill="#ffffff", font=font )
    
    save_img( img, "check-patterns-background" )

# -----------------------------------------------------------------------------------

def mk_patterns( size ):
    img =  Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

  # layout = (5, 4)
    layout = (7, 4)
    gap = size[0] * .005
    
    pat_cell = ((size[0] - gap * (layout[0]+1)) / layout[0],
                (size[1] - gap * (layout[1]+1)) / layout[1] )
    
    for i, pat in enumerate( background_pats ):
        xpos = int(i % layout[0]) * (pat_cell[0] + gap) + gap
        ypos = int(i / layout[0]) * (pat_cell[1] + gap) + gap

        ti = get_image_from_pattern( pat_cell, pat, (255, 255, 255) )
        img.paste( ti, (int(xpos), int(ypos)) )
    
    save_img( img, "check-patterns" )

# -----------------------------------------------------------------------------------
#   v determines starting point. Swatches decrease from there

def mk_color_swatches_rgb( size ):
    for v in (255, 191, 127, 64 ):
        mk_color_swatch_rgb( size, v, "fix-red-%03d-var-green-blue" % v, (1,0,0), (0,1,0), (0,0,1) )
        mk_color_swatch_rgb( size, v, "fix-green-%03d-var-blue-red" % v, (0,1,0), (0,0,1), (1,0,0) )
        mk_color_swatch_rgb( size, v, "fix-blue-%03d-var-red-green" % v, (0,0,1), (1,0,0), (0,1,0) )

# -----------------------------------------------------------------------------------
#   Hold one color constant and vary the other two in x & y
#   constant, var_x, var_y are (r,g,b) color tuples (1,0,0) (0,1,0), etc.
#   Remember 2 of r, g, b goes from 0 to gray - 255, 63, etc.,
#     while the other stays at constant gray.

def mk_color_swatch_rgb( size, gray, name, constant, var_x, var_y ):
    img =  Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    vert_cnt = 8
    layout = (int(1.* vert_cnt * size[0]/size[1]), vert_cnt )
    gap = size[0] * .005

    ci = ( 1.*gray/(layout[0]-1),  1.* gray/(layout[1]-1) )          

    cell = ((1.* size[0] - gap * (layout[0]+1)) / layout[0],
            (1.* size[1] - gap * (layout[1]+1)) / layout[1] )

    for x in range(layout[0]):
        xpos = gap + x * (cell[0] + gap)
        for y in range(layout[1]):
            ypos = gap + y * (cell[1] + gap)

            #   This is far simpler and clearer than the approach used previously of adding/resetting
            #     in conditionals or closed-form expressions. Even cleaner with map() and lambda()

            color = [int(round(constant[i] * gray + x * var_x[i] * ci[0] + y * var_y[i] * ci[1])) for i in range( 3 )]
            d.rectangle( ((xpos, ypos), (xpos + cell[0]-1, ypos + cell[1]-1)), tuple(color) )

            if text_flag:
                do_text_label( d, color, xpos, ypos, cell )

    save_img( img, "swatch-rgb-" + name )

# -----------------------------------------------------------------------------------
#   Vary hue by 30 degrees, 12 steps
#   0 red, 30 yellow-red, 60 yellow, 90 yellow-green, 120 green, 150 green-cyan
#   180 cyan, 210 cyan-blue, 240 blue, 270 blue-magenta, 300 magenta, 330 magenta-red

hues = (
        (0, "red"), (30, "yellow-red"), (60, "yellow"),
        (90, "yellow-green"), (120, "green"), (150, "green-cyan"),
        (180, "cyan"), (210, "cyan-blue"), (240, "blue"),
        (270, "blue-magenta"), (300, "magenta"), (330, "magenta-red")
       )

def mk_color_swatches_hsv( size ):
    for (hv, name) in hues:
        h = hv/360.
        mk_color_swatch_hsv( size, name, h )

# -----------------------------------------------------------------------------------
#   h is constant, vary s & v

def mk_color_swatch_hsv( size, name, h ):
    img =  Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    vert_cnt = 8
    layout = (int(1.* vert_cnt * size[0]/size[1]), vert_cnt )
    gap = size[0] * .005

    vi = 1./(layout[1]-1)
    si = 1./(layout[0]-1)

    cell = ((1.* size[0] - gap * (layout[0]+1)) / layout[0],
            (1.* size[1] - gap * (layout[1]+1)) / layout[1] )

    for x in range(layout[0]):
        xpos = gap + x * (cell[0] + gap)
        s = 1.0 - si * x

        for y in range(layout[1]):
            ypos = gap + y * (cell[1] + gap)
            v = 1.0 - vi * y

            color = [int( round( x * 255. )) for x in colorsys.hsv_to_rgb(h, s, v)]
            d.rectangle( ((xpos, ypos), (xpos + cell[0]-1, ypos + cell[1]-1)), tuple( color ) )

            if text_flag:
                do_text_label( d, color, xpos, ypos, cell )

    save_img( img, "swatch-hsv-fix-hue-%s-var-sat-val" % name )

# -----------------------------------------------------------------------------------
#   Vary hue by 30 degrees, 12 steps
#   0 red, 30 yellow-red, 60 yellow, 90 yellow-green, 120 green, 150 green-cyan
#   180 cyan, 210 cyan-blue, 240 blue, 270 blue-magenta, 300 magenta, 330 magenta-red


def mk_color_swatches_hsl( size ):
    for (hv, name) in hues:
        h = hv/360.
        mk_color_swatch_hsl( size, name, h )

# -----------------------------------------------------------------------------------
#   h is constant, vary s & l

def mk_color_swatch_hsl( size, name, h ):
    img =  Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    vert_cnt = 8
    layout = (int(1.* vert_cnt * size[0]/size[1]), vert_cnt )
    gap = size[0] * .005

    li = 1./(layout[1]-1)
    si = 1./(layout[0]-1)

    cell = ((1.* size[0] - gap * (layout[0]+1)) / layout[0],
            (1.* size[1] - gap * (layout[1]+1)) / layout[1] )

    for x in range(layout[0]):
        xpos = gap + x * (cell[0] + gap)
        s = 1.0 - si * x

        for y in range(layout[1]):
            ypos = gap + y * (cell[1] + gap)
            l = 1.0 - li * y

            color = [int( round( x * 255.) ) for x in colorsys.hls_to_rgb(h, l, s)]
            d.rectangle( ((xpos, ypos), (xpos + cell[0]-1, ypos + cell[1]-1)), tuple( color) )

            if text_flag:
                do_text_label( d, color, xpos, ypos, cell )

    save_img( img, "swatch-hsl-fix-hue-%s-var-sat-lev" % name )

# -----------------------------------------------------------------------------------
#   One common routine for all swatches. hsv on top, hsl just under, rgb at bottom

def do_text_label( d, color, xpos, ypos, cell ):
    font = ImageFont.load( "pilfonts/helvR08.pil" )

    (r, g, b) = color

    if luma3( r, g, b ) > 128:
        fill="#000000"
    else:
        fill="#ffffff"

    text_rgb = "%d  %d  %d" %  (r, g, b)
    fsize = my_textsize( d,  text_rgb, font=font )
    if fsize[0] <= cell[0]:
        xtext = xpos + cell[0]/2 - fsize[0]/2
        ytext = ypos + cell[1] - fsize[1] - 4
        d.text( (xtext, ytext), text_rgb, fill=fill, font=font )


    text_hsv = "%.3f  %.3f  %.3f" % colorsys.rgb_to_hsv(r/255., g/255., b/255.)
    fsize = my_textsize( d,  text_hsv, font=font )
    if fsize[0] <= cell[0]:
        xtext = xpos + cell[0]/2 - fsize[0]/2
        ytext = ypos + 4
        d.text( (xtext, ytext), text_hsv, fill=fill, font=font )

    text_hsl = "%.3f  %.3f  %.3f" % colorsys.rgb_to_hls(r/255., g/255., b/255.)
    fsize = my_textsize( d,  text_hsl, font=font )
    if fsize[0] <= cell[0]:
        xtext = xpos + cell[0]/2 - fsize[0]/2
        ytext = ypos + 4 + fsize[1] + 4
        d.text( (xtext, ytext), text_hsl, fill=fill, font=font )

# -----------------------------------------------------------------------------------
#   Title
#   Font sizes: 08, 10, 12, 14, 18, 24

def mk_title( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    texts = ( 
        ( 24, "Monitor / TV Test Images" ),
        ( 18, "Family: " + writer.get_res_id() ),
        ( 14, "Copyright 2014, 2026 - Bill Wetzel" ),
        ( 14, "" ),
        ( 12, "You may display these images for any purpose, personal, educational, or commercial." ),
        ( 12, "You may not distribute these images for any purpose without permission, in writing," ),
        ( 12, "which I have always granted but I want to know about the use." ),
        ( 12, "" ),
        ( 12, "Please let me know if you found these images useful." ),
        ( 12, "" ),
        ( 12, "Bill Wetzel" ),
        ( 12, "testimages@wrwetzel.com" ),
        ( 12, "" ),
        ( 12, "" ),
        ( 12, "" ),
        ( 12, "" ),
        ( 12, "Version: " + version_str ),
        ( 12, "Generated: " + time.strftime( "%A, %d %b %Y, %I:%M:%S %p" )),
    )

    xpos = size[0] * .12
    ypos = size[1] * .12

    if text_flag:
        for (size, text) in texts:
            font = ImageFont.load( "pilfonts/helvR%d.pil" % size )
            fsize = my_textsize( d,  text, font=font )
            d.text( (xpos, ypos), text, fill="#ffffff", font=font )
            ypos += fsize[1] * 1.06
    else:
            font = ImageFont.load( "pilfonts/helvR08.pil")
            # fsize = my_textsize( d,  text, font=font )
            d.text( (xpos, ypos), "Copyright 2014, 2023", fill="#ffffff", font=font )
            ypos += 14
            d.text( (xpos, ypos), "Bill Wetzel", fill="#ffffff", font=font )
            ypos += 14
            d.text( (xpos, ypos), "Version: " + version_str, fill="#ffffff", font=font )
            ypos += 14
            d.text( (xpos, ypos), time.strftime( "%A, %d %b %Y" ), fill="#ffffff", font=font )

    save_img( img, "banner" )                     

# -----------------------------------------------------------------------------------
#   pat_hlines_solid_8    # Just for testing pat_gray/pat_gray_bg colors, more visible.
#   pat_squares_2         # Not the best, didn't show issue as well as others.
#   pat_checker_square_2  # Very good, use
#   pat_hlines_2          # Very good, use

def mk_calibrate_contrast( size ):
    mk_calibrate_contrast_one( size, "checker", pat_checker_square_2 )
    mk_calibrate_contrast_one( size, "lines",   pat_hlines_2 )

# -----------------------------------------------------------------------------------
#   Gray values similar to image found on web.
#   WRW 13 Mar 2023 - Concerns about integer division are moot because numerator values below
#       are all floats. Thus division yields float quotient.
#   WRW 13 Mar 2023 - I'm not sure what this is useful for, why I did it. Lots of redundancy,
#       especially in the y axis.

def mk_calibrate_contrast_one( size, name, pat ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    levels = (
               ( 0x38, 0x50, 0x00  ),       # solid_gray, pat_gray, pat_gray_bg
               ( 0x50, 0x75, 0x00  ),
               ( 0x75, 0xaf, 0x00  ),
               ( 0xaf, 0xff, 0x00  ),
               ( 0xda, 0xff, 0xaf  ),
             )

    hori_cnt = 10   # This should be integral to len(levels)
    layout = ( hori_cnt, int( 1.* hori_cnt * size[1]/size[1]) )     # Looks like I kept the formula the same despite the degeneracy

    gap = size[0] * .004

    xcell = (( 1. * size[0] - gap * (layout[0]+1))/layout[0])
    ycell = (( 1. * size[1] - gap * (layout[1]+1))/layout[1])

    for y in range( layout[1] ):
        ypos = gap + y * (ycell + gap)
        for x in range( layout[0] ):
            xpos = gap + x * (xcell + gap)
            ilevels = x % len(levels)

            solid_gray =  levels[ ilevels ][0]
            pat_gray =    levels[ ilevels ][1]
            pat_gray_bg = levels[ ilevels ][2]

            # gamma = 1.0     # Midpoint of 1.8 / 2.2
            # solid_gray = int( (.5 ** (1./gamma)) * solid_gray )

            # Tried lined box against solid background.
            # Solid box against lined background show issue better.

            background_ti = get_image_from_pattern_with_bg( (xcell-1, ycell-1), pat,
                         ( pat_gray, pat_gray, pat_gray), (pat_gray_bg,  pat_gray_bg, pat_gray_bg) )

            img.paste( background_ti, (int(xpos), int(ypos)) )
            d.rectangle( ((xpos + xcell/4, ypos + ycell/4), (xpos+xcell*3/4 - 1, ypos+ycell*3/4 - 1)),
                           fill=(solid_gray, solid_gray, solid_gray))

    save_img( img, "check-contrast-" + name )

# -----------------------------------------------------------------------------------

def mk_gamma_combined( size ):
    mk_gamma_combined_one( size, "checker", pat_checker_square_2 )
    mk_gamma_combined_one( size, "lines",   pat_hlines_2 )

# -----------------------------------------------------------------------------------

def mk_gamma_combined_one( size, name, pat ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    gammas = ( 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6 )
    layout = ( len( gammas ), 4 )
    gap = size[0] * .004

    xcell = (( 1.* size[0] - gap * (layout[0]+1))/layout[0])
    ycell = (( 1. *size[1] - gap * (layout[1]+1))/layout[1])

    for i_color, y in enumerate( range( layout[1] )):
        ypos = gap + y * ( ycell + gap )
        color = np.array( colors_3g[ i_color ][1] )     # [0] is name, [1] is color mask

        for i_gamma, x in enumerate( range( layout[0] )):
            xpos = gap + x * ( xcell + gap )
            gamma = gammas[ i_gamma ]
            val = (.5 ** (1./gamma)) * 255.
            gray = int( val ) * color                                                  

            center_pattern = 0
            if center_pattern:
                d.rectangle( ((xpos,ypos), xpos+xcell-1, ypos+ycell-1), fill=gray)
                center_ti = get_image_from_pattern( (xcell/2, ycell/2), pat, tuple(255 * color) )
                img.paste( center_ti, (int(xpos + xcell/4), int(ypos + ycell/4)) )

            else:   # center solid, like better
                background_ti = get_image_from_pattern( (xcell-1, ycell-1), pat, tuple(255 * color) )
                img.paste( background_ti, (int(xpos), int(ypos)) )
                d.rectangle( (int(xpos + xcell/4), int(ypos + ycell/4), (int(xpos + xcell*3/4 -1), int(ypos + ycell*3/4-1)) ), fill=tuple(gray))

            # ----------------------------
            if text_flag:
                text = "%.1f" % gamma
                font = ImageFont.load( "pilfonts/helvR10.pil" )
                fsize = my_textsize( d,  text, font=font )

                xtext = xpos + xcell/2 - fsize[0]/2
                # ytext = ypos + ycell/4 - fsize[1] - 4     # for center pattern
                ytext = ypos + ycell*3/4 - fsize[1] - 4

                if luma3( gray[0], gray[1], gray[2] ) > 128:
                    d.text( (xtext, ytext), text, fill="#000000", font=font )
                else:
                    d.text( (xtext, ytext), text, fill="#ffffff", font=font )
            # ----------------------------

    save_img( img, "check-gamma-" + name )

# -----------------------------------------------------------------------------------
#   Prototype generator

def mk_prototype( size ):
    img = Image.new( "RGB", size )
    d = ImageDraw.Draw( img )

    save_img( img, "prototype" )

# -----------------------------------------------------------------------------------
#   Notes:
#       .jpg had artifact on color bars at edge of some bars, .png did not.

# -----------------------------------------------------------------------------------

help_text = """
Generates one or more families of image files of shapes determined by an
internal list or given by the -x and -y options.  The image files are
written in directories named for the family.  Those directories are
located in output_dir, default "Output" in the home directory.  The output
file names consist of a prefix formed from the family name and shape and
an image-specific identifier.

-o output_dir
    Saves output images in output_dir, default "Output" in current directory.

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
    Start with shape identified by index first and advance to next shape by adding step to index.

"""

def do_help( more_flag, shapes ):
    print('mk-patterns.py [-t] [-v] [-V] [-h] [-o output_dir] [-c output_type] [-x user_width] [-y user_height]')
    if more_flag:
        print(help_text)
        print("Version:", version_str)
        print()
        print("Family and Shape")
        for shape in shapes:
            print("%s: %d x %d" % ( shape[0], shape[1], shape[2] ))

# -----------------------------------------------------------------------------------
#   Control Parameters
#   WRW 9 March 2016 - added ( "HDTV", 3840, 2160 ), ( "HDTV", 4096, 2160 ) in response to email request.

#   WRW 12 Mar 2023 - Changed names, added a few
#       See: https://en.wikipedia.org/wiki/Computer_display_standard
#       A few of the monotor resolution names have a few other associated resolutions.
#       Only the first one is included here.

def get_shapes( test_flag ):
    if not test_flag:

        # shapes = (        # Ouch! Uncompressed output size: 297,119,744 Bytes, compressed: 257,371,010 Bytes
        #     ( "8k-UHD", 7680, 4320 ),     # 8k, 4320i/p, 8k UHD, Ultra HD UHD,   WRW 23 Mar 2023 - added, and removed, too big, taking ages
        # )

        shapes = ( 
            ( "Thumb",  160, 100 ),       # Golden exactly 161.8, 160 is off by 1.112%, no one will notice. Make it 162?

         #  ( "VGA",    640,  480 ),      # WRW 12 Mar 2023 - added and commented out, likely no interest
         #  ( "SVGA",   800,  600 ),      # WRW 12 Mar 2023 - added and commented out, likely no interest
            ( "XGA",    1024, 768 ),
            ( "WXGA",   1280, 800 ),
            ( "SXGA",   1280, 1024 ),
            ( "WXGA+",  1440, 900 ),
            ( "HD+",    1600, 900 ),
            ( "UXGA",   1600, 1200 ),
            ( "WSXGA+", 1680, 1050 ),
            ( "WUXGA",  1920, 1200 ),     # WRW 12 Mar 2023 -added, WRW 28 Nov 2023 - changed 1900 to 1920 per 'Shawn'.
            ( "QHD",    2560, 1440 ),     # Large monitor - WRW 12 Mar 2023 - added
            ( "WQXGA",  2560, 1600 ),     # WRW 12 Mar 2023 -added

         #  ( "DVD",    852, 480 ),       # Not a display (TV, monitor) resolution, no reason to generate, WRW 23 Mar 2023 - removed

            ( "NTSC",   720, 480 ),
            ( "PAL",    720, 576 ),
            ( "HD",     1280, 720 ),      # 720i/p, HD, HD Ready,
            ( "FHD",    1920, 1080 ),     # 1080i/p, full HD, FHD
            ( "UHD",    3840, 2160 ),     # 4k, 2160i/p, Ultra HD UHD, Dominant 4K resolution
         #  ( "8k-UHD", 7680, 4320 ),     # 8k, 4320i/p, 8k UHD, Ultra HD UHD,   WRW 23 Mar 2023 - added, and removed, too big, taking ages

         #  ( "DCI",    4096, 2160 ),     # AKA SMPTE-UHDTV, SMPTE 4K-4096x2160, mostly projectors, WRW 23 Mar 2023 - removed
        )

    else:
        shapes = (
            ( "WXGA", 1280, 800 ),
            ( "Thumb", 160, 100 ),
        )

        shapes = (
            ( "WXGA", 1280, 800 ),
        )

    return shapes

# -----------------------------------------------------------------------------------
# WRW 13 Mar 2023 - Added parallization

def make_all_shapes( shapes, first, step, test_flag, verbose ):
    for i in range( first, len( shapes ), step ):     
        make_one_shape( shapes[ i ], test_flag, verbose )

# -----------------------------------------------------------------------------------

def make_one_shape( shape, test_flag, verbose ):
    global text_flag

    writer.new_shape( shape, verbose )

    size = (shape[1], shape[2])

    if size[0] < 200:       # Assume thumbnail if x < 200
        text_flag = False
    else:
        text_flag = True

    # ----------------------------------

    if not test_flag:
        mk_title( size )
        mk_composite( size )
        mk_patterns( size )
        mk_patterns_with_background( size )
        mk_bars_bw_hori( size )
        mk_bars_bw_vert( size )
        mk_calibrate_contrast( size )
        mk_checkers_all( size )
        mk_clippings( size )
        mk_color_bars_all( size )
      # mk_colors_all_a( size )        # Omit for now
        mk_colors_all_b( size )
        mk_color_swatches_hsl( size )
        mk_color_swatches_hsv( size )
        mk_color_swatches_rgb( size )
        mk_color_triangle( size )
        mk_color_triangle_solid( size )
        mk_gammas( size )
        mk_gamma_combined( size )
        mk_grid( size )
        mk_hconverge( size )
        mk_hlines( size )
        mk_len_cali_both( size )
        mk_loghlines( size )
        mk_logvlines( size )
        mk_many_circles( size )
        mk_many_squares( size )
        mk_one_circle( size )
        mk_overscan( size )
        mk_points( size )
        mk_resolutions( size )
        mk_random_gray( size )
        mk_random_rgb( size )
        mk_solids( size )
        mk_squares_all( size )
        mk_squares_log( size )
        mk_star( size )
        mk_targets_all( size )
        mk_vconverge( size )
        mk_vlines( size )
        mk_wedges_log( size )     # not very interesting
        mk_wedges( size )
        mk_color_step_wipes_composite( size )
        mk_colors_rgb( size )
        mk_colors_hsv( size )
        mk_colors_hsl( size )
        mk_wipes_all_colors( size )
        mk_wipes( size )

    # ----------------------------------
    #   test_flag

    else:                           # Put images under test here
        mk_title( size )
        mk_composite( size )

    # ----------------------------------

    if verbose:
        print("Generated %d files" % writer.get_ofile_list_len() )  # Check against file count to be sure no duplicate names
    
# -----------------------------------------------------------------------------------

def main( argv ):
    global writer, version_str

    first = 0       # WRW 13 Mar 2023 - Added for parallization
    step = 1        # WRW 13 Mar 2023 - Added for parallization
    user_shape_x = 0
    user_shape_y = 0
    user_shape_name = "User"
    show_parameters_flag = False
    verbose = False
    help_flag = False
    test_flag = False
    output_dir = "~/Output"
    output_type = "png"         # or jpg, tif, ... etc.

    # ---------------------------------------------------------------
    try:
        opts, args = getopt.getopt( argv, "htvVo:c:x:y:f:s:u:" )

    except getopt.GetoptError:
        print("Unrecognized command line argument")
        do_help( False, None )
        sys.exit(2)

    # ---------------------------------------------------------------

    for (opt, arg) in opts:
        if opt == '-t':
            test_flag = 1
            version_str += " testing"

        elif opt == "-o":
            output_dir = arg

        elif opt == "-c":
            output_type = arg

        elif opt == "-v":
            verbose = 1

        elif opt == "-h":
            help_flag = 1

        elif opt == "-V":
            show_parameters_flag = 1

        elif opt == '-x':
            user_shape_x = int(arg)

        elif opt == '-y':
            user_shape_y = int(arg)

        elif opt == '-u':
            user_shape_name = arg

        elif opt == '-f':       # WRW 13 Mar 2023 - Added for parallization
            first = int(arg)

        elif opt == '-s':       # WRW 13 Mar 2023 - Added for parallization
            step = int(arg)

    # ---------------------------------------------------------------

    writer = Writer()
    writer.set_output_dir( output_dir )
    writer.set_output_type( output_type )                                        

    shapes = get_shapes( test_flag )

    if help_flag:
        do_help( True, shapes )
        sys.exit(0)

    elif show_parameters_flag:
      # print("Version:", version_str)
        for shape in shapes:
            print("%s-%dx%d" % ( shape[0], shape[1], shape[2] ))
        sys.exit(0)

    elif user_shape_x > 0 and user_shape_y > 0:
        make_one_shape( ( user_shape_name, user_shape_x, user_shape_y ), test_flag, verbose )
        sys.exit(0)

    else:
        make_all_shapes( shapes, first, step, test_flag, verbose )
        sys.exit(0)

# -----------------------------------------------------------------------------------

if __name__ == "__main__":
   main( sys.argv[ 1: ] )

# -----------------------------------------------------------------------------------
