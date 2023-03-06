from __future__ import print_function

import pdb

import datetime
import time
import numpy
import os,sys,errno
import math
from string import Template
import pix2sky
import skysources
import satellites

# import pyfits
import astropy.io.fits as pyfits
import astropy # for sun 
from astropy.time import Time # for sun

# turn-off downloading ephemeirs files :
from astropy.utils.iers import conf
conf.auto_max_age = None
from astropy.utils import iers
iers.conf.auto_download = False  


# options :
from optparse import OptionParser,OptionGroup

# copy :
import copy

# reading routines 
from eda2_aavs2_concidence import read_candidate_file
from eda2_aavs2_concidence import count_rfi
from eda2_aavs2_concidence import is_plane_path

try :
   from astropy.coordinates import SkyCoord, EarthLocation, get_sun
   # CONSTANTS :
   MWA_POS=EarthLocation.from_geodetic(lon="116:40:14.93",lat="-26:42:11.95",height=377.8)

   import sky2pix
   from astropy.time import Time
except :
   print("WARNINF : could not load astropy.coordinates - Sun elevation cuts will not work")   
   MWA_POS=None


# debug_level 
debug_level = 1

# STAT :
min_uxtime = 1e20
max_uxtime = -1e20


def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass

class FluxMeasurement:
    def __init__( self, uxtime=-1, flux=-1, rms=-1, rmsiqr=-1 ) :
        self.uxtime = uxtime
        self.flux   = flux
        self.flagged = False
        self.rms = rms
        self.rmsiqr = rmsiqr

def read_lightcurve( filename, uxtime_index=0, flux_index=1, rms_index=6, rmsiqr_index=7 ) : 
   print("read_lightcurve(%s) ..." % (filename))
   
   if not os.path.exists( filename ) :
      print("ERROR : could not read satellite info file %s" % (filename))
      return (None,0.00,None)
   
   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data
   
   lc=[]

   for line in data : 
      line=line.rstrip()
      words = line.split(' ')

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<2 :
         continue

#      print "line = %s , words = %d" % (line,len(words))

      if line[0] != "#" :
         uxtime = float( words[uxtime_index+0] )
         flux = float( words[flux_index+0] )
         rms = float( words[rms_index+0] )
         rmsiqr = float( words[rmsiqr_index+0] )
         new = FluxMeasurement( uxtime=uxtime, flux=flux, rms=rms, rmsiqr=rmsiqr )         
            
         lc.append( new )

   print("Read %d lines from file %s" % (len(lc),filename))

   return ( lc )

def find( lc , uxtime , inttime ):

   min_diff = 1e6
   closest  = None
   
   for fm in lc : 
      diff = math.fabs( fm.uxtime - uxtime )
      
      if diff < min_diff :
         min_diff = diff
         closest  = fm
         
      if (fm.uxtime - uxtime) > (10*inttime) :
         continue
         
      
   return (closest,min_diff)   

def find_max( lc , min_uxtime , max_uxtime, inttime ):

   max_val = -1e9
   max_point = None
   
   for fm in lc : 
      if min_uxtime <= fm.uxtime and fm.uxtime <= max_uxtime :
      
         if fm.flux > max_val :
            max_val = fm.flux
            max_point = fm
         
      if fm.uxtime > (max_uxtime + (2*inttime)) :
         break
         
      
   return (max_point,max_val)   

def get_radec( object_name ):
   if object_name.upper() == "B0950+08" or object_name.upper() == "B0950" :
      return ( 148.28875 , 7.92638889 )

   if object_name.upper() == "SGR1935+2154" or object_name.upper() == "SGR1935" : 
      return ( 293.750 , 21.90 )

   return (None,None)
 
def count_spikes( object_lc, off_lc, options ) :
   global min_uxtime, max_uxtime    

   mkdir_p( options.outdir )
   out_name=options.object_lightcurve
   postfix= ("_thresh%dJy.txt" % (int(round(options.threshold))))
   out_name=out_name.replace(".txt",postfix)
   out_file = ("%s/%s" % (options.outdir,out_name))
   out_f = open( out_file , "w" )
   header_line = ("# UXTIME FLUX[Jy/beam]\n")
   out_f.write( header_line )
   
   min_uxtime = 1e20
   max_uxtime = -1e20

   n_spikes = 0   
   for fm_obj in object_lc : 
      if fm_obj.uxtime < min_uxtime :
         min_uxtime = fm_obj.uxtime

      if fm_obj.uxtime > max_uxtime :
         max_uxtime = fm_obj.uxtime
   
      # check if RMS-IQR does not exceed limit :            
      if fm_obj.rmsiqr > options.maximum_rmsiqr :
         print("DEBUG : uxtime = %.2f , flux = %.4f skipped as RMSIQR = %.2f > limit = %.2f" % (fm_obj.uxtime,fm_obj.flux,fm_obj.rmsiqr,options.maximum_rmsiqr))
         continue

    
#      if math.fabs( fm_obj.uxtime-1586693741.20) <= 10 :
#         print("odo")
   
#      (fm_off,diff) = find( off_lc, fm_obj.uxtime, options.inttime )
      (fm_off_max,off_max_value ) = find_max( off_lc, fm_obj.uxtime-options.inttime, fm_obj.uxtime+options.inttime, options.inttime )
      
      # flag data points which have a spike in the OFF-object lightcurve above the same threshold 
#      if diff <= (2*options.inttime) and fm_off is not None :
#         if fm_off.flux > options.threshold :
#            fm_obj.flagged = True

      # flag when OFF flux (maximum of +/- inttime) exceeds threshold. This is becuase of side-lobes from strong RFI sources
      #  side-lobes are going +/- on image with a strong RFI and afterwards there can be also many positive (high-value) signals too. Hence, I will allow +/- 2 inttimes
      if fm_off_max is not None :
         if fm_off_max.flux > options.threshold :
            fm_obj.flagged = True
         else :
            print("DEBUG : uxtime = %.2f , flux = %.4f accepted maximum OFF-object value = %.2f below threshold = %.2f" % (fm_obj.uxtime,fm_obj.flux,fm_off_max.flux,options.threshold))

      # count not-flagged points and show them :   
      if not fm_obj.flagged and fm_obj.flux > options.threshold :  # not flagged and above the threshold 
         if options.use_diff_candidates :
         
            b_strong_rfi = False
            for cand_uxtime in range( int(fm_obj.uxtime-options.inttime-2) , int(fm_obj.uxtime+options.inttime) + 1 ) : 
               print("\tDEBUG : checking uxtime = %d" % (cand_uxtime))
               cand_time = Time( cand_uxtime ,format='unix')
               
               # chan_294_20200411T153010_I_diff_cand.txt
               utc = time.strftime("%Y%m%dT%H%M%S",time.gmtime(cand_uxtime))
               cand_file = ("chan_%d_%s_I_diff_cand.txt" % (options.freq_channel,utc))
                              
               if os.path.exists( cand_file ) :
                  print("\tDEBUG : reading transients from file %s" % (cand_file))
                  candidates = read_candidate_file( cand_file )
                  rfi_count = count_rfi( candidates, options.rfi_flux_threshold )
                  message = ""
                  if rfi_count > 0 :
                     fm_obj.flagged = True
                     message = " -> flagging point"
                  print("\tDEBUG : read %d candidates from file %s , found %d events exceeding RFI threshold = %.2f %s" % (len(candidates),cand_file,rfi_count,options.rfi_flux_threshold,message))
                  
                  if fm_obj.flagged :
                     # no need to check next files if rejected
                     break                  
               else :
                  print("\tWARNING : checking of transient candidates required, but file %s not found" % (cand_file))
               
         
         fm_obj_uxtime = Time( fm_obj.uxtime ,format='unix')         
         if options.max_sun_elevation <= 91.00 :
            if MWA_POS is not None : 
               sunpos = astropy.coordinates.get_sun( fm_obj_uxtime )
               sun_ra_deg  = sunpos.ra.hour * 15.00
               sun_dec_deg =  sunpos.dec.degree
               sun_elev_deg = -1000
               sun_az_deg   = -1000
               coord = SkyCoord( sun_ra_deg, sun_dec_deg, equinox='J2000',frame='icrs', unit='deg')
               coord.location = MWA_POS
               coord.obstime = Time( fm_obj.uxtime, scale='utc', format="unix" )
               altaz = coord.transform_to('altaz')
               sun_az_deg, sun_elev_deg = altaz.az.deg, altaz.alt.deg
               print("DEBUG : sun position calculated for uxtime = %.2f at (ra,dec) = (%.4f,%.4f) [deg] -> (az,elev) = (%.4f,%.4f) [deg]" % (fm_obj.uxtime,sun_ra_deg,sun_dec_deg,sun_az_deg,sun_elev_deg))

               if sun_elev_deg > options.max_sun_elevation :
                  print("DEBUG : warning, maximum allowed Sun elevation = %.2f [deg] exceeded with the value = %.2f [deg] -> skipeed" % (options.max_sun_elevation,sun_elev_deg))
                  continue
            else :
               print("ERROR : MWA_POS is None meaning that the import |from astropy.coordinates import SkyCoord, EarthLocation| did not work and Sun elevation cannot be checked")
               sys.exit(-1)

         # check plane paths :
         # object_name
         ra_deg = options.ra_deg
         dec_deg = options.dec_deg
         if ra_deg is None or dec_deg is None : 
            ( ra_deg , dec_deg ) = get_radec( options.object_name )
         coord_obj = SkyCoord( ra_deg , dec_deg , equinox='J2000',frame='icrs', unit='deg')   
         coord_obj.location = MWA_POS
         coord_obj.obstime = Time( fm_obj.uxtime, scale='utc', format="unix" )
         altaz_lc = coord_obj.transform_to('altaz')
         lc_az_deg, lc_elev_deg = altaz_lc.az.deg,  altaz_lc.alt.deg
         (is_plane,plane_ang_dist_deg,path_index) = is_plane_path( lc_az_deg, lc_elev_deg, radius=10 )
         if is_plane :
            print("DEBUG : uxtime = %.2f at (ra,dec) = (%.4f,%.4f) [deg] -> (az,elev) = (%.4f,%.4f) [deg] matches plane path %d (ang_dist = %.4f [deg]) -> skipped" % (fm_obj.uxtime,ra_deg,dec_deg,lc_az_deg,lc_elev_deg,path_index,plane_ang_dist_deg))
            continue
         
         
         if not fm_obj.flagged : # checking flagging again, because RFI could have been found          
            line = ("%.2f %.2f [Jy]" % (fm_obj.uxtime,fm_obj.flux))
            print("FILTERED : %s" % (line))
            out_f.write( line + "\n" )
            
            n_spikes += 1 

   out_f.close()
   return n_spikes

def show_good_spikes( object_lc ) :

  print("------------------------------")
  print("Good spikes:")
  print("------------------------------")
  for fm_obj in object_lc :
     if not fm_obj.flagged :
        print("%.2f %.2f [Jy]" % (fm_obj.uxtime,fm_obj.flux))

def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tCount spikes above specified threshold, but exclude those coinciding with OFF-OBJECT spikes (most likely RFI or other artefacts, like side-lobes etc)\n'
   parser = OptionParser(usage=usage,version=1.00)
   
#   parser.add_option('--max_delay_sec',dest="max_delay_sec",default=2,help="Maximum dispersion delay to check coincidence for [default %default]",type="float")
   parser.add_option('--coinc_radius_deg',dest="coinc_radius_deg",default=3.3,help="Coincidence radius in degrees [default 1 beam size %default]",type="float")
   parser.add_option('--object_name','--name',dest="object_name",default="B0950+08",help="Object name [default %default]")
   parser.add_option('--object_lc','--object_lightcurve','--lightcurve',dest="object_lightcurve",default="B0950+08_diff.txt",help="On object lightcurve [default %default]")   
   parser.add_option('--off_lc','--off_object_lightcurve','--off_lightcurve','--reference_lightcurve',dest="off_lightcurve",default="OFF_B0950+08_diff.txt",help="Off-object lightcurve [default %default]")
   parser.add_option('--inttime','--integration_time',dest="inttime",default=2,help="Integration time [default %default]",type="float")
   parser.add_option('--freq_ch','--ch','--channel',dest="freq_channel",default=294,help="Frequency channel [default %default]",type="int")
   parser.add_option('--thresh','--threshold',dest="threshold",default=38,help="Integration time [default %default]",type="float")
   parser.add_option('--outdir','--out_dir','--output_dir','--dir',dest="outdir",default="lc_filtered/",help="Output directory [default %default]")
   parser.add_option('--use_diff_candidates','--use_candidates',action="store_true",dest="use_diff_candidates",default=False, help="Use candidates from difference images [default %]")   
   parser.add_option('--max_rmsiqr','--maximum_rmsiqr',dest="maximum_rmsiqr",default=100,help="Maximum allowed value of RMS-IQR [default %default]",type="float")

   parser.add_option('--ra_deg',dest="ra_deg",default=None,help="RA [deg] [default %default]",type="float")
   parser.add_option('--dec_deg',dest="dec_deg",default=None,help="DEC [deg] [default %default]",type="float")
   
   # RFI excision : 
   parser.add_option('--rfi_flux_threshold','--rfi_thresh','--rfi',dest="rfi_flux_threshold",default=1500,help="RFI threshold [default %default]",type="float")
   
   # sun cuts due to very high values in side-lobes :
   parser.add_option('--max_sun_elev','--max_sun_elevation',dest="max_sun_elevation",default=100,help="Maximum Sun elevation allowed [default %default , >= 90 effectively turns this cut off]",type="float")


   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)





if __name__ == "__main__":

   (options, args) = parse_options()

   print("######################################################")
   print("PARAMETERS :")
   print("######################################################")
   print("Object lightcurve = %s" % (options.object_lightcurve))
   print("Off object lightcurve = %s" % (options.off_lightcurve))
   print("Use candidates    = %s" % (options.use_diff_candidates))
   print("Max RMS IQR       = %.2f [Jy]" % (options.maximum_rmsiqr))
   print("######################################################")

   object_lc = read_lightcurve( options.object_lightcurve )
   off_object_lc = read_lightcurve( options.off_lightcurve )   
   
   n_ok_spikes = count_spikes( object_lc, off_object_lc, options )      
#   show_good_spikes( object_lc ) 
   
   total_inttime = float(options.inttime) * len(object_lc)
   
   print("-----------------------------------------------------------------")                
   print("STATISTICS :")
   print("-----------------------------------------------------------------")
   print("OK spikes = %d" % (n_ok_spikes))
   print("Unix time range = %.2f - %.2f -> %.4f [hours]" % (min_uxtime,max_uxtime,(max_uxtime-min_uxtime)/3600.00))
   print("Total time on B0950 %.2f seconds -> %.4f [hours]" % (total_inttime,total_inttime/3600.00))
   print("-----------------------------------------------------------------")
   
   
   