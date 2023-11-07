# uvplt device='/cps' vis=chan_410_20231105T02????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select='antennae(19)' nxy=3,3

mkdir -p images

for ant in 
do
   ant_str="'antennae($ant)'"
   ant_psfile=`echo $ant | awk '{printf("vis_antenna_%03d.ps",$1);}'`   
   
   echo "uvplt device='/cps' vis=chan_410_20231105T02????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select=${ant_str} nxy=3,3"
   uvplt device='/cps' vis=chan_410_20231105T02????.uv  axis=time,phase stokes=xx,yy yrange=-200,200 select=${ant_str} nxy=3,3
   
   echo "mv pgplot.ps images/${ant_psfile}"
   mv pgplot.ps images/${ant_psfile}
done
