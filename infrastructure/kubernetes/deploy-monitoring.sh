#!/bin/bash
#
# IDKit Monitoring Stack Deployment Script
#
# Deploys Prometheus, Grafana, and Alertmanager to Kubernetes
#
# Usage:
#   ./deploy-monitoring.sh [options]
#
# Options:
#   --dry-run     Show what would be deployed without applying
#   --namespace   Override the default namespace (monitoring)
#   --help        Show this help message

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="monitoring"
DRY_RUN=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="${SCRIPT_DIR}/monitoring"

# Function to print colored output
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
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --help)
            head -20 "$0" | tail -15
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
    
    if ! command -v kustomize &> /dev/null; then
        log_warn "kustomize not found, using kubectl kustomize"
        KUSTOMIZE="kubectl kustomize"
    else
        KUSTOMIZE="kustomize"
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace ${NAMESPACE}..."
    
    if kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Namespace ${NAMESPACE} already exists"
    else
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY-RUN] Would create namespace: ${NAMESPACE}"
        else
            kubectl create namespace "${NAMESPACE}"
            log_success "Namespace ${NAMESPACE} created"
        fi
    fi
}

# Generate Grafana password secret
setup_grafana_secret() {
    log_info "Setting up Grafana admin password..."
    
    if [ -z "${GRAFANA_ADMIN_PASSWORD:-}" ]; then
        GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
        log_warn "Generated random Grafana password: ${GRAFANA_ADMIN_PASSWORD}"
        log_warn "Please save this password securely!"
    fi
    
    export GRAFANA_ADMIN_PASSWORD
}

# Deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    if [ ! -d "${MONITORING_DIR}" ]; then
        log_error "Monitoring directory not found: ${MONITORING_DIR}"
        exit 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would apply the following resources:"
        $KUSTOMIZE build "${MONITORING_DIR}" | envsubst
    else
        $KUSTOMIZE build "${MONITORING_DIR}" | envsubst | kubectl apply -f -
        log_success "Monitoring stack deployed"
    fi
}

# Wait for deployments
wait_for_ready() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would wait for deployments to be ready"
        return
    fi
    
    log_info "Waiting for deployments to be ready..."
    
    kubectl rollout status deployment/prometheus -n "${NAMESPACE}" --timeout=300s || true
    kubectl rollout status deployment/grafana -n "${NAMESPACE}" --timeout=300s || true
    kubectl rollout status deployment/alertmanager -n "${NAMESPACE}" --timeout=300s || true
    
    log_success "All monitoring components are ready"
}

# Print access information
print_access_info() {
    echo ""
    echo "=============================================="
    echo "  IDKit Monitoring Stack Deployed"
    echo "=============================================="
    echo ""
    echo "Access URLs (port-forward required):"
    echo ""
    echo "  Prometheus:"
    echo "    kubectl port-forward svc/prometheus 9090:9090 -n ${NAMESPACE}"
    echo "    URL: http://localhost:9090"
    echo ""
    echo "  Grafana:"
    echo "    kubectl port-forward svc/grafana 3000:3000 -n ${NAMESPACE}"
    echo "    URL: http://localhost:3000"
    echo "    Username: admin"
    echo "    Password: ${GRAFANA_ADMIN_PASSWORD:-<check-secret>}"
    echo ""
    echo "  Alertmanager:"
    echo "    kubectl port-forward svc/alertmanager 9093:9093 -n ${NAMESPACE}"
    echo "    URL: http://localhost:9093"
    echo ""
    echo "=============================================="
}

# Main execution
main() {
    echo ""
    log_info "IDKit Monitoring Stack Deployment"
    echo ""
    
    check_prerequisites
    create_namespace
    setup_grafana_secret
    deploy_monitoring
    wait_for_ready
    print_access_info
}

main
