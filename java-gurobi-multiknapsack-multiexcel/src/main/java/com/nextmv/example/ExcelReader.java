package com.nextmv.example;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class ExcelReader {

  public Input readExcelFile(String filePath) throws IOException {
    FileInputStream file = new FileInputStream(filePath);
    Workbook workbook = new XSSFWorkbook(file);

    List<Item> items = readItemsSheet(workbook);
    List<Knapsack> knapsacks = readKnapsacksSheet(workbook);

    workbook.close();
    file.close();

    return new Input(items, knapsacks);
  }

  private List<Item> readItemsSheet(Workbook workbook) {
    List<Item> items = new ArrayList<>();
    Sheet sheet = workbook.getSheet("items");

    Iterator<Row> rowIterator = sheet.iterator();
    // Skip header row
    if (rowIterator.hasNext()) {
      rowIterator.next();
    }

    while (rowIterator.hasNext()) {
      Row row = rowIterator.next();
      String id = row.getCell(0).getStringCellValue();
      double value = row.getCell(1).getNumericCellValue();
      double weight = row.getCell(2).getNumericCellValue();

      items.add(new Item(id, value, weight));
    }

    return items;
  }

  private List<Knapsack> readKnapsacksSheet(Workbook workbook) {
    List<Knapsack> knapsacks = new ArrayList<>();
    Sheet sheet = workbook.getSheet("knapsacks");

    Iterator<Row> rowIterator = sheet.iterator();
    // Skip header row
    if (rowIterator.hasNext()) {
      rowIterator.next();
    }

    while (rowIterator.hasNext()) {
      Row row = rowIterator.next();
      String id = row.getCell(0).getStringCellValue();
      double capacity = row.getCell(1).getNumericCellValue();

      knapsacks.add(new Knapsack(id, capacity));
    }

    return knapsacks;
  }
}

class Input {
  private List<Item> items;
  private List<Knapsack> knapsacks;

  public Input(List<Item> items, List<Knapsack> knapsacks) {
    this.items = items;
    this.knapsacks = knapsacks;
  }

  public List<Item> getItems() {
    return items;
  }

  public List<Knapsack> getKnapsacks() {
    return knapsacks;
  }
}

class Item {
  private String id;
  private double value;
  private double weight;

  public Item(String id, double value, double weight) {
    this.id = id;
    this.value = value;
    this.weight = weight;
  }

  public String getId() {
    return id;
  }

  public double getValue() {
    return value;
  }

  public double getWeight() {
    return weight;
  }
}

class Knapsack {
  private String id;
  private double capacity;

  public Knapsack(String id, double capacity) {
    this.id = id;
    this.capacity = capacity;
  }

  public String getId() {
    return id;
  }

  public double getCapacity() {
    return capacity;
  }
}
