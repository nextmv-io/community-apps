package com.nextmv.example;

import java.util.List;

public class Vehicle {
  public final int vehicle;
  public final double distance;
  public final List<Integer> stops;

  public Vehicle(int vehicle, double distance, List<Integer> stops) {
    this.vehicle = vehicle;
    this.distance = distance;
    this.stops = stops;
  }

  public int getVehicle() {
    return this.vehicle;
  }

  public double getDistance() {
    return this.distance;
  }

  public List<Integer> getStops() {
    return this.stops;
  }
  
}
