use crate::{feed::GraphQl, release::Release};
use anyhow::{Result, bail};
use serde::Serialize;
use std::collections::{HashSet, VecDeque};

#[allow(async_fn_in_trait)]
pub trait Source {
    async fn releases(&self, tags: &[String]) -> Result<Vec<Release>>;
}
#[allow(async_fn_in_trait)]
pub trait Destination {
    async fn history(&self) -> Result<Vec<String>>;
    async fn post(&self, release: &Release) -> PostOutcome;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PostOutcome {
    Confirmed,
    Rejected,
    Uncertain,
}

#[derive(Debug, Serialize)]
pub struct Decision {
    pub tag: String,
    pub title: String,
    pub url: String,
    pub action: &'static str,
}

#[derive(Default)]
pub struct PollState {
    remembered: VecDeque<String>,
}
impl PollState {
    fn remember(&mut self, url: &str) {
        if !self.remembered.iter().any(|v| v == url) {
            if self.remembered.len() == 200 {
                self.remembered.pop_front();
            }
            self.remembered.push_back(url.to_owned());
        }
    }
    // Driven on a `current_thread` runtime via `&mut Box::pin` in main —
    // the future is never spawned across threads.
    #[allow(clippy::future_not_send)]
    pub async fn poll(
        &mut self,
        source: &impl Source,
        destination: &impl Destination,
        tags: &[String],
        dry_run: bool,
    ) -> Result<Vec<Decision>> {
        let releases = source.releases(tags).await?;
        if releases.is_empty() {
            return Ok(Vec::new());
        }
        let history = destination.history().await?;
        let mut candidates = HashSet::new();
        let mut decisions = Vec::new();
        let mut failed = false;
        for release in releases {
            if !candidates.insert(release.url.clone()) {
                continue;
            }
            let action = if history.iter().any(|content| content.contains(&release.url)) {
                self.remember(&release.url);
                "already-announced"
            } else if self.remembered.iter().any(|url| url == &release.url) {
                "suppressed-local"
            } else if dry_run {
                "would-post"
            } else {
                match destination.post(&release).await {
                    PostOutcome::Confirmed => {
                        self.remember(&release.url);
                        "posted"
                    }
                    PostOutcome::Rejected => {
                        failed = true;
                        "rejected"
                    }
                    PostOutcome::Uncertain => {
                        self.remember(&release.url);
                        failed = true;
                        "uncertain"
                    }
                }
            };
            tracing::info!(tag = %release.tag, url = %release.url, action, "release decision");
            decisions.push(Decision {
                tag: release.tag,
                title: release.title,
                url: release.url,
                action,
            });
        }
        if failed {
            bail!("one or more announcement sends failed; uncertain URLs suppressed locally");
        }
        Ok(decisions)
    }
}
impl Source for GraphQl {
    async fn releases(&self, tags: &[String]) -> Result<Vec<Release>> {
        self.latest(tags).await
    }
}
