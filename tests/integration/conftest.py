import time

import httpx
import pytest


@pytest.fixture(scope="session", autouse=True)
def stack_up():
    """
    Verifica que a stack está rodando (Kong admin API responde).
    Esta fixture NÃO sobe nem derruba a stack — assume que `make up` já foi feito.
    """
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            r = httpx.get("http://localhost:8001/services", timeout=2.0)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        pytest.exit("Kong não respondeu na admin API; rode `make up` antes.")
    yield
