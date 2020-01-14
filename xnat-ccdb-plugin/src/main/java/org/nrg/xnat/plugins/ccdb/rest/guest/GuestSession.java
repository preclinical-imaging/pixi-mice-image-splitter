package org.nrg.xnat.plugins.ccdb.rest.guest;

import org.nrg.xft.utils.ResourceFile;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class GuestSession {
    private final String label;
    private final String modality;
    private List<ResourceFile> resourceFiles = new ArrayList<>();

    public GuestSession(String label, String modality, List<ResourceFile> resourceFiles) {
        this.label = label;
        this.modality = modality;
        addFiles( resourceFiles);
    }
    public String getLabel() {
        return label;
    }
    public String getModality() {
        return modality;
    }

    public List<ResourceFile> getResourceFiles() {
        return resourceFiles;
    }

    public List<File> getFiles() {
        return resourceFiles.stream()
                .map( ResourceFile::getF)
                .collect(Collectors.toList());
    }

    public void setResourceFiles(List<ResourceFile> resourceFiles) {
        this.resourceFiles = resourceFiles;
    }

    public void addFile( ResourceFile file) {
        resourceFiles.add( file);
    }

    public void addFiles( List<ResourceFile> resourceFiles) {
        this.resourceFiles.addAll( resourceFiles);
    }
}
