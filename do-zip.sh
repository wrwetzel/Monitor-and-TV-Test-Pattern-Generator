#/bin/bash

#   Zip output files from mk_patterns.py. Got list of families here from
#       mk_patterns.py -V


# FAMILIES=" \
# 8k-UHD-7680x4320
# "

FAMILIES=" \
Thumb-160x100 \
XGA-1024x768 \
WXGA-1280x800 \
SXGA-1280x1024 \
WXGA+-1440x900 \
HD+-1600x900 \
UXGA-1600x1200 \
WSXGA+-1680x1050 \
WUXGA-1920x1200 \
QHD-2560x1440 \
WQXGA-2560x1600 \
NTSC-720x480 \
PAL-720x576 \
HD-1280x720 \
FHD-1920x1080 \
UHD-3840x2160 \
"
SRC_DIR=~/Output
ZIP_DIR=~/Output/Zip

if [[ ! -d $ZIP_DIR ]]
then
    mkdir $ZIP_DIR
fi

for FAMILY in $FAMILIES
do
    ( 
    if [[ -d $SRC_DIR/$FAMILY ]]
    then
        echo $FAMILY
        cd $SRC_DIR/$FAMILY
        if [[ -f $ZIP_DIR/$FAMILY.zip ]]
        then
            rm $ZIP_DIR/$FAMILY.zip   
        fi
        zip $ZIP_DIR/$FAMILY *            # Create new zip file from all images in family
    fi
    )

done
