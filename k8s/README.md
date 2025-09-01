# Deploying to Kubernetes

This directory contains the necessary files to deploy the UniFi Release Announcer to a Kubernetes cluster.

## Prerequisites

- A running Kubernetes cluster (e.g., k3s, minikube).
- `kubectl` configured to connect to your cluster.
- A Docker Hub account or another container registry to host your image.

## Steps

### 1. Build and Push the Docker Image

First, build the Docker image and push it to a container registry. Replace `your-docker-hub-username` with your actual username.

```bash
# Build the image
docker build -t your-docker-hub-username/unifi-release-announcer:latest ..

# Push the image
docker push your-docker-hub-username/unifi-release-announcer:latest
```

### 2. Update the Deployment Image

Modify `deployment.yaml` to point to the image you just pushed:

```yaml
# k8s/deployment.yaml

# ...
containers:
  - name: unifi-release-announcer
    # Replace with your actual image path
    image: your-docker-hub-username/unifi-release-announcer:latest
# ...
```

### 3. Create Your Secrets

Update `secret.yaml` with your actual Discord bot token and channel ID. **Do not commit this file with your secrets to a public repository.**

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

### 4. Apply the Manifests

Use `kustomize` and `kubectl` to apply the configuration to your cluster.

```bash
kubectl apply -k .
```

### 5. Verify the Deployment

Check the status of your deployment and view the logs to ensure everything is running correctly.

```bash
# Check deployment status
kubectl get deployments

# Check pod status
kubectl get pods

# View logs from the pod (replace with your pod's name)
kubectl logs -f <your-pod-name>
```
