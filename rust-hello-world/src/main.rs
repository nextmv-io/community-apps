use std::env;
use std::io::{self, BufRead, Write};

fn main() {
    // Write all command-line arguments to stderr
    let args: Vec<String> = env::args().collect();
    let mut stderr = io::stderr();
    writeln!(stderr, "arguments:").expect("Unable to write to stderr");
    for arg in &args {
        writeln!(stderr, "- {}", arg).expect("Unable to write to stderr");
    }

    // Read from stdin and write to stdout
    let stdin = io::stdin();
    let handle = stdin.lock();
    let mut stdout = io::stdout();

    for line in handle.lines() {
        let line = line.expect("Unable to read line from stdin");
        writeln!(stdout, "{}", line).expect("Unable to write to stdout");
    }
}
