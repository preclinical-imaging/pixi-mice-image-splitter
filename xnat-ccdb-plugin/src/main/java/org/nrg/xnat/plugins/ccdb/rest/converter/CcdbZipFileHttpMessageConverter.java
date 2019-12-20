package org.nrg.xnat.plugins.ccdb.rest.converter;

import org.nrg.xnat.plugins.ccdb.rest.Zipper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpOutputMessage;
import org.springframework.http.MediaType;
import org.springframework.http.converter.AbstractHttpMessageConverter;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.http.converter.HttpMessageNotWritableException;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Calendar;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Component
public class CcdbZipFileHttpMessageConverter extends AbstractHttpMessageConverter< Map< String, File>> {
    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    public CcdbZipFileHttpMessageConverter() {
        super(MediaType.parseMediaType("application/zip"));
    }

    @Override
    protected boolean supports(final Class clazz) {
        return true;
    }

    @Override
    protected Map<String, File> readInternal(final Class clazz, final HttpInputMessage message) throws IOException, HttpMessageNotReadableException {
        final File directory = Files.createTempDirectory(Long.toString(Calendar.getInstance().getTimeInMillis())).toFile();
        directory.deleteOnExit();

        final Map<String, File> entries = Zipper.unzip(message.getBody(), directory.toPath());
        return entries.keySet().stream().filter(path -> entries.get(path).isFile()).collect( Collectors.toMap(Function.identity(), entries::get));
    }

    @Override
    protected void writeInternal(final Map<String, File> files, final HttpOutputMessage outputMessage) throws IOException, HttpMessageNotWritableException {
        Zipper.zip( files, outputMessage.getBody());
    }

//    private void writeFile(final ZipUtils zipper, final String path, final File file) {
//        try {
//            zipper.write(path, file);
//        } catch (IOException e) {
//            _log.warn("An error occurred writing the file {} to a Zip output stream", file.getPath());
//        }
//    }
}