# Deployment

This guide covers different deployment options for the UniFi Release Announcer.

## Docker Compose Deployment

The recommended way to run the application in production is using Docker Compose.

### Prerequisites

- Docker and Docker Compose installed
- Discord bot token and channel ID

### Steps

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd unifi-release-announcer
   ```

2. **Create environment file**:

   Create a `.env` file in the project root:

   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id
   SCRAPER_BACKEND=graphql
   TAGS=unifi-protect,unifi-network
   ```

3. **Build the image**:

   Using Taskfile:
   ```bash
   task build
   ```

   Or directly with Docker Compose:
   ```bash
   docker compose build announcer
   ```

4. **Run the service**:

   Using Taskfile:
   ```bash
   task docker-run
   ```

   Or directly with Docker Compose:
   ```bash
   docker compose up announcer
   ```

   To run in detached mode:
   ```bash
   docker compose up -d announcer
   ```

5. **View logs**:

   ```bash
   docker compose logs -f announcer
   ```

6. **Stop the service**:

   ```bash
   docker compose down
   ```

## Kubernetes Deployment

For production deployments on Kubernetes clusters (including k3s).

### Prerequisites

- A running Kubernetes cluster (e.g., k3s, minikube)
- `kubectl` configured to connect to your cluster
- A Docker Hub account or another container registry to host your image

### Steps

#### 1. Build and Push the Docker Image

First, build the Docker image and push it to a container registry. Replace `your-docker-hub-username` with your actual username.

```bash
# Build the image
docker build -t your-docker-hub-username/unifi-release-announcer:latest .

# Push the image
docker push your-docker-hub-username/unifi-release-announcer:latest
```

#### 2. Update the Deployment Image

Modify `k8s/deployment.yaml` to point to the image you just pushed:

```yaml
# k8s/deployment.yaml

# ...
containers:
  - name: unifi-release-announcer
    # Replace with your actual image path
    image: your-docker-hub-username/unifi-release-announcer:latest
# ...
```

#### 3. Create Your Secrets

Update `k8s/secret.yaml` with your actual Discord bot token and channel ID. 

!!! warning "Security Notice"
    **Do not commit this file with your secrets to a public repository.**

```yaml
# k8s/secret.yaml

apiVersion: v1
kind: Secret
metadata:
  name: unifi-release-announcer-secrets
stringData:
  DISCORD_BOT_TOKEN: "YOUR_REAL_BOT_TOKEN"
  DISCORD_CHANNEL_ID: "YOUR_REAL_CHANNEL_ID"
```

#### 4. Apply the Manifests

Use `kustomize` and `kubectl` to apply the configuration to your cluster.

```bash
cd k8s
kubectl apply -k .
```

#### 5. Verify the Deployment

Check the status of your deployment and view the logs to ensure everything is running correctly.

```bash
# Check deployment status
kubectl get deployments

# Check pod status
kubectl get pods

# View logs from the pod (replace with your pod's name)
kubectl logs -f <your-pod-name>
```

#### 6. Update the Deployment

To update the deployment with a new image:

```bash
# Pull the latest image
kubectl rollout restart deployment/unifi-release-announcer

# Check rollout status
kubectl rollout status deployment/unifi-release-announcer
```

## Development Deployment

For local development, you can use the dev container or run directly with Python.

### Using Dev Container

```bash
task dev
```

This starts a development container with all dependencies installed and volume mounts for live code editing.

### Running Locally

```bash
# Install dependencies
task dev-install

# Run the application
task run
```

## Environment Variables

Make sure to configure the following environment variables for any deployment method:

| Variable             | Description                                                                                                 | Required |
|----------------------|-------------------------------------------------------------------------------------------------------------|----------|
| `DISCORD_BOT_TOKEN`  | Your Discord bot token                                                                                      | Yes      |
| `DISCORD_CHANNEL_ID` | Discord channel ID for announcements                                                                        | Yes      |
| `SCRAPER_BACKEND`    | Backend to use for scraping: `graphql` (default) or `rss`                                                  | No       |
| `TAGS`               | Comma-separated list of UniFi product tags to monitor (e.g., "unifi-protect,unifi-network"). Defaults to "unifi-protect" if not set. | No       |

## Persistent Storage

The application stores state in `/cache/release_state.json` to track which releases have been announced. Make sure this directory is persisted across container restarts:

### Docker Compose

The `docker-compose.yml` already includes a volume mount:

```yaml
volumes:
  - ./cache:/cache
```

### Kubernetes

The Kubernetes deployment uses an `emptyDir` volume by default. For production, consider using a PersistentVolumeClaim:

```yaml
volumes:
  - name: cache
    persistentVolumeClaim:
      claimName: unifi-release-announcer-cache
```
