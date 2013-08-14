
import pytest
@pytest.fixture
def path():
    import os.path
    here = os.path.dirname(os.path.abspath(__file__))
    def j(*a):
        return os.path.join(here, *a)
    return j
