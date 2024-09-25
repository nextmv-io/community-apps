package com.nextmv.example;

import java.util.ArrayList;
import java.util.List;

import com.google.ortools.Loader;
import com.google.ortools.linearsolver.MPConstraint;
import com.google.ortools.linearsolver.MPObjective;
import com.google.ortools.linearsolver.MPSolver;
import com.google.ortools.linearsolver.MPVariable;
import com.google.ortools.linearsolver.MPSolver.ResultStatus;

public final class Main {

  public static void main(String[] args) {
    // Parse arguments. Exit on error.
    Options options = Options.fromArguments(args);

    // Load input. Exit on error.
    Input input = Input.fromString(options.getInputPath());

    // Prepare solver.
    String provider = "SCIP";
    Loader.loadNativeLibraries();
    MPSolver solver = MPSolver.createSolver(provider);

    // Apply duration limit.
    solver.setTimeLimit(options.getDuration() * 1000);

    // Create assignment variable for each item.
    List<MPVariable> variables = new ArrayList<MPVariable>();
    List<Item> inputItems = input.getItems();
    for (Item item : inputItems) {
      variables.add(solver.makeBoolVar(item.getId()));
    }

    // Create capacity constraint.
    MPConstraint ct = solver.makeConstraint(0, input.getWeightCapacity());
    for (int i = 0; i < variables.size(); ++i) {
      ct.setCoefficient(variables.get(i), inputItems.get(i).getWeight());
    }

    // Create the objective function.
    MPObjective objective = solver.objective();
    for (int i = 0; i < variables.size(); ++i) {
      objective.setCoefficient(variables.get(i), inputItems.get(i).getValue());
    }
    objective.setMaximization();

    // Solve.
    ResultStatus status = solver.solve();

    // Convert solution to output.
    List<Item> outputItems = new ArrayList<Item>();
    for (int i = 0; i < variables.size(); ++i) {
      if (variables.get(i).solutionValue() > 0.5) {
        outputItems.add(inputItems.get(i));
      }
    }
    Output output = new Output(
        inputItems,
        solver.wallTime(),
        objective.value(),
        provider,
        status.toString(),
        solver.numVariables(),
        solver.numConstraints()
    );
    
    // Write output. Exit on error.
    Output.write(options.getOutputPath(), output);
  }
}
