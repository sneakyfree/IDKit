# S3 Module for IDKit

variable "bucket_prefix" {
  description = "Prefix for bucket names"
  type        = string
}

variable "buckets" {
  description = "Bucket configurations"
  type = map(object({
    versioning = optional(bool, false)
    lifecycle_rules = optional(list(object({
      id      = string
      enabled = bool
      transition = optional(list(object({
        days          = number
        storage_class = string
      })), [])
      expiration = optional(object({
        days = number
      }), null)
    })), [])
  }))
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}

# S3 Buckets
resource "aws_s3_bucket" "main" {
  for_each = var.buckets

  bucket = "${var.bucket_prefix}-${each.key}"

  tags = merge(var.tags, {
    Name = "${var.bucket_prefix}-${each.key}"
  })
}

# Versioning
resource "aws_s3_bucket_versioning" "main" {
  for_each = var.buckets

  bucket = aws_s3_bucket.main[each.key].id

  versioning_configuration {
    status = each.value.versioning ? "Enabled" : "Disabled"
  }
}

# Server-side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  for_each = var.buckets

  bucket = aws_s3_bucket.main[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "main" {
  for_each = var.buckets

  bucket = aws_s3_bucket.main[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  for_each = { for k, v in var.buckets : k => v if length(v.lifecycle_rules) > 0 }

  bucket = aws_s3_bucket.main[each.key].id

  dynamic "rule" {
    for_each = each.value.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "transition" {
        for_each = rule.value.transition
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# CORS for media bucket
resource "aws_s3_bucket_cors_configuration" "media" {
  count  = contains(keys(var.buckets), "media") ? 1 : 0
  bucket = aws_s3_bucket.main["media"].id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# Outputs
output "bucket_ids" {
  value = { for k, v in aws_s3_bucket.main : k => v.id }
}

output "bucket_arns" {
  value = { for k, v in aws_s3_bucket.main : k => v.arn }
}

output "bucket_regional_domains" {
  value = { for k, v in aws_s3_bucket.main : k => v.bucket_regional_domain_name }
}
