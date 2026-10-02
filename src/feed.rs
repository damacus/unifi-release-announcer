use crate::{
    parser::parse_release,
    release::{RawRelease, Release, select_latest},
};
use anyhow::{Context, Result, bail};
use reqwest::{Client, Response};
use serde_json::{Value, json};
use std::time::Duration;

#[derive(Clone)]
pub struct GraphQl {
    client: Client,
    url: String,
}

pub fn feed_payload(tags: &[String]) -> Value {
    json!({ "query": include_str!("feed.graphql"), "variables": {
        "tags": tags, "betas": [], "alphas": [], "offset": 0, "limit": 50,
        "sortBy": null, "userIsFollowing": false, "featuredOnly": false,
        "searchTerm": "", "filterTags": [], "filterEATags": [], "statuses": ["PUBLISHED"]
    }})
}

pub async fn response_json(mut response: Response) -> Result<Value> {
    let status = response.status();
    if !status.is_success() {
        bail!("HTTP status {}", status.as_u16());
    }
    let mut body = Vec::new();
    while let Some(chunk) = response
        .chunk()
        .await
        .map_err(|_| anyhow::anyhow!("response read failed"))?
    {
        if body.len() + chunk.len() > 4 * 1024 * 1024 {
            bail!("response exceeds 4 MiB");
        }
        body.extend_from_slice(&chunk);
    }
    serde_json::from_slice(&body).context("invalid JSON response")
}

impl GraphQl {
    pub fn new() -> Result<Self> {
        Self::with_url("https://community.svc.ui.com/")
    }
    pub fn with_url(url: &str) -> Result<Self> {
        // Scratch has no OS certificate store. Retain bundled Mozilla roots and ring.
        let roots =
            rustls::RootCertStore::from_iter(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());
        let tls = rustls::ClientConfig::builder_with_provider(std::sync::Arc::new(
            rustls::crypto::ring::default_provider(),
        ))
        .with_safe_default_protocol_versions()?
        .with_root_certificates(roots)
        .with_no_client_auth();
        let client = Client::builder()
            .tls_backend_preconfigured(tls)
            .timeout(Duration::from_secs(30))
            .redirect(reqwest::redirect::Policy::none())
            .build()?;
        Ok(Self {
            client,
            url: url.into(),
        })
    }
    async fn request(&self, payload: &Value) -> Result<Value> {
        let response = self.client.post(&self.url)
            .header("accept", "application/graphql-response+json, application/json")
            .header("accept-language", "en-GB,en-US;q=0.9,en;q=0.8")
            .header("cache-control", "no-cache")
            .header("origin", "https://community.ui.com")
            .header("referer", "https://community.ui.com/")
            .header("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
            .json(payload).send().await.map_err(|_| anyhow::anyhow!("GraphQL request failed"))?;
        let data = response_json(response).await?;
        if data
            .get("errors")
            .is_some_and(|v| v.as_array().is_none_or(|a| !a.is_empty()))
        {
            bail!("GraphQL returned errors");
        }
        Ok(data)
    }
    pub async fn latest(&self, tags: &[String]) -> Result<Vec<Release>> {
        let data = self.request(&feed_payload(tags)).await?;
        let items = data
            .pointer("/data/releases/items")
            .and_then(Value::as_array)
            .context("missing or invalid release items")?;
        let items: Vec<RawRelease> = items
            .iter()
            .filter(|item| {
                item.get("tags")
                    .and_then(Value::as_array)
                    .is_some_and(|item_tags| {
                        item_tags.iter().any(|tag| {
                            tag.as_str()
                                .is_some_and(|tag| tags.iter().any(|configured| configured == tag))
                        })
                    })
            })
            .map(|item| {
                serde_json::from_value(item.clone()).context("invalid configured release item")
            })
            .collect::<Result<_>>()?;
        Ok(select_latest(&items, tags))
    }
    pub async fn details(&self, id: &str) -> Result<Option<Value>> {
        let data = self
            .request(&json!({
                "query": include_str!("details.graphql"),
                "variables": {"id": id}, "operationName": "ReleaseDetailQuery"
            }))
            .await?;
        match data.pointer("/data/release") {
            Some(Value::Null) => Ok(None),
            Some(v) => Ok(Some(parse_release(v, true)?)),
            None => bail!("missing release detail response"),
        }
    }
}
