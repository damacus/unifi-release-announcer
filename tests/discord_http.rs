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
use serde_json::{Value, json};
use unifi_release_announcer::{
    discord::DiscordHttp,
    pipeline::{Destination, PostOutcome},
    release::Release,
};
use wiremock::{
    Mock, MockServer, ResponseTemplate,
    matchers::{method, path, query_param},
};

fn channel(id: u64, kind: u8, parent: Option<u64>) -> Value {
    json!({"id":id.to_string(),"guild_id":"42","type":kind,"name":"unifi","position":0,
        "permission_overwrites":[],"nsfw":false,"parent_id":parent.map(|v|v.to_string()),
        "thread_metadata":{"archived":false,"auto_archive_duration":1440,
            "archive_timestamp":"2026-10-01T00:00:00Z","locked":false,"invitable":false},
        "available_tags":[],"flags":0})
}
fn message(id: u64, content: &str) -> Value {
    json!({"id":id.to_string(),"channel_id":"10","author":{"id":"42","username":"bot","discriminator":"0","avatar":null},
        "content":content,"timestamp":"2026-10-01T00:00:00Z","edited_timestamp":null,
        "tts":false,"mention_everyone":false,"mentions":[],"mention_roles":[],
        "attachments":[],"embeds":[],"pinned":false,"type":0,"components":[]})
}
fn release() -> Release {
    Release {
        title: "UniFi Application (GA)".into(),
        url: "https://community.ui.com/releases/app/id".into(),
        tag: "unifi-protect".into(),
    }
}
async fn mount_channel(server: &MockServer, kind: u8) {
    Mock::given(method("GET"))
        .and(path("/api/v10/channels/10"))
        .respond_with(ResponseTemplate::new(200).set_body_json(channel(10, kind, None)))
        .mount(server)
        .await;
}
fn client(server: &MockServer) -> DiscordHttp {
    DiscordHttp::with_proxy("synthetic", 10, Some(&server.uri())).unwrap()
}

#[tokio::test]
async fn text_history_reads_second_page() {
    let server = MockServer::start().await;
    mount_channel(&server, 0).await;
    let first: Vec<_> = (102..202).rev().map(|id| message(id, "filler")).collect();
    let second: Vec<_> = (2..102)
        .rev()
        .map(|id| {
            message(
                id,
                if id == 2 {
                    "https://community.ui.com/releases/app/id"
                } else {
                    "filler"
                },
            )
        })
        .collect();
    Mock::given(path("/api/v10/channels/10/messages"))
        .and(query_param("limit", "100"))
        .respond_with(ResponseTemplate::new(200).set_body_json(first))
        .up_to_n_times(1)
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(path("/api/v10/channels/10/messages"))
        .and(query_param("before", "102"))
        .respond_with(ResponseTemplate::new(200).set_body_json(second))
        .expect(1)
        .mount(&server)
        .await;
    let history = client(&server).history().await.unwrap();
    assert_eq!(history.len(), 200);
    assert!(history.iter().any(|v| v.contains(&release().url)));
}
#[tokio::test]
async fn partial_history_failure_discards_results() {
    let server = MockServer::start().await;
    mount_channel(&server, 0).await;
    let first: Vec<_> = (102..202).rev().map(|id| message(id, "filler")).collect();
    Mock::given(path("/api/v10/channels/10/messages"))
        .respond_with(ResponseTemplate::new(200).set_body_json(first))
        .up_to_n_times(1)
        .mount(&server)
        .await;
    Mock::given(path("/api/v10/channels/10/messages"))
        .and(query_param("before", "102"))
        .respond_with(
            ResponseTemplate::new(403)
                .set_body_json(json!({"code":50013,"message":"missing permission"})),
        )
        .mount(&server)
        .await;
    assert!(client(&server).history().await.is_err());
}
#[tokio::test]
async fn forum_history_uses_active_and_archived_starters() {
    let server = MockServer::start().await;
    mount_channel(&server, 15).await;
    Mock::given(path("/api/v10/guilds/42/threads/active"))
        .respond_with(ResponseTemplate::new(200).set_body_json(
            json!({"threads":[channel(20,11,Some(10)),channel(99,11,Some(98))],"members":[]}),
        ))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(path("/api/v10/channels/10/threads/archived/public"))
        .and(query_param("limit", "50"))
        .respond_with(ResponseTemplate::new(200).set_body_json(
            json!({"threads":[channel(30,11,Some(10))],"members":[],"has_more":false}),
        ))
        .expect(1)
        .mount(&server)
        .await;
    for id in [20, 30] {
        Mock::given(path(format!("/api/v10/channels/{id}/messages/{id}")))
            .respond_with(
                ResponseTemplate::new(200).set_body_json(message(id, &format!("starter {id}"))),
            )
            .expect(1)
            .mount(&server)
            .await;
    }
    assert_eq!(
        client(&server).history().await.unwrap(),
        ["starter 20", "starter 30"]
    );
}
#[tokio::test]
async fn text_post_disables_mentions() {
    let server = MockServer::start().await;
    mount_channel(&server, 0).await;
    Mock::given(method("POST"))
        .and(path("/api/v10/channels/10/messages"))
        .respond_with(ResponseTemplate::new(200).set_body_json(message(50, "announcement")))
        .expect(1)
        .mount(&server)
        .await;
    assert_eq!(
        client(&server).post(&release()).await,
        PostOutcome::Confirmed
    );
    let requests = server.received_requests().await.unwrap();
    let post = requests.iter().find(|r| r.method == "POST").unwrap();
    let payload: Value = serde_json::from_slice(&post.body).unwrap();
    assert_eq!(payload["allowed_mentions"]["parse"], json!([]));
    assert!(
        payload["content"]
            .as_str()
            .unwrap()
            .contains(&release().url)
    );
}
#[tokio::test]
async fn forum_post_creates_starter() {
    let server = MockServer::start().await;
    mount_channel(&server, 15).await;
    Mock::given(method("POST"))
        .and(path("/api/v10/channels/10/threads"))
        .respond_with(ResponseTemplate::new(200).set_body_json(channel(30, 11, Some(10))))
        .expect(1)
        .mount(&server)
        .await;
    assert_eq!(
        client(&server).post(&release()).await,
        PostOutcome::Confirmed
    );
    let requests = server.received_requests().await.unwrap();
    let post = requests.iter().find(|r| r.method == "POST").unwrap();
    let body = String::from_utf8_lossy(&post.body);
    assert!(body.contains("UniFi Release:"));
    assert!(body.contains(&release().url));
    assert!(body.contains("allowed_mentions"));
}
#[tokio::test]
async fn failed_post_is_not_retried() {
    for (status, outcome) in [
        (403, PostOutcome::Rejected),
        (429, PostOutcome::Rejected),
        (500, PostOutcome::Uncertain),
    ] {
        let server = MockServer::start().await;
        mount_channel(&server, 0).await;
        Mock::given(method("POST"))
            .and(path("/api/v10/channels/10/messages"))
            .respond_with(
                ResponseTemplate::new(status).set_body_json(json!({"code":0,"message":"failure"})),
            )
            .expect(1)
            .mount(&server)
            .await;
        assert_eq!(client(&server).post(&release()).await, outcome);
    }
}
#[tokio::test]
async fn oversized_message_never_posts() {
    let server = MockServer::start().await;
    let mut release = release();
    release.title = "💻".repeat(2000);
    assert_eq!(client(&server).post(&release).await, PostOutcome::Rejected);
    assert!(server.received_requests().await.unwrap().is_empty());
}

#[tokio::test]
async fn verification_reads_and_deletes_only_its_returned_message() {
    let server = MockServer::start().await;
    let content = "[Rust migration verification — no release announcement]";
    Mock::given(method("POST"))
        .and(path("/api/v10/channels/10/messages"))
        .respond_with(ResponseTemplate::new(200).set_body_json(message(50, content)))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/api/v10/channels/10/messages/50"))
        .respond_with(ResponseTemplate::new(200).set_body_json(message(50, content)))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("DELETE"))
        .and(path("/api/v10/channels/10/messages/50"))
        .respond_with(ResponseTemplate::new(204))
        .expect(1)
        .mount(&server)
        .await;
    client(&server).verification_message().await.unwrap();
}

#[tokio::test]
async fn verification_attempts_cleanup_when_read_back_fails() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/api/v10/channels/10/messages"))
        .respond_with(ResponseTemplate::new(200).set_body_json(message(50, "verification")))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/api/v10/channels/10/messages/50"))
        .respond_with(
            ResponseTemplate::new(500).set_body_json(json!({"code":0,"message":"failed"})),
        )
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("DELETE"))
        .and(path("/api/v10/channels/10/messages/50"))
        .respond_with(ResponseTemplate::new(204))
        .expect(1)
        .mount(&server)
        .await;
    assert!(client(&server).verification_message().await.is_err());
}
