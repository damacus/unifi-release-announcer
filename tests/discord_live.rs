use anyhow::Result;
use unifi_release_announcer::{config::Config, discord::DiscordHttp};

#[tokio::test]
#[ignore = "Posts one labelled verification message to the configured channel, then removes it"]
async fn verify_existing_channel() -> Result<()> {
    let config = Config::from_env()?;
    let discord = DiscordHttp::new(&config.token, config.channel_id)?;
    discord.validate().await?;
    discord.verification_message().await
}
