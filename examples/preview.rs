// Open this file in Zed to compare types, fields, calls, and declarations.
use std::fmt::Display;

const READY_LIMIT: i32 = 40;

#[derive(Debug, Clone)]
struct Sample {
    name: String,
    values: Vec<i32>,
    active: bool,
}

impl Sample {
    fn new(name: &str, values: Vec<i32>) -> Self {
        Self { name: name.to_owned(), values, active: true }
    }

    fn total(&self) -> i32 {
        self.values.iter().sum()
    }

    fn label(&self) -> String {
        let state = if self.active && self.total() >= READY_LIMIT {
            "ready"
        } else {
            "idle"
        };
        format!("{}:{}:{state}", self.name, self.total())
    }
}

fn describe<T: Display>(value: &T) -> String {
    format!("{value}")
}

fn main() {
    let sample = Sample::new("zed", vec![21, 21]);
    let label = describe(&sample.label());
    assert_eq!(label, "zed:42:ready");
    println!("{label}");
}
