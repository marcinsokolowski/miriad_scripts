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
   
   # exception from galactic cut - to allow very bright transients in the galactic plane / buldge as they are mostly RFI and are needed later for coincidence analysis 
   # and rejection of all events on the same image if many !
   parser.add_option('--min_galplane_flux_allowed','--allow_brighter_than',dest="min_galplane_flux_allowed", default=2000.00, help="Allow candidates in Galactic plane / buldge brighter than (mostly RFI) [default %default]",type="float")
   
   # Galactic long / lat cuts :
   parser.add_option('--gal_buldge_glon_range',default=25,dest="gal_buldge_glon_range", help="Excluded range of Galactic longitude [default %default]",type="float")
   parser.add_option('--gal_buldge_glat_range',default=15,dest="gal_buldge_glat_range", help="Excluded range of Galactic latitude  [default %default]",type="float")
   
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
   min_alt = 5
   min_glat = 10
   do_simul=False


   (options, args) = parse_options(1)
   
   gal_buldge_glon_range = options.gal_buldge_glon_range # degrees around (0,0) [deg]
   gal_buldge_glat_range = options.gal_buldge_glat_range # degrees around (0,0) [deg]   
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
   print("Exclude Galactic long, lat range = %.1f , %.1f [deg]" % (gal_buldge_glon_range,gal_buldge_glat_range))
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
#   os.system("mkdir -p dynamic_spectrum/")

   b_no_header=False
   starttimeindex=0

   for fitsname in fits_list :
      # wsclean_timeindex008/wsclean_1192530552_timeindex8-0001-I-dirty.fits
      # timeidx=int(fitsname[17:20])
      # cc=int(fitsname[-17:-13])
      file_start_time=time.time()

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
         
      max_value_image = numpy.amax( data )   
      min_value_image = numpy.amin( data )   

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


      if do_simul :
         # add value at random location :
         f_simul = open( "simul.txt" , "w" )
         x_simul = 75
         y_simul = 75
         simul_line = "%d %d" % (x_simul,y_simul)
         data[x_simul,y_simul] = 20*rms
         f_simul.write(simul_line)
         f_simul.close()


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
      
      x_center = (x_size/2)
      y_center = (y_size/2)

      all_y_to_process = (y_size-2*border)
      if options.window is not None :
         if not options.exclude_window :
            all_y_to_process = (options.window[3] - options.window[1])
      print("DEBUG : all_y_to_process = %d" % (all_y_to_process))
      last_progress = 0.00
      for y in range(border,y_size-border) :
#         print("DEBUG : y=%d" % (y))
         
         n_above_threshold = 0
         for x in range(border,x_size-border) :
            if options.distance_from_center is not None :
               dist_from_center = math.sqrt( (y-y_center)**2 + (x-x_center)**2 ) 
               # print("DEBUG : (%d,%d) -> dist from center = %.2f" % (x,y,dist_from_center))
               if dist_from_center > options.distance_from_center :
                  # print("DEBUG : (%d,%d) skipped dist = %.4f > %.4f" % (x,y,dist_from_center,options.distance_from_center))
                  continue
         
            if options.window is not None :
               if options.exclude_window :
                  if x >= options.window[0] and x <= options.window[2] and y >= options.window[1] and y <= options.window[3] :  
                      # skip if INSIDE the exclusion window !
                      continue
               else :
                  if x <options.window[0] or x > options.window[2] or y < options.window[1] or y > options.window[3] :
                      # skiping pixels outside window (if defined)
                      continue

            value = data[y,x]
            
            if numpy.isnan(value) :
                continue

            progress = ( float(y-border) / float(all_y_to_process) )*100.00
            
            if options.window is not None :               
               if not options.exclude_window :
                   if options.debug_level > 1 :
                       print("DEBUG : %.4f / %.4f = ???" % (float(y-options.window[1]),float(all_y_to_process)))
                   progress = ( float(y-options.window[1]) / float(all_y_to_process) )*100.00
            
            if int(progress) > int(last_progress) :
               if options.debug_level > 0 :
                  print("Progress = %.2f %% ( at y = %d / %d )" % (progress,y,(y_size-2*border)))
            last_progress = progress
            
            if rms_map is not None :
               thresh_value = median + options.threshold_in_sigma*rms_map[y-20,x-20] # take RMS value slight off the current position 

            if value > thresh_value :
               n_above_threshold += 1 
               if options.debug_level > 5 :
                  print("DEBUG : (x,y) = (%d,%d) = %.4f > %.4f" % (x,y,value,thresh_value))

               is_sun = False
               is_ateam_source = False
               # WARNING : x+1, y+1 - as WCS works in the same convention as ds9 (1-based indexes)
               (ra_deg, dec_deg) = pix2sky.pix2sky( fits, x+1, y+1, fitsname, debug_level=options.debug_level )

               coord = SkyCoord( ra_deg, dec_deg, equinox='J2000',frame='icrs', unit='deg')
               coord.location = MWA_POS
   #            coord.obstime = Time("20200507T065634", scale='utc', format="utc" )
               # chan_294_20200507T065634_I.fits

               coord.obstime = TimeCoord # Time( uxtime, scale='utc', format="unix" )
               altaz = coord.transform_to('altaz')
               az, alt = altaz.az.deg, altaz.alt.deg

               if options.debug_level > 0 :
                  print("\tDEBUG : verifying candidate (ra,dec) = (%.4f,%.4f) [deg] at unix_time = %.2f and (az,alt) = (%.4f,%.4f) [deg]" % (ra_deg,dec_deg,uxtime,az, alt))

               if numpy.isnan(ra_deg) or numpy.isnan(dec_deg) :
                  if options.debug_level > 0 :
                     print("\tDEBUG : candidate outside physical bounderies or below horizon -> ignored")
                  continue


               new_transient=True
               if options.filtering_enabled :
                  if alt <= min_alt :
                     if options.debug_level > 0 :
                        print("INFO : candidate (ra,dec) = (%.4f,%.4f) [deg] at unix_time = %.2f and (az,alt) = (%.4f,%.4f) [deg] skiped alt < %.2f [deg]" % (ra_deg,dec_deg,uxtime,az, alt,min_alt))
                     continue;

                  glon = coord.galactic.l.deg
                  glat = coord.galactic.b.deg

                  if value < options.min_galplane_flux_allowed :
                     # only reject not too bright events in the Galactic plane :
                     if math.fabs(glat) <= min_glat : # 10 deg ?
                        print("INFO : candidate (ra,dec) = (%.4f,%.4f) [deg] at unix_time = %.2f and (glon,glat) = (%.4f,%.4f) [deg] skiped |glat| < %.2f [deg] (Galactic Plane)" % (ra_deg,dec_deg,uxtime,glon,glat,min_glat))
                        continue;

                     if math.fabs(glon) < gal_buldge_glon_range and math.fabs(glat) < gal_buldge_glat_range :
                        print("INFO : candidate (ra,dec) = (%.4f,%.4f) [deg] at unix_time = %.2f and (glon,glat) = (%.4f,%.4f) [deg] skiped |glon| < %.2f and |glat| < %.2f [deg] (Galactic Buldge)" % (ra_deg,dec_deg,uxtime,glon,glat,gal_buldge_glon_range,gal_buldge_glat_range))
                        continue;
                  else :
                     print("DEBUG : very bright transient ( %.2f Jy > %.2f Jy ) at (ra,dec) = (%.4f,%.4f) and (x,y) = (%d,%d) -> Galactic plane / buldge ignored" % (value,options.min_galplane_flux_allowed,ra_deg,dec_deg,int(x+1),int(y+1)))

                  if len(ref_image_list_x) > 0 and ( gleam_sources is None or len(gleam_sources)<=0 ) :
                     index = find_source(x,y,ref_image_list_x,ref_image_list_y,radius=5)
                     if index>=0 :
                        new_transient=False

                     print("\tChecking source at (%d,%d) value = %.2f Jy ... FOUND=%s" % (x,y,value,(index>=0)))
                  else :
                     if options.debug_level >= 5 :
                        print("\tINFO : checking only GLEAM (not reference image)")

                  # check gleam :
                  if gleam_sources is not None and len(gleam_sources) > 0 :
                     new_source_ra  = ra_deg  # RA_map[x,y]   # warning verify if order x,y should not be swaped
                     new_source_dec = dec_deg # Dec_map[x,y]  # warning verify if order x,y should not be swaped

                     print("\tChecking source at (%d,%d) value = %.2f Jy in GLEAM, (ra,dec) = (%.4f,%.4f) [deg]" % (x,y,value,new_source_ra,new_source_dec))
                     (gleam_source,gleam_flux,gleam_dist_arcsec) = find_gleam.find_source(gleam_sources,gleam_fluxes,new_source_ra,new_source_dec,radius_arcsec=radius_gleam_arcmin*60.00,flux_min=0)
                     if gleam_source is not None :
                        print("\tFound in gleam source %s with flux = %.2f in distance = %.2f [arcsec]" % (gleam_source,gleam_flux,gleam_dist_arcsec))
                        new_transient=False
               else :
                  if options.debug_level > 0 :
                     print("WARNING : filtering / criteria are disabled")

               # exclude repetiations or update if with higher flux
               update_source = False
               (exists,existing_source,existing_source_index) = skysources.FindClosestSourceXY( x, y, candidates, radius=options.duplicate_rejection_radius_in_pixels, debug_level=options.debug_level ) # was 20 pixels
               if exists and existing_source_index>=0 :
                  if value > existing_source.flux :
                     if options.debug_level > 0 :
                        print("\tSource at (%d,%d) (ra,dec) = (%.4f,%.4f) [deg] - already found, but overwritting with higher flux one" % (x,y,ra_deg,dec_deg))
                     update_source = True
                     # candidates[existing_source_index] = skysources.Source( source_name, ra_deg, dec_deg, flux=flux, rms=rms, bkg=mean_val, x=x, y=y )
                  else :
                     if options.debug_level >= 5 :
                        print("\tSource at (%d,%d) (ra,dec) = (%.4f,%.4f) [deg] - already found, duplicate ignored" % (x,y,ra_deg,dec_deg))

                  # in both cases not a new source
                  new_transient = False

               # check A-team sources :
               if (new_transient or update_source) :
                  # always check for sun :
                  found_src = False
                  closest_source = None
                  min_dist_arcsec = 1e20
                  (sun_dist,sun) = skysources.GetSunDistanceArcsec( ra_deg , dec_deg )
                  if sun_dist is not None :
                     sun_dist_deg = sun_dist/3600.00

                     if sun_dist_deg <= options.sun_radius :
                        print("\tSource at (%d,%d) (ra,dec) = (%.4f,%.4f) [deg] identified as Sun" % (x,y,ra_deg,dec_deg))
                        is_sun = True
                        closest_source = sun
                        min_dist_arcsec = sun_dist
                  else :
                     print("ERROR : could not find distance to Sun amongst the catalog sources !")

                  if not is_sun and options.check_ateam_sources and options.filtering_enabled :
                     print("\tChecking A-team sources around (ra,dec) = (%.4f,%.4f) [deg] at (x,y) = (%d,%d)" % (ra_deg,dec_deg,x,y))

                     (found_src,closest_source,min_dist_arcsec) = skysources.FindClosestSource( ra_deg , dec_deg, radius_arcsec=(options.a_team_sources_radius*3600) )
                     
                     rejected = False
                     if options.transient_mode :
                        # in this mode only exclude some sources :
                        if closest_source.name in ateam_exclude_list :
                           is_ateam_source = found_src
                           rejected = True
                           
                     else :
                        is_ateam_source = found_src
                        rejected = True
   
                     if found_src :
                        print("\tFound a nearby source %s -> rejecting candidate" % (closest_source.name))

                  #
                  if is_sun or found_src :
                      if options.debug_level > 0 :
                         print("\tDEBUG : is_sun=%s, found_src=%s -> checking (ra,dec) = (%.4f,%.4f) [deg] if not already on list catatalog_sources" % (is_sun,found_src,closest_source.ra_degs, closest_source.dec_degs))
                      # (catsrc_exists,existing_catsource,existing_cat_source_index) = skysources.FindClosestSource( closest_source.ra_degs, closest_source.dec_degs, catatalog_sources, radius_arcsec=60, check_error=False ) # 20 pixels
                      (catsrc_exists,existing_catsource,existing_cat_source_index) = skysources.FindSourceByName( closest_source.name, sources=catatalog_sources )

                      # if it was already on out list
                      if catsrc_exists :
                          print("\tSource %s already exists on the list of catalog_sources (count=%d)" % (existing_catsource.name,len(catatalog_sources)))
                      else :
                          print("\tSource %s not yet on list of catalogue sources -> added" % (closest_source.name))
                          catatalog_sources.append( skysources.Source( closest_source.name, closest_source.ra_degs, closest_source.dec_degs, x=x, y=y, cat_source_index=existing_cat_source_index, cat_source_dist_arcsec=min_dist_arcsec , uxtime=uxtime ) )
   #                   else :
   #                       # update if closer :
   #                       if existing_cat_source_index >= 0 :
   #                          catatalog_sources[ existing_cat_source_index ] = skysources.Source( closest_source.name, closest_source.ra_degs, closest_source.dec_degs, x=x, y=y, cat_source_index=existing_cat_source_index, cat_source_dist_arcsec=min_dist_arcsec )
   #                       else :
   #                          print("ERROR : the source is expected to be on a list of catalog sources, but the existing_cat_source_index = %d" % (existing_cat_source_index))

                      # it's a known catalogue source -> not a transient !
                      new_transient = False
                  else :
                      if options.debug_level > 0 :
                         print("\tNo nearby catalogue source found around position (ra,dec) = (%.4f,%.4f) [deg]" % (ra_deg,dec_deg))

               if new_transient :
                  n_sigmas=(value/rms)
   #               n_sigmas_int=int(n_sigmas)
   #               f_reg.write( "circle %d %d %d # %.2f Jy = %.2f sigmas (>=%.2f x %.2f + %.2f), %s\n" % ((x+1),(y+1),n_sigmas_int,value,((value-mean_val)/rms),threshold,rms,mean_val,fitsname) ) # (x+1),(y+1) - due to ds9 indexing from 1
   #               print("\tDEBUG (reg file) : circle %d %d %d # %.2f Jy = %.2f sigmas >= (%.2f x %.2f + %.2f), %s\n" % (x,y,n_sigmas_int,value,((value-mean_val)/rms),threshold,rms,mean_val,fitsname))
   #               f_txt.write( "%s %d %d %.2f = %.2f sigma > %.2f x %.2f\n" % (fitsname,x,y,value,(value/rms),threshold,rms) )

                  source_name = "%05d" % (candidates_index)
                  if options.debug_level > 0 :
                     print("\tDEBUG : source = %s at (%d,%d) added to list" % (source_name,x,y))
                  candidates.append( skysources.Source( source_name, ra_deg, dec_deg, flux=value, rms=rms, bkg=mean_val, x=x, y=y, azim_deg=az, elev_deg=alt , uxtime=uxtime ) )
                  candidates_index += 1

   #               if value > mean_val + save_dynamic_spectrum_treshold*rms and cube_data is not None :
   #                  hdu = pyfits.PrimaryHDU()
   #                  hdu.data = np.zeros( (cube_channels,cube_timesteps))
   #                  hdulist = pyfits.HDUList([hdu])
   #                  for cube_cc in range(0,cube_channels):
   #                     for cube_time in range(0,cube_timesteps):
   #                        hdu.data[cube_cc,cube_time]=cube_data[cube_time,cube_cc,y,x]
   #
   #                  dynfile="dynamic_spectrum/start_timeindex%04d_%04d_%04d_%04dsigmas.fits" % (starttimeindex,x,y,n_sigmas_int)
   #                  hdulist.writeto(dynfile,clobber=True)
   #                  print "Saved dynamic spectrum of pixel (%d,%d) to file %s" % (x,y,dynfile)
               else:
                  if update_source :
                     if existing_source_index >= 0 :
                        candidates[existing_source_index] = skysources.Source( source_name, ra_deg, dec_deg, flux=value, rms=rms, bkg=mean_val, x=x, y=y, azim_deg=az, elev_deg=alt , uxtime=uxtime )
                     else :
                        print("ERROR : requsted to update source, but existing_source_index = %d -> ignored" % (existing_source_index))

               if options.debug_level > 0 :
                  print() # just 1 newline needed
   
         if options.debug_level > 0 :
            print("DEBUG : finished y = %d, number of pixels above threshold = %d -> number of sources = %d" % (y,n_above_threshold,len(candidates)))


      if len(candidates) > 0 :
         # if candidates identified :
         postfix_txt = ("_cand.txt")
         postfix_reg = ("_cand.reg")

         regfile=fitsname.replace('.fits', postfix_reg )
         txtfile=fitsname.replace('.fits', postfix_txt )

         # open files
         f_reg = open( regfile , "w" )
         f_reg.write("global color=white width=5 font=\"times 10 normal\"\n")
         f_txt = open( txtfile , "w" )
         f_txt.write("# FITSNAME X Y FLUX[Jy] SNR ThreshInSigma RMS RA[deg] DEC[deg] AZIM[deg] ELEV[deg] UXTIME IMAGE_MIN IMAGE_MAX\n")          

         for cand in candidates :
            n_sigmas = (cand.flux/cand.rms)
            n_sigmas_int = int(n_sigmas)
            snr = ((cand.flux-cand.bkg)/cand.rms)
            f_reg.write( "circle %d %d %d # %.2f Jy = %.2f sigmas (>=%.2f x %.2f + %.2f), %s ,  (ra,dec) = ( %.6f , %.6f ) [deg]\n" % ((cand.x+1),(cand.y+1),n_sigmas_int,cand.flux,snr,options.threshold_in_sigma,cand.rms,cand.bkg,fitsname,ra_deg,dec_deg) ) # (x+1),(y+1) - due to ds9 indexing from 1
            if options.debug_level > 0 :
               print("\tDEBUG (reg file) : circle %d %d %d # %.2f Jy = %.2f sigmas >= (%.2f x %.2f + %.2f), %s\n" % (cand.x,cand.y,n_sigmas_int,cand.flux,snr,options.threshold_in_sigma,cand.rms,cand.bkg,fitsname))
            f_txt.write( "%s %d %d %.2f %.2f %.2f %.2f %.6f %.6f %.6f %.6f %.2f %.4f %.4f\n" % (fitsname,cand.x,cand.y,cand.flux,(cand.flux/cand.rms),options.threshold_in_sigma,cand.rms,cand.ra_degs,cand.dec_degs,cand.azim_deg,cand.elev_deg,cand.uxtime,min_value_image,max_value_image) )

         f_reg.close()
         f_txt.close()

         print("Closed file %s , saved %d candidates" % (regfile,len(candidates)))
      else :
         if options.debug_level > 0 :
            print("DEBUG : no candidates identified")

      if len(catatalog_sources) > 0 :
         regfile_catsources=fitsname.replace('.fits', "_cat_sources.reg" )
         f_cat_reg = open( regfile_catsources , "w" )
         f_cat_reg.write("global color=white width=5 font=\"times 10 normal\"\n")

         for catsrc in catatalog_sources :
            ( catsrc_x , catsrc_y ) = pix2sky.sky2pix( fits, catsrc.ra_degs, catsrc.dec_degs )
   #        f_cat_reg.write( "circle %d %d %d # text={%s at (ra,dec) = (%.4f,%.4f) [deg]}\n" % ((catsrc_x+1),(catsrc_y+1),10,catsrc.name,catsrc.ra_degs,catsrc.dec_degs) )
            if not numpy.isnan( catsrc_x ) and not numpy.isnan( catsrc_y ) and not numpy.isnan( catsrc.ra_degs ) and not numpy.isnan( catsrc.dec_degs ) : 
               f_cat_reg.write( "circle %d %d %d # %s at (ra,dec) = (%.4f,%.4f) [deg]\n" % ((catsrc_x+1),(catsrc_y+1),10,catsrc.name,catsrc.ra_degs,catsrc.dec_degs) )
               f_cat_reg.write( "text %d %d {%s at (ra,dec) = (%.4f,%.4f) [deg]}\n" % ((catsrc_x+5),(catsrc_y+15),catsrc.name,catsrc.ra_degs,catsrc.dec_degs) )

         f_cat_reg.close()

         print("Closed file %s , saved %d sources" % (regfile_catsources,len(catatalog_sources)))
      else :
         print("DEBUG : no catalogue sources identified in the image")

      if b_no_header :
         starttimeindex += 1

      file_end_time=time.time()
      print("source_finder_simple.py: file %s took %.4f seconds ( %.6f - %.6f ) -> %d candidates found" % (fitsname,(file_end_time-file_start_time),file_end_time,file_start_time,len(candidates)))

   fits.close()

   end_time = time.time()
   print("source_finder_simple.py: Start_time = %.6f , end_time = %.6f -> took = %.6f seconds (including import took %.6f seconds)" % (start_time,end_time,(end_time-start_time),(end_time-start_time0)))

