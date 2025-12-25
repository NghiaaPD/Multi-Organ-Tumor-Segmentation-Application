from setuptools import setup, Extension
import numpy as np

setup(
    name="n2i",  # hoặc "n2i" nếu bạn muốn
    version="0.1",
    ext_modules=[
        Extension(
            "n2i",
            sources=["n2i.c"],
            include_dirs=[np.get_include()],  # tự động thêm numpy include
            extra_compile_args=["-std=c99"],
        )
    ],
    install_requires=["numpy"],
    description="Fast NIfTI slices to PNG using numpy array input",
)