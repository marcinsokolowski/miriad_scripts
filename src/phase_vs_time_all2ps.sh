# uvplt device='/cps' vis=chan_410_20231105T02????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select='antennae(19)' nxy=3,3

mkdir -p images

ant=1
while [[ $ant -le 256 ]];
do
   ant_str="'antennae($ant)'"
   ant_psfile=`echo $ant | awk '{printf("vis_antenna_%03d.ps",$1);}'`   
   ant_pdffile=`echo $ant | awk '{printf("vis_antenna_%03d.pdf",$1);}'`   
   
   if [[ -s images/${ant_pdffile} ]]; then
      echo "PROGRESS : file images/${ant_pdffile} already exists -> skipped ant = $ant"
   else
      echo "uvplt device='/cps' vis=chan_410_20231105T0[2,3,4]????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select=${ant_str} nxy=3,3"
      uvplt device='/cps' vis=chan_410_20231105T0[2,3,4]????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select=${ant_str} nxy=3,3
   
#   echo "mv pgplot.ps images/${ant_psfile}"
#   mv pgplot.ps images/${ant_psfile}

      echo "ps2pdf pgplot.ps images/${ant_pdffile}"
      ps2pdf pgplot.ps images/${ant_pdffile}
   fi
   
   ant=$(($ant+1))
done
