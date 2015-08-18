<<<<<<< HEAD
#! /usr/bin/env bash
#    parser.add_argument('--path',             type="str")
=======
#    parser.add_argument('--path',   type="str")
>>>>>>> 16781cc2bf04170a6609a926be9cd4c64377c1d4
#
#    parser.add_argument('--nodes',  type="int")
#    parser.add_argument('--gpus',   type="int")
#
#### Optional
#    parser.add_argument('--walltime',         type="str", default="12:00:00")
#
#    parser.add_argument('--debug',                        default=False, action="store_true")
#    parser.add_argument('--debug_pycharm',                default=False, action="store_true")
#
#    parser.add_argument('--allocation_name',  type="str", default="jvb-000-aa")
#    parser.add_argument('--job_name',         type="str", default="[Unspecified]")
#    parser.add_argument('--user_script_args', type="str", default="")

<<<<<<< HEAD
leg --path=./tuto0.py  --number_of_nodes=2 --number_of_gpus=8 --procs_per_job=8 --walltime="24:00:00" --allocation_name="jvb-000-ag"
=======

leg --path=./tuto0.py  --instances=32 --allocation_name="jvb-000-ag"
>>>>>>> 16781cc2bf04170a6609a926be9cd4c64377c1d4
