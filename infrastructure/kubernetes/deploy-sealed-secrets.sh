#!/bin/bash
#
# IDKit Sealed Secrets Deployment Script
#
# Installs Sealed Secrets controller and generates sealed secrets
#
# Usage:
#   ./deploy-sealed-secrets.sh [options]
#
# Options:
#   --dry-run      Show what would be deployed without applying
#   --generate     Generate new sealed secrets from templates
#   --namespace    Override the default namespace (default)
#   --help         Show this help message

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
NAMESPACE="default"
DRY_RUN=false
GENERATE_SECRETS=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEALED_CONTROLLER_VERSION="v0.24.5"

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --generate)
            GENERATE_SECRETS=true
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --help)
            head -16 "$0" | tail -12
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check for kubeseal
    if ! command -v kubeseal &> /dev/null; then
        log_warn "kubeseal CLI not found. Install with:"
        log_warn "  brew install kubeseal  # macOS"
        log_warn "  wget https://github.com/bitnami-labs/sealed-secrets/releases/download/${SEALED_CONTROLLER_VERSION}/kubeseal-linux-amd64 -O kubeseal"
        if [ "$GENERATE_SECRETS" = true ]; then
            log_error "kubeseal is required for --generate"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

# Deploy Sealed Secrets controller
deploy_controller() {
    log_info "Deploying Sealed Secrets controller..."
    
    CONTROLLER_URL="https://github.com/bitnami-labs/sealed-secrets/releases/download/${SEALED_CONTROLLER_VERSION}/controller.yaml"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would apply: ${CONTROLLER_URL}"
    else
        kubectl apply -f "${CONTROLLER_URL}"
        log_success "Sealed Secrets controller deployed"
    fi
}

# Wait for controller to be ready
wait_for_controller() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would wait for controller to be ready"
        return
    fi
    
    log_info "Waiting for Sealed Secrets controller..."
    kubectl rollout status deployment/sealed-secrets-controller -n kube-system --timeout=180s
    
    log_success "Sealed Secrets controller is ready"
}

# Fetch public key for sealing
fetch_public_key() {
    log_info "Fetching cluster public key..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would fetch public key"
        return
    fi
    
    kubeseal --fetch-cert > "${SCRIPT_DIR}/sealed-secrets-public-key.pem"
    log_success "Public key saved to: sealed-secrets-public-key.pem"
    log_warn "Keep this key safe - you'll need it to seal secrets"
}

# Generate sealed secrets from templates
generate_sealed_secrets() {
    log_info "Generating sealed secrets..."
    
    TEMPLATES_FILE="${SCRIPT_DIR}/sealed-secrets-templates.yaml"
    OUTPUT_FILE="${SCRIPT_DIR}/sealed-secrets-generated.yaml"
    
    if [ ! -f "${TEMPLATES_FILE}" ]; then
        log_error "Templates file not found: ${TEMPLATES_FILE}"
        exit 1
    fi
    
    # Check for required environment variables
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "OPENAI_API_KEY"
        "STRIPE_SECRET_KEY"
        "STRIPE_WEBHOOK_SECRET"
        "JWT_SECRET"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warn "The following environment variables are not set:"
        for var in "${missing_vars[@]}"; do
            log_warn "  - $var"
        done
        log_info "Using placeholder values - update before production deployment"
    fi
    
    # Create temporary secret
    TEMP_SECRET=$(mktemp)
    cat > "${TEMP_SECRET}" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: idkit-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  DATABASE_URL: "${DATABASE_URL:-postgresql://user:pass@localhost:5432/idkit}"
  REDIS_URL: "${REDIS_URL:-redis://localhost:6379/0}"
  OPENAI_API_KEY: "${OPENAI_API_KEY:-sk-placeholder}"
  STRIPE_SECRET_KEY: "${STRIPE_SECRET_KEY:-sk_test_placeholder}"
  STRIPE_WEBHOOK_SECRET: "${STRIPE_WEBHOOK_SECRET:-whsec_placeholder}"
  JWT_SECRET: "${JWT_SECRET:-$(openssl rand -hex 32)}"
  ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY:-}"
  ELEVENLABS_API_KEY: "${ELEVENLABS_API_KEY:-}"
  AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID:-}"
  AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY:-}"
EOF
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would seal the following secret:"
        cat "${TEMP_SECRET}"
    else
        # Seal the secret
        kubeseal --format yaml < "${TEMP_SECRET}" > "${OUTPUT_FILE}"
        log_success "Sealed secrets generated: ${OUTPUT_FILE}"
    fi
    
    # Cleanup
    rm -f "${TEMP_SECRET}"
}

# Apply sealed secrets
apply_sealed_secrets() {
    OUTPUT_FILE="${SCRIPT_DIR}/sealed-secrets-generated.yaml"
    
    if [ ! -f "${OUTPUT_FILE}" ]; then
        log_warn "No sealed secrets file found. Run with --generate first."
        return
    fi
    
    log_info "Applying sealed secrets..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would apply: ${OUTPUT_FILE}"
    else
        kubectl apply -f "${OUTPUT_FILE}" -n "${NAMESPACE}"
        log_success "Sealed secrets applied"
    fi
}

# Print usage information
print_usage() {
    echo ""
    echo "=============================================="
    echo "  Sealed Secrets Deployment Complete"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Set your secret values as environment variables:"
    echo "     export DATABASE_URL='postgresql://user:pass@host:5432/db'"
    echo "     export OPENAI_API_KEY='sk-your-key'"
    echo "     export STRIPE_SECRET_KEY='sk_live_your-key'"
    echo "     ... (see script for full list)"
    echo ""
    echo "  2. Generate sealed secrets:"
    echo "     ./deploy-sealed-secrets.sh --generate"
    echo ""
    echo "  3. Apply to cluster:"
    echo "     kubectl apply -f sealed-secrets-generated.yaml"
    echo ""
    echo "  4. Verify secrets:"
    echo "     kubectl get sealedsecrets -n ${NAMESPACE}"
    echo "     kubectl get secrets -n ${NAMESPACE}"
    echo ""
    echo "NOTE: Keep sealed-secrets-public-key.pem safe!"
    echo "You'll need it to seal new secrets."
    echo ""
    echo "=============================================="
}

# Main execution
main() {
    echo ""
    log_info "IDKit Sealed Secrets Deployment"
    echo ""
    
    check_prerequisites
    
    if [ "$GENERATE_SECRETS" = true ]; then
        generate_sealed_secrets
    else
        deploy_controller
        wait_for_controller
        fetch_public_key
        apply_sealed_secrets
        print_usage
    fi
}

main
