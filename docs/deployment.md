# Deployment and Rust migration

Deploy one writer. Reuse the existing channel and credentials so previous announcements remain visible to duplicate detection.

## Acceptance before deployment

1. Pass Rust tests, Python oracle tests, formatting, Clippy and documentation build.
2. Build and run non-root amd64 and arm64 images.
3. Run the explicitly ignored live test in the existing text channel. It posts one labelled verification message, reads it back and deletes only that message.
4. Run the release container in `--dry-run` for 24 hours with live feed/history and production tags. Sample every 15 seconds using `scripts/memory_acceptance.py`.
5. Require idle working set <=32 MiB after warm-up and every sample <=64 MiB. Require at least 140 successful polls and no observed poll failures.
6. Publish and record an immutable image digest. A short smoke test is not the 24-hour gate.

The sampler reads Docker working-set statistics from the host, so it works with the shell-free scratch runtime. Docker subtracts inactive file cache on Linux and rounds its displayed memory values. Docker Desktop must remain running throughout the measurement. Docker observer processes add a small amount of instrumentation overhead. If collection stops, the test fails.

## Ironstone GitOps

The source of truth is home-ops `kubernetes/apps/default/unifi-release-announcer/app/HelmRelease.yaml`. Keep existing secret references, tags, PVC, one replica and Recreate strategy. Retain the 100M request/limit for initial cutover.

Validate rendered manifests with `task k8s:yayamlls`. Keep the deployment PR in draft with auto-merge disabled until the application and memory gates pass.

Cluster deployment is the final step. First use an isolated dry-run canary with the existing secret references and tags, then replace the production image through Flux. Never give the canary a write-enabled command.

Verify the exact Flux revision and image digest, one active writer, completed polls, and a controlled restart without reposting existing releases. Repeat the 24-hour memory/error check after cutover.

## Rollback

Record the current Python digest before activation. The initial baseline was:

```text
ghcr.io/damacus/unifi-release-announcer:0.2.14@sha256:19ef75ff3c21473a49e07c91ed19aefa9187cd286b8e595d783eb2148cb4a552
```

Revert the image change through GitOps, retaining Recreate, secrets and the PVC. Confirm the Python pod is healthy and resumes polling. Do not delete state or Discord history.

Archive the OpenSpec change only after production acceptance.

The production Kubernetes manifests live in the home-ops GitOps repository at kubernetes/apps/default/unifi-release-announcer. Make rollout changes there; this application repository has no separate kubectl deployment examples.

The release workflow runs the full reusable CI suite against the exact release tag before publishing its image. The local 24-hour memory evidence remains a separate migration gate: complete it before merging the runtime migration or beginning the GitOps rollout. The memory sampler requires Python and Docker, with no RTK prerequisite.
