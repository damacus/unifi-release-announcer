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
    feed::feed_payload,
    parser::parse_feed,
    release::{RawRelease, Release, format_message, select_latest},
};
fn fixture() -> Value {
    serde_json::from_str(include_str!("fixtures/parity.json")).unwrap()
}
#[test]
fn reference_selection_and_formatting() {
    let f = fixture();
    let items: Vec<RawRelease> = serde_json::from_value(f["items"].clone()).unwrap();
    let tags: Vec<String> = serde_json::from_value(f["tags"].clone()).unwrap();
    let mut actual = select_latest(&items, &tags);
    let mut expected: Vec<Release> = serde_json::from_value(f["releases"].clone()).unwrap();
    actual.sort_by(|a, b| a.tag.cmp(&b.tag));
    expected.sort_by(|a, b| a.tag.cmp(&b.tag));
    assert_eq!(actual, expected);
    for case in f["formats"].as_array().unwrap() {
        let release = serde_json::from_value(case["release"].clone()).unwrap();
        assert_eq!(format_message(&release), case["message"].as_str().unwrap());
    }
}
#[test]
fn reference_graphql_query_and_variables() {
    let f = fixture();
    let tags: Vec<String> = serde_json::from_value(f["tags"].clone()).unwrap();
    let actual = feed_payload(&tags);
    assert_eq!(actual["variables"], f["payload"]["variables"]);
    let normal = |v: &Value| {
        v.as_str()
            .unwrap()
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ")
    };
    assert_eq!(normal(&actual["query"]), normal(&f["payload"]["query"]));
}
#[test]
fn reference_parser_fields_and_filters() {
    let f = fixture();
    let feed = json!({"data":{"releases":{"items":f["items"]}}});
    assert_eq!(
        parse_feed(&feed, &[], None, None).unwrap(),
        f["parsed"].as_array().unwrap().clone()
    );
    assert_eq!(
        parse_feed(&feed, &["unifi-protect".into()], Some("GA"), Some(1)).unwrap(),
        f["parser_filtered"].as_array().unwrap().clone()
    );
    assert_eq!(parse_feed(&feed, &[], None, Some(0)).unwrap().len(), 10);
    assert_eq!(parse_feed(&feed, &[], None, Some(-2)).unwrap().len(), 8);
    assert!(parse_feed(&json!({}), &[], None, None).is_err());
}
#[test]
fn parser_cli_matches_python() {
    let f = fixture();
    let input = std::env::temp_dir().join(format!("unifi-parser-{}.json", std::process::id()));
    std::fs::write(
        &input,
        json!({"data":{"releases":{"items":f["items"]}}}).to_string(),
    )
    .unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_release-parser"))
        .args([
            input.to_str().unwrap(),
            "--tags",
            "unifi-protect",
            "--stage",
            "GA",
            "--limit",
            "1",
        ])
        .output()
        .unwrap();
    std::fs::remove_file(input).unwrap();
    assert!(output.status.success());
    let actual: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(actual, f["parser_filtered"][0]);
}

#[test]
fn unicode_parser_cli_matches_python_byte_for_byte() {
    let f = fixture();
    let input =
        std::env::temp_dir().join(format!("unifi-parser-unicode-{}.json", std::process::id()));
    std::fs::write(
        &input,
        json!({"data":{"releases":{"items":f["unicode_items"]}}}).to_string(),
    )
    .unwrap();
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_release-parser"))
        .arg(&input)
        .output()
        .unwrap();
    std::fs::remove_file(input).unwrap();
    assert!(output.status.success());
    assert_eq!(
        String::from_utf8(output.stdout).unwrap(),
        f["unicode_parser_stdout"].as_str().unwrap()
    );
}
