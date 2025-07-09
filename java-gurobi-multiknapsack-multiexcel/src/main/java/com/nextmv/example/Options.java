package com.nextmv.example;

public class Options {
  private final String inputPath;
  private final String outputPath;
  private final int duration;

  public Options(String inputPath, String outputPath, int duration) {
    this.inputPath = inputPath;
    this.outputPath = outputPath;
    this.duration = duration;
  }

  public String getInputPath() {
    return this.inputPath;
  }

  public String getOutputPath() {
    return this.outputPath;
  }

  public int getDuration() {
    return this.duration;
  }

  public static Options fromArguments(String[] args) {
    // Set the default input/output directories as used by Nextmv Platform.
    // All input files are placed in the "inputs" directory, prior to the run.
    // And all output files will get collected in the "solutions" directory, after
    // the run.
    String inputPath = "inputs/";
    String outputPath = "outputs/";
    int duration = 30;

    for (int i = 0; i < args.length; ++i) {
      // Handle platform option style with '=' separators
      if (args[i].startsWith("-d=")) {
        duration = Integer.parseInt(args[i].substring("-d=".length()));
        continue;
      } else if (args[i].startsWith("-duration=")) {
        duration = Integer.parseInt(args[i].substring("-duration=".length()));
        continue;
      }
      switch (args[i]) {
        case "-i":
        case "--input":
          inputPath = args[++i];
          break;
        case "-o":
        case "--output":
          outputPath = args[++i];
          break;
        case "-d":
        case "--duration":
          duration = Integer.parseInt(args[++i]);
          break;
        case "-h":
        case "--help":
          System.out.println("Usage: java -jar basic_example.jar [OPTIONS]");
          System.out.println("Solve a simple linear program.");
          System.out.println();
          System.out.println("Supported options:");
          System.out.println("  -i, --input: path to the input directory");
          System.out.println("  -o, --output: path to the output directory");
          System.out.println("  -d, --duration: duration of the search in seconds");
          System.out.println("  -h, --help: print the help");
          System.exit(0);
          break;
        default:
          System.err.println("Unknown argument: '" + args[i] + "'");
          System.exit(1);
      }
    }

    return new Options(inputPath, outputPath, duration);
  }
}
