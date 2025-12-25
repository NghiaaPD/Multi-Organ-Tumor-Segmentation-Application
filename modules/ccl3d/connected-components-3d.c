#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdint.h>
#include <stdlib.h>

#define IDX(x, y, z, W, H) (((z) * (H) + (y)) * (W) + (x))

// Union-Find structure
static inline uint32_t uf_find(uint32_t *parent, uint32_t i) {
    if (parent[i] != i) {
        parent[i] = uf_find(parent, parent[i]);
    }
    return parent[i];
}

static inline void uf_union(uint32_t *parent, uint32_t a, uint32_t b) {
    uint32_t ra = uf_find(parent, a);
    uint32_t rb = uf_find(parent, b);
    if (ra < rb) parent[rb] = ra;
    else if (rb < ra) parent[ra] = rb;
}

// 26-connectivity neighbor offsets
static const int dx[26] = {-1, 0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 1, -1, 0, 1, 0, 0};
static const int dy[26] = {-1, -1, -1, 0, 0, 0, 1, 1, 1, -1, -1, -1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, -1, 1};
static const int dz[26] = {-1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0};

static PyObject* ccl3d(PyObject* self, PyObject* args) {
    PyArrayObject *input = NULL;
    if (!PyArg_ParseTuple(args, "O!", &PyArray_Type, &input))
        return NULL;
    if (PyArray_NDIM(input) != 3 || PyArray_TYPE(input) != NPY_UINT8)
        return PyErr_Format(PyExc_ValueError, "Input must be 3D uint8 array");
    npy_intp *dims = PyArray_DIMS(input);
    npy_intp D = dims[0], H = dims[1], W = dims[2];
    npy_uint8 *in_data = (npy_uint8*)PyArray_DATA(input);

    npy_intp out_dims[3] = {D, H, W};
    PyArrayObject *labels = (PyArrayObject*)PyArray_SimpleNew(3, out_dims, NPY_UINT32);
    uint32_t *lbl = (uint32_t*)PyArray_DATA(labels);
    uint32_t max_labels = D * H * W;
    uint32_t *parent = (uint32_t*)malloc(max_labels * sizeof(uint32_t));
    if (!parent) {
        Py_DECREF(labels);
        return PyErr_NoMemory();
    }
    for (uint32_t i = 0; i < max_labels; ++i) parent[i] = i;

    // Pass 1: label and union
    uint32_t next_label = 1;
    for (npy_intp z = 0; z < D; ++z) {
        for (npy_intp y = 0; y < H; ++y) {
            for (npy_intp x = 0; x < W; ++x) {
                npy_intp idx = IDX(x, y, z, W, H);
                if (in_data[idx] == 0) {
                    lbl[idx] = 0;
                    continue;
                }
                uint32_t min_label = 0;
                for (int n = 0; n < 26; ++n) {
                    int nx = x + dx[n], ny = y + dy[n], nz = z + dz[n];
                    if (nx < 0 || ny < 0 || nz < 0 || nx >= W || ny >= H || nz >= D) continue;
                    npy_intp nidx = IDX(nx, ny, nz, W, H);
                    if (in_data[nidx] && lbl[nidx]) {
                        if (!min_label || lbl[nidx] < min_label) min_label = lbl[nidx];
                    }
                }
                if (min_label) {
                    lbl[idx] = min_label;
                    for (int n = 0; n < 26; ++n) {
                        int nx = x + dx[n], ny = y + dy[n], nz = z + dz[n];
                        if (nx < 0 || ny < 0 || nz < 0 || nx >= W || ny >= H || nz >= D) continue;
                        npy_intp nidx = IDX(nx, ny, nz, W, H);
                        if (in_data[nidx] && lbl[nidx] && lbl[nidx] != min_label) {
                            uf_union(parent, min_label, lbl[nidx]);
                        }
                    }
                } else {
                    lbl[idx] = next_label++;
                }
            }
        }
    }
    // Pass 2: flatten and relabel
    uint32_t *new_labels = (uint32_t*)calloc(next_label, sizeof(uint32_t));
    uint32_t cur_label = 1;
    for (uint32_t i = 0; i < max_labels; ++i) {
        if (lbl[i]) {
            uint32_t root = uf_find(parent, lbl[i]);
            if (!new_labels[root]) new_labels[root] = cur_label++;
            lbl[i] = new_labels[root];
        }
    }
    free(parent);
    free(new_labels);
    return (PyObject*)labels;
}

static PyMethodDef CCL3DMethods[] = {
    {"ccl3d", ccl3d, METH_VARARGS, "3D Connected Component Labeling (26-connectivity)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef ccl3dmodule = {
    PyModuleDef_HEAD_INIT,
    "ccl3d",   /* name of module */
    NULL,       /* module documentation, may be NULL */
    -1,         /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    CCL3DMethods
};

PyMODINIT_FUNC PyInit_ccl3d(void) {
    import_array();
    return PyModule_Create(&ccl3dmodule);
}
