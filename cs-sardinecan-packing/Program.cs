using CommandLine;
using SC.Core.Heuristics.PrimalHeuristic;
using SC.Core.ObjectModel;
using SC.Core.ObjectModel.Additionals;
using SC.Core.ObjectModel.Configuration;
using SC.Core.ObjectModel.Interfaces;
using SC.Core.ObjectModel.IO;
using SC.Core.ObjectModel.IO.Json;
using SC.Core.Linear;
using System.Globalization;
using System.Xml.Serialization;


class Options
{
    [Option('i', "input", Required = false, HelpText = "Input file to process")]
    public string? Input { get; set; }

    [Option('c', "config", Required = false, HelpText = "Path to configuration file")]
    public string? Configuration { get; set; }

    [Option('o', "output", Required = false, HelpText = "Output file to write to")]
    public string? Output { get; set; }
}

/// <summary>
/// The main program class.
/// </summary>
class Program
{
    /// <summary>
    /// The main entry point of the program.
    /// </summary>
    private static void Main(string[] args)
    {
        Parser.Default.ParseArguments<Options>(args)
            .WithParsed(Execute);
    }

    /// <summary>
    /// Reads content from a file or stdin.
    /// </summary>
    private static (string?, string) ReadContent(string path)
    {
        try
        {
            return (string.IsNullOrWhiteSpace(path) ? Console.In.ReadToEnd() : File.ReadAllText(path), string.Empty);
        }
        catch (IOException ex)
        {
            if (string.IsNullOrWhiteSpace(path))
                return (null, $"Error reading from standard input: {ex.Message}");
            else
                return (null, $"Error reading file '{path}': {ex.Message}");
        }
        catch (UnauthorizedAccessException ex)
        {
            if (string.IsNullOrWhiteSpace(path))
                return (null, $"Access denied reading from standard input: {ex.Message}");
            else
                return (null, $"Access denied reading file '{path}': {ex.Message}");
        }
    }

    /// <summary>
    /// Write output to a file or stdout.
    /// </summary>
    private static void WriteOutput(string? path, string content)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(path))
                Console.WriteLine(content);
            else
                File.WriteAllText(path, content);
        }
        catch (IOException ex)
        {
            if (string.IsNullOrWhiteSpace(path))
                Console.WriteLine($"Error writing to standard output: {ex.Message}");
            else
                Console.WriteLine($"Error writing file '{path}': {ex.Message}");
        }
        catch (UnauthorizedAccessException ex)
        {
            if (string.IsNullOrWhiteSpace(path))
                Console.WriteLine($"Access denied writing to standard output: {ex.Message}");
            else
                Console.WriteLine($"Access denied writing file '{path}': {ex.Message}");
        }
    }

    /// <summary>
    /// Executes the program with the given options.
    /// </summary>
    private static void Execute(Options opts)
    {
        // Read the content fully first (either from file or from stdin)
        var (content, inputErr) = ReadContent(opts.Input ?? string.Empty);
        if (content == null)
        {
            Console.WriteLine(inputErr);
            return;
        }

        // Try to parse the input as a calculation
        var instance = JsonIO.From<JsonCalculation>(content);

        // If nothing useful was found, try to parse it as an unnested instance (without a configuration)
        if (instance?.Instance == null && instance?.Configuration == null)
        {
            var inst = JsonIO.From<JsonInstance>(content);
            if (inst != null)
                instance = new JsonCalculation() { Instance = inst };

            // If still nothing useful was found, abort
            if (instance?.Instance == null)
            {
                Console.WriteLine("No 'instance' found in input file.");
                return;
            }
        }

        // Read configuration if available
        if (!string.IsNullOrWhiteSpace(opts.Configuration))
        {
            var (configContent, confErr) = ReadContent(opts.Configuration);
            if (configContent == null)
            {
                Console.WriteLine(confErr);
                return;
            }
            instance.Configuration = JsonIO.From<Configuration>(configContent);
        }

        // >> Run calculation
        static void logger(string msg) => Console.Error.Write(msg);
        instance.Configuration ??= new Configuration(MethodType.ExtremePointInsertion, true);
        var result = Executor.Execute(Instance.FromJsonInstance(instance.Instance), instance.Configuration, logger);

        // Output result
        WriteOutput(opts.Output, JsonIO.To(result.Solution.ToJsonSolution()));
    }
}

/// <summary>
/// A class used to wrap the methods to enable execution by the CLI.
/// </summary>
public class Executor
{
    public static PerformanceResult Execute(Instance instance, Configuration config, Action<string>? logger)
    {
        // Prepare logging.
        void logLine(string msg) { logger?.Invoke(msg + Environment.NewLine); }
        config.Log = logger;

        // Init method.
        IMethod method;
        switch (config.Type)
        {
            case MethodType.FrontLeftBottomStyle: { method = new LinearModelFLB(instance, config); } break;
            case MethodType.TetrisStyle: { method = new LinearModelTetris(instance, config); } break;
            case MethodType.HybridStyle: { method = new LinearModelHybrid(instance, config); } break;
            case MethodType.SpaceIndexed: throw new NotImplementedException("Space indexed model not working for now.");
            case MethodType.ExtremePointInsertion: { method = new ExtremePointInsertionHeuristic(instance, config); } break;
            case MethodType.SpaceDefragmentation: { method = new SpaceDefragmentationHeuristic(instance, config); } break;
            case MethodType.PushInsertion: { method = new PushInsertion(instance, config); } break;
            case MethodType.ALNS: { method = new ALNS(instance, config); } break;
            default: throw new ArgumentException("Unknown method: " + config.Type.ToString());
        }

        // Output some information before starting.
        logLine($">>> Welcome to SardineCan");
        logLine($"Initializing ...");
        logLine($"Instance: {instance.Name}");
        logLine($"Config: {config.Name}");
        logLine($"Seed: {config.Seed}");
        logLine($"Config-details: ");
        LogConfigDetails(config, logger);
        logger?.Invoke(Environment.NewLine);

        // Execute.
        logLine($"Executing ... ");
        PerformanceResult result = method.Run();

        // Log some information to the console.
        logLine($"Finished!");
        logLine($"Result outline:");
        logLine($"Obj: {result.ObjectiveValue.ToString(CultureInfo.InvariantCulture)}");
        logLine($"VolumeContained: {result.Solution.VolumeContained.ToString(CultureInfo.InvariantCulture)}");
        logLine($"VolumeOfContainers: {result.Solution.VolumeOfContainers.ToString(CultureInfo.InvariantCulture)}");
        logLine($"VolumeContainedRelative: {(result.Solution.VolumeContainedRelative * 100).ToString(CultureInfo.InvariantCulture)}%");
        logLine($"VolumeOfContainersInUse: {result.Solution.VolumeOfContainersInUse.ToString(CultureInfo.InvariantCulture)}");
        logLine($"NumberOfContainersInUse: {result.Solution.NumberOfContainersInUse.ToString(CultureInfo.InvariantCulture)}");
        logLine($"NumberOfPiecesPacked: {result.Solution.NumberOfPiecesPacked.ToString(CultureInfo.InvariantCulture)}");
        logLine($"SolutionTime: {result.SolutionTime.TotalSeconds.ToString(CultureInfo.InvariantCulture)}s");

        // We're done here.
        return result;
    }

    /// <summary>
    /// Logs detailed information about the used configuration.
    /// </summary>
    /// <param name="config">The config to log details about.</param>
    /// <param name="logger">The logger to use.</param>
    private static void LogConfigDetails(Configuration config, Action<string>? logger)
    {
        foreach (var field in config.GetType().GetProperties())
        {
            string? value = "";
            // If the field has a xmlignore attribute: ignore it here too
            if (field.GetCustomAttributes(false).Any(a => a is XmlIgnoreAttribute))
                continue;
            // See if it already is a string
            if (field.PropertyType == typeof(string))
            {
                value = (string?)field.GetValue(config);
            }
            else
            {
                // Fetch to-string method - check whether a formatter is necessary
                var toStringMethod = field.PropertyType.GetMethod("ToString", [typeof(CultureInfo)]);
                if (field.GetValue(config) == null)
                {
                    value = null;
                }
                else
                {
                    value = toStringMethod != null ?
                        toStringMethod.Invoke(field.GetValue(config), new object[] { CultureInfo.InvariantCulture })?.ToString() :
                        field.GetValue(config)?.ToString();
                }
            }
            // Output it
            logger?.Invoke(field.Name + ": " + value + Environment.NewLine);
        }
    }
}
