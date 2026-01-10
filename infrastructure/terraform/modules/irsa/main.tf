# IRSA Module for IDKit (IAM Roles for Service Accounts)

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "oidc_provider_arn" {
  description = "OIDC provider ARN"
  type        = string
}

variable "oidc_provider_url" {
  description = "OIDC provider URL (without https://)"
  type        = string
}

variable "service_accounts" {
  description = "Service account configurations"
  type = map(object({
    namespace = string
    policies  = list(string)
  }))
}

# IAM Roles for Service Accounts
resource "aws_iam_role" "service_account" {
  for_each = var.service_accounts

  name = "${var.cluster_name}-${each.key}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${var.oidc_provider_url}:sub" = "system:serviceaccount:${each.value.namespace}:${each.key}"
            "${var.oidc_provider_url}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    ServiceAccount = each.key
    Namespace      = each.value.namespace
    Cluster        = var.cluster_name
  }
}

# Attach policies to roles
resource "aws_iam_role_policy_attachment" "service_account" {
  for_each = {
    for item in flatten([
      for sa_name, sa_config in var.service_accounts : [
        for policy in sa_config.policies : {
          sa_name    = sa_name
          policy_arn = policy
        }
      ]
    ]) : "${item.sa_name}-${basename(item.policy_arn)}" => item
  }

  policy_arn = each.value.policy_arn
  role       = aws_iam_role.service_account[each.value.sa_name].name
}

# Outputs
output "role_arns" {
  value = { for k, v in aws_iam_role.service_account : k => v.arn }
}

output "role_names" {
  value = { for k, v in aws_iam_role.service_account : k => v.name }
}
