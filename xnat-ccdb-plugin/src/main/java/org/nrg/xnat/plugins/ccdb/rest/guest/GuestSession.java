package org.nrg.xnat.plugins.ccdb.rest.guest;

import org.nrg.xft.utils.ResourceFile;

import java.util.ArrayList;
import java.util.List;

public class GuestSession {
    private final String label;
    private List<ResourceFile> resourceFiles = new ArrayList<>();

    public GuestSession(String label, List<ResourceFile> resourceFiles) {
        this.label = label;
        addFiles( resourceFiles);
    }
    public String getLabel() {
        return label;
    }

    public List<ResourceFile> getResourceFiles() {
        return resourceFiles;
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
