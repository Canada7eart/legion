


from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy as np

setup(
      cmdclass = {'build_ext': build_ext},
      ext_modules = [
                     Extension("socialism", ["__init__.py"]),
                     Extension("socialism.benevolant_dictator",            [
                                                        #'__init__.py', 
                                                        'benevolant_dictator.py', 
                                                        #'checkpoint_hdf5.py', 
                                                        #'client.py', 
                                                        #'condition_test.py',
                                                        ]),
             
                     Extension("socialism.param_serv", [
                                                        #'./param_serv/__init__.py',
                                                        #'./param_serv/headers.py',
                                                        #'./param_serv/param_utils.py',
                                                        './param_serv/server.py',
                                                        ]),
                                 

                     Extension("socialism.param_serv.param_utils", [
                                                        #'./param_serv/__init__.py',
                                                        #'./param_serv/headers.py',
                                                        './param_serv/param_utils.py',
                                                
                                                        ]),
                    ],include_dirs = [np.get_include()],
     )