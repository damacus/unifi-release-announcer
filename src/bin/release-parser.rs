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
use anyhow::{Context, Result};
use clap::Parser;
use std::{
    io::{self, Write},
    path::PathBuf,
};
use unifi_release_announcer::parser::parse_feed;

#[derive(Parser)]
#[command(about = "Filter UniFi GraphQL release JSON")]
struct Args {
    json_file: PathBuf,
    #[arg(long, value_delimiter = ',')]
    tags: Vec<String>,
    #[arg(long)]
    stage: Option<String>,
    #[arg(long, allow_hyphen_values = true)]
    limit: Option<i64>,
}
fn main() -> Result<()> {
    let args = Args::parse();
    let input = std::fs::read_to_string(args.json_file).context("could not read JSON file")?;
    let input = serde_json::from_str(&input).context("invalid JSON file")?;
    let objects = parse_feed(&input, &args.tags, args.stage.as_deref(), args.limit)?;
    let mut output = io::BufWriter::new(io::stdout().lock());
    for object in objects {
        writeln!(output, "{}", python_json(&object)?)?;
    }
    Ok(())
}

// Match json.dumps(..., indent=2, ensure_ascii=True), including surrogate pairs.
fn python_json(object: &serde_json::Value) -> Result<String> {
    use std::fmt::Write;
    let mut ascii = String::new();
    for c in serde_json::to_string_pretty(object)?.chars() {
        if c < '\u{7f}' {
            ascii.push(c);
        } else {
            let mut units = [0; 2];
            for unit in c.encode_utf16(&mut units) {
                write!(ascii, "\\u{unit:04x}")?;
            }
        }
    }
    Ok(ascii)
}
