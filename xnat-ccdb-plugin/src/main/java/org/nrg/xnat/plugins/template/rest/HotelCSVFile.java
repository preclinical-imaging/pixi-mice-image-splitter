package org.nrg.xnat.plugins.template.rest;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class HotelCSVFile {
    private List<String> _labels;
    private List<String[]> _entries;
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

        try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
            _labels = parseLabels( br);
            _entries = parseEntries( br);
        }
    }

    private List<String[]> parseEntries(BufferedReader br) throws IOException {
        List<String[]> entries = new ArrayList<>();
        String line;
        while( (line = br.readLine()) != null) {
            if( ! line.isEmpty()) {
                String[] tokens = line.split( ",");
                entries.add( tokens);
            }
        }
        return entries;
    }

    protected List<String> parseLabels( BufferedReader br) throws IOException {
        List<String> labels = new ArrayList<>();
        String line;
        while( (line = br.readLine()) != null) {
            if( ! line.isEmpty()) {
                String[] tokens = line.split( ",");
                for( String token: tokens) {
                    labels.add( token);
                }
                return labels;
            }
        }
        return labels;
    }

//    public String getHotelSubject() {
//        int foo = _labels.indexOf("Hotel Subject");
//    }
}
