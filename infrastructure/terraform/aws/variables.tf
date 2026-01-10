# IDKit AWS Infrastructure Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# EKS Configuration
variable "eks_cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.28"
}

variable "eks_general_instance_types" {
  description = "Instance types for general EKS nodes"
  type        = list(string)
  default     = ["m6i.xlarge", "m5.xlarge"]
}

variable "eks_general_min_size" {
  description = "Minimum number of general nodes"
  type        = number
  default     = 2
}

variable "eks_general_max_size" {
  description = "Maximum number of general nodes"
  type        = number
  default     = 10
}

variable "eks_general_desired_size" {
  description = "Desired number of general nodes"
  type        = number
  default     = 3
}

variable "eks_gpu_instance_types" {
  description = "Instance types for GPU EKS nodes"
  type        = list(string)
  default     = ["g4dn.xlarge", "g5.xlarge"]
}

variable "eks_gpu_min_size" {
  description = "Minimum number of GPU nodes"
  type        = number
  default     = 0
}

variable "eks_gpu_max_size" {
  description = "Maximum number of GPU nodes"
  type        = number
  default     = 5
}

variable "eks_gpu_desired_size" {
  description = "Desired number of GPU nodes"
  type        = number
  default     = 1
}

# RDS Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for CloudFront"
  type        = string
}

variable "create_dns_zone" {
  description = "Whether to create a new Route53 zone"
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  description = "Existing Route53 zone ID (if not creating new)"
  type        = string
  default     = ""
}

# Secrets
variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "heygen_api_key" {
  description = "HeyGen API key"
  type        = string
  sensitive   = true
}

variable "elevenlabs_api_key" {
  description = "ElevenLabs API key"
  type        = string
  sensitive   = true
}
