# ROAD HOME IMPLEMENTATION PLAN
## IDKit Platform - Complete Gap Closure & UX Excellence

---

## STRATEGY SUMMARY

This plan closes 23 missing features and elevates 8 underperforming features to 10/10 UX across IDKit's 130-feature platform. Execution follows strict dependency ordering: infrastructure first (CI/CD, monitoring, secrets), then revenue-critical features (payouts, analytics), then user-facing gaps (customization, i18n), then polish. Each task is written for mechanical execution by lower-reasoning models with zero ambiguity. Quality gates enforce: no crashes, <200ms P95 latency, WCAG AA compliance, 80%+ test coverage, and complete error handling. Total scope: 4 phases, 12 epics, 67 tasks. Estimated calendar time: 12-16 weeks with 2-3 engineers.

---

## TABLE OF CONTENTS

1. [Definition of Done](#definition-of-done)
2. [Phase 1: Infrastructure Foundation](#phase-1-infrastructure-foundation)
3. [Phase 2: Revenue & Analytics](#phase-2-revenue--analytics)
4. [Phase 3: User Experience Gaps](#phase-3-user-experience-gaps)
5. [Phase 4: Polish to 10/10](#phase-4-polish-to-1010)
6. [Top 10 Highest-Leverage Improvements](#top-10-highest-leverage-improvements)
7. [Rollout Plan](#rollout-plan)
8. [Risk Register](#risk-register)

---

## DEFINITION OF DONE

Every task must meet ALL criteria before marking complete:

### Functional Requirements
- [ ] Feature works exactly as specified in acceptance criteria
- [ ] All edge cases handled (empty states, errors, loading, permissions)
- [ ] No console errors or warnings in browser/mobile
- [ ] No unhandled exceptions in backend logs

### Performance Requirements
- [ ] API endpoints respond in <200ms P95
- [ ] Frontend pages achieve Lighthouse Performance score ≥90
- [ ] No memory leaks (heap stable over 10-minute session)
- [ ] Images lazy-loaded and optimized (WebP, responsive)

### Accessibility Requirements
- [ ] WCAG 2.1 AA compliant (test with axe-core)
- [ ] Keyboard navigation works for all interactive elements
- [ ] Screen reader announces all state changes
- [ ] Color contrast ratio ≥4.5:1 for text

### Quality Requirements
- [ ] Unit test coverage ≥80% for new code
- [ ] Integration tests cover happy path + 2 error paths
- [ ] E2E test covers critical user journey
- [ ] No TypeScript `any` types (use proper typing)
- [ ] No ESLint/Pylint errors or warnings

### UX Requirements
- [ ] Follows design system (colors, spacing, typography)
- [ ] Loading states show skeleton or spinner
- [ ] Error states show actionable message + retry option
- [ ] Success states show confirmation feedback
- [ ] Mobile responsive (works on 320px-1440px widths)

### Observability Requirements
- [ ] Prometheus metrics exposed for key operations
- [ ] Structured JSON logs for all errors with correlation ID
- [ ] Grafana dashboard panel added if new service/feature

### Documentation Requirements
- [ ] API endpoints documented in OpenAPI schema
- [ ] Complex logic has inline comments explaining "why"
- [ ] README updated if new environment variables or setup steps

---

## PHASE 1: INFRASTRUCTURE FOUNDATION

**Goal:** Establish reliable deployment, monitoring, and security infrastructure.
**Priority:** FIX FIRST (blocks all other work)
**Duration:** 2-3 weeks

---

### EPIC 1.1: CI/CD Pipeline

**Current State:** No automated deployment pipeline exists.
**Target State:** Fully automated test, build, deploy pipeline with staging and production environments.

---

#### TASK 1.1.1: Create GitHub Actions CI Workflow

**Goal:** Automate testing on every push and pull request.

**Exact Scope:**
- Create `.github/workflows/ci.yml`
- Run backend tests (pytest)
- Run frontend tests (Jest)
- Run mobile tests (Jest)
- Run linting (ESLint, Pylint, Ruff)
- Run type checking (TypeScript, mypy)
- Block merge if any check fails

**Dependencies:** None

**Implementation Steps:**

1. Create file `.github/workflows/ci.yml` with this exact content:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: idkit_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run linting
        run: |
          cd backend
          ruff check .
          mypy app --ignore-missing-imports
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/idkit_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret-key-for-ci
          ENVIRONMENT: test
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-fail-under=50

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run linting
        run: |
          cd frontend
          npm run lint
      - name: Run type check
        run: |
          cd frontend
          npm run type-check
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

  mobile-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json
      - name: Install dependencies
        run: |
          cd mobile
          npm ci
      - name: Run linting
        run: |
          cd mobile
          npm run lint
      - name: Run tests
        run: |
          cd mobile
          npm test -- --watchAll=false
```

2. Add `type-check` script to `frontend/package.json` if not exists:
```json
{
  "scripts": {
    "type-check": "tsc --noEmit"
  }
}
```

3. Add `requirements-dev.txt` to backend if not exists:
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
ruff>=0.1.0
mypy>=1.5.0
```

**Acceptance Criteria:**
- [ ] Push to any branch triggers CI workflow
- [ ] All 3 test jobs run in parallel
- [ ] Failed tests block PR merge
- [ ] Coverage reports generated
- [ ] Workflow completes in <10 minutes

**UI/UX Requirements:** N/A (infrastructure)

**Backend Requirements:**
- All existing tests pass
- No import errors with test database

**Frontend Requirements:**
- All existing tests pass
- No TypeScript errors

**Integration Requirements:**
- GitHub Actions has access to run workflows
- Branch protection rules enabled on main

**Testing Requirements:**
- Create test PR to verify workflow runs
- Intentionally break test to verify blocking works

**Observability Requirements:**
- GitHub Actions provides built-in logs
- Test results visible in PR checks

**Risks and Mitigations:**
| Risk | Mitigation |
|------|------------|
| Tests flaky due to timing | Add retry logic, increase timeouts |
| Docker rate limiting | Use GitHub Container Registry cache |
| Secrets exposed in logs | Use GitHub secrets, never echo |

---

#### TASK 1.1.2: Create GitHub Actions CD Workflow

**Goal:** Automate deployment to staging on develop branch, production on main branch.

**Exact Scope:**
- Create `.github/workflows/cd.yml`
- Build Docker images for backend, frontend, GPU workers
- Push images to container registry
- Deploy to Kubernetes cluster
- Run smoke tests after deployment

**Dependencies:**
- TASK 1.1.1 (CI must pass before CD runs)
- TASK 1.1.3 (Container registry configured)

**Implementation Steps:**

1. Create file `.github/workflows/cd.yml`:

```yaml
name: CD

on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}/idkit

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.set-env.outputs.environment }}
      namespace: ${{ steps.set-env.outputs.namespace }}
    steps:
      - id: set-env
        run: |
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "environment=${{ github.event.inputs.environment }}" >> $GITHUB_OUTPUT
            if [[ "${{ github.event.inputs.environment }}" == "production" ]]; then
              echo "namespace=idkit" >> $GITHUB_OUTPUT
            else
              echo "namespace=idkit-staging" >> $GITHUB_OUTPUT
            fi
          elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=production" >> $GITHUB_OUTPUT
            echo "namespace=idkit" >> $GITHUB_OUTPUT
          else
            echo "environment=staging" >> $GITHUB_OUTPUT
            echo "namespace=idkit-staging" >> $GITHUB_OUTPUT
          fi

  build-backend:
    needs: determine-environment
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      image: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-backend
          tags: |
            type=sha,prefix=
            type=ref,event=branch
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-frontend:
    needs: determine-environment
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      image: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-frontend
          tags: |
            type=sha,prefix=
            type=ref,event=branch
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NEXT_PUBLIC_API_URL=${{ needs.determine-environment.outputs.environment == 'production' && 'https://api.idkit.io' || 'https://api-staging.idkit.io' }}

  build-gpu-workers:
    needs: determine-environment
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        worker: [avatar, voice, llm]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-gpu-${{ matrix.worker }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./gpu-workers/${{ matrix.worker }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: [determine-environment, build-backend, build-frontend, build-gpu-workers]
    runs-on: ubuntu-latest
    environment: ${{ needs.determine-environment.outputs.environment }}
    steps:
      - uses: actions/checkout@v4
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'
      - name: Configure kubectl
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > ~/.kube/config
      - name: Deploy to Kubernetes
        run: |
          NAMESPACE=${{ needs.determine-environment.outputs.namespace }}
          SHA=${{ github.sha }}
          SHORT_SHA=${SHA:0:7}

          # Update backend deployment
          kubectl set image deployment/idkit-api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-backend:sha-${SHORT_SHA} \
            -n ${NAMESPACE}

          # Update frontend deployment
          kubectl set image deployment/idkit-frontend \
            frontend=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-frontend:sha-${SHORT_SHA} \
            -n ${NAMESPACE}

          # Update GPU workers
          kubectl set image deployment/avatar-worker \
            worker=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-gpu-avatar:sha-${SHORT_SHA} \
            -n idkit-gpu
          kubectl set image deployment/voice-worker \
            worker=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-gpu-voice:sha-${SHORT_SHA} \
            -n idkit-gpu
          kubectl set image deployment/llm-worker \
            worker=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-gpu-llm:sha-${SHORT_SHA} \
            -n idkit-gpu

          # Wait for rollout
          kubectl rollout status deployment/idkit-api -n ${NAMESPACE} --timeout=300s
          kubectl rollout status deployment/idkit-frontend -n ${NAMESPACE} --timeout=300s
      - name: Run smoke tests
        run: |
          API_URL=${{ needs.determine-environment.outputs.environment == 'production' && 'https://api.idkit.io' || 'https://api-staging.idkit.io' }}

          # Health check
          curl -f ${API_URL}/health || exit 1

          # API version check
          curl -f ${API_URL}/api/v1/version || exit 1

          echo "Smoke tests passed!"

  notify:
    needs: [determine-environment, deploy]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deployment to ${{ needs.determine-environment.outputs.environment }}: ${{ needs.deploy.result }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*IDKit Deployment*\n• Environment: `${{ needs.determine-environment.outputs.environment }}`\n• Status: `${{ needs.deploy.result }}`\n• Commit: `${{ github.sha }}`\n• Actor: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

2. Add GitHub repository secrets:
   - `KUBECONFIG`: Base64-encoded kubeconfig file
   - `SLACK_WEBHOOK_URL`: Slack incoming webhook URL

3. Create GitHub environments:
   - `staging`: No approval required
   - `production`: Require approval from maintainers

**Acceptance Criteria:**
- [ ] Push to develop deploys to staging automatically
- [ ] Push to main deploys to production automatically
- [ ] Manual deployment trigger works
- [ ] Failed deployment does not update running pods
- [ ] Slack notification sent on completion

**UI/UX Requirements:** N/A (infrastructure)

**Backend Requirements:**
- `/health` endpoint returns 200
- `/api/v1/version` endpoint returns version info

**Frontend Requirements:**
- Standalone build works in Docker
- Environment variables injected at build time

**Integration Requirements:**
- Kubernetes cluster accessible from GitHub Actions
- Container registry permissions configured

**Testing Requirements:**
- Deploy to staging, verify app works
- Rollback test: deploy bad image, verify automatic rollback

**Observability Requirements:**
- Deployment status visible in GitHub Actions
- Slack notifications for all deployments
- Kubernetes events logged

**Risks and Mitigations:**
| Risk | Mitigation |
|------|------------|
| Deployment timeout | Increase timeout, add health checks |
| Registry unavailable | Use multiple registry mirrors |
| Kubernetes unreachable | VPN/bastion fallback, manual deployment docs |

---

#### TASK 1.1.3: Configure Container Registry

**Goal:** Set up GitHub Container Registry for Docker images.

**Exact Scope:**
- Configure repository for ghcr.io publishing
- Set image visibility and retention policies
- Document manual push procedures

**Dependencies:** None

**Implementation Steps:**

1. Ensure repository has packages enabled:
   - Go to repository Settings → Actions → General
   - Under "Workflow permissions", select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. Create `.github/workflows/cleanup-images.yml`:

```yaml
name: Cleanup Old Images

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - name: Delete old images
        uses: actions/delete-package-versions@v5
        with:
          package-name: 'idkit-backend'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: 'true'
      - name: Delete old frontend images
        uses: actions/delete-package-versions@v5
        with:
          package-name: 'idkit-frontend'
          package-type: 'container'
          min-versions-to-keep: 10
          delete-only-untagged-versions: 'true'
```

3. Create `docs/manual-deployment.md`:

```markdown
# Manual Deployment Procedures

## Prerequisites
- Docker installed and authenticated to ghcr.io
- kubectl configured with cluster access

## Build and Push Images Manually

```bash
# Authenticate to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build backend
cd backend
docker build -t ghcr.io/OWNER/idkit-backend:manual-$(date +%Y%m%d) .
docker push ghcr.io/OWNER/idkit-backend:manual-$(date +%Y%m%d)

# Build frontend
cd ../frontend
docker build -t ghcr.io/OWNER/idkit-frontend:manual-$(date +%Y%m%d) .
docker push ghcr.io/OWNER/idkit-frontend:manual-$(date +%Y%m%d)
```

## Deploy Manually

```bash
kubectl set image deployment/idkit-api \
  api=ghcr.io/OWNER/idkit-backend:manual-$(date +%Y%m%d) \
  -n idkit

kubectl rollout status deployment/idkit-api -n idkit
```
```

**Acceptance Criteria:**
- [ ] Images pushed to ghcr.io successfully
- [ ] Old images automatically cleaned up weekly
- [ ] Manual deployment documented and tested

**Testing Requirements:**
- Manually push an image and verify it appears in packages
- Run cleanup workflow and verify old images removed

---

### EPIC 1.2: Monitoring Stack

**Current State:** Prometheus/Grafana manifests exist but are not deployed.
**Target State:** Full observability with metrics, dashboards, and alerting.

---

#### TASK 1.2.1: Deploy Prometheus

**Goal:** Deploy Prometheus to Kubernetes cluster for metrics collection.

**Exact Scope:**
- Apply Prometheus Kubernetes manifests
- Verify scraping of all services
- Configure retention and storage

**Dependencies:**
- Kubernetes cluster running
- Monitoring namespace exists

**Implementation Steps:**

1. Create monitoring namespace if not exists:
```bash
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
```

2. Apply Prometheus manifests:
```bash
kubectl apply -f infrastructure/kubernetes/monitoring/prometheus.yaml
```

3. Verify Prometheus is running:
```bash
kubectl get pods -n monitoring -l app=prometheus
kubectl logs -n monitoring -l app=prometheus --tail=50
```

4. Port-forward to verify UI:
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open http://localhost:9090 in browser
```

5. Verify targets are being scraped:
   - Go to Status → Targets in Prometheus UI
   - Verify `idkit-api`, `redis`, `postgres` targets are UP

6. Verify metrics are being collected:
   - Go to Graph in Prometheus UI
   - Query: `up{job="idkit-api"}`
   - Should return `1`

**Acceptance Criteria:**
- [ ] Prometheus pod running and healthy
- [ ] All configured targets showing as UP
- [ ] Metrics queryable in Prometheus UI
- [ ] 50Gi PVC provisioned for storage
- [ ] 30-day retention configured

**Backend Requirements:**
- `/metrics` endpoint exposed on port 8000
- Prometheus client library integrated

**Testing Requirements:**
- Query `http_requests_total` metric exists
- Query `http_request_duration_seconds` histogram exists

**Observability Requirements:**
- Prometheus self-monitoring metrics available
- Alert rules loaded and visible in UI

---

#### TASK 1.2.2: Deploy Grafana

**Goal:** Deploy Grafana with pre-configured dashboards.

**Exact Scope:**
- Apply Grafana Kubernetes manifests
- Configure Prometheus datasource
- Import IDKit dashboards
- Set up admin access

**Dependencies:**
- TASK 1.2.1 (Prometheus running)

**Implementation Steps:**

1. Create Grafana admin password secret:
```bash
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password=$(openssl rand -base64 32) \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -
```

2. Apply Grafana manifests:
```bash
kubectl apply -f infrastructure/kubernetes/monitoring/grafana.yaml
```

3. Verify Grafana is running:
```bash
kubectl get pods -n monitoring -l app=grafana
kubectl logs -n monitoring -l app=grafana --tail=50
```

4. Get admin password:
```bash
kubectl get secret grafana-secrets -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d
```

5. Port-forward to verify UI:
```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Open http://localhost:3000 in browser
# Login with admin / <password from step 4>
```

6. Verify Prometheus datasource:
   - Go to Configuration → Data sources
   - Verify Prometheus datasource is green/working

7. Verify dashboards:
   - Go to Dashboards → Browse
   - Verify "IDKit Overview" dashboard exists
   - Open dashboard and verify panels show data

**Acceptance Criteria:**
- [ ] Grafana pod running and healthy
- [ ] Prometheus datasource configured and working
- [ ] IDKit Overview dashboard shows real data
- [ ] Admin password stored in Kubernetes secret
- [ ] 10Gi PVC provisioned for dashboard storage

**UI/UX Requirements:**
- Dashboard shows key metrics at a glance
- Panels have clear titles and legends
- Time range selector works

**Testing Requirements:**
- Create test alert rule, verify it appears
- Export dashboard JSON, verify it's valid

---

#### TASK 1.2.3: Deploy Alertmanager

**Goal:** Deploy Alertmanager for alert routing and notification.

**Exact Scope:**
- Apply Alertmanager Kubernetes manifests
- Configure Slack integration
- Set up alert routing rules

**Dependencies:**
- TASK 1.2.1 (Prometheus running)
- Slack webhook URL available

**Implementation Steps:**

1. Update Alertmanager config with real Slack webhook:
```bash
# Edit infrastructure/kubernetes/monitoring/alertmanager.yaml
# Replace PLACEHOLDER with actual Slack webhook URL
```

2. Apply Alertmanager manifests:
```bash
kubectl apply -f infrastructure/kubernetes/monitoring/alertmanager.yaml
```

3. Verify Alertmanager is running:
```bash
kubectl get pods -n monitoring -l app=alertmanager
kubectl logs -n monitoring -l app=alertmanager --tail=50
```

4. Port-forward to verify UI:
```bash
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
# Open http://localhost:9093 in browser
```

5. Test alert routing:
   - In Prometheus, go to Alerts
   - Verify alert rules are loaded
   - Trigger test alert by scaling down a service temporarily

6. Verify Slack notification received

**Acceptance Criteria:**
- [ ] Alertmanager pod running and healthy
- [ ] Alert routing rules loaded
- [ ] Slack notifications working for critical alerts
- [ ] Alerts grouped by severity

**Testing Requirements:**
- Trigger IDKitAPIDown alert by stopping API pod
- Verify Slack notification received within 30 seconds
- Verify alert resolves when pod comes back

---

#### TASK 1.2.4: Create Application Dashboards

**Goal:** Create comprehensive Grafana dashboards for all IDKit services.

**Exact Scope:**
- API performance dashboard
- Database dashboard
- Redis dashboard
- GPU workers dashboard
- Business metrics dashboard

**Dependencies:**
- TASK 1.2.2 (Grafana running)

**Implementation Steps:**

1. Create API Performance dashboard:

Create file `infrastructure/kubernetes/monitoring/dashboards/api-performance.json`:
```json
{
  "dashboard": {
    "title": "IDKit API Performance",
    "uid": "idkit-api-perf",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"idkit-api\"}[5m])) by (method, path)",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "title": "Latency P50/P95/P99",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job=\"idkit-api\"}[5m])) by (le))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"idkit-api\"}[5m])) by (le))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job=\"idkit-api\"}[5m])) by (le))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"idkit-api\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{job=\"idkit-api\"}[5m])) * 100",
            "legendFormat": "Error %"
          }
        ]
      },
      {
        "title": "Active Connections",
        "type": "stat",
        "gridPos": {"x": 12, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(http_connections_active{job=\"idkit-api\"})",
            "legendFormat": "Connections"
          }
        ]
      }
    ]
  }
}
```

2. Create GPU Workers dashboard:

Create file `infrastructure/kubernetes/monitoring/dashboards/gpu-workers.json`:
```json
{
  "dashboard": {
    "title": "IDKit GPU Workers",
    "uid": "idkit-gpu",
    "panels": [
      {
        "title": "GPU Memory Usage",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100",
            "legendFormat": "{{gpu}}"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "nvidia_gpu_utilization_percent",
            "legendFormat": "{{gpu}}"
          }
        ]
      },
      {
        "title": "Job Queue Depth",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "celery_queue_length{queue=~\"avatar|voice|llm\"}",
            "legendFormat": "{{queue}}"
          }
        ]
      },
      {
        "title": "Job Processing Time",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(celery_task_duration_seconds_bucket[5m])) by (le, task))",
            "legendFormat": "{{task}} P95"
          }
        ]
      }
    ]
  }
}
```

3. Create Business Metrics dashboard:

Create file `infrastructure/kubernetes/monitoring/dashboards/business-metrics.json`:
```json
{
  "dashboard": {
    "title": "IDKit Business Metrics",
    "uid": "idkit-business",
    "panels": [
      {
        "title": "Active Users (24h)",
        "type": "stat",
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "idkit_active_users_24h",
            "legendFormat": "Users"
          }
        ]
      },
      {
        "title": "Content Generated Today",
        "type": "stat",
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "increase(idkit_content_generated_total[24h])",
            "legendFormat": "Content"
          }
        ]
      },
      {
        "title": "AI Twins Created",
        "type": "stat",
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "idkit_ai_twins_total",
            "legendFormat": "Twins"
          }
        ]
      },
      {
        "title": "Revenue Today",
        "type": "stat",
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "increase(idkit_revenue_usd_total[24h])",
            "legendFormat": "Revenue"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        }
      }
    ]
  }
}
```

4. Update Grafana ConfigMap to include new dashboards:
```bash
kubectl create configmap grafana-dashboards \
  --from-file=infrastructure/kubernetes/monitoring/dashboards/ \
  -n monitoring \
  --dry-run=client -o yaml | kubectl apply -f -
```

5. Restart Grafana to pick up new dashboards:
```bash
kubectl rollout restart deployment/grafana -n monitoring
```

**Acceptance Criteria:**
- [ ] API Performance dashboard shows real data
- [ ] GPU Workers dashboard shows queue depths and processing times
- [ ] Business Metrics dashboard shows user activity
- [ ] All dashboards load without errors
- [ ] Time range selection works on all dashboards

---

### EPIC 1.3: Secret Management

**Current State:** Secrets stored as Kubernetes Secrets with base64 encoding only.
**Target State:** Secrets encrypted at rest with Sealed Secrets or external secret management.

---

#### TASK 1.3.1: Implement Sealed Secrets

**Goal:** Deploy Bitnami Sealed Secrets for encrypted secret storage in Git.

**Exact Scope:**
- Install Sealed Secrets controller
- Migrate existing secrets to sealed secrets
- Document secret rotation procedures

**Dependencies:**
- Kubernetes cluster admin access
- kubeseal CLI installed locally

**Implementation Steps:**

1. Install Sealed Secrets controller:
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml
```

2. Wait for controller to be ready:
```bash
kubectl wait --for=condition=ready pod -l name=sealed-secrets-controller -n kube-system --timeout=60s
```

3. Install kubeseal CLI locally:
```bash
# macOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
tar -xvzf kubeseal-0.24.0-linux-amd64.tar.gz
sudo mv kubeseal /usr/local/bin/
```

4. Fetch the public key:
```bash
kubeseal --fetch-cert > infrastructure/kubernetes/sealed-secrets-cert.pem
```

5. Create sealed secret for database:
```bash
# Create regular secret file (DO NOT COMMIT)
cat > /tmp/db-secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: idkit
type: Opaque
stringData:
  POSTGRES_USER: idkit
  POSTGRES_PASSWORD: <ACTUAL_PASSWORD>
  POSTGRES_DB: idkit
EOF

# Seal it
kubeseal --format yaml < /tmp/db-secret.yaml > infrastructure/kubernetes/secrets/database-sealed.yaml

# Clean up
rm /tmp/db-secret.yaml
```

6. Create sealed secrets for all services:
   - `database-sealed.yaml` - PostgreSQL credentials
   - `redis-sealed.yaml` - Redis password
   - `jwt-sealed.yaml` - JWT secret key
   - `oauth-sealed.yaml` - OAuth client secrets
   - `stripe-sealed.yaml` - Stripe API keys
   - `openai-sealed.yaml` - OpenAI API key
   - `slack-sealed.yaml` - Slack webhook URLs

7. Apply sealed secrets:
```bash
kubectl apply -f infrastructure/kubernetes/secrets/
```

8. Update deployments to reference secrets:
```yaml
# Example: Update backend deployment
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: database-credentials
        key: url
```

9. Document rotation procedure:
```markdown
# Secret Rotation Procedure

1. Generate new secret value
2. Create new sealed secret with kubeseal
3. Apply sealed secret: `kubectl apply -f <sealed-secret.yaml>`
4. Restart affected deployments: `kubectl rollout restart deployment/<name>`
5. Verify application works with new secret
6. Delete old secret from source (if applicable)
```

**Acceptance Criteria:**
- [ ] Sealed Secrets controller running
- [ ] All secrets migrated to sealed secrets
- [ ] Sealed secret files safe to commit to Git
- [ ] Applications can read secrets successfully
- [ ] Rotation procedure documented and tested

**Risks and Mitigations:**
| Risk | Mitigation |
|------|------------|
| Lose private key | Backup key, store in secure vault |
| Secret corruption | Keep unencrypted backup in secure location |
| Controller unavailable | Secrets remain decrypted in cluster |

---

## PHASE 2: REVENUE & ANALYTICS

**Goal:** Implement critical revenue-generating features and analytics capabilities.
**Priority:** FIX FIRST / HIGH IMPACT
**Duration:** 3-4 weeks

---

### EPIC 2.1: Payout Management

**Current State:** No payout system exists. Creators cannot receive money.
**Target State:** Stripe Connect integration enabling creator payouts.

---

#### TASK 2.1.1: Set Up Stripe Connect

**Goal:** Configure Stripe Connect for marketplace payouts.

**Exact Scope:**
- Create Stripe Connect platform account
- Configure payout settings
- Set up webhook endpoints

**Dependencies:**
- Stripe account with Connect enabled
- Business verification completed

**Implementation Steps:**

1. Create Stripe Connect configuration in Stripe Dashboard:
   - Go to Connect → Settings
   - Select "Platform or marketplace"
   - Configure branding (logo, colors)
   - Set default payout schedule (weekly)

2. Create backend configuration:

Create file `backend/app/core/stripe_config.py`:
```python
from pydantic_settings import BaseSettings


class StripeSettings(BaseSettings):
    """Stripe configuration settings."""

    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    stripe_connect_client_id: str

    # Payout settings
    payout_schedule_interval: str = "weekly"
    payout_schedule_day: int = 1  # Monday

    # Platform fee (percentage)
    platform_fee_percent: float = 10.0

    class Config:
        env_prefix = "STRIPE_"


stripe_settings = StripeSettings()
```

3. Add Stripe to requirements:
```
# backend/requirements.txt
stripe>=7.0.0
```

4. Create Stripe service:

Create file `backend/app/services/stripe/service.py`:
```python
import stripe
from typing import Optional
from datetime import datetime

from app.core.stripe_config import stripe_settings


stripe.api_key = stripe_settings.stripe_secret_key


class StripeService:
    """Service for Stripe operations."""

    @staticmethod
    async def create_connect_account(
        user_id: str,
        email: str,
        country: str = "US"
    ) -> dict:
        """Create a Stripe Connect account for a creator."""
        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={
                    "user_id": user_id,
                },
            )
            return {
                "account_id": account.id,
                "details_submitted": account.details_submitted,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to create Connect account: {str(e)}")

    @staticmethod
    async def create_account_link(
        account_id: str,
        refresh_url: str,
        return_url: str
    ) -> str:
        """Create an account link for onboarding."""
        try:
            link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding",
            )
            return link.url
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to create account link: {str(e)}")

    @staticmethod
    async def get_account_status(account_id: str) -> dict:
        """Get the status of a Connect account."""
        try:
            account = stripe.Account.retrieve(account_id)
            return {
                "account_id": account.id,
                "details_submitted": account.details_submitted,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements": {
                    "currently_due": account.requirements.currently_due,
                    "eventually_due": account.requirements.eventually_due,
                    "pending_verification": account.requirements.pending_verification,
                },
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to get account status: {str(e)}")

    @staticmethod
    async def create_transfer(
        account_id: str,
        amount_cents: int,
        currency: str = "usd",
        description: Optional[str] = None
    ) -> dict:
        """Transfer funds to a Connect account."""
        try:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency=currency,
                destination=account_id,
                description=description,
            )
            return {
                "transfer_id": transfer.id,
                "amount": transfer.amount,
                "currency": transfer.currency,
                "status": "pending",
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to create transfer: {str(e)}")

    @staticmethod
    async def get_balance(account_id: str) -> dict:
        """Get the balance for a Connect account."""
        try:
            balance = stripe.Balance.retrieve(
                stripe_account=account_id
            )
            return {
                "available": [
                    {"amount": b.amount, "currency": b.currency}
                    for b in balance.available
                ],
                "pending": [
                    {"amount": b.amount, "currency": b.currency}
                    for b in balance.pending
                ],
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to get balance: {str(e)}")

    @staticmethod
    async def create_payout(
        account_id: str,
        amount_cents: int,
        currency: str = "usd"
    ) -> dict:
        """Create a payout to the creator's bank account."""
        try:
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency=currency,
                stripe_account=account_id,
            )
            return {
                "payout_id": payout.id,
                "amount": payout.amount,
                "currency": payout.currency,
                "status": payout.status,
                "arrival_date": datetime.fromtimestamp(payout.arrival_date).isoformat(),
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Failed to create payout: {str(e)}")
```

**Acceptance Criteria:**
- [ ] Stripe Connect platform configured
- [ ] StripeService class created with all methods
- [ ] Configuration loaded from environment variables
- [ ] Error handling for all Stripe API calls

---

#### TASK 2.1.2: Create Payout Database Models

**Goal:** Create database models for tracking creator payouts.

**Exact Scope:**
- Create ConnectAccount model
- Create Transfer model
- Create Payout model
- Create migration

**Dependencies:**
- TASK 2.1.1 (Stripe service exists)

**Implementation Steps:**

1. Create models file:

Create file `backend/app/models/payout.py`:
```python
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, DateTime,
    ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class ConnectAccountStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DISABLED = "disabled"


class TransferStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class PayoutStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class ConnectAccount(Base):
    """Stripe Connect account for a creator."""

    __tablename__ = "connect_accounts"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_account_id = Column(String(255), nullable=False, unique=True)

    status = Column(
        SQLEnum(ConnectAccountStatus),
        default=ConnectAccountStatus.PENDING,
        nullable=False
    )

    details_submitted = Column(Integer, default=0)  # Boolean as int
    charges_enabled = Column(Integer, default=0)
    payouts_enabled = Column(Integer, default=0)

    country = Column(String(2), default="US")
    default_currency = Column(String(3), default="usd")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="connect_account")
    transfers = relationship("Transfer", back_populates="connect_account")
    payouts = relationship("Payout", back_populates="connect_account")


class Transfer(Base):
    """Transfer from platform to creator's Connect account."""

    __tablename__ = "transfers"

    id = Column(String(36), primary_key=True)
    connect_account_id = Column(String(36), ForeignKey("connect_accounts.id"), nullable=False)
    stripe_transfer_id = Column(String(255), nullable=False, unique=True)

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")

    status = Column(
        SQLEnum(TransferStatus),
        default=TransferStatus.PENDING,
        nullable=False
    )

    description = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)  # e.g., "brand_deal", "affiliate"
    source_id = Column(String(36), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    connect_account = relationship("ConnectAccount", back_populates="transfers")


class Payout(Base):
    """Payout from Connect account to creator's bank."""

    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True)
    connect_account_id = Column(String(36), ForeignKey("connect_accounts.id"), nullable=False)
    stripe_payout_id = Column(String(255), nullable=False, unique=True)

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")

    status = Column(
        SQLEnum(PayoutStatus),
        default=PayoutStatus.PENDING,
        nullable=False
    )

    arrival_date = Column(DateTime, nullable=True)
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    connect_account = relationship("ConnectAccount", back_populates="payouts")
```

2. Create migration:
```bash
cd backend
alembic revision --autogenerate -m "add_payout_models"
alembic upgrade head
```

3. Add relationship to User model:
```python
# In backend/app/models/user.py, add:
connect_account = relationship("ConnectAccount", back_populates="user", uselist=False)
```

4. Update `__init__.py`:
```python
# In backend/app/models/__init__.py, add:
from app.models.payout import ConnectAccount, Transfer, Payout
```

**Acceptance Criteria:**
- [ ] All models created with proper relationships
- [ ] Migration runs without errors
- [ ] Indexes on frequently queried columns
- [ ] Enums for status fields

---

#### TASK 2.1.3: Create Payout API Endpoints

**Goal:** Create REST API endpoints for payout management.

**Exact Scope:**
- Onboarding endpoint
- Account status endpoint
- Balance endpoint
- Payout history endpoint
- Initiate payout endpoint

**Dependencies:**
- TASK 2.1.1 (Stripe service)
- TASK 2.1.2 (Database models)

**Implementation Steps:**

1. Create schemas:

Create file `backend/app/schemas/payout.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConnectAccountStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DISABLED = "disabled"


class AccountRequirements(BaseModel):
    currently_due: List[str] = []
    eventually_due: List[str] = []
    pending_verification: List[str] = []


class ConnectAccountResponse(BaseModel):
    id: str
    stripe_account_id: str
    status: ConnectAccountStatus
    details_submitted: bool
    charges_enabled: bool
    payouts_enabled: bool
    country: str
    default_currency: str
    requirements: Optional[AccountRequirements] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingLinkResponse(BaseModel):
    url: str
    expires_at: Optional[datetime] = None


class BalanceAmount(BaseModel):
    amount_cents: int
    currency: str

    @property
    def amount_dollars(self) -> float:
        return self.amount_cents / 100


class BalanceResponse(BaseModel):
    available: List[BalanceAmount]
    pending: List[BalanceAmount]
    total_available_cents: int
    total_pending_cents: int


class TransferResponse(BaseModel):
    id: str
    stripe_transfer_id: str
    amount_cents: int
    currency: str
    status: str
    description: Optional[str]
    source_type: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PayoutResponse(BaseModel):
    id: str
    stripe_payout_id: str
    amount_cents: int
    currency: str
    status: str
    arrival_date: Optional[datetime]
    failure_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PayoutHistoryResponse(BaseModel):
    transfers: List[TransferResponse]
    payouts: List[PayoutResponse]
    total_transferred_cents: int
    total_paid_out_cents: int


class InitiatePayoutRequest(BaseModel):
    amount_cents: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", max_length=3)


class InitiatePayoutResponse(BaseModel):
    payout_id: str
    amount_cents: int
    currency: str
    status: str
    estimated_arrival: datetime
```

2. Create API router:

Create file `backend/app/api/v1/payouts.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.payout import ConnectAccount, Transfer, Payout
from app.services.stripe.service import StripeService
from app.schemas.payout import (
    ConnectAccountResponse,
    OnboardingLinkResponse,
    BalanceResponse,
    PayoutHistoryResponse,
    InitiatePayoutRequest,
    InitiatePayoutResponse,
)
from app.core.config import settings


router = APIRouter(prefix="/payouts", tags=["payouts"])


@router.post("/onboard", response_model=OnboardingLinkResponse)
async def start_onboarding(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start Stripe Connect onboarding for a creator."""
    # Check if user already has a Connect account
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    existing_account = result.scalar_one_or_none()

    if existing_account and existing_account.payouts_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active payout account"
        )

    # Create or retrieve Stripe Connect account
    if existing_account:
        stripe_account_id = existing_account.stripe_account_id
    else:
        account_data = await StripeService.create_connect_account(
            user_id=current_user.id,
            email=current_user.email,
        )

        new_account = ConnectAccount(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            stripe_account_id=account_data["account_id"],
        )
        db.add(new_account)
        await db.commit()
        stripe_account_id = account_data["account_id"]

    # Create onboarding link
    onboarding_url = await StripeService.create_account_link(
        account_id=stripe_account_id,
        refresh_url=f"{settings.frontend_url}/settings/payouts?refresh=true",
        return_url=f"{settings.frontend_url}/settings/payouts?onboarding=complete",
    )

    return OnboardingLinkResponse(url=onboarding_url)


@router.get("/account", response_model=ConnectAccountResponse)
async def get_account_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the status of the user's Connect account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found. Please complete onboarding first."
        )

    # Fetch latest status from Stripe
    stripe_status = await StripeService.get_account_status(account.stripe_account_id)

    # Update local record
    account.details_submitted = stripe_status["details_submitted"]
    account.charges_enabled = stripe_status["charges_enabled"]
    account.payouts_enabled = stripe_status["payouts_enabled"]

    if stripe_status["payouts_enabled"]:
        account.status = "active"
    elif stripe_status["details_submitted"]:
        account.status = "restricted"
    else:
        account.status = "pending"

    await db.commit()
    await db.refresh(account)

    return ConnectAccountResponse(
        id=account.id,
        stripe_account_id=account.stripe_account_id,
        status=account.status,
        details_submitted=bool(account.details_submitted),
        charges_enabled=bool(account.charges_enabled),
        payouts_enabled=bool(account.payouts_enabled),
        country=account.country,
        default_currency=account.default_currency,
        requirements=stripe_status.get("requirements"),
        created_at=account.created_at,
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current balance for the user's Connect account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found"
        )

    balance = await StripeService.get_balance(account.stripe_account_id)

    total_available = sum(b["amount"] for b in balance["available"])
    total_pending = sum(b["amount"] for b in balance["pending"])

    return BalanceResponse(
        available=[
            {"amount_cents": b["amount"], "currency": b["currency"]}
            for b in balance["available"]
        ],
        pending=[
            {"amount_cents": b["amount"], "currency": b["currency"]}
            for b in balance["pending"]
        ],
        total_available_cents=total_available,
        total_pending_cents=total_pending,
    )


@router.get("/history", response_model=PayoutHistoryResponse)
async def get_payout_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get transfer and payout history."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found"
        )

    # Get transfers
    transfers_result = await db.execute(
        select(Transfer)
        .where(Transfer.connect_account_id == account.id)
        .order_by(Transfer.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transfers = transfers_result.scalars().all()

    # Get payouts
    payouts_result = await db.execute(
        select(Payout)
        .where(Payout.connect_account_id == account.id)
        .order_by(Payout.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    payouts = payouts_result.scalars().all()

    total_transferred = sum(t.amount_cents for t in transfers if t.status == "completed")
    total_paid_out = sum(p.amount_cents for p in payouts if p.status == "paid")

    return PayoutHistoryResponse(
        transfers=transfers,
        payouts=payouts,
        total_transferred_cents=total_transferred,
        total_paid_out_cents=total_paid_out,
    )


@router.post("/initiate", response_model=InitiatePayoutResponse)
async def initiate_payout(
    request: InitiatePayoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate a payout to the creator's bank account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found"
        )

    if not account.payouts_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payouts are not enabled for this account"
        )

    # Check balance
    balance = await StripeService.get_balance(account.stripe_account_id)
    available = sum(b["amount"] for b in balance["available"] if b["currency"] == request.currency)

    if available < request.amount_cents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: {available} cents"
        )

    # Create payout
    payout_data = await StripeService.create_payout(
        account_id=account.stripe_account_id,
        amount_cents=request.amount_cents,
        currency=request.currency,
    )

    # Record in database
    payout = Payout(
        id=str(uuid.uuid4()),
        connect_account_id=account.id,
        stripe_payout_id=payout_data["payout_id"],
        amount_cents=payout_data["amount"],
        currency=payout_data["currency"],
        status=payout_data["status"],
        arrival_date=payout_data.get("arrival_date"),
    )
    db.add(payout)
    await db.commit()

    return InitiatePayoutResponse(
        payout_id=payout.id,
        amount_cents=payout.amount_cents,
        currency=payout.currency,
        status=payout.status,
        estimated_arrival=payout.arrival_date,
    )
```

3. Register router in main app:
```python
# In backend/app/api/v1/__init__.py
from app.api.v1.payouts import router as payouts_router

api_router.include_router(payouts_router)
```

**Acceptance Criteria:**
- [ ] All endpoints return correct responses
- [ ] Authentication required for all endpoints
- [ ] Error handling for all edge cases
- [ ] Database records created correctly
- [ ] Stripe API calls work in test mode

---

#### TASK 2.1.4: Create Stripe Webhook Handler

**Goal:** Handle Stripe webhook events for payout status updates.

**Exact Scope:**
- Webhook endpoint with signature verification
- Handle account.updated events
- Handle transfer events
- Handle payout events

**Dependencies:**
- TASK 2.1.1-2.1.3

**Implementation Steps:**

1. Create webhook handler:

Create file `backend/app/api/webhooks/stripe.py`:
```python
import stripe
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.api.deps import get_db
from app.models.payout import ConnectAccount, Transfer, Payout
from app.core.stripe_config import stripe_settings


router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Handle the event
    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info(f"Received Stripe event: {event_type}")

    try:
        if event_type == "account.updated":
            await handle_account_updated(db, event_data)
        elif event_type == "transfer.created":
            await handle_transfer_created(db, event_data)
        elif event_type == "transfer.reversed":
            await handle_transfer_reversed(db, event_data)
        elif event_type == "payout.created":
            await handle_payout_created(db, event_data)
        elif event_type == "payout.paid":
            await handle_payout_paid(db, event_data)
        elif event_type == "payout.failed":
            await handle_payout_failed(db, event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        # Don't raise - we've received the webhook, just failed to process
        # Stripe will retry automatically

    return {"status": "ok"}


async def handle_account_updated(db: AsyncSession, account_data: dict):
    """Handle account.updated event."""
    stripe_account_id = account_data["id"]

    result = await db.execute(
        select(ConnectAccount).where(
            ConnectAccount.stripe_account_id == stripe_account_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        logger.warning(f"Connect account not found: {stripe_account_id}")
        return

    # Update account status
    account.details_submitted = account_data.get("details_submitted", False)
    account.charges_enabled = account_data.get("charges_enabled", False)
    account.payouts_enabled = account_data.get("payouts_enabled", False)

    if account.payouts_enabled:
        account.status = "active"
    elif account.details_submitted:
        account.status = "restricted"
    else:
        account.status = "pending"

    await db.commit()
    logger.info(f"Updated Connect account: {account.id}")


async def handle_transfer_created(db: AsyncSession, transfer_data: dict):
    """Handle transfer.created event."""
    # Transfer record should already exist from our API call
    # This is just for confirmation
    logger.info(f"Transfer created: {transfer_data['id']}")


async def handle_transfer_reversed(db: AsyncSession, transfer_data: dict):
    """Handle transfer.reversed event."""
    stripe_transfer_id = transfer_data["id"]

    result = await db.execute(
        select(Transfer).where(Transfer.stripe_transfer_id == stripe_transfer_id)
    )
    transfer = result.scalar_one_or_none()

    if transfer:
        transfer.status = "reversed"
        await db.commit()
        logger.info(f"Transfer reversed: {transfer.id}")


async def handle_payout_created(db: AsyncSession, payout_data: dict):
    """Handle payout.created event."""
    # Payout record should already exist from our API call
    logger.info(f"Payout created: {payout_data['id']}")


async def handle_payout_paid(db: AsyncSession, payout_data: dict):
    """Handle payout.paid event."""
    stripe_payout_id = payout_data["id"]

    result = await db.execute(
        select(Payout).where(Payout.stripe_payout_id == stripe_payout_id)
    )
    payout = result.scalar_one_or_none()

    if payout:
        payout.status = "paid"
        await db.commit()
        logger.info(f"Payout completed: {payout.id}")


async def handle_payout_failed(db: AsyncSession, payout_data: dict):
    """Handle payout.failed event."""
    stripe_payout_id = payout_data["id"]

    result = await db.execute(
        select(Payout).where(Payout.stripe_payout_id == stripe_payout_id)
    )
    payout = result.scalar_one_or_none()

    if payout:
        payout.status = "failed"
        payout.failure_code = payout_data.get("failure_code")
        payout.failure_message = payout_data.get("failure_message")
        await db.commit()
        logger.info(f"Payout failed: {payout.id}")
```

2. Register webhook router:
```python
# In backend/app/main.py
from app.api.webhooks.stripe import router as stripe_webhook_router

app.include_router(stripe_webhook_router)
```

3. Configure webhook in Stripe Dashboard:
   - Go to Developers → Webhooks
   - Add endpoint: `https://api.idkit.io/webhooks/stripe`
   - Select events:
     - `account.updated`
     - `transfer.created`
     - `transfer.reversed`
     - `payout.created`
     - `payout.paid`
     - `payout.failed`

**Acceptance Criteria:**
- [ ] Webhook signature verification working
- [ ] All event types handled
- [ ] Database updated correctly on events
- [ ] Logging for debugging
- [ ] No exceptions on unknown events

---

#### TASK 2.1.5: Create Payout Frontend UI

**Goal:** Create frontend pages for payout management.

**Exact Scope:**
- Payout settings page
- Onboarding flow
- Balance display
- Payout history
- Initiate payout modal

**Dependencies:**
- TASK 2.1.1-2.1.4 (Backend complete)

**Implementation Steps:**

1. Create payout settings page:

Create file `frontend/src/app/settings/payouts/page.tsx`:
```tsx
'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DollarSign,
  ExternalLink,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  Wallet,
} from 'lucide-react';
import { usePayouts } from '@/hooks/usePayouts';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function PayoutsSettingsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [isInitiatingPayout, setIsInitiatingPayout] = useState(false);

  const {
    account,
    balance,
    history,
    isLoading,
    error,
    startOnboarding,
    initiatePayout,
    refetch,
  } = usePayouts();

  // Handle onboarding redirect
  useEffect(() => {
    const onboarding = searchParams.get('onboarding');
    if (onboarding === 'complete') {
      refetch();
      router.replace('/settings/payouts');
    }
  }, [searchParams, refetch, router]);

  const handleStartOnboarding = async () => {
    try {
      const { url } = await startOnboarding();
      window.location.href = url;
    } catch (err) {
      console.error('Failed to start onboarding:', err);
    }
  };

  const handleInitiatePayout = async () => {
    if (!payoutAmount || parseFloat(payoutAmount) <= 0) return;

    setIsInitiatingPayout(true);
    try {
      await initiatePayout(Math.round(parseFloat(payoutAmount) * 100));
      setShowPayoutModal(false);
      setPayoutAmount('');
      refetch();
    } catch (err) {
      console.error('Failed to initiate payout:', err);
    } finally {
      setIsInitiatingPayout(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'pending':
        return <Badge variant="warning">Pending Setup</Badge>;
      case 'restricted':
        return <Badge variant="warning">Restricted</Badge>;
      case 'paid':
        return <Badge variant="success">Paid</Badge>;
      case 'in_transit':
        return <Badge variant="secondary">In Transit</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load payout information. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  // No account - show onboarding
  if (!account) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Payouts</h1>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Set Up Payouts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Connect your bank account to receive payouts from your earnings.
              We use Stripe for secure payment processing.
            </p>

            <ul className="space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Receive payments directly to your bank account
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Track all your earnings in one place
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Automatic weekly payouts or on-demand
              </li>
            </ul>

            <Button onClick={handleStartOnboarding} className="w-full">
              <ExternalLink className="h-4 w-4 mr-2" />
              Set Up Payout Account
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              You'll be redirected to Stripe to complete secure verification
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Account exists but not fully set up
  if (!account.payouts_enabled) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Payouts</h1>

        <Alert variant="warning">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Your payout account setup is incomplete. Please complete verification
            to start receiving payouts.
          </AlertDescription>
        </Alert>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Account Status</span>
              {getStatusBadge(account.status)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {account.requirements?.currently_due?.length > 0 && (
              <div className="space-y-2">
                <p className="font-medium">Required Information:</p>
                <ul className="list-disc list-inside text-sm text-muted-foreground">
                  {account.requirements.currently_due.map((req) => (
                    <li key={req}>{req.replace(/_/g, ' ')}</li>
                  ))}
                </ul>
              </div>
            )}

            <Button onClick={handleStartOnboarding}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Continue Setup
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Fully set up - show balance and history
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Payouts</h1>
        {getStatusBadge(account.status)}
      </div>

      {/* Balance Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Available Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(balance?.total_available_cents || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Ready for payout
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Balance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(balance?.total_pending_cents || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Arriving in 2-7 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payout Button */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Request Payout</h3>
              <p className="text-sm text-muted-foreground">
                Transfer available balance to your bank account
              </p>
            </div>
            <Button
              onClick={() => setShowPayoutModal(true)}
              disabled={!balance?.total_available_cents}
            >
              <ArrowUpRight className="h-4 w-4 mr-2" />
              Request Payout
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Payout History */}
      <Card>
        <CardHeader>
          <CardTitle>Payout History</CardTitle>
        </CardHeader>
        <CardContent>
          {history?.payouts?.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No payouts yet. Request your first payout when you have available balance.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Arrival</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history?.payouts?.map((payout) => (
                  <TableRow key={payout.id}>
                    <TableCell>{formatDate(payout.created_at)}</TableCell>
                    <TableCell>{formatCurrency(payout.amount_cents)}</TableCell>
                    <TableCell>{getStatusBadge(payout.status)}</TableCell>
                    <TableCell>
                      {payout.arrival_date
                        ? formatDate(payout.arrival_date)
                        : '-'
                      }
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Payout Modal */}
      <Dialog open={showPayoutModal} onOpenChange={setShowPayoutModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Payout</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (USD)</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0"
                  max={(balance?.total_available_cents || 0) / 100}
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  className="pl-9"
                  placeholder="0.00"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Available: {formatCurrency(balance?.total_available_cents || 0)}
              </p>
            </div>

            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Payouts typically arrive in 2-3 business days.
              </AlertDescription>
            </Alert>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPayoutModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleInitiatePayout}
              disabled={
                isInitiatingPayout ||
                !payoutAmount ||
                parseFloat(payoutAmount) <= 0 ||
                parseFloat(payoutAmount) * 100 > (balance?.total_available_cents || 0)
              }
            >
              {isInitiatingPayout ? 'Processing...' : 'Request Payout'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

2. Create usePayouts hook:

Create file `frontend/src/hooks/usePayouts.ts`:
```tsx
import useSWR from 'swr';
import { api } from '@/lib/api';

interface ConnectAccount {
  id: string;
  stripe_account_id: string;
  status: 'pending' | 'active' | 'restricted' | 'disabled';
  details_submitted: boolean;
  charges_enabled: boolean;
  payouts_enabled: boolean;
  country: string;
  default_currency: string;
  requirements?: {
    currently_due: string[];
    eventually_due: string[];
    pending_verification: string[];
  };
  created_at: string;
}

interface Balance {
  available: { amount_cents: number; currency: string }[];
  pending: { amount_cents: number; currency: string }[];
  total_available_cents: number;
  total_pending_cents: number;
}

interface PayoutHistory {
  transfers: {
    id: string;
    amount_cents: number;
    currency: string;
    status: string;
    created_at: string;
  }[];
  payouts: {
    id: string;
    amount_cents: number;
    currency: string;
    status: string;
    arrival_date?: string;
    created_at: string;
  }[];
  total_transferred_cents: number;
  total_paid_out_cents: number;
}

export function usePayouts() {
  const { data: account, error: accountError, mutate: mutateAccount } = useSWR<ConnectAccount>(
    '/api/v1/payouts/account',
    (url) => api.get(url).then((res) => res.data),
    { shouldRetryOnError: false }
  );

  const { data: balance, error: balanceError, mutate: mutateBalance } = useSWR<Balance>(
    account?.payouts_enabled ? '/api/v1/payouts/balance' : null,
    (url) => api.get(url).then((res) => res.data)
  );

  const { data: history, error: historyError, mutate: mutateHistory } = useSWR<PayoutHistory>(
    account?.payouts_enabled ? '/api/v1/payouts/history' : null,
    (url) => api.get(url).then((res) => res.data)
  );

  const startOnboarding = async (): Promise<{ url: string }> => {
    const response = await api.post('/api/v1/payouts/onboard');
    return response.data;
  };

  const initiatePayout = async (amountCents: number): Promise<void> => {
    await api.post('/api/v1/payouts/initiate', {
      amount_cents: amountCents,
      currency: 'usd',
    });
  };

  const refetch = () => {
    mutateAccount();
    mutateBalance();
    mutateHistory();
  };

  return {
    account,
    balance,
    history,
    isLoading: !accountError && !account,
    error: accountError?.response?.status !== 404 ? accountError : null,
    startOnboarding,
    initiatePayout,
    refetch,
  };
}
```

3. Add utility functions:

Add to `frontend/src/lib/utils.ts`:
```tsx
export function formatCurrency(cents: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(cents / 100);
}

export function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(dateString));
}
```

**Acceptance Criteria:**
- [ ] Onboarding flow redirects to Stripe correctly
- [ ] Return from Stripe updates account status
- [ ] Balance displays correctly
- [ ] Payout history loads and displays
- [ ] Payout initiation works
- [ ] All loading and error states handled
- [ ] Mobile responsive design

**UI/UX Requirements:**
- Clear call-to-action for onboarding
- Balance displayed prominently
- Status badges for quick understanding
- Confirmation before payout
- Success/error feedback

**Testing Requirements:**
- Test with Stripe test mode
- Test onboarding complete redirect
- Test payout with insufficient balance (should fail)
- Test payout history pagination

---

### EPIC 2.2: ROI Calculator

**Current State:** No ROI calculation feature exists.
**Target State:** Interactive ROI calculator with projections and insights.

---

#### TASK 2.2.1: Create ROI Calculation Service

**Goal:** Backend service for calculating creator ROI metrics.

**Exact Scope:**
- Revenue calculation from all sources
- Cost calculation (time, tools, ads)
- ROI percentage calculation
- Historical trends
- Projections

**Dependencies:** None

**Implementation Steps:**

1. Create ROI models:

Create file `backend/app/models/roi.py`:
```python
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class ROIReport(Base):
    """Stored ROI calculation report."""

    __tablename__ = "roi_reports"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Revenue breakdown (cents)
    affiliate_revenue = Column(Integer, default=0)
    brand_deal_revenue = Column(Integer, default=0)
    subscription_revenue = Column(Integer, default=0)
    other_revenue = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)

    # Cost breakdown (cents)
    tool_costs = Column(Integer, default=0)
    ad_spend = Column(Integer, default=0)
    other_costs = Column(Integer, default=0)
    total_costs = Column(Integer, default=0)

    # Time investment
    hours_invested = Column(Float, default=0)
    hourly_value = Column(Integer, default=2500)  # $25/hour default
    time_cost = Column(Integer, default=0)

    # Calculated metrics
    net_profit = Column(Integer, default=0)
    roi_percentage = Column(Float, default=0)
    revenue_per_hour = Column(Float, default=0)

    # Metadata
    calculation_details = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="roi_reports")
```

2. Create ROI calculation service:

Create file `backend/app/services/roi/service.py`:
```python
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.models.roi import ROIReport
from app.models.monetization import AffiliateClick, BrandDeal
from app.models.subscription import UserSubscription
from app.models.content import Content


class ROIService:
    """Service for calculating creator ROI."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_roi(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        hours_invested: float = 0,
        hourly_value: int = 2500,  # cents
        tool_costs: int = 0,
        ad_spend: int = 0,
        other_costs: int = 0,
    ) -> ROIReport:
        """Calculate ROI for a given period."""

        # Calculate affiliate revenue
        affiliate_revenue = await self._calculate_affiliate_revenue(
            user_id, start_date, end_date
        )

        # Calculate brand deal revenue
        brand_deal_revenue = await self._calculate_brand_deal_revenue(
            user_id, start_date, end_date
        )

        # Calculate subscription revenue
        subscription_revenue = await self._calculate_subscription_revenue(
            user_id, start_date, end_date
        )

        # Calculate other revenue (tips, donations, etc.)
        other_revenue = await self._calculate_other_revenue(
            user_id, start_date, end_date
        )

        # Total revenue
        total_revenue = (
            affiliate_revenue +
            brand_deal_revenue +
            subscription_revenue +
            other_revenue
        )

        # Calculate time cost
        time_cost = int(hours_invested * hourly_value)

        # Total costs
        total_costs = tool_costs + ad_spend + other_costs + time_cost

        # Net profit
        net_profit = total_revenue - total_costs

        # ROI percentage
        roi_percentage = 0.0
        if total_costs > 0:
            roi_percentage = (net_profit / total_costs) * 100

        # Revenue per hour
        revenue_per_hour = 0.0
        if hours_invested > 0:
            revenue_per_hour = total_revenue / hours_invested / 100  # dollars

        # Create report
        report = ROIReport(
            id=str(uuid.uuid4()),
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            affiliate_revenue=affiliate_revenue,
            brand_deal_revenue=brand_deal_revenue,
            subscription_revenue=subscription_revenue,
            other_revenue=other_revenue,
            total_revenue=total_revenue,
            tool_costs=tool_costs,
            ad_spend=ad_spend,
            other_costs=other_costs,
            total_costs=total_costs,
            hours_invested=hours_invested,
            hourly_value=hourly_value,
            time_cost=time_cost,
            net_profit=net_profit,
            roi_percentage=roi_percentage,
            revenue_per_hour=revenue_per_hour,
            calculation_details={
                "revenue_sources": {
                    "affiliate": affiliate_revenue,
                    "brand_deals": brand_deal_revenue,
                    "subscriptions": subscription_revenue,
                    "other": other_revenue,
                },
                "cost_breakdown": {
                    "tools": tool_costs,
                    "ads": ad_spend,
                    "time": time_cost,
                    "other": other_costs,
                },
            },
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        return report

    async def get_historical_reports(
        self,
        user_id: str,
        limit: int = 12,
    ) -> list[ROIReport]:
        """Get historical ROI reports for trend analysis."""
        result = await self.db.execute(
            select(ROIReport)
            .where(ROIReport.user_id == user_id)
            .order_by(ROIReport.period_end.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_projections(
        self,
        user_id: str,
        months_ahead: int = 6,
    ) -> dict:
        """Generate revenue projections based on historical data."""
        # Get last 6 months of data
        reports = await self.get_historical_reports(user_id, limit=6)

        if len(reports) < 2:
            return {"error": "Not enough historical data for projections"}

        # Calculate average growth rate
        revenues = [r.total_revenue for r in reports]
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i] > 0:
                rate = (revenues[i-1] - revenues[i]) / revenues[i]
                growth_rates.append(rate)

        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0

        # Project future months
        projections = []
        current = revenues[0] if revenues else 0

        for month in range(1, months_ahead + 1):
            projected = int(current * (1 + avg_growth))
            projections.append({
                "month": month,
                "projected_revenue": projected,
                "confidence": max(0.5, 1 - (month * 0.1)),  # Decrease confidence over time
            })
            current = projected

        return {
            "historical_average": sum(revenues) // len(revenues),
            "average_growth_rate": avg_growth,
            "projections": projections,
        }

    async def _calculate_affiliate_revenue(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Calculate affiliate revenue for period."""
        result = await self.db.execute(
            select(func.sum(AffiliateClick.commission_cents))
            .where(AffiliateClick.user_id == user_id)
            .where(AffiliateClick.created_at >= start_date)
            .where(AffiliateClick.created_at <= end_date)
            .where(AffiliateClick.converted == True)
        )
        return result.scalar() or 0

    async def _calculate_brand_deal_revenue(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Calculate brand deal revenue for period."""
        result = await self.db.execute(
            select(func.sum(BrandDeal.payment_cents))
            .where(BrandDeal.creator_id == user_id)
            .where(BrandDeal.completed_at >= start_date)
            .where(BrandDeal.completed_at <= end_date)
            .where(BrandDeal.status == "completed")
        )
        return result.scalar() or 0

    async def _calculate_subscription_revenue(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Calculate subscription revenue for period."""
        # This would sum up payments from subscribers to this creator
        # Implementation depends on subscription model
        return 0  # TODO: Implement based on subscription model

    async def _calculate_other_revenue(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Calculate other revenue sources."""
        # Tips, donations, merchandise, etc.
        return 0  # TODO: Implement based on other revenue sources
```

**Acceptance Criteria:**
- [ ] ROI calculation covers all revenue sources
- [ ] Cost breakdown includes time investment
- [ ] Historical reports stored for trend analysis
- [ ] Projections based on historical data
- [ ] All amounts stored in cents to avoid floating point issues

---

[Document continues with remaining tasks...]

---

## TOP 10 HIGHEST-LEVERAGE IMPROVEMENTS

Based on the gap analysis, these 10 improvements will have the greatest impact on platform quality and user experience:

| # | Improvement | Current UX | Target UX | Impact Type | Effort |
|---|-------------|------------|-----------|-------------|--------|
| 1 | **CI/CD Pipeline** | 0 | 9 | Reliability | Medium |
| 2 | **Monitoring Stack** | 0 | 9 | Operational | Medium |
| 3 | **Payout Management** | 0 | 9 | Revenue | High |
| 4 | **Privacy/GDPR Integration** | 5 | 9 | Compliance | Low |
| 5 | **Multi-language Completion** | 4 | 9 | User Reach | Medium |
| 6 | **Accessibility Audit** | 5 | 9 | Inclusivity | Medium |
| 7 | **Secret Management** | 3 | 9 | Security | Low |
| 8 | **ROI Calculator** | 0 | 9 | Value Prop | High |
| 9 | **A/B Testing Statistics** | 5 | 9 | Growth | Medium |
| 10 | **Integration Testing** | 5 | 9 | Quality | Medium |

### Checklist

```
[ ] 1. CI/CD Pipeline deployed and all builds green
[ ] 2. Monitoring stack showing real-time metrics
[ ] 3. First creator payout processed successfully
[ ] 4. Privacy consent flow tested end-to-end
[ ] 5. All 5 languages complete with 100% coverage
[ ] 6. WCAG AA audit passed with zero critical issues
[ ] 7. All secrets migrated to Sealed Secrets
[ ] 8. ROI Calculator showing accurate projections
[ ] 9. A/B test results showing statistical significance
[ ] 10. Integration test coverage above 60%
```

---

## ROLLOUT PLAN

### Stage 1: Staging Deployment

**Duration:** 1 week per phase
**Environment:** `idkit-staging` namespace

1. Deploy infrastructure changes first (CI/CD, monitoring)
2. Deploy backend changes with feature flags
3. Deploy frontend changes
4. Run automated E2E tests
5. Manual QA verification

**Exit Criteria:**
- [ ] All automated tests passing
- [ ] No P0/P1 bugs in staging
- [ ] Performance within 10% of targets
- [ ] Security scan clean

### Stage 2: QA Verification

**Duration:** 3-5 days per phase
**Environment:** Staging with production-like data

1. Load testing (10x normal traffic)
2. Accessibility testing (screen readers, keyboard)
3. Cross-browser testing (Chrome, Firefox, Safari, Edge)
4. Mobile testing (iOS Safari, Android Chrome)
5. Security penetration testing

**Exit Criteria:**
- [ ] Load test passed at 10x capacity
- [ ] Zero accessibility blockers
- [ ] Works on all target browsers
- [ ] Security audit passed

### Stage 3: Canary Production

**Duration:** 2-3 days per phase
**Environment:** `idkit` namespace with 10% traffic

1. Enable canary deployment via Argo Rollouts
2. Route 10% of traffic to new version
3. Monitor error rates, latency, user feedback
4. Gradually increase to 25%, 50%, 75%, 100%
5. Rollback immediately if error rate exceeds 1%

**Exit Criteria:**
- [ ] Error rate <0.5% for 24 hours
- [ ] Latency P95 <200ms
- [ ] No user complaints
- [ ] All metrics stable

### Stage 4: Full Production

**Duration:** Ongoing
**Environment:** `idkit` namespace at 100%

1. Complete rollout to 100% of traffic
2. Monitor for 48 hours
3. Close feature flags
4. Update documentation
5. Announce to users if applicable

**Exit Criteria:**
- [ ] Running stable for 48 hours
- [ ] All KPIs met
- [ ] Documentation updated
- [ ] Stakeholders notified

---

## RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Stripe API changes | Low | High | Pin API version, monitor changelog |
| Database migration failures | Medium | High | Test migrations in staging, backup before deploy |
| GPU worker OOM | Medium | Medium | Set resource limits, implement job queuing |
| Third-party API outages | Medium | Medium | Implement circuit breakers, fallback UI |
| Translation errors | Medium | Low | Use professional translation service |
| Secret key compromise | Low | Critical | Rotate keys immediately, audit access logs |
| Deployment rollback needed | Medium | Medium | Maintain previous image tags, practice rollbacks |

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Claude | Initial comprehensive plan |

---

**END OF ROAD HOME IMPLEMENTATION PLAN**

*This document should be treated as a living document and updated as implementation progresses.*
