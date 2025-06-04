package com.nextmv.example;

import java.io.PrintStream;
import java.util.ArrayList;
import java.util.List;
import com.hexaly.optimizer.*;

public final class Main {

  public static void main(String[] args) {
    // Redirect standard output to stderr until the solver is done.
    PrintStream originalOut = System.out;
    System.setOut(System.err);

    try (HexalyOptimizer optimizer = new HexalyOptimizer()) {
      // Parse arguments and load input as before
      Options options = Options.fromArguments(args);
      Input input = Input.fromString(options.getInputPath());
      List<Item> inputItems = input.getItems();

      // Setup Hexaly environment and model
      HxModel model = optimizer.getModel();

      HxExpression[] x = new HxExpression[inputItems.size()];
      for (int i = 0; i < inputItems.size(); i++) {
        x[i] = model.boolVar();
      }

      // Create capacity constraint
      HxExpression knapsackWeight = model.sum();
      for (int i = 0; i < inputItems.size(); i++) {
        HxExpression itemWeight = model.prod(x[i], inputItems.get(i).getWeight());
        knapsackWeight.addOperand(itemWeight);
      }
      model.constraint(model.leq(knapsackWeight, input.getWeightCapacity()));

      // Create objective function for maximizing value
      HxExpression knapsackValue = model.sum();
      for (int i = 0; i < inputItems.size(); i++) {
        HxExpression itemValue = model.prod(x[i], inputItems.get(i).getValue());
        knapsackValue.addOperand(itemValue);
      }
      model.maximize(knapsackValue);

      // End model definition
      model.close();

      // Apply duration limit
      optimizer.getParam().setTimeLimit(options.getDuration());

      // Solve the model
      optimizer.solve();

      // Restore standard output
      System.setOut(originalOut);

      // Convert solution to output
      List<Item> outputItems = new ArrayList<>();
      for (int i = 0; i < inputItems.size(); i++) {
        if (x[i].getValue() > 0.5) {
          outputItems.add(inputItems.get(i));
        }
      }
      Output output = new Output(
          outputItems,
          optimizer.getStatistics().getRunningTime(),
          knapsackValue.getDoubleValue(),
          "Hexaly",
          optimizer.getSolution().getStatus().toString(),
          model.getNbDecisions(),
          model.getNbExpressions(),
          model.getNbConstraints());

      // Write output
      Output.write(options.getOutputPath(), output);

    } catch (Exception e) {
      System.out.println("Error: " + e.getMessage());
      e.printStackTrace();
    }
  }
}
