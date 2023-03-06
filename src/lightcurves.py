
import count_spikes
from count_spikes import FluxMeasurement
import math
import sys

# options :
from optparse import OptionParser,OptionGroup

def beamcorrXY2I( lc_filename_x, lc_filename_y, outfile_lc_i , inttime=0.000000000001 ) :
   lc_x = count_spikes.read_lightcurve( lc_filename_x , uxtime_index=0, flux_index=8 )   
   lc_y = count_spikes.read_lightcurve( lc_filename_y , uxtime_index=0, flux_index=8 )   

   # lc_i = xy2i( lc_x, lc_y )   
   # save to file :
   
   lc_out = []
   
   len_x = len(lc_x)
   len_y = len(lc_y)
   
   use_find = False
   if len_x != len_y :
      print("WARNING : different lengths of XX and YY lightcurves ( %d != %d ) - will use longer procedure (find etc.)" % (len_x,len_y))
      use_find = True
      
   out_f = open( outfile_lc_i , "w" )   
   out_f.write("# UXTIME FLUX_I[Jy]\n")
   
   if use_find :
      print("ERROR : the path using find due to different lengths of the XX and YY lightcurves has not been implemented yet")
   else :
      for t in range(0,len_x) :
         m_x = lc_x[t]
         m_y = lc_y[t]
         
         if math.fabs( m_x.uxtime - m_y.uxtime ) > inttime  :
            print("ERROR : unix time of X and Y lightcurves is different %.2f != %.2f -> exiting now" % (m_x.uxtime,m_y.uxtime))
            sys.exit(0)
         
         flux_i = (m_x.flux + m_y.flux)/2.00
         
         m_i = FluxMeasurement( uxtime=m_x.uxtime, flux=flux_i )
         lc_out.append( m_i )
         
         line = "%.4f %.4f\n" % (m_x.uxtime,flux_i)
         out_f.write( line )
               
   out_f.close()                
      
   return (lc_out)      


def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tXX and YY lightcurves -> Stokes I\n'
   parser = OptionParser(usage=usage,version=1.00)

#   parser.add_option('--coinc_radius_deg',dest="coinc_radius_deg",default=3.3,help="Coincidence radius in degrees [default 1 beam size %default]",type="float")
#   parser.add_option('--object_lc','--object_lightcurve','--lightcurve',dest="object_lightcurve",default="B0950+08_diff.txt",help="On object lightcurve [default %default]")
#   parser.add_option('--off_lc','--off_object_lightcurve','--off_lightcurve','--reference_lightcurve',dest="off_lightcurve",default="OFF_B0950+08_diff.txt",help="Off-object lightcurve [default %default]")
#   parser.add_option('--inttime','--integration_time',dest="inttime",default=2,help="Integration time [default %default]",type="float")
#   parser.add_option('--freq_ch','--ch','--channel',dest="freq_channel",default=294,help="Frequency channel [default %default]",type="int")
#   parser.add_option('--thresh','--threshold',dest="threshold",default=38,help="Integration time [default %default]",type="float")
   parser.add_option('--outdir','--out_dir','--output_dir','--dir',dest="outdir",default="./",help="Output directory [default %default]")
   parser.add_option('--input_base_name','--in_basename','--base',dest="input_base_name",default="B0950+08_%s_320.00MHz_BeamCorrZEA.txt",help="Input basename [default %default]")
   parser.add_option('--outname','--out_file','--outfile','--out_lc',dest="outfile",default="B0950+08_I_320.00MHz_BeamCorrZEA.txt",help="Output file name with Stokes I [default %default]")
#   parser.add_option('--use_diff_candidates','--use_candidates',action="store_true",dest="use_diff_candidates",default=False, help="Use candidates from difference images [default %]")   

   # RFI excision : 
#   parser.add_option('--rfi_flux_threshold','--rfi_thresh','--rfi',dest="rfi_flux_threshold",default=2500,help="RFI threshold [default %default]",type="float")

   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)


if __name__ == "__main__":

   (options, args) = parse_options()
   
   x_filename = (options.input_base_name % "XX")
   y_filename = (options.input_base_name % "YY")

   print("######################################################")
   print("PARAMETERS :")
   print("######################################################")
   print("In base name  = %s -> %s / %s" % (options.input_base_name,x_filename,y_filename))
   print("Out file name = %s" % (options.outfile))
   print("######################################################")
   

   lc_out = beamcorrXY2I( x_filename, y_filename, options.outfile )
   print("Written %d Stokes I flux measurements to the output file %s" % (len(lc_out),options.outfile))
     
