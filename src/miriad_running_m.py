
# python script to calculate difference images references to median/running median or mean or running mean image :

import time
start_time0=time.time()

import astropy.io.fits as pyfits
import numpy as np
import sys
import os
import errno
from optparse import OptionParser,OptionGroup

def mkdir_p(path):
   try:
      os.makedirs(path)
      print("Created directory %s" % (path))
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
   usage+='\tmiriad_running_m.py fits_list_I\n'   
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option("-o","--outdir","--out_dir","--dir",dest="out_dir",default=None, help="Output directory for running median/mean [default %default]")
   parser.add_option("--outdir_diff","--out_dir_diff","--diff",dest="out_dir_diff",default=None, help="Output directory for difference images [default %default]")
   parser.add_option('-m','--median',dest="median",action="store_true",default=False,help="Calc running median (default running average) [default %default]")
   parser.add_option('-r','--radius',dest="radius",default=1, help="Radius in FITS files to calculate running median/mean over +/- this number of images around the current one [default %default]",type="int")
   parser.add_option("--tmp_list_name",dest="tmp_list_name",default="tmp_mean_list.txt",help="Name of a temporary list file [default %default]");
   parser.add_option('-s','--subtract',dest="subtract",action="store_true",default=False,help="Subtract the resulting running median/mean image [default %default]")
   
   (options, args) = parser.parse_args()
   return (options, args)

if __name__ == '__main__':
   include_central_image = False
   
   start_time = time.time()
   print("miriad_running_m.py : import took %.6f [seconds]" % (start_time-start_time0))
   
   listname="fits_list_I"
   if len(sys.argv) > 1: 
      listname = sys.argv[1]

   (options, args) = parse_options()
   n_files = options.radius*2 + 1
   
   if options.out_dir is None :
      options.out_dir = "running_mean%d/" % (n_files)
      if options.median :
         options.out_dir = "running_median%d/" % (n_files)

   if options.out_dir_diff is None :
      options.out_dir_diff = "difference_mean%d/" % (n_files)
      if options.median :
         options.out_dir_diff = "difference_median%d/" % (n_files)
   
   print("####################################################")
   print("PARAMTERS :")
   print("####################################################")
   print("listname        = %s" % listname)
   print("Median          = %s" % options.median)
   print("radius          = %d ( n_files = %d )" % (options.radius,n_files))
   print("outdir          = %s" % (options.out_dir))
   print("outdir diff     = %s" % (options.out_dir_diff))
   print("subtract        = %s" % (options.subtract))
   print("####################################################")

   mkdir_p( options.out_dir )

   if options.subtract :
      mkdir_p( options.out_dir_diff )
      
   
   fits_list = read_list( listname )
   
 
   fits_idx = 0
   for fitsname in fits_list :
      print("Processing FITS file %s (fits_idx = %d)" % (fitsname,fits_idx))

      avg_list_f = open( options.tmp_list_name ,"w")
      start_idx = (fits_idx - options.radius)
      for idx in range(start_idx,fits_idx+options.radius+1) :
         if idx >=0 and idx < len(fits_list) :
            if idx != fits_idx or include_central_image :
               line = "%s\n" % (fits_list[idx])         
               avg_list_f.write( line )
               
            
      avg_list_f.close()      

      cmd = "ERROR"      
      fitsname_out = "ERROR.fits"
      rmsname_out  = "ERROR_RMS.fits"
      out_median_fits = "ERROR_MEDIAN.fits"
      out_rms_fits    = "ERROR_RMSIQR.fits"
      # CALL 
      if options.median :
         # median_images_fits
         fitsname_out = fitsname.replace(".fits","_median.fits")
         rmsname_out  = fitsname.replace(".fits","_rmsiqr.fits")
         out_median_fits = ( "%s/%s" % (options.out_dir,fitsname_out))
         out_rms_fits    = ( "%s/%s" % (options.out_dir,rmsname_out))
         cmd = "median_images_fits %s %s %s" % (options.tmp_list_name,out_median_fits,out_rms_fits)
         
      else :
         # avg_images 
         fitsname_out = fitsname.replace(".fits","_mean.fits")
         rmsname_out  = fitsname.replace(".fits","_rms.fits")
         out_median_fits = ( "%s/%s" % (options.out_dir,fitsname_out))
         out_rms_fits    = ( "%s/%s" % (options.out_dir,rmsname_out))
         cmd = "avg_images %s %s %s" % (options.tmp_list_name,out_median_fits,out_rms_fits)

      if os.path.exists( out_median_fits ) :
         print("DEBUG : file %s already exist - skipped (use --force to re-generate)" % (out_median_fits))
      else :
         print("%s" % cmd)         
         os.system( cmd )   
      
      if options.subtract :
         fitsname_diff = fitsname.replace(".fits","_diff.fits")
         fitsname_diff_out = ( "%s/%s" % (options.out_dir_diff,fitsname_diff))
         
         if os.path.exists( fitsname_diff_out ) :
            print("DEBUG : file %s already exist - skipped (use --force to re-generate)" % (fitsname_diff_out))
         else :
            cmd_diff = "calcfits_bg %s - %s %s" % (fitsname,out_median_fits,fitsname_diff_out)
         
            print("%s" % cmd_diff)
            os.system( cmd_diff )   
   
      fits_idx += 1       
      
      