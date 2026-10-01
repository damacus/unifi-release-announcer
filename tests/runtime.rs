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
