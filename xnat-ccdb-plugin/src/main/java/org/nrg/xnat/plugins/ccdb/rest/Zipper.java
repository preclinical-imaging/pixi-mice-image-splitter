package org.nrg.xnat.plugins.ccdb.rest;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

/**
 * Implementation of Zipper that unzips to a temp directory.
 *
 *
 */
public class Zipper {

    /**
     * unzip the stream into a set of files in a temp directory.
     *
     * @param is InputStream to zipped data.
     * @return List of File contained in zip.
     * @throws IOException if input stream IO error occurs.
     */
    public static Map<String, File> unzip(InputStream is, Path tmpDir) throws IOException {
        try (ZipInputStream zis = new ZipInputStream( new BufferedInputStream( is))) {
            Map<String, File> fileMap = new HashMap<>();
            ZipEntry zipEntry;
            while( (zipEntry = zis.getNextEntry()) != null) {
                File newFile = tmpDir.resolve( zipEntry.getName()).toFile();
                if( zipEntry.isDirectory()) {
                    if( ! newFile.mkdir()) {
                        throw new IOException("unzip failed to create directory: " + newFile);
                    }
                }
                else {
                    Files.copy( zis, newFile.toPath());
                    fileMap.put( zipEntry.getName(), newFile);
                }
            }
            return fileMap;
        }
    }

//    public Map<String, File> extractMap(final InputStream is, final String destination, final boolean overwrite, final EventMetaI ci) throws IOException {
//        final Map<String, File> extractedFiles = new HashMap<>();
//
//        final File destinationFolder = new File(destination);
//        if (!destinationFolder.exists()) {
//            destinationFolder.mkdirs();
//        }
//
//        // Loop over all of the entries in the zip file
//        final byte[]   data = new byte[FileUtils.LARGE_DOWNLOAD];
//        //  Create a ZipInputStream to read the zip file
//        try (final ZipInputStream zis = new ZipInputStream(new BufferedInputStream(is))) {
//            ZipEntry entry;
//            while ((entry = zis.getNextEntry()) != null) {
//                final String name = entry.getName();
//                if (!entry.isDirectory()) {
//                    final File f = new File(destination, name);
//
//                    if (f.exists() && !overwrite) {
//                        _duplicates.add(name);
//                    } else {
//                        if (f.exists()) {
//                            FileUtils.MoveToHistory(f, EventUtils.getTimestamp(ci));
//                        }
//                        f.getParentFile().mkdirs();
//
//                        // Write the file to the file system
//                        try (final BufferedOutputStream dest = new BufferedOutputStream(new FileOutputStream(f), FileUtils.LARGE_DOWNLOAD)) {
//                            int count;
//                            while ((count = zis.read(data, 0, FileUtils.LARGE_DOWNLOAD)) != -1) {
//                                dest.write(data, 0, count);
//                            }
//                        }
//                        extractedFiles.put(name, new File(f.getAbsolutePath()));
//                    }
//                } else {
//                    final File subfolder = new File(destination, name);
//                    if (!subfolder.exists()) {
//                        subfolder.mkdirs();
//                    }
//                    extractedFiles.put(name, subfolder);
//                }
//            }
//        }
//        return extractedFiles;
//    }


    public static void zip(Map<String, File> fileMap, OutputStream os) throws IOException {
        if( os != null) {
            ZipOutputStream zos = new ZipOutputStream( os);
            for( String fileName: fileMap.keySet()) {
                zipFile( fileName, fileMap.get(fileName), zos);
            }
        }
    }

    private static void zipFile( String fileName, File fileToZip, ZipOutputStream zipOut) throws IOException {
        if (fileToZip.isHidden()) {
            return;
        }
        if (fileToZip.isDirectory()) {
            if (fileName.endsWith("/")) {
                zipOut.putNextEntry(new ZipEntry(fileName));
                zipOut.closeEntry();
            } else {
                zipOut.putNextEntry(new ZipEntry(fileName + "/"));
                zipOut.closeEntry();
            }
            File[] children = fileToZip.listFiles();
            for (File childFile : children) {
                zipFile( fileName + "/" + childFile.getName(), childFile, zipOut);
            }
            return;
        }
        FileInputStream fis = new FileInputStream(fileToZip);
        ZipEntry zipEntry = new ZipEntry(fileName);
        zipOut.putNextEntry(zipEntry);
        byte[] bytes = new byte[1024];
        int length;
        while ((length = fis.read(bytes)) >= 0) {
            zipOut.write(bytes, 0, length);
        }
        fis.close();
    }
}
