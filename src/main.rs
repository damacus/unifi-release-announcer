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
                match tokio::time::timeout(Duration::from_secs(30), &mut poll).await {
                    Ok(result) => { if result.is_err() { tracing::warn!("in-flight poll failed during shutdown"); } }
                    Err(_) => tracing::warn!("in-flight poll cancelled at shutdown deadline"),
                }
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
