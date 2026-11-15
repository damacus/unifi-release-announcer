// JSON object indexing returns Null for absent keys rather than panicking;
// array-index sites remain to be audited.
#![allow(clippy::indexing_slicing)]

use anyhow::{Context, Result, bail};
use chrono::{DateTime, NaiveDateTime};
use serde_json::{Value, json};

pub fn parse_release(raw: &Value, details: bool) -> Result<Value> {
    for field in ["title", "slug", "stage", "version", "createdAt"] {
        if raw.get(field).and_then(Value::as_str).is_none() {
            bail!("missing or invalid release field: {field}");
        }
    }
    if raw.get("tags").and_then(Value::as_array).is_none() {
        bail!("missing release tags");
    }
    let created = raw["createdAt"].as_str().context("missing timestamp")?;
    let date = DateTime::parse_from_rfc3339(created)
        .map(|v| v.date_naive())
        .or_else(|_| {
            NaiveDateTime::parse_from_str(created, "%Y-%m-%dT%H:%M:%S%.f").map(|v| v.date())
        })
        .context("invalid release timestamp")?;
    let mut parsed = json!({
        "title": raw["title"], "slug": raw["slug"],
        "url": format!("https://community.ui.com/releases/{}", raw["slug"].as_str().unwrap_or_default()),
        "tags": raw["tags"], "stage": raw["stage"], "version": raw["version"],
        "created_at": raw["createdAt"], "created_date": date.to_string(),
        "stats": raw.get("stats").cloned().unwrap_or_else(|| json!({})),
        "has_engagement": raw.get("hasUiEngagement").cloned().unwrap_or(json!(false)),
    });
    if details {
        parsed["author"] = raw.get("author").cloned().unwrap_or(Value::Null);
        parsed["last_activity"] = raw.get("lastActivityAt").cloned().unwrap_or(Value::Null);
    }
    Ok(parsed)
}

pub fn parse_feed(
    data: &Value,
    tags: &[String],
    stage: Option<&str>,
    limit: Option<i64>,
) -> Result<Vec<Value>> {
    let items = data
        .pointer("/data/releases/items")
        .and_then(Value::as_array)
        .context("missing release items")?;
    let mut parsed: Vec<Value> = items
        .iter()
        .map(|v| parse_release(v, false))
        .collect::<Result<_>>()?;
    parsed.retain(|v| {
        (tags.is_empty()
            || tags.iter().any(|tag| {
                v["tags"]
                    .as_array()
                    .is_some_and(|a| a.iter().any(|t| t == tag))
            }))
            && stage.is_none_or(|s| s.is_empty() || v["stage"] == s)
    });
    if let Some(limit) = limit.filter(|v| *v != 0) {
        let length = if limit < 0 {
            parsed
                .len()
                .saturating_sub(usize::try_from(limit.unsigned_abs()).unwrap_or(usize::MAX))
        } else {
            usize::try_from(limit).unwrap_or(usize::MAX)
        };
        parsed.truncate(length);
    }
    Ok(parsed)
}
