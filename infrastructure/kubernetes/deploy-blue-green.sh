#!/bin/bash
#
# Blue-Green Deployment Script for IDKit
#
# Implements zero-downtime deployments using blue-green strategy
#
# Usage:
#   ./deploy-blue-green.sh [options]
#
# Options:
#   --target         Target environment (blue|green)
#   --version        Version to deploy
#   --namespace      Kubernetes namespace
#   --rollback       Rollback to previous deployment
#   --dry-run        Show what would be deployed
#   --help           Show this help message

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
NAMESPACE="idkit"
VERSION=""
TARGET=""
ROLLBACK=false
DRY_RUN=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target) TARGET="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        --namespace) NAMESPACE="$2"; shift 2 ;;
        --rollback) ROLLBACK=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help) head -18 "$0" | tail -14; exit 0 ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Get current active deployment (blue or green)
get_active_deployment() {
    kubectl get service idkit-api -n "$NAMESPACE" -o jsonpath='{.spec.selector.deployment}' 2>/dev/null || echo "blue"
}

# Get inactive deployment
get_inactive_deployment() {
    local active=$(get_active_deployment)
    if [ "$active" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy to target environment
deploy_to_target() {
    local target=$1
    local version=$2
    
    log_info "Deploying version ${version} to ${target} environment..."
    
    # Update deployment manifest
    local deployment_file="${SCRIPT_DIR}/blue-green/${target}-deployment.yaml"
    
    if [ ! -f "$deployment_file" ]; then
        log_error "Deployment file not found: $deployment_file"
        exit 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would apply: $deployment_file with version $version"
        return
    fi
    
    # Apply deployment with new version
    cat "$deployment_file" | \
        sed "s|IMAGE_TAG|${version}|g" | \
        kubectl apply -n "$NAMESPACE" -f -
    
    log_success "Deployment applied to ${target}"
}

# Wait for deployment to be ready
wait_for_deployment() {
    local target=$1
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would wait for ${target} deployment"
        return
    fi
    
    log_info "Waiting for ${target} deployment to be ready..."
    
    kubectl rollout status deployment/idkit-api-${target} -n "$NAMESPACE" --timeout=300s
    
    log_success "${target} deployment is ready"
}

# Health check the new deployment
health_check() {
    local target=$1
    local max_attempts=30
    local attempt=1
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would health check ${target}"
        return 0
    fi
    
    log_info "Running health checks on ${target}..."
    
    # Get the pod IP for internal testing
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l app=idkit-api,deployment="$target" -o jsonpath='{.items[0].metadata.name}')
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl exec -n "$NAMESPACE" "$pod_name" -- curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Switch traffic to target deployment
switch_traffic() {
    local target=$1
    
    log_info "Switching traffic to ${target}..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would update service selector to deployment=${target}"
        return
    fi
    
    # Patch the service to point to new deployment
    kubectl patch service idkit-api -n "$NAMESPACE" \
        -p "{\"spec\":{\"selector\":{\"deployment\":\"${target}\"}}}"
    
    log_success "Traffic switched to ${target}"
}

# Rollback to previous deployment
rollback() {
    local active=$(get_active_deployment)
    local inactive=$(get_inactive_deployment)
    
    log_warn "Rolling back from ${active} to ${inactive}..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would switch traffic back to ${inactive}"
        return
    fi
    
    # Switch traffic back
    switch_traffic "$inactive"
    
    log_success "Rollback complete - traffic now routed to ${inactive}"
}

# Clean up old deployment (optional)
cleanup_old() {
    local target=$1
    
    log_info "Scaling down old ${target} deployment..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would scale down ${target}"
        return
    fi
    
    kubectl scale deployment/idkit-api-${target} -n "$NAMESPACE" --replicas=0
    
    log_success "Old deployment scaled down"
}

# Print deployment status
print_status() {
    echo ""
    echo "=============================================="
    echo "  Blue-Green Deployment Status"
    echo "=============================================="
    echo ""
    
    local active=$(get_active_deployment)
    
    echo "  Active:   ${active}"
    echo "  Inactive: $(get_inactive_deployment)"
    echo "  Namespace: ${NAMESPACE}"
    echo ""
    
    if [ "$DRY_RUN" = false ]; then
        echo "Blue Deployment:"
        kubectl get deployment idkit-api-blue -n "$NAMESPACE" --no-headers 2>/dev/null || echo "  Not found"
        echo ""
        echo "Green Deployment:"
        kubectl get deployment idkit-api-green -n "$NAMESPACE" --no-headers 2>/dev/null || echo "  Not found"
    fi
    
    echo ""
    echo "=============================================="
}

# Main execution
main() {
    echo ""
    log_info "IDKit Blue-Green Deployment"
    echo ""
    
    # Handle rollback
    if [ "$ROLLBACK" = true ]; then
        rollback
        print_status
        exit 0
    fi
    
    # Validate inputs
    if [ -z "$VERSION" ]; then
        log_error "Version is required. Use --version flag."
        exit 1
    fi
    
    # Auto-detect target if not specified
    if [ -z "$TARGET" ]; then
        TARGET=$(get_inactive_deployment)
        log_info "Auto-selected target: ${TARGET}"
    fi
    
    # Deploy
    deploy_to_target "$TARGET" "$VERSION"
    wait_for_deployment "$TARGET"
    
    # Health check
    if ! health_check "$TARGET"; then
        log_error "Deployment failed health checks. Aborting."
        exit 1
    fi
    
    # Switch traffic
    switch_traffic "$TARGET"
    
    # Optional: scale down old deployment
    log_info "Old deployment kept running for quick rollback"
    log_info "Run with --rollback to switch back if needed"
    
    print_status
    
    echo ""
    log_success "Blue-green deployment complete!"
    log_info "Monitor the deployment and run with --rollback if issues arise"
}

main
