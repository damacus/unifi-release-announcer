use anyhow::{Result, bail};
use std::env;

pub const ALLOWED_TAGS: &[&str] = &[
    "60GHz",
    "aircontrol",
    "airfiber",
    "airfiber-ltu",
    "airmax",
    "airmax-aircube",
    "amplifi",
    "community-feedback",
    "edgemax",
    "edgeswitch",
    "general",
    "gigabeam",
    "innerspace",
    "isp",
    "isp-design-center",
    "routing",
    "security",
    "site-manager",
    "solar",
    "switching",
    "ufiber",
    "uid",
    "uisp-app",
    "uisp-power",
    "unifi",
    "unifi-access",
    "unifi-cloud-gateway",
    "unifi-connect",
    "unifi-design-center",
    "unifi-drive",
    "unifi-gateway-cloudkey",
    "unifi-led",
    "unifi-mobility",
    "unifi-network",
    "unifi-play",
    "unifi-portal",
    "unifi-protect",
    "unifi-routing-switching",
    "unifi-switching",
    "unifi-talk",
    "unifi-video",
    "unifi-voip",
    "unifi-wireless",
    "unms",
    "wave",
    "wifiman",
];

pub struct Config {
    pub token: String,
    pub channel_id: u64,
    pub tags: Vec<String>,
}

impl Config {
    // Designated config loader — the only sanctioned env::var call site.
    #[allow(clippy::disallowed_methods)]
    pub fn from_env() -> Result<Self> {
        let token = env::var("DISCORD_BOT_TOKEN").unwrap_or_default();
        if token.trim().is_empty() {
            bail!("DISCORD_BOT_TOKEN is required");
        }
        let channel_id = env::var("DISCORD_CHANNEL_ID")
            .unwrap_or_default()
            .parse::<u64>()
            .map_err(|_| anyhow::anyhow!("DISCORD_CHANNEL_ID must be a positive integer"))?;
        if channel_id == 0 {
            bail!("DISCORD_CHANNEL_ID must be a positive integer");
        }
        let tags = parse_tags(&env::var("TAGS").unwrap_or_default())?;
        Ok(Self {
            token,
            channel_id,
            tags,
        })
    }
}

pub fn parse_tags(value: &str) -> Result<Vec<String>> {
    if value.trim().is_empty() {
        return Ok(vec!["unifi-protect".into()]);
    }
    let mut tags = Vec::new();
    for tag in value.split(',').map(str::trim).filter(|t| !t.is_empty()) {
        if !ALLOWED_TAGS.contains(&tag) {
            bail!("invalid TAGS entry");
        }
        if !tags.iter().any(|t| t == tag) {
            tags.push(tag.to_owned());
        }
    }
    if tags.is_empty() {
        bail!("TAGS must contain at least one valid tag");
    }
    Ok(tags)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn configured_tags() {
        assert_eq!(parse_tags(" ").unwrap(), ["unifi-protect"]);
        assert_eq!(
            parse_tags(" unifi-network,,unifi-drive,unifi-network ").unwrap(),
            ["unifi-network", "unifi-drive"]
        );
        assert!(parse_tags("UNIFI-PROTECT").is_err());
        assert!(parse_tags("unifi-drive,invalid").is_err());
        assert!(parse_tags(", ,").is_err());
    }
}
