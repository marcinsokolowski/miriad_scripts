import astropy.io.fits as pyfits
import numpy as np
import sys
import os
import errno
import getopt

# global parameters :
debug=0
fitsname="file.fits"
fitsname2="fits2.fits"
oper="/"
out_fitsname="sum.fits"
do_show_plots=0
do_gif=0

center_x=1025
center_y=1025
radius=600

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise
                                            
def usage():
   print("miriad_fits_div.py FITS_FILE1 OPERATION[*,-] FITS_FILE2 OUT_FITSFILE[default saved to FITS_FITS1]")
   print("\n")
   print("-d : increases verbose level")
   print("-h : prints help and exists")
   print("-g : produce gif of (channel-avg) for all integrations")

if len(sys.argv) > 1:
   fitsname = sys.argv[1]

if len(sys.argv) > 2:
   oper = sys.argv[2]

if len(sys.argv) > 3:
   fitsname2 = sys.argv[3]


out_fitsname=fitsname   
if len(sys.argv) > 4:
   out_fitsname = sys.argv[4]
   


print("####################################################")
print("PARAMTERS :")
print("####################################################")
print("fitsname        = %s" % fitsname)
print("oper            = %s" % oper)
print("fitsname2       = %s" % fitsname2)
print("out_fitsname   = %s" % out_fitsname)
print("####################################################")

fits = pyfits.open(fitsname)
x_size=fits[0].header['NAXIS1']
y_size=fits[0].header['NAXIS2']
print('Read fits file %s' % fitsname)
print('FITS size = %d x %d' % (x_size,y_size))

fits2 = pyfits.open(fitsname2)
x_size2=fits2[0].header['NAXIS1']
# channels=100
y_size2=fits2[0].header['NAXIS2']
print('Read fits file 2 %s' % fitsname)
print('FITS size 2 = %d x %d' % (x_size,y_size))

if x_size!=x_size2 or y_size!=y_size2 :
   print("ERROR : cannot execute operation %s on files of different sizes (%d,%d) != (%d,%d)" % (oper,x_size,y_size,x_size2,y_size2))
   exit;

# data1=fits[0].data[0][0]
data1 = None
if fits[0].data.ndim >= 4 :
   data1 = fits[0].data[0,0]
else :
   data1 = fits[0].data


# data2=fits2[0].data[0][0]
data2 = None
if fits2[0].data.ndim >= 4 :
   data2 = fits2[0].data[0,0]
else :
   data2 = fits2[0].data


print("DEBUG : shape = %d x %d" % (data1.shape[0],data1.shape[1]))

# print 'BEFORE (%d,%d) = %.2f' % (x_size/2,y_size/2,data[y_size/2][x_size/2])

data_out = np.zeros((x_size,y_size))

if oper == "*" : 
   data_out = data1 * data2

if oper == "-" : 
   data_out = data1 - data2

if oper == "/" : 
   with np.errstate(divide='ignore'):
      data_out = data1 / data2
   
   data_out[np.isnan(data_out)] = 0.00

if oper == "+" : 
   data_out = data1 + data2
            

if fits[0].data.ndim >= 4 :
   fits[0].data[0,0] = data_out
else :
   fits[0].data = data_out

fits.writeto(out_fitsname,overwrite=True)

# hdulist = pyfits.HDUList([hdu_out])
# hdulist.writeto(out_fitsname,overwrite=True)
         
print("Resulting image saved to file %s" % out_fitsname)

print("DEBUG : (90,90) %.8f / %.8f = %.8f" % (data1[90][90],data2[90][90],data_out[90][90]))

       

