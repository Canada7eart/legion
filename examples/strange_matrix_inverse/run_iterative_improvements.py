
import time
import numpy as np


def generate_big_matrix(N):

    original_seed = np.random.randint(low=0, high=1000000)
    np.random.seed(42)
    big_matrix = np.random.randn(N,N)
    np.random.seed(original_seed)

    return big_matrix





def try_one_guess(current_inv_approx, big_matrix, stddev, current_error=None):

    N = big_matrix.shape[0]
    proposed_inv_approx = current_inv_approx + stddev * np.random.randn(N, N)

    #proposed_error = np.abs(proposed_inv_approx.dot(big_matrix) - np.eye(N)).mean()
    proposed_error = get_error(proposed_inv_approx, big_matrix)

    if current_error is None or proposed_error < current_error:
        return ('success', proposed_inv_approx, proposed_error)
    else:
        return ('failure', current_inv_approx, current_error)


def get_error(A, big_matrix):
    return np.abs(A.dot(big_matrix) - np.eye(big_matrix.shape[0])).mean()

def run_alone():

    N = 1000
    big_matrix = generate_big_matrix(N)

    current_inv_approx = np.eye(N)
    current_error = None
    noise = 0.0001

    for i in range(100000):
        (status, current_inv_approx, current_error) = try_one_guess(current_inv_approx, big_matrix, noise, current_error)
        print "update %s, current_error %0.12f" % (status, current_error)


def run_legion():

    from legion import Client

    client = Client()
    alpha = 0.5
    beta = 0.5

    N = 100
    big_matrix = generate_big_matrix(N)

    current_inv_approx = np.eye(N)
    client.create_if_not_already_created("current_inv_approx", current_inv_approx)
    current_inv_approx = client.pull_full("current_inv_approx")
    #print "type(current_inv_approx)"
    #print type(current_inv_approx)


    current_error = get_error(current_inv_approx, big_matrix)
    original_noise = 0.001
    current_noise = original_noise

    last_index_with_good_proposal = 0
    for i in range(1000):
        (status, current_inv_approx, current_error) = try_one_guess(current_inv_approx, big_matrix, current_noise, current_error)
        #print "update %s, current_error %0.4f" % (status, current_error)

        time.sleep(1)

        if status == 'success':
            client.push_full("current_inv_approx", current_inv_approx, alpha, beta)
            print "Pushed current_inv_approx with error %0.12f to server." % current_error
            current_inv_approx = client.pull_full("current_inv_approx")
            last_index_with_good_proposal = i
            current_noise = original_noise
        else:
            current_noise = 0.9 * current_noise

        if last_index_with_good_proposal == i or 25 < last_index_with_good_proposal - i:
            current_inv_approx = client.pull_full("current_inv_approx")
            current_error = get_error(current_inv_approx, big_matrix)
            print "Pulled current_inv_approx with error %0.12f from server." % current_error

    """

    /home/dpln/NIPS/legion/bin/legion /home/dpln/NIPS/trylegion/script1.py --instances=1 --debug --walltime=00:02:00

    """


if __name__ == "__main__":
    #run_alone()
    run_legion()






