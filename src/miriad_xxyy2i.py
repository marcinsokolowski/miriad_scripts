
import time
start_time0=time.time()

import astropy.io.fits as pyfits
import numpy as np
import sys
import os
import errno
from optparse import OptionParser,OptionGroup

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

def read_list( list_filename ) :
   out_fits_list=[]

   print("read_list : reading file %s" % (list_filename))

   if os.path.exists( list_filename ) and os.stat( list_filename ).st_size > 0 :
      file=open( list_filename ,'r')
      data=file.readlines()
      for line in data :
         line=line.rstrip()
         words = line.split(' ')
         if line[0] == '#' :
            continue

         if line[0] != "#" :
            uvbase = words[0+0] 
            out_fits_list.append( uvbase )
            print("DEBUG : added %s" % (uvbase))
            
      file.close()
   else :
      print("WARNING : empty or non-existing file %s" % (list_filename))


   return out_fits_list



def parse_options():
   usage="Usage: %prog [options]\n"
   usage+='\tBeam correct XX and YY images (by dividing by beamXX and beamYY) then calculate Stokes I = (XX_corr + YY_corr)/2.00\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option("-b","--beam_base","--beam_file",dest="beam_base",default="beam", help="Beam base name [default %default]")
   parser.add_option("-o","--outdir","--out_dir","--dir",dest="out_dir",default="./", help="Output directory to beam corrected files [default %default]")
#   parser.add_option('-t','--threshold',dest="threshold",default=5, help="Threshold to find sources (expressed in sigmas) [default %default sigma]",type="float")
#   parser.add_option('-f','--fits_type',dest="fits_type",default=0, help="FITS file type 0-single x,y image, 1-multi-axis [default %default]",type="int")
#   parser.add_option('-w','--window',nargs = 4, dest="window", help="Window to calculate RMS [default %default]",type="int")   
#   parser.add_option('-r','--regfile',action="store_true",dest="save_regfile",default=False, help="Save regfile with found pixels [default %default]")
#   parser.add_option('-x','--x',dest="position_x",default=-1,help="X coordinate to calculate RMS around [default %default]",type="int")
#   parser.add_option('-y','--y',dest="position_y",default=-1,help="Y coordinate to calculate RMS around [default %default]",type="int")
#   parser.add_option('--center','--around_center',dest="around_center",action="store_true",default=False,help="In specified radius around the center [default %default]")
#   parser.add_option('--radius',dest="radius",default=1,help="Radius to calculate RMS around (X,Y) passed in -x and -y options [default %default]",type="int")
#   parser.add_option('--plotname',dest="plotname",default=None,help="Png file name if plot is required too [default %default]",type="string")
#   parser.add_option('--outfile',dest="outfile",default="rms.txt",help="Output file [default %default]",type="string")
   (options, args) = parser.parse_args()
   return (options, args)

if __name__ == '__main__':
   start_time = time.time()
   print("miriad_xxyy2i.py : import took %.6f [seconds]" % (start_time-start_time0))
   
   # ls wsclean_timeindex???/wsclean_1192530552_timeindex8-000?-I-dirty.fits > list_for_dedisp
   listname="fits_list_xx"
   if len(sys.argv) > 1: 
      listname = sys.argv[1]

   (options, args) = parse_options()
   
   mkdir_p( "beam_uncorr/" )

   print("####################################################")
   print("PARAMTERS :")
   print("####################################################")
   print("listname        = %s" % listname)
   print("####################################################")
   
   list = []
   if listname.find(".fits") >= 0 :
      list.append(listname)
   else :
      list = read_list( listname )
      
   beam_xx_fits = options.beam_base + "_XX.fits"   
   beam_yy_fits = options.beam_base + "_YY.fits"   
   
   beam_xx = None   
   beam_yy = None
   beam_xx_data = None
   beam_yy_data = None
   if os.path.exists( beam_xx_fits ) and os.path.exists( beam_yy_fits ) :
       beam_xx = pyfits.open( beam_xx_fits )
       beam_yy = pyfits.open( beam_yy_fits )
       
       if beam_xx[0].data.ndim >= 4 :
          beam_xx_data = beam_xx[0].data[0,0]
       else :
          beam_xx_data = beam_xx[0].data

       if beam_yy[0].data.ndim >= 4 :
          beam_yy_data = beam_yy[0].data[0,0]
       else :
          beam_yy_data = beam_yy[0].data
       
       print("OK : read beam FITS files %s and %s" % (beam_xx_fits,beam_yy_fits))
   else :
       print("WARNING : beam files %s and/or %s do not exist -> no beam correction applied" % (beam_xx_fits,beam_yy_fits))
      

   for fitsname_base in list : 
       print("\nPROGRESS : processing file %s ..." % (fitsname_base))
   
       fitsname_xx = fitsname_base
       if fitsname_base.find("_XX") < 0 :
          fitsname_xx = fitsname_base + "_XX.fits"
   
       fitsname_yy = fitsname_xx.replace("_XX.fits","_YY.fits")
       fitsname_i  = fitsname_xx.replace("_XX.fits","_I.fits")
   
       fits_xx = pyfits.open(fitsname_xx)
       x_size=fits_xx[0].header['NAXIS1']
       y_size=fits_xx[0].header['NAXIS2']
       print('\tRead fits file %s' % fitsname_xx)
       print('\tFITS size = %d x %d' % (x_size,y_size))

       fits_yy = pyfits.open(fitsname_yy)
       x_size2=fits_yy[0].header['NAXIS1']
       # channels=100
       y_size2=fits_yy[0].header['NAXIS2']
       print('\tRead fits file 2 %s' % fitsname_yy)
       print('\tFITS size 2 = %d x %d' % (x_size2,y_size2))

       if x_size!=x_size2 or y_size!=y_size2 :
           print("ERROR : cannot execute operation %s on files of different sizes (%d,%d) != (%d,%d)" % (oper,x_size,y_size,x_size2,y_size2))
           exit;

       data_xx = None
       if fits_xx[0].data.ndim >= 4 :
          data_xx = fits_xx[0].data[0,0]
       else :
          data_xx = fits_xx[0].data
          
       data_yy = None
       if fits_yy[0].data.ndim >= 4 :
          data_yy = fits_yy[0].data[0,0]
       else :
          data_yy = fits_yy[0].data
   

       # beam correct XX :
       if beam_xx_data is not None : 
          if options.out_dir == "./" :
             cp_cmd = "cp %s beam_uncorr/" % (fitsname_xx)
             print("\t%s\n" % cp_cmd) 
             os.system( cp_cmd )
       
          with np.errstate(divide='ignore'):
             data_xx = data_xx / beam_xx_data  
             data_xx[np.isnan(data_xx)] = 0.00
             
          if fits_xx[0].data.ndim >= 4 :
             fits_xx[0].data[0,0] = data_xx
          else :
             fits_xx[0].data = data_xx
             
          out_xx = options.out_dir + "/" + fitsname_xx   
          fits_xx.writeto(out_xx,overwrite=True)
          print("\tOK : saved beam corrected XX image to %s" % (out_xx))
                          

       # beam correct YY :
       if beam_yy_data is not None : 
          if options.out_dir == "./" :
             cp_cmd = "cp %s beam_uncorr/" % (fitsname_yy)
             print("\t%s\n" % cp_cmd)
             os.system( cp_cmd )
       
          with np.errstate(divide='ignore'):
             data_yy = data_yy / beam_yy_data  
             data_yy[np.isnan(data_yy)] = 0.00

          if fits_yy[0].data.ndim >= 4 :
             fits_yy[0].data[0,0] = data_yy
          else :
             fits_yy[0].data = data_yy
             
          out_yy = options.out_dir + "/" + fitsname_yy   
          fits_yy.writeto( out_yy,overwrite=True)
          print("\tOK : saved beam corrected YY image to %s" % (out_yy))

       print("\tDEBUG : shape = %d x %d" % (data_xx.shape[0],data_xx.shape[1]))

       data_i = np.zeros((x_size,y_size))
       data_i = ( data_xx + data_yy ) / 2.00
                   

       if fits_xx[0].data.ndim >= 4 :
           fits_xx[0].data[0,0] = data_i
       else :
           fits_xx[0].data = data_i

       out_i = options.out_dir + "/" + fitsname_i
       fits_xx.writeto(out_i,overwrite=True)      
       print("\tResulting image saved to file %s" % out_i)
       print("\tDEBUG : (90,90) %.8f / %.8f = %.8f" % (data_xx[90][90],data_yy[90][90],data_i[90][90]))

       

