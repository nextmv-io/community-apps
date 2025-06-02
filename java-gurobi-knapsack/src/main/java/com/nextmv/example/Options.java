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
    String inputPath = "";
    String outputPath = "";
    int duration = 30;

    for (int i = 0; i < args.length; ++i) {
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
          System.out.println("  -i, --input: path to the input file");
          System.out.println("  -o, --output: path to the output file");
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
