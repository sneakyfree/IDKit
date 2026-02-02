#!/bin/bash
#
# IDKit Infrastructure Master Deployment Script
#
# Deploys all IDKit infrastructure components to Kubernetes
#
# Usage:
#   ./deploy-all.sh [options]
#
# Options:
#   --dry-run         Show what would be deployed without applying
#   --skip-secrets    Skip sealed secrets deployment
#   --skip-monitoring Skip monitoring stack deployment
#   --namespace       Application namespace (default: idkit)
#   --help            Show this help message

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
DRY_RUN=false
SKIP_SECRETS=false
SKIP_MONITORING=false
NAMESPACE="idkit"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --skip-secrets) SKIP_SECRETS=true; shift ;;
        --skip-monitoring) SKIP_MONITORING=true; shift ;;
        --namespace) NAMESPACE="$2"; shift 2 ;;
        --help) head -17 "$0" | tail -13; exit 0 ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Build dry-run arg
DRY_RUN_ARG=""
if [ "$DRY_RUN" = true ]; then
    DRY_RUN_ARG="--dry-run"
    log_warn "Running in dry-run mode"
fi

header() {
    echo ""
    echo "=============================================="
    echo "  IDKit Infrastructure Deployment"
    echo "=============================================="
    echo ""
    echo "  Namespace:       ${NAMESPACE}"
    echo "  Dry Run:         ${DRY_RUN}"
    echo "  Skip Secrets:    ${SKIP_SECRETS}"
    echo "  Skip Monitoring: ${SKIP_MONITORING}"
    echo ""
}

check_cluster() {
    log_info "Checking Kubernetes cluster connection..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Connected to cluster: $(kubectl config current-context)"
}

create_namespace() {
    log_info "Creating namespace: ${NAMESPACE}"
    
    if kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Namespace already exists"
    else
        if [ "$DRY_RUN" = false ]; then
            kubectl create namespace "${NAMESPACE}"
            log_success "Namespace created"
        else
            log_info "[DRY-RUN] Would create namespace"
        fi
    fi
}

deploy_sealed_secrets() {
    if [ "$SKIP_SECRETS" = true ]; then
        log_info "Skipping sealed secrets (--skip-secrets)"
        return
    fi
    
    log_info "Deploying Sealed Secrets..."
    
    if [ -f "${SCRIPT_DIR}/deploy-sealed-secrets.sh" ]; then
        chmod +x "${SCRIPT_DIR}/deploy-sealed-secrets.sh"
        "${SCRIPT_DIR}/deploy-sealed-secrets.sh" ${DRY_RUN_ARG}
    else
        log_warn "deploy-sealed-secrets.sh not found, skipping"
    fi
}

deploy_core_infrastructure() {
    log_info "Deploying core infrastructure..."
    
    KUBECTL_CMD="kubectl apply -n ${NAMESPACE}"
    if [ "$DRY_RUN" = true ]; then
        KUBECTL_CMD="kubectl apply --dry-run=client -n ${NAMESPACE}"
    fi
    
    # Apply in order
    resources=(
        "namespace.yaml"
        "configmap.yaml"
        "secrets.yaml"
        "database-deployment.yaml"
        "api-deployment.yaml"
        "celery-deployment.yaml"
        "frontend-deployment.yaml"
        "ingress.yaml"
    )
    
    for resource in "${resources[@]}"; do
        if [ -f "${SCRIPT_DIR}/${resource}" ]; then
            log_info "Applying ${resource}..."
            $KUBECTL_CMD -f "${SCRIPT_DIR}/${resource}"
        else
            log_warn "${resource} not found, skipping"
        fi
    done
    
    log_success "Core infrastructure deployed"
}

deploy_gpu_workers() {
    log_info "Deploying GPU workers..."
    
    if [ -f "${SCRIPT_DIR}/gpu-workers-deployment.yaml" ]; then
        if [ "$DRY_RUN" = true ]; then
            kubectl apply --dry-run=client -n "${NAMESPACE}" -f "${SCRIPT_DIR}/gpu-workers-deployment.yaml"
        else
            kubectl apply -n "${NAMESPACE}" -f "${SCRIPT_DIR}/gpu-workers-deployment.yaml"
        fi
        log_success "GPU workers deployed"
    else
        log_warn "GPU workers deployment not found"
    fi
}

deploy_monitoring() {
    if [ "$SKIP_MONITORING" = true ]; then
        log_info "Skipping monitoring (--skip-monitoring)"
        return
    fi
    
    log_info "Deploying monitoring stack..."
    
    if [ -f "${SCRIPT_DIR}/deploy-monitoring.sh" ]; then
        chmod +x "${SCRIPT_DIR}/deploy-monitoring.sh"
        "${SCRIPT_DIR}/deploy-monitoring.sh" ${DRY_RUN_ARG}
    else
        log_warn "deploy-monitoring.sh not found, skipping"
    fi
}

wait_for_pods() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would wait for pods"
        return
    fi
    
    log_info "Waiting for pods to be ready..."
    
    kubectl wait --for=condition=ready pod -l app=idkit-api -n "${NAMESPACE}" --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=idkit-frontend -n "${NAMESPACE}" --timeout=300s || true
    
    log_success "All pods ready"
}

print_summary() {
    echo ""
    echo "=============================================="
    echo "  Deployment Complete"
    echo "=============================================="
    echo ""
    
    if [ "$DRY_RUN" = false ]; then
        echo "Pods:"
        kubectl get pods -n "${NAMESPACE}" --no-headers 2>/dev/null | head -10
        echo ""
        echo "Services:"
        kubectl get svc -n "${NAMESPACE}" --no-headers 2>/dev/null | head -10
    fi
    
    echo ""
    echo "Next steps:"
    echo "  - Check pod status: kubectl get pods -n ${NAMESPACE}"
    echo "  - View logs: kubectl logs -f deployment/idkit-api -n ${NAMESPACE}"
    echo "  - Access via ingress or port-forward"
    echo ""
    echo "=============================================="
}

main() {
    header
    check_cluster
    create_namespace
    deploy_sealed_secrets
    deploy_core_infrastructure
    deploy_gpu_workers
    deploy_monitoring
    wait_for_pods
    print_summary
}

main
