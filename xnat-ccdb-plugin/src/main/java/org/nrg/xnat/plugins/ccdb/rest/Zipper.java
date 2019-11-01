package org.nrg.xnat.plugins.ccdb.rest;

import java.io.Closeable;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;

public interface Zipper extends Closeable {

    List<File> unzip(InputStream is) throws IOException;
}
