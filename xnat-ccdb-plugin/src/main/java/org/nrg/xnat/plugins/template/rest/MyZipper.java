package org.nrg.xnat.plugins.template.rest;

import com.google.common.io.Files;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Implementation of Zipper that unzips to a temp directory.
 *
 * Call close() to clear the temp directory.
 *
 */
public class MyZipper implements Zipper {
    private final byte[] _buffer;
    private File _tmpDir;

    public MyZipper() {
        _buffer = new byte[8196];
        _tmpDir = Files.createTempDir();
    }

    /**
     * unzip the stream into a set of files in a temp directory.
     *
     * @param is InputStream to zipped data.
     * @return List of File contained in zip.
     * @throws IOException if input stream is not to zip or IO error occurs.
     */
    @Override
    public List<File> unzip(InputStream is) throws IOException {
        try (ZipInputStream zis = new ZipInputStream(is)) {
            List<File> files = new ArrayList<>();
            ZipEntry zipEntry;
            while( (zipEntry = zis.getNextEntry()) != null) {
                File newFile = new File( getTempDir(), zipEntry.getName());
                copy( zis, newFile);
                files.add( newFile);
            }
            return files;
        }
    }

    /**
     * Get the temp directory.
     *
     * @return the temp directory, create it if necessary.
     */
    private File getTempDir() {
        if( _tmpDir == null) _tmpDir = Files.createTempDir();
        return _tmpDir;
    }

    /**
     * Copy from stream into file.
     *
     * @param is
     * @param f
     * @throws IOException
     */
    private void copy( InputStream is, File f) throws IOException {
        try(FileOutputStream fos = new FileOutputStream( f)) {
            int len;
            while ((len = is.read(_buffer)) > 0) {
                fos.write(_buffer, 0, len);
            }
        }
    }

    /**
     * Clean up the temp directory.
     */
    @Override
    public void close() {
        if( _tmpDir != null) {
            _tmpDir.delete();
            _tmpDir = null;
        }
    }
}
