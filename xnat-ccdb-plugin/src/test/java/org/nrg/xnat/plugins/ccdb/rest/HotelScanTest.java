package org.nrg.xnat.plugins.ccdb.rest;

import org.junit.Test;
import org.nrg.xnat.plugins.ccdb.rest.hotel.HotelScan;

import java.io.File;
import java.io.IOException;
import java.util.List;

import static junit.framework.TestCase.fail;

public class HotelScanTest {

    @Test
    public void opencsv() {
        File file = new File( getClass().getClassLoader().getResource("CCDB_scans_updated_07June2019-jg.csv").getFile());
        try {
            List<HotelScan> hotelSessions = HotelScan.readCSV( file);
            System.out.println("done");
        } catch (IOException e) {
            fail("Unexpected exception: " + e);
        }

    }
}