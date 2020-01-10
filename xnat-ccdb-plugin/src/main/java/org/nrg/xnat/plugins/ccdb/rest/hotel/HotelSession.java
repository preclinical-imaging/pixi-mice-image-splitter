package org.nrg.xnat.plugins.ccdb.rest.hotel;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

/**
 * Model the Hotel Session.
 *
 * The HotelSession maps to a subject assessor. As such it has subject label and a list of HotelScan.
 */
public class HotelSession {
    private String _subjectLabel;
    private List<HotelScan> _scans;

    /**
     * Create the HotelSession with the given subject label and empty list of scans.
     *
     * @param subjectLabel
     */
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

    /**
     * Create a collection of HotelSession from a list of files.
     * The assumption is that the list of files contains one CSV file and one pair of 'img' and 'hdr' files per session.
     *
     * @param files
     * @return
     * @throws FileNotFoundException
     */
    public static Collection<HotelSession> getSessionsFromFiles(List<File> files) throws FileNotFoundException {
        return getSessions( HotelScan.createScans( files));
    }

    /**
     * Create a collection of HotelSession from the list of HotelScan.
     *
     * @param scans
     * @return
     */
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

    public String getSubjectLabel() {
        return _subjectLabel;
    }
}
