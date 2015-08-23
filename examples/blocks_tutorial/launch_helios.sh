#! /usr/bin/env bash

if [ $1 == "--debug" ]
then
    legion ./tuto0.py --debug --user_script_args="1";
else
    legion ./tuto0.py --allocation="jvb-000-ag" --instances=10 --user_script_args="1";
fi;
