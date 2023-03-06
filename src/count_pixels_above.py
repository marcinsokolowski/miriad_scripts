#!/opt/caastro/ext/anaconda/bin/python

# example usage : python source_finder_simple.py FITS_FILE --thresh_in_sigma=5

# based on examples
# http://docs.astropy.org/en/stable/io/fits/ 
# https://python4astronomers.github.io/astropy/fits.html

from __future__ import print_function

import time
start_time0=time.time()

# turn off downloading :
import astropy
from astropy.utils.iers import conf
conf.auto_max_age = None
from astropy.utils import iers
iers.conf.auto_download = False  

# astropy modules :
import astropy.io.fits as pyfits
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time

import pylab
import math
from array import *
import matplotlib.pyplot as plt
import numpy
import string
import sys
import os
import errno
import getopt
import find_gleam
import pix2sky
import skysources
import miriad_rms
from optparse import OptionParser,OptionGroup
import time
import datetime

import random
random.seed( 357420512948 )

class Pixel:
    def __init__(self,x,y) :
        self.x = x
        self.y = y



# TODO :
# 0/ use parse_options and proper parameters not the mess as it is ...
# 1/ add local MEAN / RMS calculation - create rms.py or bkg.py module with : Interpolation or fitting a surface over a couple of points with locally (specified by radius parameter) calculated RMS 
#     See example in fit_surface_test.py
#    Emil used the same way : ~/Desktop/SKA/Tim/doc/Beam_Model/Beam_model_on_real_data/FINAL/paper/Emil/20170706/marcin/TEST/my/AFTER_EMIL_FIXES/CLEANED



def parse_options(idx):
   usage="Usage: %prog [options]\n"
   usage+='\tDedisperse images \n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-a','--a_team','--ateam','--a_team_sources',action="store_true",dest="check_ateam_sources", default=True, help="Check A-team sources [default %default]")
   parser.add_option('--dont_check_ateam_sources','--allow_team_sources',action="store_false",dest="check_ateam_sources", default=True, help="Check A-team sources [default %default]")
   parser.add_option('-r','--a_team_radius','--aradius','--a_team_sources_radius',dest="a_team_sources_radius", default=3.8, help="A-team sources radius [deg] should be at least 1 beam size [default %default is beam size at 150 MHz]")
   parser.add_option('--transients','--transient_mode',dest="transient_mode",default=False,action="store_true",help="Transient mode [default %default]")
   parser.add_option('--exclude_ateam_list',dest="ateam_exclude_list", default="CenA,HerA,HydA,PicA,3C444,ForA,VirA", help="List of A-team sources to be excluded [default %default]")
   parser.add_option('-s','--sun_radius','--sradius','--sunradius',dest="sun_radius", default=8, help="Sun radius [deg] might even be 10 degrees [default %default is ~2 beam sizes at 150 MHz]")
   parser.add_option('-t','--threshold','--thresh_in_sigma',dest="threshold_in_sigma", default=5, help="Thresholod in sigma [default %default]",type="float")
   parser.add_option('--threshold_in_jy','--thresh_in_jy',dest="threshold_in_jy", default=None, help="Thresholod in Jy [default %default]",type="float")
   parser.add_option('--disable_filtering',dest="filtering_enabled",default=True,action="store_false",help="Disable filtering of known GLEAM sources and other criteria [default %default]")
   parser.add_option('--debug_level',dest="debug_level",default=0,help="Debug level [default %default]",type="int")
   parser.add_option('-w','--window',nargs = 4, dest="window", default=None, help="Window to calculate RMS [default %default]",type="int")
   parser.add_option('--exclude_window','--out_of_window',dest="exclude_window",default=False,action="store_true",help="Exclude window [default %default]")
   parser.add_option('--duplicate_rejection_radius_in_pixels',default=5,dest="duplicate_rejection_radius_in_pixels", help="Radius to reject duplicates [default %default]",type="int")
   parser.add_option('--rms_radius',default=None,dest="rms_radius", help="Radius to calculate RMS around central (or other position provided in parameter --rms_center [default %default]",type="int")
   parser.add_option('-b','--border',default=2,dest="border", help="Border [default %default]",type="int")
   parser.add_option('--overwrite',dest="overwrite",default=False,action="store_true",help="Overwrite [default %default]")
   parser.add_option('--rms_map','--rms_map_file','--rms_map_fits',dest="rms_map_fits",default=None,help="FITS file with RMS map [default %default]")
   parser.add_option('--distance_from_center','--dist_from_center',dest="distance_from_center", default=None, help="Distance from center in pixels [default %default]",type="int")
   
   parser.add_option('--radius','--fiducial_radius',dest="fiducial_radius", default=116, help="Fiducial radius [default %default]",type="int")
   
   # exception from galactic cut - to allow very bright transients in the galactic plane / buldge as they are mostly RFI and are needed later for coincidence analysis 
   # and rejection of all events on the same image if many !
   parser.add_option('--min_galplane_flux_allowed','--allow_brighter_than',dest="min_galplane_flux_allowed", default=2000.00, help="Allow candidates in Galactic plane / buldge brighter than (mostly RFI) [default %default]",type="float")
   
   # Monte Carlo :
   parser.add_option('--n_pixels','--npix','--monte_carlo_pixels',dest="monte_carlo_pixels", default=1000, help="Number of Monte Carlo pixels [default %default]",type="int")
   
#   parser.add_option('-m','--mean_cc',action="store_true",dest="mean_cc",default=True, help="Mean of coarse channels [default %]")
#   parser.add_option('--no_mean_cc',action="store_false",dest="mean_cc",default=True, help="Turn off calculation of mean of coarse channels [default %]")
#   parser.add_option('-o','--outdir',dest="outdir",default=None, help="Output directory [default %]")
#   parser.add_option('--meta_fits','--metafits',dest="metafits",default=None, help="Metafits file [default %]")

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)



def find_source( x, y, list_x, list_y, radius=5 ):
   if len(list_x) != len(list_y) :
      print("ERROR : wrong list sizes !!!")
      return -1


   for i in range(0,len(list_x)) :
      x_ref = list_x[i]
      y_ref = list_y[i]
      
      if math.fabs(x-x_ref)<radius and math.fabs(y-y_ref)<radius :
         return i
         
   return -1

if __name__ == "__main__":
   start_time = time.time()
   print("fixCoordHdr.py : import took %.6f [seconds]" % (start_time-start_time0))

   # ls wsclean_timeindex???/wsclean_1192530552_timeindex8-000?-I-dirty.fits > list_for_dedisp
   listname="list_for_dedisp"
   if len(sys.argv) > 1:
     listname = sys.argv[1]

   # threshold=5
   # if len(sys.argv) > 2:
   #   threshold = float(sys.argv[2])

   ref_image=None
   # if len(sys.argv) > 3 and sys.argv[3] != "-" :
   #   ref_image=sys.argv[3]

   save_dynamic_spectrum_treshold=7
   # if len(sys.argv) > 4:
   #   save_dynamic_spectrum_treshold=int(sys.argv[4])

   cube_fits=None
   # if len(sys.argv) > 5 and sys.argv[5] != "-" :
   #   cube_fits=sys.argv[5]

   radius_gleam_arcmin=-1 # 2 should be good
   #if len(sys.argv) > 7:
   #   radius_gleam_arcmin = int(sys.argv[7])

   radius=1

   # TODO : algorithms parameters (to be added as options)
   max_rms=1.00
   min_alt = 25
   min_glat = 10
   gal_buldge_glon_range = 25 # degrees around (0,0) [deg]
   gal_buldge_glat_range = 15 # degrees around (0,0) [deg]

   do_simul=False


   (options, args) = parse_options(1)
   
   ateam_exclude_list=options.ateam_exclude_list.split(",")

   border = options.border
   #if len(sys.argv) > 6:
   #   border=int(sys.argv[6])
   if border < 0 :
      border = 0

   print("##############################################################")
   print("PARAMETERS :")
   print("##############################################################")
   print("listname                       = %s" % (listname))
   print("ref_image                      = %s" % (ref_image))
   print("rms_map_fits                   = %s" % (options.rms_map_fits))
   print("threshold                      = %.2f x sigma" % (options.threshold_in_sigma))
   if options.threshold_in_jy is not None :
      print("threshold in Jy                = %.2f [Jy]" % (options.threshold_in_jy))
   print("save_dynamic_spectrum_treshold = %.2f x sigma" % (save_dynamic_spectrum_treshold))
   print("image border                   = %d" % (border))
   print("radius_gleam_arcmin            = %d   [arcmin]" % (radius_gleam_arcmin))
   print("do_simul                       = %s" % (do_simul))
   print("filtering_enabled              = %s" % (options.filtering_enabled))
   print("debug_level                    = %d" % (options.debug_level))
   if options.rms_radius is not None :
      print("rms_radius                     = %d" % (options.rms_radius))
   if options.window is not None :
         print("window    = (%d,%d)-(%d,%d)" % (options.window[0],options.window[1],options.window[2],options.window[3]))
   if options.distance_from_center is not None :
      print("Distance from center           = %d" % (options.distance_from_center))
   print("A-team exclude list            = %s" % (options.ateam_exclude_list))
   print("Transient mode                 = %s" % (options.transient_mode))
   print("Monte Carlo pixels             = %d" % (options.monte_carlo_pixels))
   print("##############################################################")

   fits_list=[]
   if listname.find(".fits") >= 0 :
      print("Treating listname = %s as a single fits file" % (listname))
      fits_list.append( listname )
   else :
      print("Listname = %s is list of fits files" % (listname))
      f = open (listname,"r")
      while 1:
         fitsname = f.readline().strip()
         fits_list.append( fitsname )

         if not fitsname:
            break

      f.close()
      print("Read fits files from list file")



   ref_image_list_x=[]
   ref_image_list_y=[]

   RA_map=None
   Dec_map=None
   gleam_sources=None
   gleam_fluxes=None
   radius_gleam_out=None
   MWA_POS=EarthLocation.from_geodetic(lon="116:40:14.93",lat="-26:42:11.95",height=377.8)

   if ref_image is not None :
      if radius_gleam_arcmin > 0 :
         (RA_map,Dec_map,gleam_sources,gleam_fluxes,radius_gleam_out) = find_gleam.select_gleam_sources( ref_image )
         print("Selected %d GLEAM sources %.2f [deg] around image %s center" % (len(gleam_sources),radius_gleam_out,ref_image))

      if ref_image.find(".fits") >= 0 :
         fits = pyfits.open( ref_image )
         x_size=fits[0].header['NAXIS1']
         y_size=fits[0].header['NAXIS2']

         print()
         print('# \tRead reference fits file %s of size %d x %d' % (ref_image,x_size,y_size))

         data = None
         if fits[0].data.ndim >= 4 :
            data = fits[0].data[0,0]
         else :
            data=fits[0].data


         # calculate MEAN/RMS :
         sum=0
         sum2=0
         count=0
         for y_c in range(radius,y_size-radius) :
            for x_c in range(radius,x_size-radius) :
               # count_test=0
               # final_value=0
               # for y in range (y_c-radius,(y_c+radius+1)):
               #   for x in range (x_c-radius,(x_c+radius+1)):
               # value = data[y_c,x_c]
               # final_value = final_value + value
               #  count_test = count_test + 1
               # final_value = final_value / count_test

               final_value=data[y_c,x_c]
               sum = sum + final_value
               sum2 = sum2 + final_value*final_value
               count = count + 1

               # print "count_test = %d" % (count_test)

         mean_val = (sum/count)
         rms = math.sqrt(sum2/count - mean_val*mean_val)
         print("%s : mean +/- rms = %.4f +/- %.4f (based on %d points)" % (ref_image,mean_val,rms,count))

   #      postfix_txt = ("_%.2fsigma.txt" % (threshold))
   #      postfix_reg = ("_%.2fsigma.reg" % (threshold))
         postfix_txt = ("_refsources.txt")
         postfix_reg = ("_refsources.reg")


         reffile=ref_image.replace('.fits', postfix_txt )
         regfile=ref_image.replace('.fits', postfix_reg )
         f_ref = open( reffile , "w" )
         f_reg = open( regfile , "w" )
         f_reg.write("global color=white width=5 font=\"times 10 normal\"\n")
         for y in range(0,y_size) :
            for x in range(0,x_size) :
               value = data[y,x]

               if value > mean_val + options.threshold_in_sigma*rms :
                  if find_source(x,y,ref_image_list_x,ref_image_list_y,radius=5) < 0 :
                     f_ref.write( "%d %d %.2f = %.2f sigma > %.2f x %.2f\n" % (x,y,value,(value/rms),options.threshold_in_sigma,rms) )
                     f_reg.write( "circle %d %d 5 # %.2f Jy\n" % ((x+1),(y+1),value) ) # (x+1),(y+1) - due to ds9 indexing from 1
                     if options.debug_level > 0 :
                        print("DEBUG (ref-regfile) : circle %d %d 5 # %.2f Jy\n" % (x,y,value))

                     ref_image_list_x.append(x)
                     ref_image_list_y.append(y)



         print("%d sources found in reference image %s above threshold of %.2f sigma (= %.2f Jy)" % (len(ref_image_list_x),ref_image,options.threshold_in_sigma,(mean_val + options.threshold_in_sigma*rms)))

         f_ref.close()
         f_reg.close()

      else : # just a list file to read :
         file=open(ref_image,'r')
         # reads the entire file into a list of strings variable data :
         data=file.readlines()
         for line in data :
            words = line.split(' ')

            if line[0] == '#' :
               continue

            if line[0] != "#" :
               x=float(words[0+0])
               y=float(words[1+0])

               ref_image_list_x.append(x)
               ref_image_list_y.append(y)

         file.close()

         print("Read %d sources from reference list %s" % (len(ref_image_list_x),ref_image))

      print("Reference list of sources has %d sources:" % (len(ref_image_list_x)))
      for s in range(0,len(ref_image_list_x)) :
         print("\t%d %d" % (ref_image_list_x[s],ref_image_list_y[s]))



   rms_map = None
   if options.rms_map_fits is not None :
      rms_map_fits = pyfits.open( options.rms_map_fits )
      rms_map_x_size = rms_map_fits[0].header['NAXIS1']
      rms_map_y_size = rms_map_fits[0].header['NAXIS2']

      print()
      print('# \tRead RMS MAP FITS file %s of size %d x %d' % (options.rms_map_fits,rms_map_x_size,rms_map_y_size))

      if rms_map_fits[0].data.ndim >= 4 :
         rms_map = rms_map_fits[0].data[0,0]
      else :
         rms_map = rms_map_fits[0].data


   # x_c=250
   # if len(sys.argv) > 1:
   #   x_c = int(sys.argv[1])

   # outdir="dedispersed/"
   # os.system("mkdir -p dedispersed/")
   os.system("mkdir -p dynamic_spectrum/")

   b_no_header=False
   starttimeindex=0

   for fitsname in fits_list :
      # wsclean_timeindex008/wsclean_1192530552_timeindex8-0001-I-dirty.fits
      # timeidx=int(fitsname[17:20])
      # cc=int(fitsname[-17:-13])
      file_start_time=time.time()
      print("PROGRESS : processing file %s" % (fitsname))

      try :
         fits = pyfits.open( fitsname )
      except :
         print("ERROR : could not read FITS file %s -> skipped" % (fitsname))
         continue
      
      x_size = int( fits[0].header['NAXIS1'] )
      y_size = int( fits[0].header['NAXIS2'] )
   #   try :
   #      starttimeindex=fits[0].header['STTIDX']
   #   except :
   #      print("WARNING : Keyword STTIDX not found in fits file %s (not needed)" % (fitsname))
   #      b_no_header = True

      print()
      print('# Read fits file %s of size %d x %d' % (fitsname,x_size,y_size))

      if fits[0].data.ndim >= 4 :
         data = fits[0].data[0,0]
      else :
         data=fits[0].data

      rms_radius = options.rms_radius
      if rms_radius is None :
         rms_radius = radius=int(x_size/4)
      (mean_val,rms,max_value,count,median,iqr,rms_iqr,window) = miriad_rms.rms_around_base( data, x_size, y_size, radius=rms_radius, window=options.window )
   #   thresh_value = mean_val + options.threshold_in_sigma*rms
      thresh_value = median + options.threshold_in_sigma*rms_iqr
      
      if options.threshold_in_jy is not None :
         thresh_value = options.threshold_in_jy
         
      print("\t%s : median +/- rms_iqr = %.4f +/- %.4f (based on %d points) -> threshold = %.4f , search window = (%d,%d)-(%d,%d)" % \
                    (fitsname,median,rms_iqr,count,thresh_value,border,border,x_size-border,y_size-border))



      candidates=[]
      catatalog_sources=[]
      candidates_index = 0

      uxtime = 0
      utc = ""
      try :
         utc = fitsname[9:24]
         uxtime = time.mktime(datetime.datetime.strptime(utc, "%Y%m%dT%H%M%S").timetuple()) + 8*3600 # just for Perth !!!
      except :
         print("\tWARNING : could not get UTC from fitsname = %s (utc = %s) -> trying fits header" % (fitsname,utc))

         utc = fits[0].header['DATE-OBS']
         if options.debug_level > 0 :
            print("\tDEBUG : utc from FITS header = %s" % (utc))
         uxtime = time.mktime(datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%S.0").timetuple()) + 8*3600 # just for Perth !!!
         if options.debug_level > 0 :
            print("\tDEBUG : utc = %s -> uxtime = %.4f" % (utc,uxtime))


      TimeCoord = Time( uxtime, scale='utc', format="unix" )
      
      # skysources.LoadSources( uxtime=uxtime )
      skysources.SetGlobalUnixTime( uxtime=uxtime )
      print("set uxtime = %.2f" % (uxtime))
      time.sleep(5)
      
      check_sun = True
      sun = skysources.GetSun()
      coord = SkyCoord( sun.ra_degs, sun.dec_degs, equinox='J2000',frame='icrs', unit='deg')
      coord.location = MWA_POS
      coord.obstime = TimeCoord # Time( uxtime, scale='utc', format="unix" )
      sun_altaz = coord.transform_to('altaz')
      sun_az, sun_alt = sun_altaz.az.deg, sun_altaz.alt.deg
      print("INFO : sun coordinates (ra,dec) = (%.4f,%.4f) [deg] -> (sun_az,sun_alt) = (%.4f,%.4f) [deg]" % (sun.ra_degs, sun.dec_degs, sun_az, sun_alt))
      if sun_alt < 0 :
         print("INFO : sun coordinates (sun_az,sun_alt) = (%.4f,%.4f) [deg] -> Sun below horizon -> no need to check" % (sun_az, sun_alt))
         check_sun = False

      
      x_center = (x_size/2)
      y_center = (y_size/2)

      all_y_to_process = (y_size-2*border)
      if options.window is not None :
         if not options.exclude_window :
            all_y_to_process = (options.window[3] - options.window[1])
      print("DEBUG : all_y_to_process = %d" % (all_y_to_process))
      last_progress = 0.00
      
      all_pixels = (x_size*y_size)
      all_pixels_above_min_alt = 0
      all_analysed_pixels = 0

      min_elev = 25
      count_above=0
      
      for y in range(0,y_size) :
         print("   y = %d ( pixels above elevation %.2f deg = %d out of %d )" % (y,min_elev,count_above,all_pixels));
         for x in range(0,x_size) :
            (ra_deg, dec_deg) = pix2sky.pix2sky( fits, x+1, y+1, fitsname, debug_level=options.debug_level )
               
            if numpy.isnan(ra_deg) or numpy.isnan(dec_deg) :
               continue

            coord = SkyCoord( ra_deg, dec_deg, equinox='J2000',frame='icrs', unit='deg')
            coord.location = MWA_POS
   #            coord.obstime = Time("20200507T065634", scale='utc', format="utc" )
               # chan_294_20200507T065634_I.fits

            coord.obstime = TimeCoord # Time( uxtime, scale='utc', format="unix" )
            altaz = coord.transform_to('altaz')
            az, alt = altaz.az.deg, altaz.alt.deg
               
            if alt > min_elev :
               count_above += 1
                        
            if options.debug_level > 0 :
               print("\tDEBUG : verifying candidate (ra,dec) = (%.4f,%.4f) [deg] at unix_time = %.2f and (az,alt) = (%.4f,%.4f) [deg]" % (ra_deg,dec_deg,uxtime,az, alt))


   print("Number of pixels above elevation %.2f [deg] = %d out of total %d pixels" % (min_elev,count_above,all_pixels))

   fits.close()

   end_time = time.time()
   print("source_finder_simple.py: Start_time = %.6f , end_time = %.6f -> took = %.6f seconds (including import took %.6f seconds)" % (start_time,end_time,(end_time-start_time),(end_time-start_time0)))

