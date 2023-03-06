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

try :
   from astropy.coordinates import SkyCoord, EarthLocation, get_sun
   # CONSTANTS :
   MWA_POS=EarthLocation.from_geodetic(lon="116:40:14.93",lat="-26:42:11.95",height=377.8)

   import sky2pix
   from astropy.time import Time
except :
   print("WARNING : could not load astropy.coordinates - Sun elevation cuts will not work")   
   MWA_POS=None


# debug_level 
debug_level = 1

# STATISTICS :
min_uxtime = 1e20
max_uxtime = -1e20
min_uxtime_eda2 = 1e20
max_uxtime_eda2 = -1e20
min_uxtime_aavs2 = 1e20
max_uxtime_aavs2 = -1e20
min_uxtime_coinc = 1e20
max_uxtime_coinc = -1e20

# global variables:
# list of diff images:
low_freq_diff_fits_list = None
high_freq_diff_fits_list = None


def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass

class CandidateCounter:
    def __init__( self, uxtime=-1, start_counter=0, sat_above_hor_all=0, sat_above_min_elev=0, random_match_probability=0, low_cand_count=-1, high_cand_count=-1, file="", low_file="" ):
        self.file = file
        self.uxtime = uxtime
        self.counter = start_counter
        self.sat_above_hor_all = sat_above_hor_all
        self.sat_above_min_elev = sat_above_min_elev
        self.random_match_probability = random_match_probability
        self.low_file = low_file
        self.low_cand_count = 0
        if low_cand_count >= 0 :
           self.low_cand_count = low_cand_count
        self.high_cand_count = 0
        if high_cand_count >= 0 :
           self.high_cand_count = high_cand_count
           
    def increment( self ) :     
       self.counter = self.counter + 1
       
    def update( self, uxtime=-1, sat_above_hor_all=-1, sat_above_min_elev=-1, random_match_probability=None, low_cand_count=-1, high_cand_count=-1 ) :
       if uxtime >= 0 :
          self.uxtime = uxtime
       if sat_above_hor_all >= 0 :
          self.sat_above_hor_all = sat_above_hor_all
       if sat_above_min_elev >= 0 :
          self.sat_above_min_elev = sat_above_min_elev          
       if random_match_probability is not None and random_match_probability >= 0 :
          self.random_match_probability = random_match_probability
       if low_cand_count >= 0 :
          self.low_cand_count = low_cand_count
       if high_cand_count >= 0 :
          self.high_cand_count = high_cand_count
       
       if self.random_match_probability <= 0 : # [4] <= 0 :
          if random_match_probability is not None and random_match_probability >= 0 :
             self.random_match_probability = random_match_probability
       else : 
          if random_match_probability is not None and random_match_probability >= 0 : 
             if math.fabs( self.random_match_probability - random_match_probability ) > 0.000001 :  # [4] - random_match_probability ) > 0.000001 :
                 print("WARNING : random match probability for image %s was %.8f and now is different and = %.8f - looks like bug in code, please verify !!!" %\
                        (self.file,self.random_match_probability,random_match_probability))
       
       self.counter = self.counter + 1

#   candidates_per_image = {}
def init_candidate_counter( candidates_per_image, candidates_high_freq, candidates_low_freq ):
    start_time = time.time()
    print("PROGRESS : init_candidate_counter started at uxtime = %.2f" % (start_time))
    last_index = 0
    
    for high_freq_candidate in candidates_high_freq :              
       if not high_freq_candidate.file in candidates_per_image.keys() :
          # print("init_candidate_counter : counting candidates in image %s , starting from last_index" % (high_freq_candidate.file))
          save_last_index = last_index
          (cnt,last_index) = count_candidates( candidates_high_freq , high_freq_candidate.file, last_index )
          print("init_candidate_counter : counted candidates in image %s , starting from last_index = %d, count = %d" % (high_freq_candidate.file,save_last_index,cnt))
          candidates_per_image[ high_freq_candidate.file ] = CandidateCounter( high_cand_count=cnt, file=high_freq_candidate.file, uxtime=high_freq_candidate.uxtime, low_cand_count=0 )
   
    print("PROGRESS : init_candidate_counter finished after %.3f seconds" % (time.time()-start_time))


class CoincCandidate:
    def __init__( self, evt_name, mean_ra_degs, mean_dec_degs, min_dist_arcsec, delay_sec, cand_high, cand_low, sun_dist_arcsec, 
                  mean_az_degs , mean_elev_degs, satinfo_trunc, satdist_arcsec,  source_info, source_dist, all_above_horizon_count, 
                  random_match_probability, classif, n_low, n_high ) :
        self.evt_name = evt_name
        self.mean_ra_degs = mean_ra_degs
        self.mean_dec_degs = mean_dec_degs
        self.min_dist_arcsec = min_dist_arcsec
        self.delay_sec = delay_sec
        self.cand_high = copy.copy( cand_high )
        self.cand_low = copy.copy( cand_low )
        self.sun_dist_arcsec = sun_dist_arcsec
        self.mean_az_degs = mean_az_degs
        self.mean_elev_degs = mean_elev_degs
        self.satinfo_trunc = satinfo_trunc
        self.satdist_arcsec = satdist_arcsec
        self.source_info = source_info
        self.source_dist = source_dist
        self.all_above_horizon_count = all_above_horizon_count
        self.random_match_probability = random_match_probability
        self.classif = classif
        self.n_low = n_low
        self.n_high = n_high
        
#        self.min_val = min_val
#        self.max_val = max_val


def FlagRFI( coinc_candidates, high_fits_file ) :
   flagged = 0
   for candidate in coinc_candidates :
      if candidate.cand_high.file == high_fits_file :
         if candidate.classif is not None and candidate.classif != "" and len(candidate.classif)>0 : 
            if candidate.classif.find("RFI") < 0 :
               # do not add many RFI flags 
               if candidate.classif.find("TRANSIENT_CANDIDATE") >= 0 :
                  candidate.classif = "RFI"
               else :
                  candidate.classif = candidate.classif + ",RFI"
               print("\tDEBUG : evt_name = %s on high file = %s rejected" % (candidate.evt_name,candidate.cand_high.file))
         else :
            candidate.classif = "RFI"
         flagged += 1
      else :
         if candidate.cand_high.file > high_fits_file :
            break   
            
   return flagged
      

# Post-coincidence criteria :
#   1/ reject events from the same image where strong RFI was found (see page 8 of /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200410/20200905_data20200410_reanalysis.odt ) 
#      sidelobes can be ~0.00765 -> ~ -21dB -> exceed ~20Jy (5sigma) when there is a flash ~2500 Jy 
# 
def PostCoinc( coinc_candidates, 
               sidelobe_threshold=1000 ) : # 20200410 data seems to suggest that the sidelobes can be even ~0.01 - 0.02 so ~ -20 - -17 dB - not super-high supression 

   # if very bright RFI (PLANE) found -> flag the rest of events based on SIDE-LOBE criteria
   for candidate in coinc_candidates :
      if candidate.classif.find("PLANE") >= 0 or candidate.classif.find("RFI") >= 0 : # RFI are already flagged no need to add here 
         if candidate.cand_high.flux > sidelobe_threshold :
            for cand2 in coinc_candidates :
               if cand2.cand_high.file == candidate.cand_high.file :
                  if cand2.classif[0:9] == "TRANSIENT" : 
                     cand2.classif = "SIDELOBE_PLANE(%.1f,%.1f)" % (candidate.cand_high.flux,candidate.cand_low.flux)
                  
               if cand2.cand_high.file > candidate.cand_high.file :
                  break

         if candidate.cand_low.flux > sidelobe_threshold :
            for cand2 in coinc_candidates :
               if cand2.cand_low.file == candidate.cand_low.file :
                  if cand2.classif[0:9] == "TRANSIENT" : 
                     cand2.classif = "SIDELOBE_PLANE(%.1f,%.1f)" % (candidate.cand_high.flux,candidate.cand_low.flux)
                  
               if cand2.cand_high.file > candidate.cand_high.file :
                  break

def save_coinc_event( cand_high, cand_low, out_f ,  min_dist_arcsec, sun_dist_arcsec, evt_name ) :
                      
   delay_sec = (cand_low.uxtime - cand_high.uxtime)           
   mean_ra_degs = ( cand_high.ra_degs + cand_low.ra_degs ) / 2.00
   mean_dec_degs = ( cand_high.dec_degs + cand_low.dec_degs ) / 2.00
   mean_az_degs = (cand_high.azim_deg+cand_low.azim_deg)/2.00
   mean_elev_degs = (cand_high.elev_deg+cand_low.elev_deg)/2.00
   mean_ux =  ( cand_high.uxtime + cand_low.uxtime ) / 2.00
                          
   out_line = "%s %010.5f %010.5f %06.4f %07.3f %s %08.3f %05.1f %010.5f %010.5f %05.1f %05.1f %08.3f %s %08.3f %05.1f %10.5f %10.5f %05.1f %05.1f %10.4f %06.1f %06.2f %06.2f %20s %07.1f %2s %07.1f %d %.06f %d %d %s\n" % ( \
                                                            evt_name, mean_ra_degs, mean_dec_degs, 
                                                            (min_dist_arcsec/3600.00),delay_sec, \
                                                            cand_high.file,cand_high.flux,cand_high.snr, \
                                                            cand_high.ra_degs,cand_high.dec_degs,cand_high.x,cand_high.y,cand_high.uxtime, \
                                                            cand_low.file,cand_low.flux,cand_low.snr,cand_low.ra_degs,cand_low.dec_degs, \
                                                            cand_low.x,cand_low.y,cand_low.uxtime,(sun_dist_arcsec/3600.00), \
                                                            mean_az_degs , mean_elev_degs, 
                                                            "-", (360*3600), 
                                                            "-", (360*3600),
                                                            -1, -1, -1, -1, "-" 
                                                        )
   out_f.write( out_line )
   
   
def save_coinc_candidates( coinc_candidates , out_f ) :
   for cand in coinc_candidates :
#      print("DEBUG_SATINFO : |%s|" % (cand.satinfo_trunc))
      out_line = "%s %010.5f %010.5f %06.4f %07.3f %s %08.3f %05.1f %010.5f %010.5f %05.1f %05.1f %08.3f %s %08.3f %05.1f %10.5f %10.5f %05.1f %05.1f %10.4f %06.1f %06.2f %06.2f %40s %07.1f %2s %07.1f %d %.06f %d %d %s\n" % ( \
                                                                cand.evt_name, cand.mean_ra_degs, cand.mean_dec_degs, 
                                                                (cand.min_dist_arcsec/3600.00),cand.delay_sec, \
                                                                cand.cand_high.file,cand.cand_high.flux,cand.cand_high.snr, \
                                                                cand.cand_high.ra_degs,cand.cand_high.dec_degs,cand.cand_high.x,cand.cand_high.y,cand.cand_high.uxtime, \
                                                                cand.cand_low.file,cand.cand_low.flux,cand.cand_low.snr,cand.cand_low.ra_degs,cand.cand_low.dec_degs, \
                                                                cand.cand_low.x,cand.cand_low.y,cand.cand_low.uxtime,(cand.sun_dist_arcsec/3600.00), \
                                                                cand.mean_az_degs , cand.mean_elev_degs, 
                                                                cand.satinfo_trunc, cand.satdist_arcsec, 
                                                                cand.source_info, cand.source_dist,
                                                                cand.all_above_horizon_count, cand.random_match_probability,
                                                                cand.n_low, cand.n_high,
                                                                cand.classif
                                                            )
      out_f.write( out_line )
   
   
   print("DEBUG : closing output coinc file")
   out_f.close()

def count_candidates( candidates , file, start_index=0 ) :
   count = 0
   l = len(candidates)
   # for cand in candidates :
   last_index = start_index
   for i in range(start_index,l) :      
      cand = candidates[i]
      if cand.file == file :
         count += 1 
         
      last_index = i   
   
      if cand.file > file :
         break

   return (count,last_index)

# PATH1 (ARC1) : see pages 6-8 of : /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200410/20200905_data20200410_reanalysis.odt
def plane_path_az( azim ) :
   p0 = 19.2353     #  +/-   1.55819     
   p1 =  0.682664   #  +/-   0.0444157   
   p2 = -0.00432763 #  +/-   0.000281785 
   alt_fit = p0 + p1*azim + p2*(azim*azim)
   
   return (azim,alt_fit)

# PATH2 (ARC2) see page 8 of /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200410/20200905_data20200410_reanalysis.odt
def plane_path2_az( azim ) :
   p0 = -406.238    # +/-   10.5769     
   p1 =  3.2948     # +/-   0.0773042   
   p2 = -0.00589933 # +/-   0.000138803    
   alt_fit = p0 + p1*azim + p2*(azim*azim)

   return (azim,alt_fit)


# see : page 7 of /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200410/20200905_data20200410_reanalysis.odt   
def is_plane_path( azim , alt , radius=10 ) :
   if debug_level > 1 :
      print("DEBUG (is_plane_path) : checking (azim,alt) = (%.4f,%.4f) [deg]" % (azim,alt))

   # check path1 :
   (az_fit,alt_fit) = plane_path_az( azim )   
   ang_dist_arcsec = skysources.angdist_arcsec( azim , alt , az_fit, alt_fit )   
   ang_dist_deg = ang_dist_arcsec / 3600.00   
   ang_dist1_deg = ang_dist_deg
   if debug_level > 1 :
      print("DEBUG (is_plane_path) : Path1 in distance = %.4f [deg]" % (ang_dist_deg))
   if ang_dist_deg < radius :
      return (True,ang_dist_deg,1)

   # check path2 :
   (az_fit,alt_fit) = plane_path2_az( azim )   
   ang_dist_arcsec = skysources.angdist_arcsec( azim , alt , az_fit, alt_fit )   
   ang_dist_deg = ang_dist_arcsec / 3600.00   
   ang_dist2_deg = ang_dist_deg
   if debug_level > 1 :
      print("DEBUG (is_plane_path) : Path2 in distance = %.4f [deg]" % (ang_dist_deg))
   if ang_dist_deg < radius :
      return (True,ang_dist_deg,2)
   
   ret_ang_dist_min = min( ang_dist1_deg, ang_dist2_deg )   
   
   return (False,ret_ang_dist_min,0)
    


def read_sattest_output( filename, transient_ra_deg, transient_dec_deg, sat_radius_deg=360.00, min_elevation=0.00, max_sat_distance_km=1e20 ) : 
   print("read_data(%s) ..." % (filename))
   
   if not os.path.exists( filename ) :
      print("ERROR : could not read satellite info file %s" % (filename))
      return (None,0.00,None,None,None,None)
   
   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data
   
   satlist=[]
   closest_sat = None
   min_ang_dist_arcsec = 1e20
   min_ang_dist_name = None
   all_above_horizon_count = 0
   above_min_elevation_count = 0

   for line in data : 
      line=line.rstrip()
      words = line.split(' ')

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<4 :
         continue

#      print "line = %s , words = %d" % (line,len(words))

      if line[0] != "#" :
         ut_dtm  = words[0+0]
         ra_degs = float( words[1+0] )
         dec_degs = float( words[2+0] )
         azim_degs = float( words[3+0] )
         elev_degs = float( words[4+0] )
         alt_km = float( words[5+0] )
         uxtime = float( words[6+0] )
         satname = words[7+0]
         ha_degs = float( words[8+0] )
         is_geostat = int( words[9+0] )
         
         if alt_km > max_sat_distance_km : 
            # skipping satellites further than the limit
            continue
         
         # count all satellites above horizon :
         all_above_horizon_count += 1 
         if elev_degs > min_elevation :
            above_min_elevation_count += 1 
         
         ang_dist_arcsec = skysources.angdist_arcsec( ra_degs, dec_degs, transient_ra_deg, transient_dec_deg )
         
         new_min_distance = False
         if ang_dist_arcsec < min_ang_dist_arcsec :
            # find minimum distance satellite :
            min_ang_dist_arcsec = ang_dist_arcsec
            min_ang_dist_name = satname
            new_min_distance = True
         
         if (ang_dist_arcsec/3600.00) <= sat_radius_deg :
            new_sat = satellites.Satellite( name=satname, ra_degs=ra_degs, dec_degs=dec_degs, azim_deg=azim_degs, elev_deg=elev_degs, ut_dtm=ut_dtm, is_geostat=is_geostat, uxtime=uxtime, file=filename )
            if new_min_distance : # checked ang_dist_arcsec < min_ang_dist_arcsec : earlier and already over-written min_ang_dist_arcsec := ang_dist_arcsec
               closest_sat = new_sat 

            # create a list of all satellites closer to required distance :
            satlist.append( new_sat )
            

   print("Read %d lines from file %s" % (len(satlist),filename))

   return ( closest_sat , min_ang_dist_arcsec , satlist, all_above_horizon_count, above_min_elevation_count, min_ang_dist_name )

def count_rfi( candidates, treshold ) :
   count = 0
   for cand1 in candidates :   
      if cand1.flux > treshold :
         count += 1
         
   return count

def count_candidates_per_image( candidates ) :

   max_candidates_per_image = 0 
   
   cand1_idx = 0
   for cand1 in candidates :
      count_cand_per_image = 1 
      uxtime = cand1.uxtime
      
      cand2_idx = 0
      for cand2 in candidates :
         if cand1_idx != cand2_idx and math.fabs( cand1.uxtime - cand2.uxtime ) < 0.001 :
            count_cand_per_image += 1             
         
         cand2_idx += 1 
         
         

      cand1.sources_per_image = count_cand_per_image         
      cand1_idx += 1 
      
      if count_cand_per_image > max_candidates_per_image :
         max_candidates_per_image = count_cand_per_image

   return max_candidates_per_image

# FITSNAME X Y FLUX[Jy] SNR ThreshInSigma RMS RA[deg] DEC[deg] AZIM[deg] ELEV[deg]
# chan_204_20200530T073345_I_diff.fits 145 134 83.41 9.67 5.00 8.62 71.496394 18.913049 310.267509 25.763331
def read_candidate_file( filename, candidates=None, max_candidates=1e20 ) :
   global min_uxtime
   global max_uxtime
   
   if candidates is not None and len(candidates) > max_candidates :
      print("WARNING : number of candidates %d exceeded limit = %d -> not reading more" % (len(candidates),max_candidates))
      return (candidates)


   # for time to be UTC :
   os.environ["TZ"] = "UTC"

# format : date; time; azimuth; elevation; right ascension; declination; and peak flux density
   print("read_data(%s) ..." % (filename))
   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data
   
   if candidates is None :
      # initalise empty if needed :
      candidates = []

   for line in data : 
      line=line.rstrip()
      words = line.split(' ')

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<4 :
         continue

#      print "line = %s , words = %d" % (line,len(words))

      if line[0] != "#" :
#         print line[:-1]
# # FITSNAME X Y FLUX[Jy] SNR ThreshInSigma RMS RA[deg] DEC[deg] AZIM[deg] ELEV[deg]
# chan_204_20200530T073345_I_diff.fits 145 134 83.41 9.67 5.00 8.62 71.496394 18.913049 310.267509 25.763331
         fitsname=words[0+0]
         x    = int( words[1+0] )
         y    = int( words[2+0] )
         flux = float( words[3+0] )
         snr  = float( words[4+0] )
         thresh_in_sigma = float( words[5+0] )
         rms = float( words[6+0] )
         ra  = float( words[7+0] )
         dec = float( words[8+0] )
         azim = float( words[9+0] )
         elev = float( words[10+0] )
         uxtime = 0
         min_val = None
         max_val = None
         
         print("\tDEBUG : len(words) = %d (%s)" % (len(words),words[10]))
         if len(words) > 11 :
            uxtime = float( words[11+0] )
            print("\tDEBUG : using direct uxtime from 11-th (0-index) column of the log file")
            
            if len(words) >= 12 :
               min_val = float( words[12+0] )
               print("\tDEBUG : min_val = %.4f" % (min_val))
               
            if len(words) >= 13 :
               max_val = float( words[13+0] )
               print("\tDEBUG : max_val = %.4f" % (max_val))
               
         else :
            utc = fitsname[9:24]
            dt_utc = datetime.datetime.strptime(utc,'%Y%m%dT%H%M%S')
            uxtime = float( dt_utc.strftime('%s') )
            
         
         if uxtime > max_uxtime :
            max_uxtime = uxtime

         if uxtime < min_uxtime :
            min_uxtime = uxtime
         
         candidates.append( skysources.Source( name=fitsname, ra = ra, dec = dec,  flux=flux, x=x, y=y, snr=snr, rms=rms, azim_deg=azim, elev_deg=elev, uxtime=uxtime, file=fitsname, min_val=min_val, max_val=max_val ) )
         
         if len(candidates) > max_candidates :
            print("WARNING : number of candidates %d exceeded limit = %d -> not reading more" % (len(candidates),max_candidates))
            break

#    max_candidates_per_image = count_candidates_per_image( candidates )

   print("Read %d lines from file %s" % (len(candidates),filename))      

   return (candidates)

def read_list_file( list_filename ) :
   out_fits_list=[]

   print("read_list_file : reading file %s" % (list_filename))

   candidates=[]
   if os.path.exists( list_filename ) and os.stat( list_filename ).st_size > 0 :
      file=open( list_filename ,'r')
      data=file.readlines()
      for line in data :
         line=line.rstrip()
         words = line.split(' ')
         if line[0] == '#' :
            continue

         if line[0] != "#" :
            candfile = words[0+0] 
            out_fits_list.append( candfile )
            
      file.close()
   else :
      print("WARNING : empty or non-existing file %s" % (list_filename))


   return candidates


def read_candidates( list_filename ) :
   out_fits_list=[]

   print("read_list : reading file %s" % (list_filename))

   candidates=[]
   if os.path.exists( list_filename ) and os.stat( list_filename ).st_size > 0 :
      file=open( list_filename ,'r')
      data=file.readlines()
      for line in data :
         line=line.rstrip()
         words = line.split(' ')
         if line[0] == '#' :
            continue

         if line[0] != "#" :
            candfile = words[0+0] 
            out_fits_list.append( candfile )
            print("Reading candidates from file %s ..." % (candfile))
            
            read_candidate_file( candfile, candidates )   
            print("\tnumber of candidates = %d" % (len(candidates)))
            
      file.close()
   else :
      print("WARNING : empty or non-existing file %s" % (list_filename))


   return candidates


# min_sun_dist_deg = 3 beam sizes 
def coincidence( candidates_high_freq, candidates_low_freq, 
                 outfile="coinc_eda2_aavs2.txt", 
                 reject_file = "coinc_rejected_eda2_aavs2.txt",
                 coinc_radius_deg=3.3, max_delay_sec=2, outdir="coinc/" , 
                 min_sun_dist_deg=10.00, 
                 min_elevation=-100,
                 options=None,
                 cand_per_image_file="coinc_cand_per_image.txt"
#                 plane_flux_threshold=300                 
               ) :
   global min_uxtime_coinc,max_uxtime_coinc            
                  
   ateam_exclude_list = options.ateam_exclude_list.split(",")
   
   out_f = open( outdir + "/" + outfile , "w" )
   reject_f = open( outdir + "/" + reject_file , "w" )

   outfile_all_coinc = outfile.replace(".txt","_all_coinc.txt")
   out_all_coinc_f = open( outdir + "/" + outfile_all_coinc , "w" )

   header_line = "# EVTNAME MEAN_RA[deg] MEAN_DEC[deg] ANG_DIST[deg] DELAY[sec] FITSFILE_highfreq Flux_high[Jy] SNR_high RA_high[deg] DEC_high[deg] X_high Y_high UXTIME_high FITSFILE_lowfreq Flux_low[Jy] SNR_low RA_low[deg] DEC_low[deg] X_low Y_low UXTIME_low DIST_sun[deg] AZIM_mean[deg] ELEV_mean[deg] SATINFO SAT_DIST[arcsec] OBJECT OBJ_DIST[arcsec] TLE_SAT_PER_IMAGE RANDOM_MATCH_PROBABILITY #LOW #HIGH CLASSIF \n" 
   out_f.write( header_line )
   reject_f.write( header_line )
   out_all_coinc_f.write( header_line )
   
   sunpos = None
   sun_ra_deg = None
   sun_dec_deg = None

   evtidx = 0

   # pre-calculated constants used later :   
   coinc_radius_rad = coinc_radius_deg * ( math.pi / 180.00 )
   min_elevation_rad = min_elevation * ( math.pi / 180.00 )
   sin_val = math.sin( coinc_radius_rad / 2.00 ) / math.sin( (math.pi/2.00 - min_elevation_rad)/2.00 )


   # brightest on the last image :
   ret_low_last = None
   brightest_low_last = None 
   brightest_low_dist_arcsec_last = 0.00
   ret_high_last = None
   brightest_high_last = None 
   brightest_high_dist_arcsec_last = 0.00
   
   
   candidates_per_image = {}
   # def init_candidate_counter( candidates_per_image, candidates_high_freq, candidates_low_freq ):
   init_candidate_counter( candidates_per_image, candidates_high_freq, candidates_low_freq )
   
   coinc_candidates = []
   
   n_coinc=0
   
   # list of flagged images to avoid multiple flagging :
   flagged_images = []
   
   sun_positions = {}
      
   for cand_high in candidates_high_freq :
      if options.fits_file is not None :
         if cand_high.file != options.fits_file :
            continue
   
      # check if no RFI in the image:
      if options.min_image_value is not None :
         if cand_high.min_val is not None and cand_high.min_val <= options.min_image_value :
            print("DEBUG : candidate on image %s skipped due to min_image_value = %.4f < min_val_allowed = %.4f" % (cand_high.file,cand_high.min_val,options.min_image_value))
            continue
            
      if options.max_image_value is not None :
         if cand_high.max_val is not None and cand_high.max_val >= options.max_image_value :
            print("DEBUG : candidate on image %s skipped due to max_image_value = %.4f > max_val_allowed = %.4f" % (cand_high.file,cand_high.max_val,options.max_image_value))
            continue
            
   
      random_match_probability = 0.00
      max_uxtime = cand_high.uxtime + max_delay_sec
      
      cand_high_time = Time( cand_high.uxtime ,format='unix')
      cand_high_uxtime_int = int( cand_high.uxtime )
      sun_ra_deg = -1000
      sun_dec_deg = -1000
      sun_elev_deg = -1000
      sun_az_deg   = -1000
      if cand_high_uxtime_int in sun_positions.keys() :
         sun_ra_deg  = sun_positions[ cand_high_uxtime_int ][0]
         sun_dec_deg = sun_positions[ cand_high_uxtime_int ][1]
         print("DEBUG(cached) : sun position calculated for uxtime = %d at (ra,dec) = (%.4f,%.4f) [deg]" % (cand_high_uxtime_int,sun_ra_deg,sun_dec_deg))
      else :       
         sunpos = astropy.coordinates.get_sun( cand_high_time )
         sun_ra_deg  = sunpos.ra.hour * 15.00
         sun_dec_deg =  sunpos.dec.degree
         print("DEBUG : sun position calculated for uxtime = %.2f at (ra,dec) = (%.4f,%.4f) [deg]" % (cand_high.uxtime,sun_ra_deg,sun_dec_deg))
         sun_positions[ cand_high_uxtime_int ] = numpy.array( [sun_ra_deg,sun_dec_deg] )
         
      # def angdist_arcsec( ra_deg, dec_deg, ra_find_deg, dec_find_deg ):
      sun_dist_arcsec = skysources.angdist_arcsec( cand_high.ra_degs, cand_high.dec_degs, sun_ra_deg, sun_dec_deg )
      sun_dist_deg = (sun_dist_arcsec / 3600.00)
      
      if sun_dist_deg <= min_sun_dist_deg :
         # Sun 
         continue
         
      if cand_high.elev_deg < min_elevation :
         # too low :
         continue
         
      # if maximum RMS is exceeded -> ignore candidate:
      if cand_high.rms > options.max_rms :
         print("DEBUG : candidate on image %s has RMS = %.4f Jy > limit = %.4f Jy -> image flagged" % (cand_high.file,cand_high.rms,options.max_rms))
         if not cand_high.file in flagged_images :
            flagged_images.append( cand_high.file )
            print("DEBUG : very high RMS  = %.4f Jy > limit = %.4f Jy -> image %s flagged" % (cand_high.rms,options.max_rms,cand_high.file))
         continue   

      # t = Time(unix_time,format='unix')
      if options.max_sun_elevation <= 91.00 :
         if MWA_POS is not None : 
            sunpos = get_sun( cand_high_time )
            print("INFO : sun position = (RA,DEC) = (%.4f,%.4f) [deg]" % (sunpos.ra.degree, sunpos.dec.degree))
            # calculate az,za of the sun ( was : sunpos.ra.degree, sunpos.dec.degree )
            coord = SkyCoord( sun_ra_deg, sun_dec_deg, equinox='J2000',frame='icrs', unit='deg')
            coord.location = MWA_POS
            coord.obstime = Time( cand_high.uxtime, scale='utc', format="unix" )
            altaz = coord.transform_to('altaz')
            sun_az_deg, sun_elev_deg = altaz.az.deg, altaz.alt.deg

            if sun_elev_deg > options.max_sun_elevation :
               print("DEBUG : warning, maximum allowed Sun elevation = %.2f [deg] exceeded with the value = %.2f [deg] -> skipeed" % (options.max_sun_elevation,sun_elev_deg))
               continue
         else :
            print("ERROR : MWA_POS is None meaning that the import |from astropy.coordinates import SkyCoord, EarthLocation| did not work and Sun elevation cannot be checked")
            sys.exit(-1)
         
      # since two stations might be a bit out of synch min_uxtime has to be +/- integration time :   
      (ret,cand_low,min_dist_arcsec) = skysources.FindClosestSource( cand_high.ra_degs, cand_high.dec_degs, 
                                                                     sources=candidates_low_freq, 
                                                                     min_uxtime=(cand_high.uxtime - options.inttime), 
                                                                     max_uxtime=max_uxtime, 
                                                                     radius_arcsec=coinc_radius_deg*3600.00,
                                                                     check_error=False # ignore WARNING message as this is coincidence and source does not have to exist in the other station list !
                                                                   )

      # HERE : check number of candidates on corresponding image from LOW station :
      # counters :
      #  def __init__( self, uxtime=-1, start_counter=0, sat_above_hor_all=0, sat_above_min_elev=0, random_match_probability=0 ):
      # candidates_per_image[ cand_high.file ] = CandidateCounter( uxtime=cand_high.uxtime, start_counter=0, sat_above_hor_all=0, sat_above_min_elev=0, random_match_probability=0 )
      cand_high_counter = candidates_per_image[ cand_high.file ]
      n_low = cand_high_counter.low_cand_count
      low_file = ""
#      if cand_low is not None and cand_high_counter.low_cand_count <= 0 :
      if cand_high_counter.low_cand_count <= 0 :
         # if not initialised number on LOW-freq station :
         print("DEBUG_NEW : image %s does not have low-freq counterpart identified yet -> checking now" % (cand_high.file))
         time_diff = 1e6
         cand_low_tmp = None
         if cand_low is not None :
            time_diff = cand_low.uxtime - cand_high.uxtime
            cand_low_tmp = cand_low
            
         if math.fabs( time_diff ) > 0.1 :
            # if not the same second try to find closest in time :
            # WARNING : use different names of variables to not overwrite (ret,cand_low,min_dist_arcsec) 
            (ret_tmp,cand_low_tmp,min_dist_sec) = skysources.FindClosestInTime( cand_high.uxtime, min_uxtime=(cand_high.uxtime - options.inttime), max_uxtime=max_uxtime, sources=candidates_low_freq )
            if cand_low_tmp is not None :
               print("DEBUG_NEW : checked closest in time low-image to uxtime = %.2f (%s) -> found %s (uxtime = %.2f)" % (cand_high.uxtime,cand_high.file,cand_low_tmp.file,cand_low_tmp.uxtime))
            else :
               print("DEBUG_NEW : checked closest in time low-image to uxtime = %.2f (%s) -> not found anything ???" % (cand_high.uxtime,cand_high.file))
            
         if cand_low_tmp is not None :
            (n_low,last_index)  = count_candidates( candidates_low_freq , cand_low_tmp.file, start_index=0 )
            cand_high_counter.low_cand_count = n_low
            cand_high_counter.low_file = cand_low_tmp.file
            low_file = cand_low_tmp.file
            print("DEBUG_NEW : low image = %s (counterpart of high %s) has %d candidates" % (cand_low_tmp.file,cand_high.file,n_low))
         else :
            print("WARNING : bug in code ??? could not find closest in time image to high freq. file %s" % (cand_high.file))

      print("DEBUG_NEW : %s : number of events on low/high = %d/%d , cand low = %s" % (cand_high.file,cand_high_counter.low_cand_count,cand_high_counter.high_cand_count,low_file))

      cand_high_counter.update( uxtime=cand_high.uxtime )
      # [ 0 , cand_high.uxtime, 0 , 0 , 0 ] # CAND_PER_IMAGE | UNIXTIME | TLE_SAT_ABOVE_HOR | TLE_SAT_ABOVE_MINELEV | RANDOM_MATCH_PROBABILITY
      
      
      
      if ret :
         n_coinc = n_coinc + 1
      
         delay_sec = (cand_low.uxtime - cand_high.uxtime)                           
         mean_ra_degs = ( cand_high.ra_degs + cand_low.ra_degs ) / 2.00
         mean_dec_degs = ( cand_high.dec_degs + cand_low.dec_degs ) / 2.00
         mean_az_degs = (cand_high.azim_deg+cand_low.azim_deg)/2.00
         mean_elev_degs = (cand_high.elev_deg+cand_low.elev_deg)/2.00
         mean_ux =  ( cand_high.uxtime + cand_low.uxtime ) / 2.00
         satinfo = None # "TRANSIENT_CANDIDATE"
         is_sat = False
         satdist_arcsec = 0.00
         # evt_name  = ("EVT%08d" % evtidx)
         evt_name  = ("EVT%08d" % n_coinc) # using n_coinc to have unique evt name per coinc event otherwise it was lost due to continue later on ...
         all_above_horizon_count = 0
         
         # save coinc each coinc event to a separate file :
         save_coinc_event( cand_high, cand_low, out_all_coinc_f, min_dist_arcsec, sun_dist_arcsec, evt_name )
         
         # check if not A-team source sneaking in :
         ateam_ret = False
         ateam_src = None 
         ateam_dist_arcsec = -1000
         if options.ateam_exclude_list is not None and len(ateam_exclude_list) > 0 and options is not None :
            (ateam_ret, ateam_src, ateam_dist_arcsec ) = skysources.FindClosestSource( mean_ra_degs, mean_dec_degs, radius_arcsec=options.a_team_sources_radius*3600 )
            if options.debug_level > 0 :
               print("DEBUG(2) : checking if (ra,dec) = (%.4f,%.4f) [deg] is A-team source" % (mean_ra_degs, mean_dec_degs))
                        
            if ateam_ret : 
                if ateam_src.name in ateam_exclude_list :
                   if options.debug_level > 0 :
                      print("DEBUG : %s rejected by being close to A-team source %s ( <= %.2f arcsec )" % (evt_name,ateam_src.name,ateam_dist_arcsec))
                   
                   out_line = "%s %010.5f %010.5f %06.4f %07.3f %s %08.3f %05.1f %010.5f %010.5f %05.1f %05.1f %08.3f %s %08.3f %05.1f %10.5f %10.5f %04.1f %04.1f %08.4f %04.1f %06.2f %06.2f %s %07.1f %s %07.1f %d %.6f\n" % ( \
                                                                evt_name, mean_ra_degs, mean_dec_degs, 
                                                                (min_dist_arcsec/3600.00),delay_sec, \
                                                                cand_high.file,cand_high.flux,cand_high.snr, \
                                                                cand_high.ra_degs,cand_high.dec_degs,cand_high.x,cand_high.y,cand_high.uxtime, \
                                                                cand_low.file,cand_low.flux,cand_low.snr,cand_low.ra_degs,cand_low.dec_degs,cand_low.x,cand_low.y,cand_low.uxtime,(sun_dist_arcsec/3600.00), \
                                                                mean_az_degs , mean_elev_degs, ateam_src.name, ateam_dist_arcsec, ateam_src.name, ateam_dist_arcsec, \
                                                                all_above_horizon_count, random_match_probability \
                                                            )
                   reject_f.write( out_line )
                   continue                                                            
            
         above_min_elevation_count = 0
         all_above_horizon_count = 0
         
         # satellites checking :
         if os.path.exists( options.tle_path ) and options.sat_radius_deg > 0 :
            print("DEBUG : checking nearby satellites for evt_name = %s" % (evt_name))
            
            evt_time = Time( mean_ux ,format='unix')
#            d=evt_time.to_datetime()
            evt_dt = evt_time.to_datetime().strftime("%Y%m%d")
            tle_file = ( "%s/%s/satelitesdb.tle" % (options.tle_path,evt_dt) )
            
            if not os.path.exists( tle_file ) :                                    
               tle_file = ( "%s/satelitesdb.tle" % (options.tle_path) )
               
               if not os.path.exists( tle_file ) :
                   tle_file = ( "%s/%s_satelitesdb.tle" % (options.tle_path,evt_dt) )

               
            if os.path.exists( tle_file ) :      
               satfile = ( "%.4f.txt" % mean_ux )
               satfile_exists = os.path.exists( satfile )
                   
               if not satfile_exists or options.sat_force :
                  # only LEO orbit <= 2000 km :
                  # -max_alt=2000 option will not be used here only in read_sattest_output function - so that the files are generated with all satellites and filtering is done later !
#                  cmd = "sattest %.4f -tle=%s -all -mwa -qth=mro.qth -ra=%.8f  -dec=%.8f -outregfile=%.4f.reg  -outfile=%.4f.txt -print_header -no_spaces -min_elevation=-1000.0000 -radius=360 > %.4f.out 2>&1" % (mean_ux,tle_file,mean_ra_degs,mean_dec_degs,mean_ux,mean_ux,mean_ux)
                  cmd = "sattest %.4f -tle=%s -all -mwa -qth=mro.qth  -outregfile=%.4f.reg  -outfile=%.4f.txt -print_header -no_spaces -min_elevation=0.0 -radius=360 > %.4f.out 2>&1" % (mean_ux,tle_file,mean_ux,mean_ux,mean_ux)                   
                  print("DEBUG : %s" % cmd )
                  ret = os.system( cmd )
               
                  print("DEBUG command returned %d : %s" % (ret,cmd) )
               else :
                  print("DEBUG : satellite info file %s already exists (use --sat_force to re-generated)" % (satfile))
               
#               if ret != 0 :
#                   print("WARNING : could not execute command %s" % (cmd))
#               else :   
               (  closest_sat , min_ang_dist_arcsec , satellites , all_above_horizon_count, above_min_elevation_count, min_ang_dist_name ) = read_sattest_output( satfile, mean_ra_degs, mean_dec_degs, sat_radius_deg=options.sat_radius_deg, min_elevation=min_elevation, max_sat_distance_km=options.max_sat_distance_km )
               satdist_arcsec = min_ang_dist_arcsec
               if closest_sat is not None :
                   satinfo = "SAT_" + closest_sat.name
                   is_sat = True
               else :
                   is_sat = False
                   if min_ang_dist_name is not None :
                      satinfo = "SAT_" + min_ang_dist_name
                      
                      
               
                   
               # calculate probability of random match of a TLE satellite to event - calculated per single event in the image 
               # see Equation 1 in : /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200808_random_transient2sat_match_probability.odt
               # P( T TLE Satellites) = T * N * PI^2 R^2 / 129600 
               # Exect formula is P( N = 1 ) = T * Omega_TLE / 4PI = T * (4PI sin^2( R_rad / 2 )) / 4PI = T sin^2( R_rad / 2 )
               # N = 1 
               # T = all_above_horizon_count
               # R = coinc_radius_deg -> R_rad = coinc_radius_rad
               #  
               # random_match_probability = all_above_horizon_count * 1 * (math.pi*math.pi) * (coinc_radius_deg*coinc_radius_deg) / 129600.00
               # coinc_radius_rad = coinc_radius_deg * ( math.pi / 180.00 )
               # sin_val = math.sin( coinc_radius_rad / 2.00 )
               # random_match_probability = all_above_horizon_count * 1 * (sin_val*sin_val)                
               random_match_probability = above_min_elevation_count * 1 * (sin_val*sin_val) # calculate probability using number of satellites above the min elevation criteria value
               # print("\tDEBUG : %d * (%.4f*%.4f) = %.8f for coinc_radius_deg = %.2f [deg] , min_elevation = %.2f [deg]" % (above_min_elevation_count,sin_val,sin_val,random_match_probability,coinc_radius_deg,min_elevation))
            else :
               print("WARNING : could not find TLE file satelitesdb.tle in %s" % (options.tle_path))
               
               
         source_info = "-"
         source_dist = -1000
         if ateam_ret and ateam_src is not None : # ateam_ret = True - means that the source is within the matching distance = a_team_sources_radius [deg]
            source_info = ateam_src.name
            source_dist = ateam_dist_arcsec

         classif = "TRANSIENT_CANDIDATE"
         if is_sat :
            classif = "SATELLITE"
         if satinfo is None :
            satinfo = "-"   
                     
         satinfo_trunc = satinfo
         # Do not truncate to keep full name with NORAD-ID
         if len(satinfo_trunc) > 40 :
            satinfo_trunc = satinfo[0:40]
            
         # if ASTRO-source is closer to the candidate than the satellite - flag it :
         if source_dist > 0 :
            if source_dist < min_ang_dist_arcsec or closest_sat is None :
               classif = "SOURCE"   
               
         # def is_plane_path( azim , alt , radius=10 ) :
         # Check ARC1 : Ill.6 in /home/msok/Desktop/SKA/papers/2020/M_Sokolowski/Transients/logbooks/20200410/20200905_data20200410_reanalysis.odt
         # Only this range of azimuths :
#         if classif == "TRANSIENT_CANDIDATE" : # if still not rejected by earlier criteria :
         if True : # always check PLANES :
            # if (mean_az_degs >= 10 and mean_az_degs <= 140) or (mean_az_degs >= 210 and mean_az_degs <= 350) : # path1 or path2 
            if True : # do not limit to the earlier AZIMUTH range otherwise some planes seem to be missed !
               (is_plane,path_ang_dist_deg,plane_path_index) = is_plane_path( mean_az_degs, mean_elev_degs, radius=3*options.beam_size_deg )
               if is_plane :
                  # on plane path 
                  # since two stations might be a bit out of synch min_uxtime has to be +/- integration time :   
                  (ret_low,brightest_low,brightest_low_dist_arcsec) = skysources.FindBrightestSource( cand_high.ra_degs, cand_high.dec_degs, 
                                                                                           sources=candidates_low_freq, 
                                                                                           min_uxtime=(cand_high.uxtime - options.inttime), 
                                                                                           max_uxtime=max_uxtime, 
                                                                                           radius_arcsec=3*options.beam_size_deg*3600.00,
                                                                                           check_error=False # ignore WARNING message as this is coincidence and source does not have to exist in the other station list !
                                                                                          )

                  (ret_high,brightest_high,brightest_high_dist_arcsec) = skysources.FindBrightestSource( cand_high.ra_degs, cand_high.dec_degs, 
                                                                                           sources=candidates_high_freq, 
                                                                                           min_uxtime=(cand_high.uxtime - options.inttime), 
                                                                                           max_uxtime=max_uxtime, 
                                                                                           radius_arcsec=3*options.beam_size_deg*3600.00,
                                                                                           check_error=False # ignore WARNING message as this is coincidence and source does not have to exist in the other station list !                                                                                           
                                                                                          )

                  print("DEBUG : %s candidate on planes path detected, maximum flux within 3 beams are low_freq = %.1f [Jy] and high_freq = %.1f [Jy]" % (evt_name,brightest_low.flux,brightest_high.flux))

                  if ( ret_low and brightest_low.flux > options.plane_flux_threshold ) or ( ret_high and brightest_high.flux > options.plane_flux_threshold ) : 
                     # require to be on path and have a very bright flux within 3 beams :
                     plane_str = "PLANE%d(%.1f,%.1f)" % (plane_path_index,brightest_low.flux,brightest_high.flux) 
                     if classif == "TRANSIENT_CANDIDATE" :
                        classif = plane_str
                     else :
                        classif += (",%s" % (plane_str))    
                  else :
                     print("DEBUG : %s candidate on planes path detected, but does not satisfy flux requirement to be > %.4f Jy " % (evt_name,options.plane_flux_threshold))
                     
                     if (brightest_low_last is not None and brightest_low_dist_arcsec_last is not None) or (brightest_high_last is not None and brightest_high_dist_arcsec_last is not None) :                     
                        # if there was a super-bright RFI on the previous image check if the candidate is not very close to it, in which case it could have been a blink form a plane 
                        # and then on the next image it's just continuation/fading of this blink -> hence need to be rejected
                        last_low_flux = 0
                        last_high_flux = 0 
                        if brightest_low_last is not None and brightest_low_dist_arcsec_last is not None :                         
                           dist_to_last_brightest_arcsec = skysources.angdist_arcsec( cand_high.ra_degs, cand_high.dec_degs, brightest_low_last.ra_degs, brightest_low_last.dec_degs )
                           if (dist_to_last_brightest_arcsec/3600.00) < 3*options.beam_size_deg*3600.00 :
                              last_low_flux = brightest_low_last.flux
                              print("DEBUG_PLANES : transient %s : (%.1f,%.1f) %.2f Jy (azim,el) = (%.2f,%.2f) [deg] matched to brightest object from last image (low flux = %.1f Jy)" % (cand_high.file,cand_high.x,cand_high.y,cand_high.flux,mean_az_degs, mean_elev_degs, last_low_flux))
                               
                        if brightest_high_last is not None and brightest_high_dist_arcsec_last is not None :                         
                           dist_to_last_brightest_arcsec = skysources.angdist_arcsec( cand_high.ra_degs, cand_high.dec_degs, brightest_high_last.ra_degs, brightest_high_last.dec_degs )
                           if (dist_to_last_brightest_arcsec/3600.00) < 3*options.beam_size_deg*3600.00 :
                              last_high_flux = brightest_high_last.flux
                              print("DEBUG_PLANES : transient %s : (%.1f,%.1f) %.2f Jy (azim,el) = (%.2f,%.2f) [deg] matched to brightest object from last image (high flux = %.1f Jy)" % (cand_high.file,cand_high.x,cand_high.y,cand_high.flux,mean_az_degs, mean_elev_degs,last_high_flux))
                               
                        plane_str = None       
                        if last_low_flux > options.plane_flux_threshold :
                           if last_high_flux > options.plane_flux_threshold :
                              plane_str = "PLANE_LAST(%.1f,%.1f)" % (last_low_flux,last_high_flux)
                           else :
                              plane_str = "PLANE_LAST(%.1f)" % (last_low_flux)                           
                        else :                         
                           if last_high_flux > options.plane_flux_threshold :
                              plane_str = "PLANE_LAST(%.1f)" % (last_high_flux)                           
                        
                        if plane_str is not None :
                           if classif == "TRANSIENT_CANDIDATE" :
                              classif = plane_str
                           else :
                              classif += (",%s" % (plane_str))

                     else :
                        print("WARNING : event on a plane path (%s at %.1f,%.1f,%s at %.1f,%.1f), but does not satisfy max flux criteria : (az,alt) = (%.4f,%.4f) [deg] , flux_low = %.1f [Jy] , flux_high = %.1f [Jy]" %  (cand_high.file,cand_high.x,cand_high.y,cand_low.file,cand_low.x,cand_low.y,mean_az_degs, mean_elev_degs, brightest_low.flux,brightest_high.flux))
              
               else :
                  print("DEBUG : %s candidate at (az,alt) = (%.4f,%.4f) [deg] not matched to any plane path, minimum distance = %.4f [deg]" % (evt_name, mean_az_degs, mean_elev_degs, path_ang_dist_deg))      
#         out_line = "%s %010.5f %010.5f %06.4f %07.3f %s %08.3f %05.1f %010.5f %010.5f %05.1f %05.1f %08.3f %s %08.3f %05.1f %10.5f %10.5f %05.1f %05.1f %10.4f %06.1f %06.2f %06.2f %20s %07.1f %2s %07.1f %d %.06f %s\n" % ( \
#                                                                evt_name, mean_ra_degs, mean_dec_degs, 
#                                                                (min_dist_arcsec/3600.00),delay_sec, \
#                                                                cand_high.file,cand_high.flux,cand_high.snr, \
#                                                                cand_high.ra_degs,cand_high.dec_degs,cand_high.x,cand_high.y,cand_high.uxtime, \
#                                                                cand_low.file,cand_low.flux,cand_low.snr,cand_low.ra_degs,cand_low.dec_degs, \
#                                                                cand_low.x,cand_low.y,cand_low.uxtime,(sun_dist_arcsec/3600.00), \
#                                                                mean_az_degs , mean_elev_degs, 
#                                                                satinfo_trunc, satdist_arcsec, 
#                                                                source_info,source_dist,
#                                                                all_above_horizon_count, random_match_probability,
#                                                                classif
#                                                            )
#         out_f.write( out_line )

#         n_high = count_candidates( candidates_high_freq , cand_high.file )
         # (n_low,last_index)  = count_candidates( candidates_low_freq , cand_low.file, start_index=0 )
         n_low  = cand_high_counter.low_cand_count
         n_high = cand_high_counter.high_cand_count
#         n_low  = candidates_per_image[ cand_high.file ].low_cand_count

         # STAT :
         if cand_high.uxtime < min_uxtime_coinc :
             min_uxtime_coinc = cand_high.uxtime
         if cand_high.uxtime > max_uxtime_coinc :
             max_uxtime_coinc = cand_high.uxtime
         
         coinc_candidates.append( CoincCandidate( evt_name=evt_name, mean_ra_degs=mean_ra_degs, mean_dec_degs=mean_dec_degs, min_dist_arcsec=min_dist_arcsec, delay_sec=delay_sec,\
                                                  cand_high=cand_high, cand_low=cand_low, sun_dist_arcsec=sun_dist_arcsec,\
                                                  mean_az_degs=mean_az_degs, mean_elev_degs=mean_elev_degs,\
                                                  satinfo_trunc=satinfo_trunc, satdist_arcsec=satdist_arcsec,\
                                                  source_info=source_info, source_dist=source_dist, all_above_horizon_count=all_above_horizon_count,\
                                                  random_match_probability=random_match_probability, classif=classif, n_low=n_low, n_high=n_high ) )
         
         # 
         # def update( self, uxtime, sat_above_hor_all, sat_above_min_elev, random_match_probability ) :
         cand_high_counter.update( uxtime=mean_ux, sat_above_hor_all=all_above_horizon_count,\
                                   sat_above_min_elev=above_min_elevation_count, random_match_probability=random_match_probability,
                                   low_cand_count=n_low ) # No need to update this high_cand_count=n_high - they are initialised before the main loop

#         print("DEBUG : stat for image %s is coinc-cand-count = %d, uxtime=%.2f , sat_above_hor_all = %d," % (cand_high.file,candidates_per_image[ cand_high.file ].counter,candidates_per_image[ cand_high.file ].uxtime,candidates_per_image[ cand_high.file ].sat_above_hor_all))
         print("DEBUG : stat for image %s is coinc-cand-count = %d, uxtime=%.2f , sat_above_hor_all = %d, sat_above_min_elev = %d, random_match_probability = %.8f, count candidates low / high = %d / %d" %\
                (cand_high.file,\
                 cand_high_counter.counter,\
                 cand_high_counter.uxtime,\
                 cand_high_counter.sat_above_hor_all,\
                 cand_high_counter.sat_above_min_elev,\
                 cand_high_counter.random_match_probability,\
                 cand_high_counter.low_cand_count,\
                 cand_high_counter.high_cand_count\
                )\
              )
#         candidates_per_image[ cand_high.file ].increment()      # [0] += 1 # increase the counter, do not touch unixtime
#         candidates_per_image[ cand_high.file ].uxtime = mean_ux # [1] = mean_ux
#         candidates_per_image[ cand_high.file ].all_above_horizon_count = all_above_horizon_count # .[2] = all_above_horizon_count
#         candidates_per_image[ cand_high.file ].above_min_elevation_count = above_min_elevation_count # [3] = above_min_elevation_count
#         if candidates_per_image[ cand_high.file ].random_match_probability <= 0 : # [4] <= 0 :
#            candidates_per_image[ cand_high.file ].random_match_probability = random_match_probability
#         else :  
#            if math.fabs( candidates_per_image[ cand_high.file ].random_match_probability - random_match_probability ) > 0.000001 :  # [4] - random_match_probability ) > 0.000001 :
#                print("WARNING : random match probability for image %s was %.8f and now is different and = %.8f - looks like bug in code, please verify !!!" % (candidates_per_image[ cand_high.file ].random_match_probability,random_match_probability))
         
         reg_high_file = cand_high.file.replace(".fits","_high.reg")
         reg_high_f = open( outdir + "/" + reg_high_file , "w" )
         reg_line = "circle %d %d %d # color=red\n" % (cand_high.x,cand_high.y,10)
         reg_high_f.write( reg_line )
         reg_high_f.close()

         reg_low_file = cand_low.file.replace(".fits","_low.reg")
         reg_low_f = open( outdir + "/" + reg_low_file , "w" )
         reg_line = "circle %d %d %d # color=red" % (cand_low.x,cand_low.y,10)
         reg_low_f.write( reg_line )
         reg_low_f.close()
         

         evtidx += 1 
   
      # coincindece found 
#      if cand_high.file == "chan_294_20200411T153311_I_diff.fits" :
#         print("odo")

      # Save brightest events on previous image          
      # For low frequency image allow +/- inttime from current HIGH-FREQ image :
      (ret_low_last,brightest_low_last,brightest_low_dist_arcsec_last) = skysources.FindBrightestSource( cand_high.ra_degs, cand_high.dec_degs, 
                                                                                           sources=candidates_low_freq, 
                                                                                           min_uxtime=(cand_high.uxtime - options.inttime), 
                                                                                           max_uxtime=(cand_high.uxtime + options.inttime),
                                                                                           radius_arcsec=(360*3600),
                                                                                           file=None,
                                                                                           check_error=False, # ignore WARNING message as this is coincidence and source does not have to exist in the other station
                                                                                           desc="LOW"
                                                                                          )

      # require this exact uxtime (no +/-)
      (ret_high_last,brightest_high_last,brightest_high_dist_arcsec_last) = skysources.FindBrightestSource( cand_high.ra_degs, cand_high.dec_degs, 
                                                                                           sources=candidates_high_freq, 
                                                                                           min_uxtime=cand_high.uxtime, # - options.inttime) 
                                                                                           max_uxtime=cand_high.uxtime, # + options.inttime)
                                                                                           radius_arcsec=(360*3600),
                                                                                           file=None,
                                                                                           check_error=False, # ignore WARNING message as this is coincidence and source does not have to exist in the other station
                                                                                           desc="HIGH"
                                                                                          )
      if brightest_high_last is not None :                                                                                          
         print("DEBUG_BRIGHTEST_HIGH : brightest objects in high %s is %.2f [Jy] at (%.1f,%.1f)" % (brightest_high_last.file,brightest_high_last.flux,brightest_high_last.x,brightest_high_last.y))

      if brightest_low_last is not None :
         print("DEBUG_BRIGHTEST_LOW  : brightest objects in low  %s is %.2f [Jy] at (%.1f,%.1f)" % (brightest_low_last.file,brightest_low_last.flux,brightest_low_last.x,brightest_low_last.y))

#      if cand_high_counter.low_cand_count < 0 :
#         (n_low,last_index)  = count_candidates( candidates_low_freq , cand_low.file, start_index=0 )

      # reject all if there is a bright object on image and many other events :
      if True : # ret : - do not require the MEGA-BRIGHT ones to be in coincidence even (matching the positions very well as they are large and can be at slightly different positions in both stations !)
         # TODO : what's the parallax ???
         # only of event visible in both stations :
         if brightest_high_last is not None and brightest_low_last is not None :
            low_count = candidates_per_image[ cand_high.file ].low_cand_count
            if low_count < options.min_rfi_cand_count :
               # check if there is more event on the brightest_low_last.file file
               print("DEBUG_NEW : bright RFI detected, but only %d images on %s (low counterpart of %s) - checking other image %s" % (low_count,cand_high.file,candidates_per_image[ cand_high.file ].low_file,brightest_low_last.file))
               (low_count_test,low_count_index) = count_candidates( candidates_low_freq , brightest_low_last.file, start_index=0 )
               print("DEBUG_NEW : low_count_test = %d" % (low_count_test))
               if low_count_test > low_count :
                  print("DEBUG_NEW : low_count_test = %d > low_count = %d -> using the value from the image %s" % (low_count_test,low_count,brightest_low_last.file))
                  low_count = low_count_test
               
         
            print("DEBUG_BRIGHTEST_LOW and DEBUG_BRIGHTEST_HIGH -> is RFI ( compare %.2f and %.2f vs. %.2f - both above to flag all on %s ? ) number of events low/high = %d/%d ?" % (brightest_high_last.flux,brightest_low_last.flux,options.rfi_flux_threshold,cand_high.file,low_count,candidates_per_image[ cand_high.file ].high_cand_count))
            if brightest_high_last.flux > options.rfi_flux_threshold and brightest_low_last.flux > options.rfi_flux_threshold :
               print("DEBUG : RFI detected in both high / low images ( %.4f / %.4f ) [Jy/beam] > threshold = %.4f [Jy]" % (brightest_high_last.flux,brightest_low_last.flux,options.rfi_flux_threshold))
               if low_count >= options.min_rfi_cand_count and candidates_per_image[ cand_high.file ].high_cand_count >= options.min_rfi_cand_count :
                  if not cand_high.file in flagged_images :
                  # if not already flagged all events in this image -> do it now :
                  # flagged = FlagRFI( coinc_candidates, cand_high.file )
                     flagged_images.append( cand_high.file )
                     print("DEBUG : RFI detected and number of events on low/high = %d / %d > max = %d -> high file %s added to flagged list !" % (low_count,candidates_per_image[ cand_high.file ].high_cand_count,options.min_rfi_cand_count,cand_high.file))
                  else :
                     print("DEBUG : file %s already on the list of flagged images" % (cand_high.file))
               else :
                  print("DEBUG : low_count = %d , high_count = %d -> one is below threshold of %d candidates" % (low_count,candidates_per_image[ cand_high.file ].high_cand_count,options.min_rfi_cand_count))   
            
      print("PROGRESS : number of coinc events = %d" % (evtidx))
      
   reject_f.close()
   out_all_coinc_f.close()
   
   # reject flagged events :
   print("DEBUG : post coincindence flagging of RFI affected images")
   for flagged_high_file in flagged_images :
      flagged = FlagRFI( coinc_candidates, flagged_high_file )
      print("\t%s : rejected %d coinc-candidates" % (flagged_high_file,flagged))
   
   # post coincidence criteria 
   PostCoinc( coinc_candidates )
   
   # save candidates :
   save_coinc_candidates( coinc_candidates, out_f )
   

   # save number of candidates per image coming out of coincidence :
   out_f_cand_per_image = open( outdir + "/" + cand_per_image_file , "w" )
   out_f_cand_per_image.write( "# FITSFILE UXTIME CAND_PER_IMAGE TLE_ABOVE_HOR TLE_ABOVE_elev%.2fdeg RANDOM_MATCH_PROBABILITY PROB0 PROB1 PROB2\n" % (min_elevation) )
   for k in candidates_per_image.keys() :
      # calculate total probobabilities of having 0,1 and 2 matches :
      random_match_probability = candidates_per_image[k].random_match_probability
      n_candidates_in_image    = candidates_per_image[k].counter
      prob_zero_matches = (1.00 - random_match_probability)**n_candidates_in_image
      prob_one_match    = n_candidates_in_image*random_match_probability*(1.00 - random_match_probability)**(n_candidates_in_image-1)
      prob_two_matches  = (n_candidates_in_image*(n_candidates_in_image-1)/2)*(random_match_probability**2)*(1.00 - random_match_probability)**(n_candidates_in_image-2)	
   
      line = "%s %.4f %d %d %d %.8f %.8f %.8f %.8f\n" % (k, # k is really FITS file string (key)\
                                                         candidates_per_image[k].uxtime,\
                                                         candidates_per_image[k].counter,\
                                                         candidates_per_image[k].sat_above_hor_all,\
                                                         candidates_per_image[k].sat_above_min_elev,\
                                                         candidates_per_image[k].random_match_probability,\
                                                         prob_zero_matches,\
                                                         prob_one_match,\
                                                         prob_two_matches )
      out_f_cand_per_image.write( line )
      
   out_f_cand_per_image.close()
   
   # save flagged images :
   out_flagged_f = open( options.outdir + "/flagged_images.txt" , "w" )
   for flagged_fits in flagged_images :
      out_flagged_f.write( flagged_fits + "\n" )
   out_flagged_f.close()
   
   return n_coinc

def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tCoincidence between two log files\n'
   parser = OptionParser(usage=usage,version=1.00)
   
   parser.add_option('--list_high_freq',dest="list_high_freq",default="cand_list_aavs2",help="High frequency candidates list [default %default]")
   parser.add_option('--list_low_freq',dest="list_low_freq",default="cand_list_eda2",help="Low frequency candidates list [default %default]")
   parser.add_option('--max_delay_sec',dest="max_delay_sec",default=2,help="Maximum dispersion delay to check coincidence for [default %default]",type="float")
   parser.add_option('--coinc_radius_deg',dest="coinc_radius_deg",default=3.3,help="Coincidence radius in degrees [default 1 beam size %default]",type="float")
   parser.add_option('--beam_size_deg',dest="beam_size_deg",default=3.3,help="Beam size in degrees [default %default]",type="float")
   parser.add_option('--outfile','--out_file','--out',dest="out_file",default="coinc_eda2_aavs2.txt",help="Output file [default %default]")
   parser.add_option('--outdir','--out_dir','--output_dir','--dir',dest="outdir",default="coinc/",help="Output directory [default %default]")
   
   # min elevation
   parser.add_option('--min_elevation','--min_elev',dest="min_elevation",default=-100,help="Minimum elevation required [default %default]",type="float")
   
   # TLE elements :
   parser.add_option('--tle_dir','--tle_path',dest="tle_path",default="TLE/",help="Path to where TLE files are stored [default %default]")
   parser.add_option('--sat_radius_deg',dest="sat_radius_deg",default=4.00,help="Satellite detection radius in degrees [default %default]",type="float")
   parser.add_option('--sat_force','--force_sattest','--sattest_force',action="store_true",dest="sat_force",default=False, help="Force sattest even if satfile already exists [default %default]")
   parser.add_option("--max_sat_distance_km","--max_dist_km","--sat_max_dist",dest="max_sat_distance_km", default=1e20, help="Maximum distance to satellite in km [default %default]",type="float")
   
   # exclude A-team sources (should be done by the transient founder, but was missing in the older version - hence added here) :
   parser.add_option('--exclude_ateam_list',dest="ateam_exclude_list", default="CenA,HerA,HydA,PicA,3C444,ForA,VirA", help="List of A-team sources to be excluded [default %default]")
   parser.add_option('-r','--a_team_radius','--aradius','--a_team_sources_radius',dest="a_team_sources_radius", default=3.8, help="A-team sources radius [deg] should be at least 1 beam size [default %default is beam size at 150 MHz]")
   
   # acquisition parameters might require modification :
   parser.add_option('-i','--inttime','--int_time',dest="inttime",default=2.00,help="Integration time [default %default]",type="float")
   
   # debug level :
   parser.add_option('--debug_level','--debug','--verbose_level','--verb_level',dest="debug_level",default=1,help="Debug level [default %default]",type="int")
   
   # FITS FILE :
   parser.add_option('--fits_file','--fits',dest="fits_file",default=None,help="DEBUGGING : Only check events from this FITS file [default None - not set]")
   
   # do not analyse just read and print stat :
   parser.add_option('--do_not_analyse','--no_analysis',action="store_false",dest="do_coinc",default=True, help="Turns off coincidence and analysis [default %default]")
   
   # thresholds for cuts :
   parser.add_option('--plane_flux_threshold','--plane_thresh','--plane',dest="plane_flux_threshold",default=300,help="Plane threshold [default %default]",type="float")
   parser.add_option('--rfi_flux_threshold','--rfi_thresh','--rfi',dest="rfi_flux_threshold",default=300,help="RFI threshold [default %default]",type="float")
   
   # 2021-01-20 was 10 changed to 3 as this is not critical requirement here:
   parser.add_option('--min_rfi_cand_count','--max_image_cand_count','--rfi_cand_count',dest="min_rfi_cand_count",default=3,help="RFI threshold [default %default]",type="int")
   
   # sun cuts due to very high values in side-lobes :
   parser.add_option('--max_sun_elev','--max_sun_elevation',dest="max_sun_elevation",default=100,help="Maximum Sun elevation allowed [default %default , >= 90 effectively turns this cut off]",type="float")
   
   # MIN (for negative) and MAX for RFI :
   parser.add_option('--min_image_value',dest="min_image_value",default=-2000,help="Minimum allowed value to reject negatives images (- side-lobes from previous RFI image) [default %default]",type="float")
   parser.add_option('--max_image_value',dest="max_image_value",default=2000,help="Maximum allowed value to reject bright RFI / side-lobes [default %default]",type="float")
     
#   parser.add_option('-r','--remap','--do_remapping','--remapping',dest="do_remapping",default=False,action="store_true", help="Re-mapping [default %default]",metavar="STRING")
#   parser.add_option('-p','--pol','--polarisation',dest="polarisation",default=None, help="Polarisation [default %default]")
#   parser.add_option('-a','--azim','--az','--az_deg','--azim_deg',dest="azim_deg",default=0, help="Azimuth [deg]",type="float")
#   parser.add_option('-z','--zenith_angle','--za','--za_deg',dest="za_deg",default=0, help="Zenith angle [deg]",type="float")
#   parser.add_option('-f','--freq_mhz','--frequency_mhz','--frequency',dest="frequency_mhz",default=160, help="Frequency [MHz]",type="float")
#   parser.add_option('--projection',dest="projection",default="zea", help="Projection [default %default]")
#   parser.add_option('--time_azh_file',dest="time_azh_file",default=None, help="File name to convert (AZ,H) [deg] -> Beam X/Y values and multiply flux if available [format :  date; time; azimuth; elevation; righ

   # add option -ignore_negatives to ignore transients on NEGATIVE image (the next after a very bright RFI one !)
   # workaround until I have MIN / MAX value in image implemented and RMS in the image is also useful !
   # RMS should be from the image corner !
   parser.add_option('--max_rms',dest="max_rms",default=1000000000000000,help="Maximum allowed RMS [default %default]",type="float")

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)





if __name__ == "__main__":
   (options, args) = parse_options()

   print("######################################################")
   print("PARAMETERS (version2.00 + NORAD-ID ) :")
   print("######################################################")
   print("High frequency candidates list = %s" % (options.list_high_freq))
   print("Low  frequency candidates list = %s" % (options.list_low_freq))
   print("Do coinc / analysis            = %s" % (options.do_coinc))
   print("Maximum dispersion delay       = %.4f" % (options.max_delay_sec))
   print("Minimum elevation required     = %.4f [deg]" % (options.min_elevation))
   print("ateam_exclude_list             = %s" % (options.ateam_exclude_list))
   print("Maximum sun elevation          = %.2f [deg]" % (options.max_sun_elevation))
   print("Maximum RMS allowed            = %.4f [Jy]" % (options.max_rms))
   print("######################################################")
   
   
   high_freq_candidates = read_candidates( options.list_high_freq )
   min_uxtime_aavs2 = min_uxtime
   max_uxtime_aavs2 = max_uxtime
   
   min_uxtime = 1e20
   max_uxtime = -1e20
   low_freq_candidates  = read_candidates( options.list_low_freq )   
   min_uxtime_eda2 = min_uxtime
   max_uxtime_eda2 = max_uxtime


   n_coinc = 0 
   if options.do_coinc :   
      mkdir_p( options.outdir )
      n_coinc = coincidence( high_freq_candidates, low_freq_candidates, outfile=options.out_file, coinc_radius_deg=options.coinc_radius_deg, max_delay_sec=options.max_delay_sec, outdir=options.outdir, 
                             min_elevation=options.min_elevation, options=options )
                
                
   print("-----------------------------------------------------------------")                
   print("STATISTICS :")
   print("-----------------------------------------------------------------")
   print("Analysed time range:")
   print("   BOTH  : %.2f - %.2f -> %.4f hours" % (min_uxtime,max_uxtime,(max_uxtime-min_uxtime)/3600.00))
   print("   EDA2  : %.2f - %.2f -> %.4f hours" % (min_uxtime_eda2,max_uxtime_eda2,(max_uxtime_eda2-min_uxtime_eda2)/3600.00))
   print("   AAVS2 : %.2f - %.2f -> %.4f hours" % (min_uxtime_aavs2,max_uxtime_aavs2,(max_uxtime_aavs2-min_uxtime_aavs2)/3600.00))
   print("   COINC : %.2f - %.2f -> %.4f hours" % (min_uxtime_coinc,max_uxtime_coinc,(max_uxtime_coinc-min_uxtime_coinc)/3600.00))
   print("Number of low frequency candidates  = %d" % (len(low_freq_candidates)))                  
   print("Number of high frequency candidates = %d" % (len(high_freq_candidates)))                  
   print("After coincidence                   = %d" % (n_coinc))
   print("-----------------------------------------------------------------")
   
   