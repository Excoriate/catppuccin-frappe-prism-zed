# Provider-free Terraform: this fixture plans no resources.
terraform {
  required_version = ">= 1.5.0"
}

variable "name" {
  description = "Stable fixture label\nwithout infrastructure effects"
  type        = string
  default     = "zed"
  validation {
    condition     = length(trimspace(var.name)) > 0
    error_message = "name must not be blank"
  }
}

variable "values" {
  type    = list(number)
  default = [21, 21]
}

variable "active" {
  type    = bool
  default = true
}

locals {
  total = sum(var.values)
  state = var.active && local.total >= 40 ? "ready" : "idle"
  label = "${var.name}:${local.total}:${local.state}"
  tags = {
    owner = var.name
    mode  = local.state
  }
  doubled = [for value in var.values : value * 2 if value > 0]
  selected = {
    for key, value in local.tags : upper(key) => value
  }
  note = <<-TEXT
    theme "${var.name}"
    total = ${local.total}
  TEXT
}

output "label" {
  description = "Expected semantic oracle: zed:42:ready"
  value       = local.label
}

output "details" {
  value = { doubled = local.doubled, tags = local.selected }
}
