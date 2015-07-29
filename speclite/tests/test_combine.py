# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.tests.helper import pytest
from ..combine import accumulate
import numpy as np
import numpy.ma as ma


def test_invalid_types():
    data = np.zeros((10,), dtype=[('wlen', float), ('flux', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=0, data2_in=data)
    with pytest.raises(ValueError):
        accumulate(data1_in=data, data2_in=0)
    with pytest.raises(ValueError):
        accumulate(data1_in=data, data2_in=data, data_out=0)


def test_incompatible_shapes():
    data1 = np.zeros((10,), dtype=[('wlen', float), ('flux', float)])
    data2 = np.zeros((11,), dtype=[('wlen', float), ('flux', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2)


def test_not_structured_input():
    data = np.zeros((10,), dtype=[('wlen', float), ('flux', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=np.arange(10), data2_in=data, join=0)
    with pytest.raises(ValueError):
        accumulate(data1_in=data, data2_in=np.arange(10), join=0)


def test_no_common_fields():
    data1 = np.zeros((10,), dtype=[('wlen1', float), ('flux1', float)])
    data2 = np.zeros((10,), dtype=[('wlen2', float), ('flux2', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2)


def test_invalid_join():
    data1 = np.zeros((10,), dtype=[('wlen', float), ('flux1', float)])
    data2 = np.zeros((10,), dtype=[('wlen', float), ('flux2', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, join=0)
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, join='flux1')
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, join='flux12')
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, join=('wlen', 0))


def test_invalid_add():
    data1 = np.zeros((10,), dtype=[('wlen', float), ('f1', float)])
    data2 = np.zeros((10,), dtype=[('wlen', float), ('f2', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add=0)
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add='f1')
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add='f12')
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add=('wlen', 1))


def test_unmatched_join():
    data1 = np.zeros((10,), dtype=[('wlen', float)])
    data2 = np.ones((10,), dtype=[('wlen', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, join='wlen')


def test_invalid_weight():
    data1 = np.zeros((10,), dtype=[('f', float)])
    data2 = np.zeros((10,), dtype=[('f', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add='f', weight=0)
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2, add='f', weight=('f',))


def test_no_results():
    data1 = np.zeros((10,), dtype=[('f', float)])
    data2 = np.zeros((10,), dtype=[('f', float)])
    with pytest.raises(ValueError):
        accumulate(data1_in=data1, data2_in=data2)


def test_add_no_weight():
    data1 = np.ones((10,), dtype=[('f', float)])
    data2 = np.ones((10,), dtype=[('f', float)])
    result = accumulate(data1_in=data1, data2_in=data2, add='f')
    assert result.dtype == data1.dtype, 'Unexpected result dtype.'
    assert result.shape == data1.shape, 'Unexpected result shape.'
    assert np.all(result['f'] == 1), 'Incorrect addition result.'
    result = accumulate(data1_in=data1, data2_in=data2, add='f', weight='w')
    assert np.all(result['f'] == 1), 'Incorrect addition result.'
    assert np.all(result['w'] == 2), 'Incorrect addition result.'


def test_add_weighted():
    data1 = np.ones((10,), dtype=[('f', float), ('w', float)])
    data2 = np.ones((10,), dtype=[('f', float), ('w', float)])
    result = accumulate(data1_in=data1, data2_in=data2, add='f', weight='w')
    assert result.dtype == data1.dtype, 'Unexpected result dtype.'
    assert result.shape == data1.shape, 'Unexpected result shape.'
    assert np.all(result['f'] == 1), 'Incorrect addition result.'
    assert np.all(result['w'] == 2), 'Incorrect addition result.'


def test_add_iterative():
    data1 = np.ones((10,), dtype=[('f', float), ('w', float)])
    data2 = np.ones((10,), dtype=[('f', float), ('w', float)])
    for i in range(99):
        result = accumulate(data1_in=data1, data2_in=data2, data_out=data1,
                            add='f', weight='w')
    assert result is data1, 'Expected result is data1_in.'
    assert np.all(result['f'] == 1), 'Incorrect iterative result.'
    assert np.all(result['w'] == 100), 'Incorrect iterative result.'


def test_one_masked():
    data1 = ma.ones((10,), dtype=[('f', float), ('w', float)])
    data2 = np.ones((10,), dtype=[('f', float), ('w', float)])
    data1.mask = False
    data1['f'].mask[2] = True
    result = accumulate(data1_in=data1, data2_in=data2, add='f', weight='w')
    assert not ma.isMA(result), 'Result should not be masked.'
    assert np.all(result['f'] == 1), 'Incorrect addition result.'
    assert np.array_equal(result['w'][1:4], (2, 1, 2)),\
        'Mask not used correctly.'


def test_both_masked():
    data1 = ma.ones((10,), dtype=[('f', float), ('w', float)])
    data2 = ma.ones((10,), dtype=[('f', float), ('w', float)])
    data1.mask = False
    data1['f'].mask[2:4] = True
    data2.mask = False
    data2['f'].mask[3:5] = True
    result = accumulate(data1_in=data1, data2_in=data2, add='f', weight='w')
    assert not ma.isMA(result), 'Result should not be masked.'
    assert np.all(result['f'] == 1), 'Incorrect addition result.'
    assert np.array_equal(result['w'][1:6], (2, 1, 0, 1, 2)),\
        'Mask not used correctly.'
