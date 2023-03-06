#!/bin/bash

image1=fits1.fits
if [[ -n "$1" && "$1" != "-" ]]; then
   image1=`basename $1`
fi

image2=fits2.fits
if [[ -n "$2" && "$2" != "-" ]]; then
   image2=`basename $2`
fi

diff_image=${image2%%.fits}_diff.fits
if [[ -n "$3" && "$3" != "-" ]]; then
   diff_image=`basename $3`
fi


image1_uv=${image1%%.fits}_tmp.uv
image2_uv=${image2%%.fits}_tmp.uv
diff_image_uv=${diff_image%%.fits}_tmp.uv

echo "rm -fr ${diff_image_uv} ${image1_uv} ${image2_uv}"
rm -fr ${diff_image_uv} ${image1_uv} ${image2_uv}

if [[ ! -d ${image1_uv} ]]; then
   echo "fits op=xyin in=${image1} out=${image1_uv}"
   fits op=xyin in=${image1} out=${image1_uv}
else
   echo "INFO : ${image1_uv} already exists"
fi

if [[ ! -d ${image2_uv} ]]; then
   echo "fits op=xyin in=${image2} out=${image2_uv}"
   fits op=xyin in=${image2} out=${image2_uv}
else
   echo "INFO : ${image2_uv} already exists"
fi   


echo "maths exp=\"($image1_uv-$image2_uv)\" out=${diff_image_uv}"
maths exp="($image1_uv-$image2_uv)" out=${diff_image_uv}


echo "fits op=xyout in=${diff_image_uv} out=${diff_image}"
fits op=xyout in=${diff_image_uv} out=${diff_image}

echo "rm -fr ${diff_image_uv} ${image1_uv} ${image2_uv}"
rm -fr ${diff_image_uv} ${image1_uv} ${image2_uv}






