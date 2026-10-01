use regex::{Captures, Regex};
use serde::{Deserialize, Serialize};
use std::sync::LazyLock;

#[derive(Debug, Clone, Deserialize)]
pub struct RawRelease {
    pub id: String,
    pub title: String,
    pub version: String,
    pub slug: String,
    #[serde(rename = "createdAt")]
    pub created_at: String,
    #[serde(default)]
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Release {
    pub title: String,
    pub url: String,
    pub tag: String,
}

fn allowed(title: &str, tag: &str) -> bool {
    let required = match tag {
        "unifi-protect" => Some("protect"),
        "unifi-network" => Some("network"),
        "unifi-access" => Some("access"),
        "unifi-talk" => Some("talk"),
        "unifi-drive" => Some("drive"),
        "unifi-connect" => Some("connect"),
        "unifi-portal" => Some("portal"),
        _ => None,
    };
    if let Some(product) = required {
        return title.contains(product) && title.contains("application");
    }
    ![
        "android",
        "ios",
        "iphone",
        "ipad",
        "tvos",
        "sfp wizard",
        "ups",
        "advisory",
    ]
    .iter()
    .any(|pattern| title.contains(pattern))
}

pub fn select_latest(items: &[RawRelease], tags: &[String]) -> Vec<Release> {
    tags.iter()
        .filter_map(|tag| {
            let mut latest: Option<&RawRelease> = None;
            for item in items {
                if !item.tags.contains(tag) || !allowed(&item.title.to_lowercase(), tag) {
                    continue;
                }
                if latest.is_none_or(|old| item.created_at > old.created_at) {
                    latest = Some(item);
                }
            }
            latest.map(|item| {
                let version = item.version.to_lowercase();
                let beta = version.contains("beta")
                    || item.title.to_lowercase().contains("beta")
                    || version.contains("rc")
                    || version.contains("candidate");
                Release {
                    title: format!(
                        "{} {} ({})",
                        item.title,
                        item.version,
                        if beta { "Beta" } else { "GA" }
                    ),
                    url: format!(
                        "https://community.ui.com/releases/{}/{}",
                        item.slug, item.id
                    ),
                    tag: tag.clone(),
                }
            })
        })
        .collect()
}

static MARKDOWN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
    r#"(?m)(?P<url><[^: >]+:/[^ >]+>|(?:https?|steam)://[^\s<]+[^<.,:;"'\]\s])|(?P<markdown>[_\\~|*\x60]|^>(?:>>)?\s|\[.+\]\(.+\)|^#{1,3}|^\s*-)"#
).expect("constant Markdown expression")
});

pub fn escape_title(title: &str) -> String {
    MARKDOWN
        .replace_all(title, |caps: &Captures<'_>| {
            if let Some(url) = caps.name("url") {
                url.as_str().to_owned()
            } else {
                format!("\\{}", &caps["markdown"])
            }
        })
        .replace('[', "\\[")
        .replace(']', "\\]")
}

pub fn format_message(release: &Release) -> String {
    let title = escape_title(&release.title);
    let lower = title.to_lowercase();
    let emoji = if lower.contains("ios") {
        "📱"
    } else if lower.contains("android") {
        "🤖"
    } else if lower.contains("desktop") || lower.contains("application") {
        "💻"
    } else {
        "🔧"
    };
    format!(
        "🎉 **New UniFi Release Posted**\n\n🔗 [{title}]({}) {emoji}",
        release.url
    )
}
