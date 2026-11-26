
import os
import logging
import azure.functions as func

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

app = func.FunctionApp()

# Read configuration from Function App environment variables
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")

RESOURCE_GROUP = os.getenv("TARGET_RESOURCE_GROUP")

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def process_vms(action: str):
    """
    Start or deallocate all VMs tagged AutoSchedule=true.
    """

    logging.info("Requested action: %s", action)
    logging.info("Resource group: %s", RESOURCE_GROUP)
    logging.info("Dry run mode: %s", DRY_RUN)

    # Authenticate using the Function App Managed Identity
    credential = DefaultAzureCredential()

    compute_client = ComputeManagementClient(
        credential=credential,
        subscription_id=SUBSCRIPTION_ID
    )

    failures = []

    try:
        # Get VMs from the target resource group
        vms = compute_client.virtual_machines.list(
            RESOURCE_GROUP
        )

        for vm in vms:

            # Only process VMs with AutoSchedule=true
            tags = vm.tags or {}

            if tags.get("AutoSchedule", "").lower() != "true":
                logging.info(
                    "Skipping VM %s: AutoSchedule tag is not true",
                    vm.name
                )
                continue

            vm_name = vm.name

            try:
                # Check the current VM power state
                instance_view = (
                    compute_client.virtual_machines.instance_view(
                        RESOURCE_GROUP,
                        vm_name
                    )
                )

                power_state = "unknown"

                for status in instance_view.statuses or []:
                    if status.code.startswith("PowerState/"):
                        power_state = status.code.split("/", 1)[1].lower()
                        break

                logging.info(
                    "VM: %s | Current state: %s",
                    vm_name,
                    power_state
                )

                if action == "start":

                    if power_state == "running":
                        logging.info(
                            "VM %s is already running. Skipping.",
                            vm_name
                        )
                        continue

                    if power_state not in ("deallocated", "stopped"):
                        logging.warning(
                            "VM %s is in state %s. Skipping start.",
                            vm_name,
                            power_state
                        )
                        continue

                    if DRY_RUN:
                        logging.info(
                            "[DRY RUN] Would start VM: %s",
                            vm_name
                        )
                    else:
                        logging.info("Starting VM: %s", vm_name)

                        compute_client.virtual_machines.begin_start(
                            RESOURCE_GROUP,
                            vm_name
                        ).result()

                        logging.info(
                            "VM %s started successfully.",
                            vm_name
                        )

                elif action == "deallocate":

                    if power_state == "deallocated":
                        logging.info(
                            "VM %s is already deallocated. Skipping.",
                            vm_name
                        )
                        continue

                    if power_state not in ("running", "stopped"):
                        logging.warning(
                            "VM %s is in state %s. Skipping deallocation.",
                            vm_name,
                            power_state
                        )
                        continue

                    if DRY_RUN:
                        logging.info(
                            "[DRY RUN] Would deallocate VM: %s",
                            vm_name
                        )
                    else:
                        logging.info("Deallocating VM: %s", vm_name)

                        compute_client.virtual_machines.begin_deallocate(
                            RESOURCE_GROUP,
                            vm_name
                        ).result()

                        logging.info(
                            "VM %s deallocated successfully.",
                            vm_name
                        )

                else:
                    raise ValueError(
                        f"Unsupported VM action: {action}"
                    )

            except Exception:
                logging.exception(
                    "Failed to process VM: %s",
                    vm_name
                )
                failures.append(vm_name)

        if failures:
            raise RuntimeError(
                f"VM operation failed for: {', '.join(failures)}"
            )

        logging.info(
            "VM %s operation completed.",
            action
        )

    finally:
        credential.close()


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