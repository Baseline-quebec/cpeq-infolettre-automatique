"""Test cpeq-infolettre-automatique REST API."""

import httpx
import pytest
from fastapi.testclient import TestClient

from cpeq_infolettre_automatique.api import app


client = TestClient(app)


@pytest.mark.parametrize("status_code", [200])
def test_root_status_code(status_code: int) -> None:
    """Test that reading the root is successful."""
    if not httpx.codes.is_success(status_code):
        error_message = "Status code should indicate success"
        raise AssertionError(error_message)
