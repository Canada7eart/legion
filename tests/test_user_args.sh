#! /usr/bin/env bash
USER_ARGS='--arg0 --the_str="foo_bar_321"'

RES=$(legion ./accomp_test_user_args.py --debug --user_script_args="$USER_ARGS")

python -c "
import sys
res=sys.argv[1]

assert 'arg0=True' in res and 'arg1=False' in res and 'the_str=\'foo_bar_321\'' in res, 'Failed. The value was \'%s\'' % str(res)
print 'Success.'
" "$RES"

