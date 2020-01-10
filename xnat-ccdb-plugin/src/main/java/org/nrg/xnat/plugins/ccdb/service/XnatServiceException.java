package org.nrg.xnat.plugins.ccdb.service;

public class XnatServiceException extends Exception {

    public XnatServiceException(String msg, Exception e) {
        super( msg, e);
    }
    public XnatServiceException(String msg) {
        super( msg);
    }
}
