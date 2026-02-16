#!/bin/bash
# Sealed Secrets Installation Script
# Helix Repair I11-1 — Install Sealed Secrets controller, convert secrets

set -euo pipefail

NAMESPACE="${NAMESPACE:-kube-system}"
VERSION="${SEALED_SECRETS_VERSION:-0.25.0}"

echo "==========================================="
echo " Sealed Secrets Installation"
echo "==========================================="

# 1. Install kubeseal CLI
echo "[1/4] Installing kubeseal CLI v${VERSION}..."
if ! command -v kubeseal &> /dev/null; then
  ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
  curl -sL "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${VERSION}/kubeseal-${VERSION}-linux-${ARCH}.tar.gz" | tar xz -C /tmp
  sudo install -m 755 /tmp/kubeseal /usr/local/bin/kubeseal
  echo "  ✅ kubeseal installed"
else
  echo "  ✅ kubeseal already installed ($(kubeseal --version))"
fi

# 2. Install Sealed Secrets controller
echo "[2/4] Installing Sealed Secrets controller..."
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm upgrade --install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace "$NAMESPACE" \
  --set fullnameOverride=sealed-secrets-controller \
  --wait --timeout 120s
echo "  ✅ Controller installed"

# 3. Verify controller is running
echo "[3/4] Verifying controller..."
kubectl rollout status deployment/sealed-secrets-controller -n "$NAMESPACE" --timeout=60s
echo "  ✅ Controller running"

# 4. Convert existing secrets
echo "[4/4] Converting existing secrets to SealedSecrets..."
TARGET_DIR="$(dirname "$0")/sealed-secrets"
mkdir -p "$TARGET_DIR"

for ns in idkit idkit-staging; do
  echo ""
  echo "  Processing namespace: $ns"
  SECRETS=$(kubectl get secrets -n "$ns" -o name --field-selector='type!=kubernetes.io/service-account-token' 2>/dev/null || echo "")
  
  for secret in $SECRETS; do
    SECRET_NAME=$(echo "$secret" | sed 's|secret/||')
    # Skip Helm and default secrets
    if [[ "$SECRET_NAME" == sh.helm.* ]] || [[ "$SECRET_NAME" == default-token-* ]]; then
      continue
    fi
    
    echo "    Sealing: $SECRET_NAME"
    kubectl get secret "$SECRET_NAME" -n "$ns" -o json | \
      kubeseal --format yaml > "$TARGET_DIR/${ns}-${SECRET_NAME}.yaml" 2>/dev/null || \
      echo "    ⚠ Skipped: $SECRET_NAME (cannot seal)"
  done
done

echo ""
echo "==========================================="
echo " Installation Complete!"
echo "==========================================="
echo " Sealed secrets saved to: $TARGET_DIR/"
echo " To use: kubectl apply -f $TARGET_DIR/<sealed-secret>.yaml"
echo ""
echo " New secrets workflow:"
echo "   1. Create normal K8s secret YAML"
echo "   2. Run: kubeseal < secret.yaml > sealed-secret.yaml"
echo "   3. Commit sealed-secret.yaml to git"
echo "   4. Apply: kubectl apply -f sealed-secret.yaml"
echo "==========================================="
