package org.nrg.xnat.plugins.ccdb.rest.hotel;

import com.opencsv.bean.CsvBindAndSplitByName;
import com.opencsv.bean.CsvBindByName;
import com.opencsv.bean.CsvToBeanBuilder;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Models the HotelScan.
 *
 * Multiple hotelScans map into a single subject assessor (Hotel Session).
 * Each row in a CSV file maps to a unique hotelScan.
 *
 */
public class HotelScan {
    @CsvBindByName( column = "Hotel Subject", required = true)
    private String hotelSubject;

    @CsvBindByName( column = "Scan Name", required = true)
    private String scanName;

    @CsvBindByName( column = "Scan Type", required = true)
    private String scanType;

    @CsvBindByName( column = "Time Points", required = false)
    private String timePoints;

    @CsvBindByName( column = "Hotel Position", required = false)
    private String hotelPosition;

    @CsvBindAndSplitByName( column = "Animal #", required = false, elementType = String.class, splitOn = ",")
    private List<String> animalNumbers;

    @CsvBindByName( column = "Animal Weight(g)", required = false)
    private String animalWeight;

    @CsvBindByName( column = "Date of Birth", required = false)
    private String dateOfBirth;

    @CsvBindByName( column = "Date Weaned", required = false)
    private String dateWeaned;

    @CsvBindByName( column = "Sex", required = false)
    private String sex;

    @CsvBindByName( column = "Activity(mCi)", required = false)
    private String activity ;

    @CsvBindByName( column = "Scan Time", required = true)
    private String scanTime;

    @CsvBindByName( column = "Injection Time", required = false)
    private String injectionTime;

    @CsvBindByName( column = "Scanner", required = true)
    private String scanner;

    @CsvBindByName( column = "Tracer", required = true)
    private String tracer;

    @CsvBindByName( column = "Study Date", required = true)
    private String studyDate;

    @CsvBindByName( column = "Study Name", required = true)
    private String studyName;

    @CsvBindByName( column = "Protocol Number", required = false)
    private String protocolNumber;

    @CsvBindByName( column = "Species", required = false)
    private String species;

    @CsvBindByName( column = "Strain", required = false)
    private String strain;

    @CsvBindByName( column = "Litter ID", required = false)
    private String litterID;

    @CsvBindByName( column = "Notes", required = false)
    private String notes;

    private List<File> _imageFiles;

    /**
     * Parse the CSV to create the list of entries.
     *
     * @param f The Hotel-Scan CSV file to parse.
     * @return List of HotelScan entries.
     * @throws FileNotFoundException
     */
    static List<HotelScan> readCSV(File f) throws FileNotFoundException {
        return new CsvToBeanBuilder( new FileReader(f))
                .withType(HotelScan.class).build().parse();
    }

    /**
     * Construct the list of HotelScans from the list of specified files.
     *
     * It is assumed the list of files contains one csv file with scan meta-data and a corresponding image '.hdr'
     * and '.img' file for each scan entry.
     *
     * @param files List of files composing the HotelScans.
     * @return list of HotelScans.
     * @throws FileNotFoundException
     */
    static List<HotelScan> createScans( List<File> files) throws FileNotFoundException {
        List<HotelScan> scans = new ArrayList<>();
        for( File f: files) {
            if( isHotelScanCSV(f)) {
                scans = readCSV(f);
            }
        }

        for( HotelScan scan: scans) {
            scan.addImages( files);
        }
        return scans;
    }

    /**
     * Filter the list of files for the ones appropriate to this scan and add them to this scan.
     * Here, appropriate means files whose name begins with the scan name.
     * @param files
     */
    public void addImages( List<File> files) {
        String prefix = getScanName();
        _imageFiles = files.stream()
                .filter( f -> f.getName().startsWith(prefix))
                .collect(Collectors.toList());
    }

    public List<File> getImages() {
        return _imageFiles;
    }

    public static boolean isHotelScanCSV( File f) {
        return f.getName().endsWith(".csv");
    }

    public String getHotelSubject() {
        return hotelSubject;
    }

    public void setHotelSubject(String hotelSubject) {
        this.hotelSubject = hotelSubject;
    }

    public String getScanName() {
        return scanName;
    }

    public void setScanName(String scanName) {
        this.scanName = scanName;
    }

    public String getScanType() {
        return scanType;
    }

    public void setScanType(String scanType) {
        this.scanType = scanType;
    }

    public String getTimePoints() {
        return timePoints;
    }

    public void setTimePoints(String timePoints) {
        this.timePoints = timePoints;
    }

    public String getHotelPosition() {
        return hotelPosition;
    }

    public void setHotelPosition(String hotelPosition) {
        this.hotelPosition = hotelPosition;
    }

    public List<String> getAnimalNumbers() {
        return animalNumbers;
    }

    public void setAnimalNumbers(List<String> animalNumbers) {
        this.animalNumbers = animalNumbers;
    }

    public String getAnimalWeight() {
        return animalWeight;
    }

    public void setAnimalWeight(String animalWeight) {
        this.animalWeight = animalWeight;
    }

    public String getDateOfBirth() {
        return dateOfBirth;
    }

    public void setDateOfBirth(String dateOfBirth) {
        this.dateOfBirth = dateOfBirth;
    }

    public String getDateWeaned() {
        return dateWeaned;
    }

    public void setDateWeaned(String dateWeaned) {
        this.dateWeaned = dateWeaned;
    }

    public String getSex() {
        return sex;
    }

    public void setSex(String sex) {
        this.sex = sex;
    }

    public String getActivity() {
        return activity;
    }

    public void setActivity(String activity) {
        this.activity = activity;
    }

    public String getScanTime() {
        return scanTime;
    }

    public void setScanTime(String scanTime) {
        this.scanTime = scanTime;
    }

    public String getInjectionTime() {
        return injectionTime;
    }

    public void setInjectionTime(String injectionTime) {
        this.injectionTime = injectionTime;
    }

    public String getScanner() {
        return scanner;
    }

    public void setScanner(String scanner) {
        this.scanner = scanner;
    }

    public String getTracer() {
        return tracer;
    }

    public void setTracer(String tracer) {
        this.tracer = tracer;
    }

    public String getStudyDate() {
        return studyDate;
    }

    public void setStudyDate(String studyDate) {
        this.studyDate = studyDate;
    }

    public String getStudyName() {
        return studyName;
    }

    public void setStudyName(String studyName) {
        this.studyName = studyName;
    }

    public String getProtocolNumber() {
        return protocolNumber;
    }

    public void setProtocolNumber(String protocolNumber) {
        this.protocolNumber = protocolNumber;
    }

    public String getSpecies() {
        return species;
    }

    public void setSpecies(String species) {
        this.species = species;
    }

    public String getStrain() {
        return strain;
    }

    public void setStrain(String strain) {
        this.strain = strain;
    }

    public String getLitterID() {
        return litterID;
    }

    public void setLitterID(String litterID) {
        this.litterID = litterID;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
