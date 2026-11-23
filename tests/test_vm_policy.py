import os
from types import SimpleNamespace

import pytest

from function_app import eligible

@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setenv("TARGET_ENVIRONMENT", "dev")
    monkeypatch.delenv("ALLOW_PROD_AUTOMATION", raising=False)

def test_eligible_dev_vm():
    vm = SimpleNamespace(tags={"Environment": "Dev", "AutoSchedule": "true"})
    assert eligible(vm)

def test_other_environment_is_skipped():
    vm = SimpleNamespace(tags={"Environment": "QA", "AutoSchedule": "true"})
    assert not eligible(vm)

def test_untagged_vm_is_skipped():
    vm = SimpleNamespace(tags=None)
    assert not eligible(vm)

def test_prod_requires_explicit_flag(monkeypatch):
    monkeypatch.setenv("TARGET_ENVIRONMENT", "prod")
    vm = SimpleNamespace(tags={"Environment": "Prod", "AutoSchedule": "true"})
    assert not eligible(vm)
