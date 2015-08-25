
import os
import subprocess
import pickle
import re
import sets

import numpy as np

import matplotlib
matplotlib.use('Agg')
import pylab
import matplotlib.pyplot as plt


def run():

    #experiment_dir = os.getcwd()
    #experiment_dir = "/rap/jvb-000-aa/data/alaingui/experiments_legion"
    experiment_dir = "/home/dpln/NIPS/experiments_legion"

    read_results_and_plot(experiment_dir, 'train_cross_entropy')
    read_results_and_plot(experiment_dir, 'train_error_rate')
    read_results_and_plot(experiment_dir, 'valid_cross_entropy')
    read_results_and_plot(experiment_dir, 'valid_error_rate')


def read_results_and_plot(experiment_dir, criterion):

    # assert criterion in ['cost', 'error_rate']

    #if criterion == 'cross_entropy':
    #    D_colors = {'train_cross_entropy' : ('#00cc66', '#006600'),
    #                'valid_cross_entropy' : ('#ff9933', '#cc6600')}
    #    outputfile = os.path.join(experiment_dir, "cross_entropy.png")
    #elif criterion == 'error_rate':
    #    D_colors = {'train_error_rate' : ('#9999ff', '#0000ff'),
    #                'valid_error_rate' : ('#ff66b2', '#cc0066')}
    #    outputfile = os.path.join(experiment_dir, "error_rate.png")


    L_result_files = find_result_files(experiment_dir)

    if len(L_result_files) == 0:
        print "ERROR. You can't do anything with zero result files."
        quit()

    L_legend_handles = []
    L_legend_tags = []

    pylab.hold(True)

    L_results = []
    for result_file in L_result_files:

        path = result_file['path']
        worker_id = result_file['worker_id']
        exp_path = result_file['exp_path']

        A = pickle.load(open(path, "r"))

        L_step = []

        D_logged = dict(train_cross_entropy = [],
                        train_error_rate = [],
                        valid_cross_entropy = [],
                        valid_error_rate = [])

        for (step,v) in A.items():

            if all([v.has_key(k) for k in D_logged.keys()]):

                if not v.has_key('timestamp'):
                    print "You are probably not using the `Timestamp` blocks extension because there is no 'timestamp' entry in the logs."
                    quit()

                L_step.append(v['timestamp'])
                for k in D_logged.keys():
                    D_logged[k].append(v[k])

        print "Parsed results from %s. Found %d values to plot." % (result_file, len(L_step))

        L_results.append({'A_step':np.array(L_step), 'D_logged':D_logged, 'exp_path':exp_path})


    # This is the smallest value encountered for all the steps (in any given experiment).
    # We shouldn't plot anything before we come up with this value.
    D_step_min = {}
    for res in L_results:
        exp_path = res['exp_path']
        if D_step_min.has_key(exp_path):
            D_step_min[exp_path] = np.min([res['A_step'].min(), D_step_min[exp_path]])
        else:
            D_step_min[exp_path] = res['A_step'].min()

    D_colors = {'alone_3h' : '#2299ff',
                '4workers_3h' : '#9999ff',
                '8workers_3h' : '#9944ff'}

    # TODO : You need to iterate with the exp_path and then you can
    #        plot one per exp_path.

    pylab.hold(True)
    L_legend_handles = []
    legend_checkbox_trick = set()
    for exp_path in ['alone_3h', '4workers_3h', '8workers_3h']:
    
        legend_has_been_set_for_at_least_one_plot = False

        for res in L_results:

            if res['exp_path'] != exp_path:
                continue

            domain = res['A_step'] - D_step_min[exp_path]
            D_logged = res['D_logged']

            color = D_colors[exp_path]

            if legend_has_been_set_for_at_least_one_plot:
                h = pylab.plot(domain, D_logged[k], c=color, label=exp_path)
                L_legend_handles.append(h)
                legend_has_been_set_for_at_least_one_plot = True
            else:
                h = pylab.plot(domain, D_logged[k], c=color)


    if criterion in ['train_error_rate', 'valid_error_rate']:
        pylab.ylim(ymin=0.0, ymax=1.0)
    elif criterion in ['train_cross_entropy', 'valid_cross_entropy']:
        pylab.ylim(ymin=0.0)


    #outputfile = os.path.join(experiment_dir, "%s_%s.png" % (exp_path, criterion))
    outputfile = os.path.join(experiment_dir, "%s.png" % (criterion,))

    plt.legend(handles=L_legend_handles)
    pylab.draw()
    pylab.savefig(outputfile, dpi=150)
    pylab.close()
    print "Wrote %s." % outputfile




def find_result_files(dir):
    """
    Find all the files called "checkpoint_35492_log" in the directory.
    """

    L_files = sorted([e for e in subprocess.check_output("find %s -name 'checkpoint*log'" % (dir,), shell=True).split("\n") if len(e)>0])

    L_result_files = []
    for path in L_files:
        m = re.match(r".*/(\w*)/checkpoint_(\d+)_log", path)
        if m:
            L_result_files.append({'path' : path, 'worker_id' : int(m.group(2)), 'exp_path' : m.group(1)})

    return L_result_files




if __name__ == "__main__":
    run()


"""

rsync -av --delete helios:/rap/jvb-000-aa/data/alaingui/experiments_legion ${HOME}/NIPS

"""