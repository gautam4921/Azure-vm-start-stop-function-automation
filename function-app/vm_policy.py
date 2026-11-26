
def eligible(vm, allow_prod=False):
    """
    Determine whether a VM is eligible for automation.

    Required tags:
      Environment = dev
      AutoSchedule = true

    Production VMs are excluded unless allow_prod=True.
    """

    if not vm:
        return False

    # Support both Azure SDK VM objects and dictionaries used in tests.
    if isinstance(vm, dict):
        tags = vm.get("tags") or {}
    else:
        tags = getattr(vm, "tags", None) or {}

    environment = str(tags.get("Environment", "")).strip().lower()
    auto_schedule = str(tags.get("AutoSchedule", "")).strip().lower()

    if auto_schedule != "true":
        return False

    if environment == "dev":
        return True

    if environment == "prod" and allow_prod:
        return True

    return False
