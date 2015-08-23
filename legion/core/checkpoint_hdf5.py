from __future__ import print_function, with_statement, division, generators, absolute_import
from traceback import format_exc
import os, sys
import h5py
import legion.core.param_serv.param_utils


def server_save_db_to_hdf5(path, db):
    """
    Save the server's db to hdf5.
    :param path: Where to save.
    :param db: db to save.
    :return: Nothing.
    """
    if os.path.exists(path):
        legion.param_serv.param_utils.pwh("save_db_to_hdf5 - overwriting %s" % path)
    h5 = h5py.File(path, "w")

    for key, value in db.iteritems():
        with value:
            h5.create_dataset(key, shape=value.inner.shape, dtype=value.inner.dtype, data=value.inner)

    h5.close()


def server_load_db_from_hdf5(path, creation_lock):
    """
    Load the server's db from hdf5.
    :param path: Path load the db from.
    :return: The db object.
    """

    h5 = h5py.File(path, "r")

    db = {}
    with creation_lock:
        for key, value in h5.iterkeys():
            db[key] = legion.param_serv.param_utils.Entry(value)

    h5.close()
    return db


def client_load_db_from_hdf5(path):
    """
    -> Not currently used.
    Load the client's db from hdf5.
    :param path: Path load the db from.
    :return: The db object.
    """

    h5 = h5py.File(path, "r")

    db = {}
    for key, value in h5.iterkeys():
        db[key] = legion.param_serv.param_utils.Entry(value)

    h5.close()
    return db


def client_save_db_to_hdf5(path, db):
    """
    -> Not currently used.
    Save the client's db to hdf5.
    :param path: Where to save.
    :param db: db to save.
    :return: Nothing.
    """

    if os.path.exists(path):
        legion.param_serv.param_utils.pwh("save_db_to_hdf5 - overwriting %s" % path)

    h5 = h5py.File(path, "w")

    for key, value in db.iteritems():
        h5.create_dataset(key, shape=value.shape, dtype=value.dtype, data=value)

    h5.save()
    h5.close()


