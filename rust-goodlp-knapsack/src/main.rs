use std::error::Error;
use std::fs::File;
use std::io::{self, Read, Write};
use std::time::Duration;
use std::time::Instant;

use clap::Parser;
use good_lp::{
    Expression, ProblemVariables, Solution, SolverModel, Variable, WithTimeLimit, constraint,
    default_solver, variable,
};
use serde::{Deserialize, Serialize};

#[derive(Parser, Debug)]
#[command(name = "goodlp-knapsack")]
#[command(about = "Solve a knapsack problem using good_lp", long_about = None)]
struct Cli {
    /// Input JSON file; if not provided, read from stdin
    #[arg(short, long)]
    input: Option<String>,

    /// Output JSON file; if not provided, write to stdout
    #[arg(short, long)]
    output: Option<String>,

    /// Maximum solve duration in seconds (default: 30)
    #[arg(short = 'd', long = "duration", default_value_t = 30)]
    duration_secs: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct Item {
    id: String,
    value: f64,
    weight: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct Input {
    items: Vec<Item>,
    weight_capacity: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputOptions {
    input: String,
    output: String,
    duration: i64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputSolution {
    items: Vec<Item>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputStatisticsResultCustom {
    status: String,
    num_items: usize,
    num_selected: usize,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputStatisticsResult {
    value: f64,
    custom: OutputStatisticsResultCustom,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputStatisticsRun {
    duration: f64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct OutputStatistics {
    run: OutputStatisticsRun,
    result: OutputStatisticsResult,
    schema: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct Output {
    options: OutputOptions,
    solution: OutputSolution,
    statistics: OutputStatistics,
    assets: Vec<serde_json::Value>,
}

fn read_input(cli: &Cli) -> Result<(Input, String), Box<dyn Error>> {
    let mut buf = String::new();
    let input_source = if let Some(path) = &cli.input {
        eprintln!("Reading input from {}", path);
        let mut f = File::open(path)?;
        f.read_to_string(&mut buf)?;
        path.clone()
    } else {
        eprintln!("Reading input from stdin");
        let mut stdin = io::stdin();
        stdin.read_to_string(&mut buf)?;
        String::new()
    };
    let parsed: Input = serde_json::from_str(&buf)?;
    Ok((parsed, input_source))
}

fn write_output(cli: &Cli, output: &Output) -> Result<(), Box<dyn Error>> {
    let json = serde_json::to_string_pretty(output)?;
    match &cli.output {
        Some(path) => {
            eprintln!("Writing output to {}", path);
            let mut f = File::create(path)?;
            f.write_all(json.as_bytes())?;
        }
        None => {
            let mut stdout = io::stdout();
            stdout.write_all(json.as_bytes())?;
        }
    }
    Ok(())
}

fn solve_knapsack(
    data: &Input,
    max_duration: Duration,
) -> Result<(Vec<Item>, f64, String), Box<dyn Error>> {
    let n = data.items.len();
    let mut vars = ProblemVariables::new();
    let x: Vec<Variable> = (0..n)
        .map(|i| vars.add(variable().binary().name(&format!("x_{i}"))))
        .collect();

    let objective_expr: Expression = x
        .iter()
        .enumerate()
        .map(|(i, v)| data.items[i].value * *v)
        .sum();

    let mut model = vars
        .maximise(objective_expr.clone())
        .using(default_solver)
        .with_time_limit(max_duration.as_secs_f64());

    // capacity constraint
    let weight_expr: Expression = x
        .iter()
        .enumerate()
        .map(|(i, v)| data.items[i].weight * *v)
        .sum();
    model = model.with(constraint!(weight_expr <= data.weight_capacity));

    let solution = model.solve()?;
    let mut chosen = Vec::new();
    for i in 0..n {
        let take = solution.value(x[i]);
        if take.round() as i32 == 1 {
            chosen.push(data.items[i].clone());
        }
    }
    let objective = solution.eval(objective_expr);

    let status = format!("{:?}", solution.status());
    Ok((chosen, objective, status))
}

fn main() -> Result<(), Box<dyn Error>> {
    let cli = Cli::parse();
    let start = Instant::now();
    let (input_data, input_path) = read_input(&cli)?;

    let (chosen_items, objective_value, status) =
        solve_knapsack(&input_data, Duration::from_secs(cli.duration_secs))?;

    let duration_run = start.elapsed().as_secs_f64();

    // options block
    let options = OutputOptions {
        input: input_path,
        output: cli.output.clone().unwrap_or_default(),
        duration: cli.duration_secs as i64,
    };

    let num_items = input_data.items.len();
    let num_selected = chosen_items.len();
    let solution = OutputSolution {
        items: chosen_items,
    };

    let statistics = OutputStatistics {
        run: OutputStatisticsRun {
            duration: duration_run,
        },
        result: OutputStatisticsResult {
            value: objective_value,
            custom: OutputStatisticsResultCustom {
                status,
                num_items,
                num_selected,
            },
        },
        schema: "v1".to_string(),
    };

    let output = Output {
        options,
        solution,
        statistics,
        assets: vec![],
    };

    write_output(&cli, &output)?;
    Ok(())
}
