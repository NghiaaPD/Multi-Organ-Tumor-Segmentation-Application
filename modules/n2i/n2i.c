#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>  // cho INFINITY

static PyObject* export_slices_fast(PyObject* self, PyObject* args) {
    PyArrayObject* array_obj;
    const char* base_path;
    const char* format = "png";   // mặc định
    int quality = 95;             // mặc định cho JPEG

    if (!PyArg_ParseTuple(args, "O!ss|ii", 
                          &PyArray_Type, &array_obj,
                          &base_path, &format, &quality))
        return NULL;

    if (PyArray_NDIM(array_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "Input array must be 3D (x, y, z)");
        return NULL;
    }

    if (PyArray_TYPE(array_obj) != NPY_FLOAT32 && PyArray_TYPE(array_obj) != NPY_FLOAT64) {
        PyErr_SetString(PyExc_ValueError, "Array must be float32 or float64");
        return NULL;
    }

    npy_intp* dims = PyArray_DIMS(array_obj);
    int nx = (int)dims[0];
    int ny = (int)dims[1];
    int nz = (int)dims[2];

    // Tìm min/max để chuẩn hóa
    double min_val = INFINITY, max_val = -INFINITY;
    double* data = (double*)PyArray_DATA(array_obj);
    npy_intp total = nx * ny * nz;
    for (npy_intp i = 0; i < total; ++i) {
        double v = data[i];
        if (v < min_val) min_val = v;
        if (v > max_val) max_val = v;
    }
    double range = max_val - min_val;
    if (range <= 0) range = 1.0;

    unsigned char* img = malloc(nx * ny);
    if (!img) {
        PyErr_NoMemory();
        return NULL;
    }

    char outname[4096];

    for (int z = 0; z < nz; ++z) {
        // Fill buffer grayscale
        for (int y = 0; y < ny; ++y) {
            for (int x = 0; x < nx; ++x) {
                double val = data[z * ny * nx + y * nx + x];
                unsigned char pixel = (unsigned char)(((val - min_val) / range) * 255.0);
                img[y * nx + x] = pixel;
            }
        }

        // Xử lý định dạng và chuẩn hóa đuôi file
        int success = 0;
        const char* ext = "png";  // mặc định

        if (strcmp(format, "png") == 0) {
            success = stbi_write_png(outname, nx, ny, 1, img, nx);
            ext = "png";
        }
        else if (strcmp(format, "jpg") == 0 || strcmp(format, "jpeg") == 0) {
            if (quality < 1) quality = 1;
            if (quality > 100) quality = 100;
            success = stbi_write_jpg(outname, nx, ny, 1, img, quality);
            ext = "jpeg"; 
        }
        else if (strcmp(format, "bmp") == 0) {
            success = stbi_write_bmp(outname, nx, ny, 1, img);
            ext = "bmp";
        }
        else if (strcmp(format, "tga") == 0) {
            success = stbi_write_tga(outname, nx, ny, 1, img);
            ext = "tga";
        }
        else {
            PyErr_Format(PyExc_ValueError, "Unsupported format: '%s'. Use 'png', 'jpg', 'jpeg', 'bmp', or 'tga'.", format);
            free(img);
            return NULL;
        }

        // Tạo tên file cuối cùng với đuôi đã chuẩn hóa
        snprintf(outname, sizeof(outname), "%s_slice_%03d.%s", base_path, z, ext);

        if (!success) {
            PyErr_Format(PyExc_IOError, "Failed to write image: %s", outname);
            free(img);
            return NULL;
        }
    }

    free(img);
    Py_RETURN_NONE;
}

static PyMethodDef N2iMethods[] = {
    {"export_slices", export_slices_fast, METH_VARARGS,
     "Export 3D numpy array (float) slices to images.\n"
     "Args: array (3D), base_path (str), format='png' (str: png/jpg/jpeg/bmp/tga), quality=95 (int for jpg/jpeg)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef n2imodule = {
    PyModuleDef_HEAD_INIT,
    "n2i",
    NULL,
    -1,
    N2iMethods
};

PyMODINIT_FUNC PyInit_n2i(void) {
    import_array();
    return PyModule_Create(&n2imodule);
}