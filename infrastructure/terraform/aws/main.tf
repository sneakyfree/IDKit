# IDKit AWS Infrastructure
# Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "idkit-terraform-state"
    key            = "aws/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "idkit-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "IDKit"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "../modules/vpc"

  name               = "idkit-${var.environment}"
  cidr               = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true
  enable_dns_support     = true

  tags = local.common_tags
}

# EKS Cluster
module "eks" {
  source = "../modules/eks"

  cluster_name    = "idkit-${var.environment}"
  cluster_version = var.eks_cluster_version

  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids

  # Node groups
  node_groups = {
    general = {
      instance_types = var.eks_general_instance_types
      min_size       = var.eks_general_min_size
      max_size       = var.eks_general_max_size
      desired_size   = var.eks_general_desired_size
      disk_size      = 100
    }
    gpu = {
      instance_types = var.eks_gpu_instance_types
      min_size       = var.eks_gpu_min_size
      max_size       = var.eks_gpu_max_size
      desired_size   = var.eks_gpu_desired_size
      disk_size      = 200
      ami_type       = "AL2_x86_64_GPU"
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }

  tags = local.common_tags
}

# RDS PostgreSQL
module "rds" {
  source = "../modules/rds"

  identifier     = "idkit-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"

  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  database_name = "idkit"
  username      = "idkit_admin"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.database_security_group_id]

  multi_az               = var.environment == "production"
  backup_retention_period = var.environment == "production" ? 30 : 7
  deletion_protection    = var.environment == "production"

  performance_insights_enabled = var.environment == "production"

  tags = local.common_tags
}

# ElastiCache Redis
module "elasticache" {
  source = "../modules/elasticache"

  cluster_id      = "idkit-${var.environment}"
  engine          = "redis"
  engine_version  = "7.0"
  node_type       = var.redis_node_type
  num_cache_nodes = var.environment == "production" ? 3 : 1

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.cache_security_group_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  tags = local.common_tags
}

# S3 Buckets
module "s3" {
  source = "../modules/s3"

  bucket_prefix = "idkit-${var.environment}"

  buckets = {
    media = {
      versioning = true
      lifecycle_rules = [
        {
          id      = "archive-old-media"
          enabled = true
          transition = [
            {
              days          = 90
              storage_class = "STANDARD_IA"
            },
            {
              days          = 365
              storage_class = "GLACIER"
            }
          ]
        }
      ]
    }
    models = {
      versioning = true
    }
    backups = {
      versioning = true
      lifecycle_rules = [
        {
          id      = "delete-old-backups"
          enabled = true
          expiration = {
            days = 90
          }
        }
      ]
    }
  }

  tags = local.common_tags
}

# CloudFront CDN
module "cloudfront" {
  source = "../modules/cloudfront"

  domain_name         = var.domain_name
  s3_bucket_name      = module.s3.bucket_ids["media"]
  s3_bucket_domain    = module.s3.bucket_regional_domains["media"]
  certificate_arn     = var.acm_certificate_arn
  price_class         = var.environment == "production" ? "PriceClass_All" : "PriceClass_100"

  tags = local.common_tags
}

# Secrets Manager
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "idkit/${var.environment}/app-secrets"
  description = "IDKit application secrets"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    database_url     = module.rds.connection_string
    redis_url        = module.elasticache.connection_string
    jwt_secret       = var.jwt_secret
    openai_api_key   = var.openai_api_key
    heygen_api_key   = var.heygen_api_key
    elevenlabs_api_key = var.elevenlabs_api_key
  })
}

# IAM Roles for Service Accounts (IRSA)
module "irsa" {
  source = "../modules/irsa"

  cluster_name      = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url

  service_accounts = {
    idkit-api = {
      namespace = "idkit"
      policies = [
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
        "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
      ]
    }
    idkit-worker = {
      namespace = "idkit-gpu"
      policies = [
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
      ]
    }
  }
}

# ECR Repositories
resource "aws_ecr_repository" "repositories" {
  for_each = toset([
    "idkit-api",
    "idkit-frontend",
    "idkit-gpu-worker-avatar",
    "idkit-gpu-worker-voice",
    "idkit-gpu-worker-llm",
  ])

  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

# Lifecycle policy for ECR
resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each   = aws_ecr_repository.repositories
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Route53 DNS
resource "aws_route53_zone" "main" {
  count = var.create_dns_zone ? 1 : 0
  name  = var.domain_name

  tags = local.common_tags
}

resource "aws_route53_record" "api" {
  zone_id = var.create_dns_zone ? aws_route53_zone.main[0].zone_id : var.route53_zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.eks.load_balancer_hostname
    zone_id                = module.eks.load_balancer_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "cdn" {
  zone_id = var.create_dns_zone ? aws_route53_zone.main[0].zone_id : var.route53_zone_id
  name    = "cdn.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.cloudfront.domain_name
    zone_id                = module.cloudfront.hosted_zone_id
    evaluate_target_health = false
  }
}

# Local variables
locals {
  common_tags = {
    Project     = "IDKit"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
