package org.nrg.xnat.plugins.template.rest;

import org.junit.Test;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;

import static junit.framework.TestCase.fail;

class HotelCSVFileTest {

    @Test
    void parse() {
        File file = new File( getClass().getClassLoader().getResource("CCDB_scans_updated_07June2019-jg.csv").getFile());
        try {
            HotelCSVFile hotelCSVFile = new HotelCSVFile(Arrays.asList( file));
        } catch (IOException e) {
            fail("Unexpected exception: " + e);
        }

    }
}