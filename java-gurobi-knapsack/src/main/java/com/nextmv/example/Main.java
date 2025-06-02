package com.nextmv.example;

import java.util.ArrayList;
import java.util.List;

import com.gurobi.gurobi.*;

public final class Main {

  public static void main(String[] args) {
    gurobiKnapsack(args);
  }

  public static void gurobiKnapsack(String[] args) {
    try {
      // Parse arguments.
      Options options = Options.fromArguments(args);

      // Load input.
      Input input = Input.fromString(options.getInputPath());

      // Setup Gurobi environment and model.
      GRBEnv env = new GRBEnv(true);
      env.set("OutputFlag", "0"); // Disable output
      env.start();
      GRBModel model = new GRBModel(env);

      // Apply duration limit.
      model.set(GRB.DoubleParam.TimeLimit, options.getDuration());

      // Create assignment variable for each item.
      List<GRBVar> variables = new ArrayList<>();
      List<Item> inputItems = input.getItems();
      for (Item item : inputItems) {
        variables.add(model.addVar(0.0, 1.0, 0.0, GRB.BINARY, item.getId()));
      }

      // Integrate new variables
      model.update();

      // Create capacity constraint.
      GRBLinExpr capacityExpr = new GRBLinExpr();
      for (int i = 0; i < variables.size(); ++i) {
        capacityExpr.addTerm(inputItems.get(i).getWeight(), variables.get(i));
      }
      model.addConstr(capacityExpr, GRB.LESS_EQUAL, input.getWeightCapacity(), "capacity");

      // Create the objective function.
      GRBLinExpr objectiveExpr = new GRBLinExpr();
      for (int i = 0; i < variables.size(); ++i) {
        objectiveExpr.addTerm(inputItems.get(i).getValue(), variables.get(i));
      }
      model.setObjective(objectiveExpr, GRB.MAXIMIZE);

      // Solve.
      model.optimize();

      // Convert solution to output.
      List<Item> outputItems = new ArrayList<>();
      for (int i = 0; i < variables.size(); ++i) {
        if (variables.get(i).get(GRB.DoubleAttr.X) > 0.5) {
          outputItems.add(inputItems.get(i));
        }
      }
      Output output = new Output(
          inputItems,
          model.get(GRB.DoubleAttr.Runtime),
          model.get(GRB.DoubleAttr.ObjVal),
          "Gurobi",
          String.valueOf(model.get(GRB.IntAttr.Status)),
          model.get(GRB.IntAttr.NumVars),
          model.get(GRB.IntAttr.NumConstrs));

      // Write output.
      Output.write(options.getOutputPath(), output);

      // Dispose of model and environment.
      model.dispose();
      env.dispose();

    } catch (GRBException e) {
      System.out.println("Error code: " + e.getErrorCode() + ". " + e.getMessage());
      e.printStackTrace();
    }
  }
}
