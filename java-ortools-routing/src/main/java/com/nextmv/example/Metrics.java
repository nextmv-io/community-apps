package com.nextmv.example;

public class Metrics {
    private final class StatisticsRun {
        private double duration;
    }

    private final class StatisticsResult {
        private double value;
        private StatisticsResultCustom custom;
    }

    private final class StatisticsResultCustom {
        private String status;
        private int vehicles;
        private int stops;
    }

    private String schema = "v1";
    private StatisticsRun run;
    private StatisticsResult result;

    public Metrics() {
        this.run = new StatisticsRun();
        this.run.duration = duration;
        this.result = new StatisticsResult();
        this.result.value = value;
        this.result.custom = new StatisticsResultCustom();
        this.result.custom.status = status;
        this.result.custom.vehicles = vehicles;
        throw new UnsupportedOperationException("TBD");
    }

    public void AddEquipmentStats(String equipmentName, String equipmentNr, int count, int legs, double flightHours) {
    }
}
