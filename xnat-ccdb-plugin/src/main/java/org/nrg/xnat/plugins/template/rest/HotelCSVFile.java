package org.nrg.xnat.plugins.template.rest;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class HotelCSVFile {
    private List<String> _labels;
    private List<List<String>> _entries;

    /**
     * create the HotelCSVFile from the list of files.
     *
     * @param files list of files from which to extract the hotel csv.
     * @throws IllegalArgumentException if the file list contains more than one csv.
     */
    public HotelCSVFile( List<File> files) throws IllegalArgumentException, IOException {
        List<File> csvFiles = new ArrayList<>();
        for( File f: files) {
            if( isHotelCSV( f)) {
                csvFiles.add(f);
            }
        }
        if( csvFiles.isEmpty()) {
            throw new IllegalArgumentException("Failed to find hotel csv.");
        }
        else if( csvFiles.size() > 1) {
            throw new IllegalArgumentException("Found multiple csv files.");
        }

        parse( csvFiles.get(0));
    }

    protected boolean isHotelCSV( File f) {
        return f.getName().endsWith(".csv");
    }

    protected void parse( File csvFile) throws IOException {
        String line;
        String cvsSplitBy = ",";
        CSVParser csvParser = new CSVParser();

        try( Scanner scanner = new Scanner( csvFile)) {
            // read column labels in first non-empty line.
            while( (line = scanner.nextLine()) != null) {
                if( ! line.isEmpty()) {
                    _labels = csvParser.parseLine( line);
                    break;
                }
            }

            // read entries in remaining non-empty lines.
            while( (line = scanner.nextLine()) != null) {
                if( ! line.isEmpty()) {
                    _entries.add( csvParser.parseLine( line));
                }
            }
        }
    }

//    public String getHotelSubject() {
//        int foo = _labels.indexOf("Hotel Subject");
//    }
}
