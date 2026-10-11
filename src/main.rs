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
use anyhow::Result;
use clap::Parser;
use std::time::Duration;
use unifi_release_announcer::{
    config::Config, discord::DiscordHttp, feed::GraphQl, pipeline::PollState,
};

#[derive(Parser)]
#[command(version, about = "HTTP-only UniFi release announcer")]
struct Args {
    #[arg(long)]
    once: bool,
    #[arg(long)]
    dry_run: bool,
}

async fn shutdown() -> std::io::Result<()> {
    #[cfg(unix)]
    {
        let mut terminate =
            tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())?;
        tokio::select! { result = tokio::signal::ctrl_c() => result, _ = terminate.recv() => Ok(()) }
    }
    #[cfg(not(unix))]
    tokio::signal::ctrl_c().await
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .json()
        .with_writer(std::io::stderr)
        .with_env_filter(tracing_subscriber::EnvFilter::new("info"))
        .init();
    let args = Args::parse();
    let config = Config::from_env()?;
    let destination = DiscordHttp::new(&config.token, config.channel_id)?;
    let source = GraphQl::new()?;
    let mut state = PollState::default();
    let mut shutdown = Box::pin(shutdown());
    tokio::select! { result = destination.validate() => result?, result = &mut shutdown => { result?; return Ok(()); } }
    tracing::info!(dry_run = args.dry_run, "announcer ready");
    let mut interval = tokio::time::interval(Duration::from_secs(600));
    interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
    loop {
        tokio::select! { _ = interval.tick() => {}, result = &mut shutdown => { result?; break; } }
        tracing::info!(phase = "polling", "poll started");
        let mut poll = Box::pin(state.poll(&source, &destination, &config.tags, args.dry_run));
        let result = tokio::select! {
            result = &mut poll => result,
            signal = &mut shutdown => {
                signal?;
                if let Ok(result) = tokio::time::timeout(Duration::from_secs(30), &mut poll).await { if result.is_err() { tracing::warn!("in-flight poll failed during shutdown"); } } else { tracing::warn!("in-flight poll cancelled at shutdown deadline") }
                break;
            }
        };
        match result {
            Ok(decisions) => {
                if args.dry_run {
                    for decision in decisions {
                        println!("{}", serde_json::to_string(&decision)?);
                    }
                }
                tracing::info!(phase = "idle", success = true, "poll completed");
            }
            Err(error) => {
                tracing::warn!(phase = "idle", success = false, error = %error, "poll failed");
                if args.once {
                    return Err(error);
                }
            }
        }
        if args.once {
            break;
        }
    }
    tracing::info!("announcer stopped");
    Ok(())
}
