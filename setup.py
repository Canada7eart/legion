from distutils.core import setup
from distutils.extension import Extension
#from Cython.Distutils import build_ext
import numpy as np
from Cython.Build import cythonize
from Cython.Distutils import build_ext
cmdclass = { }

extensions = ["socialism/*.py", 
	          "socialism/param_serv/*.py"]
		

setup(name = 'socialism', 
      packages = ["socialism", "socialism.param_serv"],
      ext_modules = cythonize(extensions),
      include_dirs = [np.get_include()],
     )
