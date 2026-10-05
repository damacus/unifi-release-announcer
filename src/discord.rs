use crate::{
    pipeline::{Destination, PostOutcome},
    release::{Release, format_message},
};
use anyhow::{Result, bail};
use serde_json::{Value, json};
use serenity::{
    http::{Http, HttpBuilder, MessagePagination},
    model::{
        channel::{Channel, ChannelType},
        id::{ChannelId, MessageId},
    },
};
use std::time::Duration;

pub struct DiscordHttp {
    http: Http,
    channel_id: ChannelId,
}

fn safe_error(error: &serenity::Error) -> anyhow::Error {
    match error {
        serenity::Error::Http(e) if e.status_code().is_some() => anyhow::anyhow!(
            "Discord HTTP status {}",
            e.status_code().map_or(0, |s| s.as_u16())
        ),
        _ => anyhow::anyhow!("Discord request failed"),
    }
}

#[must_use]
pub fn classify_send_error(error: &serenity::Error) -> PostOutcome {
    if let serenity::Error::Http(e) = error
        && let Some(status) = e.status_code()
        && status.is_client_error()
        && status.as_u16() != 408
    {
        return PostOutcome::Rejected;
    }
    PostOutcome::Uncertain
}

impl DiscordHttp {
    pub fn new(token: &str, channel_id: u64) -> Result<Self> {
        Self::with_proxy(token, channel_id, None)
    }
    pub fn with_proxy(token: &str, channel_id: u64, proxy: Option<&str>) -> Result<Self> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .redirect(reqwest::redirect::Policy::none())
            .build()?;
        let mut builder = HttpBuilder::new(token).client(client);
        if let Some(proxy) = proxy {
            builder = builder.proxy(proxy).ratelimiter_disabled(true);
        }
        Ok(Self {
            http: builder.build(),
            channel_id: ChannelId::new(channel_id),
        })
    }
    pub async fn validate(&self) -> Result<()> {
        tokio::time::timeout(Duration::from_secs(30), async {
            self.http
                .get_current_user()
                .await
                .map_err(|e| safe_error(&e))?;
            let channel = self
                .http
                .get_channel(self.channel_id)
                .await
                .map_err(|e| safe_error(&e))?;
            match channel {
                Channel::Guild(ref c) if supported(c.kind) => Ok(()),
                Channel::Private(_) => Ok(()),
                _ => bail!("unsupported Discord channel"),
            }
        })
        .await
        .map_err(|_| anyhow::anyhow!("Discord startup timed out"))?
    }
    async fn load_history(&self) -> Result<Vec<String>> {
        let channel = self
            .http
            .get_channel(self.channel_id)
            .await
            .map_err(|e| safe_error(&e))?;
        if let Channel::Guild(channel) = &channel
            && channel.kind == ChannelType::Forum
        {
            let active = self
                .http
                .get_guild_active_threads(channel.guild_id)
                .await
                .map_err(|e| safe_error(&e))?;
            let archived = self
                .http
                .get_channel_archived_public_threads(self.channel_id, None, Some(50))
                .await
                .map_err(|e| safe_error(&e))?;
            let mut contents = Vec::new();
            let mut visited = std::collections::HashSet::new();
            for thread in active
                .threads
                .iter()
                .filter(|t| t.parent_id == Some(self.channel_id))
                .chain(archived.threads.iter().take(50))
            {
                if !visited.insert(thread.id) {
                    continue;
                }
                let message = self
                    .http
                    .get_message(thread.id, MessageId::new(thread.id.get()))
                    .await
                    .map_err(|e| safe_error(&e))?;
                contents.push(message.content);
            }
            return Ok(contents);
        }
        match channel {
            Channel::Guild(ref c) if supported(c.kind) => {}
            Channel::Private(_) => {}
            _ => bail!("unsupported Discord channel"),
        }
        let mut contents = Vec::new();
        let mut before = None;
        while contents.len() < 200 {
            // Bounded to [1, 100] by the loop guard and min() — the fallback is unreachable.
            let limit = u8::try_from((200 - contents.len()).min(100)).unwrap_or(100);
            let messages = self
                .http
                .get_messages(
                    self.channel_id,
                    before.map(MessagePagination::Before),
                    Some(limit),
                )
                .await
                .map_err(|e| safe_error(&e))?;
            let count = messages.len();
            if count == 0 {
                break;
            }
            let next = messages.iter().map(|m| m.id).min();
            if next == before {
                bail!("Discord history pagination did not advance");
            }
            before = next;
            contents.extend(messages.into_iter().map(|m| m.content));
            if count < usize::from(limit) {
                break;
            }
        }
        Ok(contents)
    }
    pub async fn verification_message(&self) -> Result<()> {
        let message = json!({
            "content": "[Rust migration verification — no release announcement]",
            "allowed_mentions": {"parse": [], "replied_user": false}
        });
        let sent = tokio::time::timeout(
            Duration::from_secs(30),
            self.http.send_message(self.channel_id, vec![], &message),
        )
        .await
        .map_err(|_| {
            anyhow::anyhow!("verification send outcome uncertain; inspect channel before retry")
        })?
        .map_err(|e| safe_error(&e))?;
        tracing::info!(message_id = %sent.id, "verification message sent");
        // Keep a separate cleanup budget even if read-back fails or times out.
        // Three bounded stages cap the complete lifecycle at 90 seconds.
        let check = tokio::time::timeout(
            Duration::from_secs(30),
            self.http.get_message(self.channel_id, sent.id),
        )
        .await
        .map_err(|_| anyhow::anyhow!("verification read-back timed out"))
        .and_then(|result| result.map_err(|e| safe_error(&e)));
        let cleanup = tokio::time::timeout(
            Duration::from_secs(30),
            self.http.delete_message(self.channel_id, sent.id, None),
        )
        .await
        .map_err(|_| anyhow::anyhow!("verification cleanup timed out; remove message {}", sent.id))
        .and_then(|result| result.map_err(|e| safe_error(&e)));
        cleanup?;
        let check = check?;
        if check.content
            != message
                .get("content")
                .and_then(Value::as_str)
                .unwrap_or_default()
        {
            bail!("verification message content mismatch");
        }
        tracing::info!(message_id = %sent.id, "verification message read back and removed");
        Ok(())
    }
}

const fn supported(kind: ChannelType) -> bool {
    matches!(
        kind,
        ChannelType::Text
            | ChannelType::News
            | ChannelType::Forum
            | ChannelType::PublicThread
            | ChannelType::PrivateThread
            | ChannelType::NewsThread
    )
}

impl Destination for DiscordHttp {
    async fn history(&self) -> Result<Vec<String>> {
        tokio::time::timeout(Duration::from_secs(120), self.load_history())
            .await
            .map_err(|_| anyhow::anyhow!("Discord history timed out; posting skipped"))?
    }
    async fn post(&self, release: &Release) -> PostOutcome {
        let content = format_message(release);
        if content.encode_utf16().count() > 2000 {
            return PostOutcome::Rejected;
        }
        let action = async {
            let channel = self
                .http
                .get_channel(self.channel_id)
                .await
                .map_err(|_| PostOutcome::Rejected)?;
            let payload = json!({"content": content, "allowed_mentions": {"parse": [], "replied_user": false}});
            let result = if matches!(channel, Channel::Guild(ref c) if c.kind == ChannelType::Forum)
            {
                let name = format!("UniFi Release: {}", release.title);
                if name.encode_utf16().count() > 100 {
                    return Err(PostOutcome::Rejected);
                }
                self.http
                    .create_forum_post(
                        self.channel_id,
                        &json!({"name": name, "message": payload}),
                        None,
                    )
                    .await
                    .map(|_| ())
            } else {
                self.http
                    .send_message(self.channel_id, vec![], &payload)
                    .await
                    .map(|_| ())
            };
            result.map_err(|e| classify_send_error(&e))
        };
        match tokio::time::timeout(Duration::from_secs(30), action).await {
            Ok(Ok(())) => PostOutcome::Confirmed,
            Ok(Err(outcome)) => outcome,
            Err(_) => PostOutcome::Uncertain,
        }
    }
}
