#![warn(
    clippy::pedantic,
    clippy::nursery,
    clippy::cargo,
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
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
        clippy::unreachable,
        clippy::disallowed_methods,
        clippy::future_not_send,
        clippy::assert_is_empty,
        // Fake/test impls are async only because the real trait is.
        clippy::unused_async_trait_impl,
    )
)]
// JSON object indexing returns Null for absent keys rather than panicking;
// array-index sites remain to be audited.
#![allow(clippy::indexing_slicing)]

use anyhow::{Context, Result, bail, ensure};
use clap::Parser;
use serde::Deserialize;
use serde_json::Value;
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    time::{Duration, Instant},
};
use tokio::{
    process::Command,
    time::{sleep, timeout},
};
use unifi_release_announcer::memory::{Acceptance, Sample, working_set};

#[derive(Parser)]
#[command(about = "Measure a Docker candidate for the 24-hour memory acceptance gate")]
struct Args {
    container: String,
    output: PathBuf,
    #[arg(long, default_value_t = 24.0)]
    hours: f64,
    #[arg(long, default_value = "docker")]
    docker: PathBuf,
}

#[derive(Debug, Deserialize, PartialEq, Eq)]
struct ContainerState {
    running: bool,
    image: String,
    started_at: String,
}

async fn docker(args: &Args, command: &[&str]) -> Result<(String, String)> {
    let output = timeout(
        Duration::from_secs(30),
        Command::new(&args.docker)
            .args(command)
            .kill_on_drop(true)
            .output(),
    )
    .await
    .context("Docker observation timed out")?
    .context("could not start Docker")?;
    ensure!(output.status.success(), "Docker observation failed");
    Ok((
        String::from_utf8(output.stdout)?,
        String::from_utf8(output.stderr)?,
    ))
}

async fn inspect(args: &Args) -> Result<ContainerState> {
    let (stdout, _) = docker(args, &["inspect", "--format",
        "{\"running\":{{.State.Running}},\"image\":{{json .Image}},\"started_at\":{{json .State.StartedAt}}}",
        &args.container]).await?;
    let state: ContainerState = serde_json::from_str(&stdout)?;
    ensure!(state.running, "candidate container stopped");
    Ok(state)
}

async fn sample(args: &Args, elapsed: f64) -> Result<Sample> {
    let (usage, _) = docker(
        args,
        &[
            "stats",
            "--no-stream",
            "--format",
            "{{.MemUsage}}",
            &args.container,
        ],
    )
    .await?;
    let (stdout, stderr) = docker(args, &["logs", "--tail", "100", &args.container]).await?;
    let mut sample = Sample {
        at: chrono::DateTime::<chrono::Utc>::from(std::time::SystemTime::now()).to_rfc3339(),
        working_set_bytes: working_set(&usage)?,
        phase: None,
        latest_poll_success: None,
        latest_poll_at: None,
        elapsed_seconds: elapsed,
    };
    for line in stdout.lines().chain(stderr.lines()) {
        let Ok(entry) = serde_json::from_str::<Value>(line) else {
            continue;
        };
        let fields = &entry["fields"];
        if let Some(phase) = fields["phase"].as_str() {
            sample.phase = Some(phase.into());
        }
        match fields["message"].as_str() {
            Some("poll failed") => bail!("poll failure observed"),
            Some("poll completed") => {
                if fields["success"].as_bool() == Some(false) {
                    bail!("poll failure observed");
                }
                sample.latest_poll_success = fields["success"].as_bool();
                sample.latest_poll_at = entry["timestamp"].as_str().map(String::from);
            }
            _ => {}
        }
    }
    Ok(sample)
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<std::process::ExitCode> {
    let args = Args::parse();
    ensure!(
        args.hours.is_finite() && args.hours > 0.0,
        "hours must be positive and finite"
    );
    let duration = Duration::try_from_secs_f64(args.hours * 3600.0).context("invalid duration")?;
    fs::create_dir_all(&args.output)?;
    let mut evidence = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(args.output.join("samples.ndjson"))
        .context("evidence path already exists or is unwritable")?;
    let start = Instant::now();
    let mut gate = Acceptance::default();
    let mut image = None;
    let observation: Result<()> = async {
        let baseline = inspect(&args).await?;
        image = Some(baseline.image.clone());
        loop {
            ensure!(
                inspect(&args).await? == baseline,
                "candidate restarted or image changed"
            );
            let mut observed = sample(&args, start.elapsed().as_secs_f64()).await?;
            observed.elapsed_seconds = start.elapsed().as_secs_f64();
            serde_json::to_writer(&mut evidence, &observed)?;
            writeln!(evidence)?;
            evidence.flush()?;
            if !gate.observe(&observed) || start.elapsed() >= duration {
                break;
            }
            sleep(Duration::from_secs(15)).await;
        }
        Ok(())
    }
    .await;
    if let Err(error) = observation {
        gate.fail(&error.to_string());
    }
    let summary = gate.finish(args.container, image, start.elapsed().as_secs_f64());
    fs::write(
        args.output.join("summary.json"),
        serde_json::to_string_pretty(&summary)? + "\n",
    )?;
    println!("{}", serde_json::to_string(&summary)?);
    Ok(if summary.passed_24h_gate {
        std::process::ExitCode::SUCCESS
    } else {
        std::process::ExitCode::FAILURE
    })
}
