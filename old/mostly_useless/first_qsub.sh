#!//bin/bash
#PBS -A jvb-000-aa
#PBS -l walltime=10
#PBS -l nodes=2:gpus=2
#PBS -r n
#PBS -N FIRST_JOB 
 
cd /home/julesgm/experimentations/ 
python -c "import sys; print str(sys.version_info)" >> ./hihihaha.log


