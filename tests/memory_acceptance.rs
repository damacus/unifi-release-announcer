#![warn(
    clippy::pedantic,
    clippy::nursery,
    clippy::cargo,
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing,
    clippy::exit,
    clippy::dbg_macro,
    clippy::todo,
    clippy::unimplemented,
    clippy::unreachable,
    clippy::undocumented_unsafe_blocks,
    clippy::as_conversions
)]
#![allow(
    // Transitive duplicate versions are outside our control.
    clippy::multiple_crate_versions,
    // Error behaviour is documented at module level, not via per-fn
    // Errors sections; the public surface is consumed internally.
    clippy::missing_errors_doc,
    clippy::missing_panics_doc,
    // Function length is governed by cognitive-complexity, not lines.
    clippy::too_many_lines,
    // Licence/keyword metadata is a maintainer decision, not a lint.
    clippy::cargo_common_metadata,
)]
#![cfg_attr(
    test,
    allow(
        clippy::unwrap_used,
        clippy::expect_used,
        clippy::panic,
        clippy::indexing_slicing,
        clippy::unreachable,
        clippy::disallowed_methods,
        clippy::future_not_send,
        clippy::assert_is_empty,
        // Fake/test impls are async only because the real trait is.
        clippy::unused_async_trait_impl,
    )
)]
#![cfg(unix)]

use std::{fs, os::unix::fs::PermissionsExt, path::PathBuf, process::Command};
use unifi_release_announcer::memory::Summary;

struct Evidence(PathBuf);
impl Evidence {
    fn new(name: &str) -> Self {
        let path = std::env::temp_dir().join(format!("unifi-memory-{name}-{}", std::process::id()));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Evidence {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn short_observation_collects_docker_evidence_without_passing_or_overwriting() {
    let temp = Evidence::new("short");
    let docker = temp.0.join("docker");
    fs::write(&docker, r#"#!/bin/sh
case "$1" in
inspect) printf '%s\n' '{"running":true,"image":"sha256:candidate","started_at":"2026-10-01T00:00:00Z"}';;
stats) printf '%s\n' '2.5MiB / 100MiB';;
logs) printf '%s\n' '{"timestamp":"2026-10-01T00:00:01Z","fields":{"phase":"idle","message":"poll completed","success":true}}';;
*) exit 1;;
esac
"#).unwrap();
    fs::set_permissions(&docker, fs::Permissions::from_mode(0o700)).unwrap();
    let output = temp.0.join("evidence");
    let run = || {
        Command::new(env!("CARGO_BIN_EXE_memory-acceptance"))
            .arg("candidate")
            .arg(&output)
            .args(["--hours", "0.000000000001", "--docker"])
            .arg(&docker)
            .output()
            .unwrap()
    };
    assert!(!run().status.success());
    let original = fs::read(output.join("summary.json")).unwrap();
    let summary: Summary = serde_json::from_slice(&original).unwrap();
    assert!(!summary.passed_24h_gate);
    assert!(summary.failures.is_empty());
    assert_eq!(summary.samples, 1);
    assert_eq!(summary.successful_polls, 1);
    assert_eq!(summary.peak_bytes, 2_621_440);
    assert_eq!(summary.image_id.as_deref(), Some("sha256:candidate"));
    assert!(!run().status.success());
    assert_eq!(fs::read(output.join("summary.json")).unwrap(), original);
}

#[test]
fn docker_startup_failure_records_failed_summary() {
    let temp = Evidence::new("failure");
    let output = temp.0.join("evidence");
    let result = Command::new(env!("CARGO_BIN_EXE_memory-acceptance"))
        .arg("candidate")
        .arg(&output)
        .arg("--docker")
        .arg(temp.0.join("missing-docker"))
        .output()
        .unwrap();
    assert!(!result.status.success());
    let summary: Summary =
        serde_json::from_slice(&fs::read(output.join("summary.json")).unwrap()).unwrap();
    assert_eq!(summary.samples, 0);
    assert_eq!(summary.failures.len(), 1);
    assert!(summary.failures[0].contains("could not start Docker"));
    assert!(!summary.passed_24h_gate);
}
