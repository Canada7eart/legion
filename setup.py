from distutils.core import setup
from distutils.extension import Extension
#from Cython.Distutils import build_ext
import numpy as np
from Cython.Build import cythonize
from Cython.Distutils import build_ext
cmdclass = { }

extensions = ["legion/*.py", 
	          "legion/param_serv/*.py"]
		

setup(name = 'legion', 
      packages = ["legion", "legion.param_serv"],
      ext_modules = cythonize(extensions),
      include_dirs = [np.get_include()],
     )
