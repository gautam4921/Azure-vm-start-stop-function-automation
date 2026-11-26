import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

app = func.FunctionApp()

def required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing application setting: {name}")
    return value

def eligible(vm) -> bool:
    tags = vm.tags or {}
    target = required_setting("TARGET_ENVIRONMENT").lower()
    environment = str(tags.get("Environment", "")).lower()
    auto_schedule = str(tags.get("AutoSchedule", "")).lower()

    if environment != target or auto_schedule != "true":
        return False

    if target == "prod" and os.getenv("ALLOW_PROD_AUTOMATION", "false").lower() != "true":
        logging.warning("Production automation is disabled.")
        return False

    return True

def get_power_state(client, resource_group: str, vm_name: str) -> str:
    view = client.virtual_machines.instance_view(resource_group, vm_name)
    for status in view.statuses or []:
        code = status.code or ""
        if code.lower().startswith("powerstate/"):
            return code.split("/", 1)[1].lower()
    return "unknown"

def run_vm_action(action: str) -> None:
    if action not in {"start", "deallocate"}:
        raise ValueError("Action must be start or deallocate.")

    subscription_id = required_setting("AZURE_SUBSCRIPTION_ID")
    resource_group = required_setting("TARGET_RESOURCE_GROUP")
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    credential = DefaultAzureCredential()
    client = ComputeManagementClient(credential, subscription_id)

    try:
        for vm in client.virtual_machines.list(resource_group):
            if not eligible(vm):
                logging.info("Skipping VM %s: tags do not match.", vm.name)
                continue

            state = get_power_state(client, resource_group, vm.name)

            if action == "start" and state == "running":
                logging.info("VM %s is already running.", vm.name)
                continue
            if action == "deallocate" and state in {"deallocated", "stopped"}:
                logging.info("VM %s is already stopped/deallocated.", vm.name)
                continue

            if dry_run:
                logging.warning("DRY RUN: would %s VM %s.", action, vm.name)
                continue

            logging.info("Submitting %s for VM %s.", action, vm.name)
            if action == "start":
                client.virtual_machines.begin_start(resource_group, vm.name).result()
            else:
                client.virtual_machines.begin_deallocate(resource_group, vm.name).result()
            logging.info("Completed %s for VM %s.", action, vm.name)
    finally:
        credential.close()

@app.timer_trigger(
    schedule="%VM_START_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def start_vms(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Start timer is past due.")
    run_vm_action("start")

@app.timer_trigger(
    schedule="%VM_DEALLOCATE_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def deallocate_vms(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Deallocate timer is past due.")
    run_vm_action("deallocate")

# Additional HTTP health-check endpoint
@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Health check request received")

    try:
        logging.info("Function executed successfully")

        return func.HttpResponse(
            "Function App is healthy",
            status_code=200
        )

    except Exception:
        logging.exception("Health check failed")
        raise