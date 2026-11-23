variable "subscription_id" {
  description = "Azure subscription ID."
  type        = string
}

variable "location" {
  description = "Azure region. Flex Consumption support must be confirmed in this region before apply."
  type        = string
  default     = "South India"
}

variable "function_resource_group_name" {
  type    = string
  default = "rg-vm-automation"
}

variable "vm_resource_group_name" {
  type    = string
  default = "rg-vm-automation-target"
}

variable "function_app_name_prefix" {
  type    = string
  default = "func-vm-auto"
}

variable "vm_names" {
  description = "Names of the development VMs to create."
  type        = set(string)
  default     = ["vm-dev-01", "vm-dev-02"]
}

variable "vm_size" {
  description = "Choose a size available in South India and allowed by your subscription quota."
  type        = string
  default     = "Standard_B2s"
}

variable "vm_admin_username" {
  type    = string
  default = "azureadmin"
}

variable "admin_ssh_public_key" {
  description = "Contents of your SSH public key (for example, ~/.ssh/id_rsa.pub)."
  type        = string
  sensitive   = true
}

variable "admin_source_cidr" {
  description = "Your trusted public IP in CIDR format, for example 203.0.113.10/32. Do not use 0.0.0.0/0."
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_source_cidr, 0)) && var.admin_source_cidr != "0.0.0.0/0"
    error_message = "Provide a valid restricted CIDR. SSH from 0.0.0.0/0 is not allowed."
  }
}

variable "target_environment" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "qa", "prod"], lower(var.target_environment))
    error_message = "target_environment must be dev, qa, or prod."
  }
}

variable "dry_run" {
  description = "Keep true until the VM selection and permissions have been verified."
  type        = bool
  default     = true
}

variable "start_schedule_utc" {
  description = "Timer NCRONTAB schedule in UTC. 02:30 UTC = 08:00 IST."
  type        = string
  default     = "0 30 2 * * *"
}

variable "deallocate_schedule_utc" {
  description = "Timer NCRONTAB schedule in UTC. 14:30 UTC = 20:00 IST."
  type        = string
  default     = "0 30 14 * * *"
}

variable "maximum_instance_count" {
  type    = number
  default = 10
}

variable "instance_memory_in_mb" {
  type    = number
  default = 2048
}
