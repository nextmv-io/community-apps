package com.nextmv.example;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.List;

/**
 * ExcelWriter class to write the solution to an Excel file.
 * It creates two sheets: one for assignments and one for unassigned items.
 */
public class ExcelWriter {

    /**
     * Writes the solution to an Excel file.
     *
     * @param solution The solution containing assignments and unassigned items.
     * @param filePath The path where the Excel file will be saved.
     * @throws IOException If an I/O error occurs while writing the file.
     */
    public void writeSolutionToExcel(Solution solution, String filePath) throws IOException {
        Workbook workbook = new XSSFWorkbook();

        // Create a sheet for assignments
        Sheet assignmentsSheet = workbook.createSheet("Assignments");
        createAssignmentsSheet(assignmentsSheet, solution.getAssignments());

        // Create a sheet for unassigned items
        Sheet unassignedSheet = workbook.createSheet("Unassigned");
        createUnassignedSheet(unassignedSheet, solution.getUnassigned());

        // Write the output to a file
        try (FileOutputStream fileOut = new FileOutputStream(filePath)) {
            workbook.write(fileOut);
        }

        workbook.close();
    }

    private void createAssignmentsSheet(Sheet sheet, List<Assignment> assignments) {
        // Create header row
        Row headerRow = sheet.createRow(0);
        headerRow.createCell(0).setCellValue("Item ID");
        headerRow.createCell(1).setCellValue("Knapsack ID");

        // Create data rows
        int rowNum = 1;
        for (Assignment assignment : assignments) {
            Row row = sheet.createRow(rowNum++);
            row.createCell(0).setCellValue(assignment.getItemId());
            row.createCell(1).setCellValue(assignment.getKnapsackId());
        }
    }

    private void createUnassignedSheet(Sheet sheet, List<String> unassigned) {
        // Create header row
        Row headerRow = sheet.createRow(0);
        headerRow.createCell(0).setCellValue("Item ID");

        // Create data rows
        int rowNum = 1;
        for (String itemId : unassigned) {
            Row row = sheet.createRow(rowNum++);
            row.createCell(0).setCellValue(itemId);
        }
    }
}

/**
 * Represents a solution containing assignments of items to knapsacks
 * and a list of unassigned items.
 */
class Solution {
    private List<Assignment> assignments;
    private List<String> unassigned;

    public Solution(List<Assignment> assignments, List<String> unassigned) {
        this.assignments = assignments;
        this.unassigned = unassigned;
    }

    public List<Assignment> getAssignments() {
        return assignments;
    }

    public List<String> getUnassigned() {
        return unassigned;
    }
}

/**
 * Represents an assignment of an item to a knapsack.
 */
class Assignment {
    private String itemId;
    private String knapsackId;

    public Assignment(String itemId, String knapsackId) {
        this.itemId = itemId;
        this.knapsackId = knapsackId;
    }

    public String getItemId() {
        return itemId;
    }

    public String getKnapsackId() {
        return knapsackId;
    }
}
