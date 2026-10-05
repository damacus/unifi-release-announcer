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
use anyhow::{Result, bail};
use std::{
    cell::{Cell, RefCell},
    collections::VecDeque,
};
use unifi_release_announcer::{
    pipeline::{Destination, PollState, PostOutcome, Source},
    release::Release,
};

struct Feed {
    releases: Vec<Release>,
    fails: Cell<bool>,
}
impl Source for Feed {
    async fn releases(&self, _: &[String]) -> Result<Vec<Release>> {
        if self.fails.get() {
            bail!("feed failure");
        }
        Ok(self.releases.clone())
    }
}
struct Target {
    history: RefCell<Vec<String>>,
    fails: Cell<bool>,
    sends: Cell<usize>,
    outcomes: RefCell<VecDeque<PostOutcome>>,
}
impl Destination for Target {
    async fn history(&self) -> Result<Vec<String>> {
        if self.fails.get() {
            bail!("history failure");
        }
        Ok(self.history.borrow().clone())
    }
    async fn post(&self, _: &Release) -> PostOutcome {
        self.sends.set(self.sends.get() + 1);
        self.outcomes
            .borrow_mut()
            .pop_front()
            .unwrap_or(PostOutcome::Confirmed)
    }
}
fn setup() -> (Feed, Target, PollState) {
    let release = Release {
        title: "UniFi Application (GA)".into(),
        url: "https://community.ui.com/releases/a/id".into(),
        tag: "unifi-protect".into(),
    };
    (
        Feed {
            releases: vec![release],
            fails: Cell::new(false),
        },
        Target {
            history: RefCell::new(vec![]),
            fails: Cell::new(false),
            sends: Cell::new(0),
            outcomes: RefCell::new(VecDeque::new()),
        },
        PollState::default(),
    )
}
#[tokio::test]
async fn duplicate_tags_and_repeated_polls_send_once() {
    let (mut feed, target, mut state) = setup();
    let mut copy = feed.releases[0].clone();
    copy.tag = "unifi-network".into();
    feed.releases.push(copy);
    assert_eq!(
        state.poll(&feed, &target, &[], false).await.unwrap().len(),
        1
    );
    state.poll(&feed, &target, &[], false).await.unwrap();
    assert_eq!(target.sends.get(), 1);
}
#[tokio::test]
async fn history_failure_prevents_posting_and_recovers() {
    let (feed, target, mut state) = setup();
    target.fails.set(true);
    assert!(state.poll(&feed, &target, &[], false).await.is_err());
    assert_eq!(target.sends.get(), 0);
    target.fails.set(false);
    state.poll(&feed, &target, &[], false).await.unwrap();
    assert_eq!(target.sends.get(), 1);
}
#[tokio::test]
async fn source_failure_leaves_future_polls_possible() {
    let (feed, target, mut state) = setup();
    feed.fails.set(true);
    assert!(state.poll(&feed, &target, &[], false).await.is_err());
    assert_eq!(target.sends.get(), 0);
    feed.fails.set(false);
    state.poll(&feed, &target, &[], false).await.unwrap();
    assert_eq!(target.sends.get(), 1);
}
#[tokio::test]
async fn dry_run_does_not_post_or_mark_success() {
    let (feed, target, mut state) = setup();
    assert_eq!(
        state.poll(&feed, &target, &[], true).await.unwrap()[0].action,
        "would-post"
    );
    assert_eq!(target.sends.get(), 0);
    state.poll(&feed, &target, &[], false).await.unwrap();
    assert_eq!(target.sends.get(), 1);
}
#[tokio::test]
async fn uncertain_send_is_not_replayed_and_history_is_reconciled() {
    let (feed, target, mut state) = setup();
    target
        .outcomes
        .borrow_mut()
        .push_back(PostOutcome::Uncertain);
    assert!(state.poll(&feed, &target, &[], false).await.is_err());
    assert_eq!(
        state.poll(&feed, &target, &[], false).await.unwrap()[0].action,
        "suppressed-local"
    );
    target
        .history
        .borrow_mut()
        .push(feed.releases[0].url.clone());
    assert_eq!(
        state.poll(&feed, &target, &[], false).await.unwrap()[0].action,
        "already-announced"
    );
    assert_eq!(target.sends.get(), 1);
}
#[tokio::test]
async fn rejected_send_does_not_mark_success() {
    let (feed, target, mut state) = setup();
    target
        .outcomes
        .borrow_mut()
        .push_back(PostOutcome::Rejected);
    assert!(state.poll(&feed, &target, &[], false).await.is_err());
    state.poll(&feed, &target, &[], false).await.unwrap();
    assert_eq!(target.sends.get(), 2);
}
#[tokio::test]
async fn restart_uses_discord_history() {
    let (feed, target, mut state) = setup();
    target.history.borrow_mut().push(format!(
        "previous [{}]({})",
        feed.releases[0].title, feed.releases[0].url
    ));
    state.poll(&feed, &target, &[], false).await.unwrap();
    PollState::default()
        .poll(&feed, &target, &[], false)
        .await
        .unwrap();
    assert_eq!(target.sends.get(), 0);
}
