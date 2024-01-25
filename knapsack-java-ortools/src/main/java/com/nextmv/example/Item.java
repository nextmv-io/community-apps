package com.nextmv.example;

public class Item {
  private final String id;
  private final double weight;
  private final double value;

  public Item(String id, double weight, double value) {
    this.id = id;
    this.weight = weight;
    this.value = value;
  }

  public String getId() {
    return this.id;
  }

  public double getWeight() {
    return this.weight;
  }

  public double getValue() {
    return this.value;
  }
}
