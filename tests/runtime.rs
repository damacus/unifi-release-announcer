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
use std::process::Command;
#[test]
fn invalid_config_fails_without_printing_token() {
    let output = Command::new(env!("CARGO_BIN_EXE_unifi-release-announcer"))
        .arg("--once")
        .env("DISCORD_BOT_TOKEN", "do-not-print-this-token")
        .env("DISCORD_CHANNEL_ID", "not-an-id")
        .output()
        .unwrap();
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("DISCORD_CHANNEL_ID"));
    assert!(!stderr.contains("do-not-print-this-token"));
}
#[test]
fn help_and_version_do_not_need_credentials() {
    for flag in ["--help", "--version"] {
        let output = Command::new(env!("CARGO_BIN_EXE_unifi-release-announcer"))
            .arg(flag)
            .env_remove("DISCORD_BOT_TOKEN")
            .env_remove("DISCORD_CHANNEL_ID")
            .output()
            .unwrap();
        assert!(output.status.success());
    }
}
