from setuptools import setup, Extension
import numpy

module = Extension(
    'connected-components-3d',
    sources=['connected-components-3d.c'],
    include_dirs=[numpy.get_include()],
    extra_compile_args=['-O3'],
)

setup(
    name='connected-components-3d',
    version='1.0',
    description='Fast 3D Connected Component Labeling (26-connectivity, two-pass, union-find, C extension)',
    ext_modules=[module],
)