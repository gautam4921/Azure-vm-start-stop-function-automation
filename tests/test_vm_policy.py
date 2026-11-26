
from function_app import eligible


def test_dev_vm_is_eligible():

    vm = {
        "name": "vm-dev-01",
        "tags": {
            "Environment": "dev",
            "AutoSchedule": "true"
        }
    }

    assert eligible(vm) is True


def test_dev_vm_with_uppercase_tag_values():

    vm = {
        "name": "vm-dev-02",
        "tags": {
            "Environment": "DEV",
            "AutoSchedule": "TRUE"
        }
    }

    assert eligible(vm) is True


def test_vm_without_autoschedule_tag():

    vm = {
        "name": "vm-dev-03",
        "tags": {
            "Environment": "dev"
        }
    }

    assert eligible(vm) is False


def test_vm_autoschedule_false():

    vm = {
        "name": "vm-dev-04",
        "tags": {
            "Environment": "dev",
            "AutoSchedule": "false"
        }
    }

    assert eligible(vm) is False


def test_prod_vm_is_not_eligible_by_default():

    vm = {
        "name": "vm-prod-01",
        "tags": {
            "Environment": "prod",
            "AutoSchedule": "true"
        }
    }

    assert eligible(vm) is False


def test_prod_vm_can_be_enabled_explicitly():

    vm = {
        "name": "vm-prod-02",
        "tags": {
            "Environment": "prod",
            "AutoSchedule": "true"
        }
    }

    assert eligible(vm, allow_prod=True) is True


def test_qa_vm_is_not_eligible():

    vm = {
        "name": "vm-qa-01",
        "tags": {
            "Environment": "qa",
            "AutoSchedule": "true"
        }
    }

    assert eligible(vm) is False


def test_vm_without_tags():

    vm = {
        "name": "vm-dev-05",
        "tags": None
    }

    assert eligible(vm) is False


def test_empty_vm():

    assert eligible(None) is False

