# IDKit AWS Infrastructure Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

# EKS Outputs
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate" {
  description = "EKS cluster CA certificate"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "eks_kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
}

output "rds_port" {
  description = "RDS port"
  value       = module.rds.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.database_name
}

# ElastiCache Outputs
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.endpoint
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.port
}

# S3 Outputs
output "s3_media_bucket" {
  description = "S3 media bucket name"
  value       = module.s3.bucket_ids["media"]
}

output "s3_models_bucket" {
  description = "S3 models bucket name"
  value       = module.s3.bucket_ids["models"]
}

output "s3_backups_bucket" {
  description = "S3 backups bucket name"
  value       = module.s3.bucket_ids["backups"]
}

# CloudFront Outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name"
  value       = module.cloudfront.domain_name
}

# ECR Outputs
output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    for name, repo in aws_ecr_repository.repositories : name => repo.repository_url
  }
}

# DNS Outputs
output "api_endpoint" {
  description = "API endpoint"
  value       = "https://api.${var.domain_name}"
}

output "cdn_endpoint" {
  description = "CDN endpoint"
  value       = "https://cdn.${var.domain_name}"
}

# Secrets Outputs
output "secrets_arn" {
  description = "Secrets Manager ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

# IRSA Outputs
output "service_account_roles" {
  description = "IAM roles for service accounts"
  value       = module.irsa.role_arns
}
