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
        writeln!(output, "{}", serde_json::to_string_pretty(&object)?)?;
    }
    Ok(())
}
