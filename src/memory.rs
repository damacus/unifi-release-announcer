use serde::{Deserialize, Serialize};
use std::collections::HashSet;

#[derive(Debug, Serialize)]
pub struct Sample {
    pub at: String,
    pub working_set_bytes: u64,
    pub phase: Option<String>,
    pub latest_poll_success: Option<bool>,
    pub latest_poll_at: Option<String>,
    pub elapsed_seconds: f64,
}

#[derive(Default)]
pub struct Acceptance {
    samples: u64,
    peak: u64,
    idle_peak: u64,
    successful_polls: HashSet<String>,
    failures: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Summary {
    pub container: String,
    pub image_id: Option<String>,
    pub duration_seconds: f64,
    pub samples: u64,
    pub successful_polls: usize,
    pub idle_peak_bytes: u64,
    pub peak_bytes: u64,
    pub failures: Vec<String>,
    pub passed_24h_gate: bool,
}

impl Acceptance {
    pub fn observe(&mut self, sample: &Sample) -> bool {
        self.samples += 1;
        self.peak = self.peak.max(sample.working_set_bytes);
        if sample.phase.as_deref() == Some("idle") && sample.elapsed_seconds >= 60.0 {
            self.idle_peak = self.idle_peak.max(sample.working_set_bytes);
        }
        if sample.latest_poll_success == Some(true) {
            if let Some(at) = &sample.latest_poll_at {
                self.successful_polls.insert(at.clone());
            }
        } else if sample.latest_poll_success == Some(false) {
            self.fail("poll failure observed");
        }
        if self.peak > 64 * 1024 * 1024 || self.idle_peak > 32 * 1024 * 1024 {
            self.fail("memory threshold exceeded");
        }
        self.failures.is_empty()
    }

    pub fn fail(&mut self, error: &str) {
        self.failures.push(error.to_string());
    }

    #[must_use]
    pub fn finish(self, container: String, image_id: Option<String>, elapsed: f64) -> Summary {
        let passed = self.failures.is_empty()
            && elapsed >= 86400.0
            && self.idle_peak > 0
            && self.successful_polls.len() >= 140;
        Summary {
            container,
            image_id,
            duration_seconds: elapsed,
            samples: self.samples,
            successful_polls: self.successful_polls.len(),
            idle_peak_bytes: self.idle_peak,
            peak_bytes: self.peak,
            failures: self.failures,
            passed_24h_gate: passed,
        }
    }
}

// The f64->u64 cast is guarded by the ensure! above: finite, non-negative,
// and strictly below 2^64 — no truncation, sign loss, or UB is possible.
#[allow(
    clippy::as_conversions,
    clippy::cast_possible_truncation,
    clippy::cast_sign_loss
)]
pub fn working_set(usage: &str) -> anyhow::Result<u64> {
    let amount = usage.split('/').next().unwrap_or_default().trim();
    let number_end = amount
        .find(|c: char| !c.is_ascii_digit() && c != '.')
        .unwrap_or(amount.len());
    let number: f64 = amount[..number_end].parse()?;
    let unit = amount[number_end..].trim();
    let multiplier = match unit {
        "B" => 1.0,
        "kB" => 1_000.0,
        "MB" => 1_000_000.0,
        "GB" => 1_000_000_000.0,
        "KiB" => 1024.0,
        "MiB" => 1_048_576.0,
        "GiB" => 1_073_741_824.0,
        _ => anyhow::bail!("unrecognised Docker memory units"),
    };
    let bytes = number * multiplier;
    anyhow::ensure!(
        // 2^64 in f64 — u64::MAX itself is not exactly representable.
        bytes.is_finite() && (0.0..18_446_744_073_709_551_616.0).contains(&bytes),
        "invalid Docker memory value"
    );
    Ok(bytes as u64)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn observed(at: &str, elapsed: f64, memory: u64) -> Sample {
        Sample {
            at: at.into(),
            working_set_bytes: memory,
            phase: Some("idle".into()),
            latest_poll_success: Some(true),
            latest_poll_at: Some(at.into()),
            elapsed_seconds: elapsed,
        }
    }
    #[test]
    fn duration_poll_count_and_thresholds_are_all_required() {
        let mut gate = Acceptance::default();
        for n in 0..140 {
            assert!(gate.observe(&observed(&n.to_string(), 60.0, 1024)));
        }
        assert!(!gate.finish("test".into(), None, 86399.0).passed_24h_gate);
        let mut gate = Acceptance::default();
        for n in 0..139 {
            gate.observe(&observed(&n.to_string(), 60.0, 1024));
        }
        assert!(!gate.finish("test".into(), None, 86400.0).passed_24h_gate);
        let mut gate = Acceptance::default();
        for n in 0..140 {
            gate.observe(&observed(&n.to_string(), 60.0, 32 * 1024 * 1024));
        }
        assert!(gate.finish("test".into(), None, 86400.0).passed_24h_gate);
    }
    #[test]
    fn repeated_polls_failures_and_idle_overage_cannot_pass() {
        for failure in [false, true] {
            let mut gate = Acceptance::default();
            for _ in 0..144 {
                gate.observe(&observed("same", 60.0, 1024));
            }
            if failure {
                gate.fail("observer failed");
            }
            assert!(!gate.finish("test".into(), None, 86400.0).passed_24h_gate);
        }
        let mut gate = Acceptance::default();
        assert!(!gate.observe(&observed("poll", 60.0, 32 * 1024 * 1024 + 1)));
        let mut startup = observed("poll", 0.0, 64 * 1024 * 1024 + 1);
        startup.phase = Some("polling".into());
        assert!(!Acceptance::default().observe(&startup));
    }
    #[test]
    fn docker_units_and_malformed_values() {
        assert_eq!(working_set("2.5MiB / 100MiB").unwrap(), 2_621_440);
        assert_eq!(working_set("900kB / 1GB").unwrap(), 900_000);
        for invalid in ["NaNMiB", "2TB", "-1MiB", "infB", "", "1.2.3MiB"] {
            assert!(working_set(invalid).is_err(), "{invalid}");
        }
    }
}
