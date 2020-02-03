package org.nrg.xnat.plugins.ccdb.rest;


import org.junit.Ignore;
import org.junit.Test;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.util.Calendar;
import java.util.Map;

import static junit.framework.TestCase.*;

public class ZipperTest {
    @Test
    public void testUnZip() {
        try {
            InputStream is = ZipperTest.class.getResourceAsStream("/small.zip");
            final File directory = Files.createTempDirectory(Long.toString(Calendar.getInstance().getTimeInMillis())).toFile();
            directory.deleteOnExit();

            Map<String, File> map = Zipper.unzip(is, directory.toPath() );

            assertFalse( map.isEmpty() );
            assertTrue( map.keySet().contains("small.csv"));
            assertTrue( map.keySet().contains("mpet3762a_ct1.img"));
            assertTrue( map.keySet().contains("mpet3762a_ct1.hdr"));
            assertTrue( map.keySet().contains("mpet3762a_em1.img"));
            assertTrue( map.keySet().contains("mpet3762a_em1.hdr"));
            assertEquals( 493, map.get("small.csv").length());
        }
        catch (Exception e) {
            fail("Unexpected exception: " + e);
        }
    }

    @Test
    public void testMultiDirUnZip() {
        try {
            InputStream is = ZipperTest.class.getResourceAsStream("/multiDirZip.zip");
            final File directory = Files.createTempDirectory(Long.toString(Calendar.getInstance().getTimeInMillis())).toFile();
            directory.deleteOnExit();

            Map<String, File> map = Zipper.unzip(is, directory.toPath() );

            assertFalse( map.isEmpty() );
            assertTrue( map.keySet().contains("file1.txt"));
            assertTrue( map.keySet().contains("dir1/file1.txt"));
            assertTrue( map.keySet().contains("dir1/file2.txt"));
            assertTrue( map.keySet().contains("dir2/file2.txt"));
            assertEquals( 18, map.get("dir2/file2.txt").length());
        }
        catch (Exception e) {
            fail("Unexpected exception: " + e);
        }
    }

    @Test
    @Ignore
    // TODO: This creates a zip file but I think it is not closed correctly.
    public void testZip() {
        try {
            InputStream is = ZipperTest.class.getResourceAsStream("/multiDirZip.zip");
            final File directory = Files.createTempDirectory(Long.toString(Calendar.getInstance().getTimeInMillis())).toFile();
            directory.deleteOnExit();

            Map<String, File> map = Zipper.unzip(is, directory.toPath() );

            final File outZip = Files.createTempFile("ccdb.", ".zip").toFile();
            outZip.deleteOnExit();

            Zipper.zip( map, new FileOutputStream( outZip));

            assertTrue( outZip.exists() );
        }
        catch (Exception e) {
            fail("Unexpected exception: " + e);
        }
    }
}
