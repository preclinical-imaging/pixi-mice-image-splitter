package org.nrg.xnat.plugins.template.rest;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class HotelSession {
    private String _subjectLabel;
    private List<HotelScan> _scans;

    public HotelSession( String subjectLabel) {
        _subjectLabel = subjectLabel;
        _scans = new ArrayList<>();
    }

    public void addScan( HotelScan scan) {
        _scans.add(scan);
    }

    public List<HotelScan> getScans() {
        return _scans;
    }

    public static Collection<HotelSession> getSessionsFromFiles(List<File> files) throws FileNotFoundException {
        return getSessions( HotelScan.createScans( files));
    }

    public static Collection<HotelSession> getSessions(List<HotelScan> scans) {
        Map<String,HotelSession> sessionMap = new HashMap<>();

        for( HotelScan scan: scans) {
            String subjectLabel = scan.getHotelSubject();
            if( ! sessionMap.containsKey( subjectLabel)) {
                sessionMap.put( subjectLabel, new HotelSession( subjectLabel));
            }
            sessionMap.get( subjectLabel).addScan( scan);
        }
        return sessionMap.values();
    }
}
