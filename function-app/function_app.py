
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

from vm_policy import eligible


# Azure Functions application
app = func.FunctionApp()


def get_required_setting(name):
    """
    Read required configuration at runtime.
    Do not access Azure configuration during module import.
    """
    value = os.getenv(name)

    if not value:
        raise ValueError(
            f"Required application setting is missing: {name}"
        )

    return value


def get_bool_setting(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() == "true"


def get_compute_client():
    """
    Authenticate using the Function App's Managed Identity.
    """

    subscription_id = get_required_setting(
        "AZURE_SUBSCRIPTION_ID"
    )

    credential = DefaultAzureCredential()

    return ComputeManagementClient(
        credential,
        subscription_id
    )


def process_vms(action):
    """
    Process eligible VMs.

    action = start or deallocate
    """

    resource_group = get_required_setting(
        "TARGET_RESOURCE_GROUP"
    )

    dry_run = get_bool_setting(
        "DRY_RUN",
        default=True
    )

    allow_prod = get_bool_setting(
        "ALLOW_PROD_AUTOMATION",
        default=False
    )

    logging.info(
        "VM automation started. Action=%s, ResourceGroup=%s, "
        "DryRun=%s, AllowProd=%s",
        action,
        resource_group,
        dry_run,
        allow_prod
    )

    compute_client = get_compute_client()

    vms = compute_client.virtual_machines.list(
        resource_group_name=resource_group
    )

    processed = 0

    for vm in vms:

        vm_name = vm.name

        if not eligible(vm, allow_prod=allow_prod):
            logging.info(
                "Skipping VM %s because it is not eligible.",
                vm_name
            )
            continue

        logging.info(
            "Eligible VM identified: %s",
            vm_name
        )

        if dry_run:
            logging.info(
                "[DRY RUN] Would %s VM: %s",
                action,
                vm_name
            )
            continue

        try:

            if action == "start":

                logging.info(
                    "Starting VM: %s",
                    vm_name
                )

                poller = compute_client.virtual_machines.begin_start(
                    resource_group_name=resource_group,
                    vm_name=vm_name
                )

            elif action == "deallocate":

                logging.info(
                    "Deallocating VM: %s",
                    vm_name
                )

                poller = compute_client.virtual_machines.begin_deallocate(
                    resource_group_name=resource_group,
                    vm_name=vm_name
                )

            else:
                raise ValueError(
                    f"Unsupported VM action: {action}"
                )

            # Wait for Azure operation to finish.
            poller.result()

            processed += 1

            logging.info(
                "Successfully completed %s operation for VM %s",
                action,
                vm_name
            )

        except Exception:
            logging.exception(
                "Failed to %s VM: %s",
                action,
                vm_name
            )

    logging.info(
        "VM automation completed. Successfully processed VMs: %s",
        processed
    )


# ==========================================================
# TIMER 1: START VMs
# ==========================================================

@app.timer_trigger(
    schedule="%VM_START_SCHEDULE%",
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=True
)
def start_vms(mytimer: func.TimerRequest):

    if mytimer.past_due:
        logging.warning(
            "VM start timer is running late."
        )

    logging.info("Starting scheduled VM start operation.")

    process_vms("start")


# ==========================================================
# TIMER 2: DEALLOCATE VMs
# ==========================================================

@app.timer_trigger(
    schedule="%VM_DEALLOCATE_SCHEDULE%",
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=True
)
def deallocate_vms(mytimer: func.TimerRequest):

    if mytimer.past_due:
        logging.warning(
            "VM deallocation timer is running late."
        )

    logging.info("Starting scheduled VM deallocation operation.")

    process_vms("deallocate")


# Timer Trigger: Start VMs at 8 AM IST (02:30 UTC)
@app.timer_trigger(
    schedule="%VM_START_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def start_vms(timer: func.TimerRequest):

    logging.info("Scheduled VM start trigger executed.")
    process_vms("start")


# Timer Trigger: Deallocate VMs at 8 PM IST (14:30 UTC)
@app.timer_trigger(
    schedule="%VM_STOP_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def stop_vms(timer: func.TimerRequest):

    logging.info("Scheduled VM deallocation trigger executed.")
    process_vms("deallocate")


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