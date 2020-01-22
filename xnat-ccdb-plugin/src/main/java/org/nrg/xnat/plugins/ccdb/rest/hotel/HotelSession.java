package org.nrg.xnat.plugins.ccdb.rest.hotel;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Model the Hotel Session.
 *
 * The HotelSession maps to a subject assessor. As such it has subject label and a list of HotelScan.
 */
public class HotelSession {
    private String _hotelSubjectLabel;
    private String _hotelSessionLabel;
    private List<String> _subjectOrder;
    private List<HotelScan> _scans;

    /**
     * Create the HotelSession with the given subject label and empty list of scans.
     *
     * @param hotelSessionLabel
     */
    public HotelSession( String hotelSubjectLabel, String hotelSessionLabel, List<String> subjectOrder) {
        _hotelSubjectLabel = hotelSubjectLabel;
        _hotelSessionLabel = hotelSessionLabel;
        _subjectOrder = subjectOrder;
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
            String hotelSessionLabel = scan.getScanName();
            String hotelSubjectLabel = scan.getHotelSubject();
            List<String> subjectOrder = scan.getAnimalNumbers();
            if( ! sessionMap.containsKey( hotelSessionLabel)) {
                sessionMap.put( hotelSessionLabel, new HotelSession( hotelSubjectLabel, hotelSessionLabel, subjectOrder));
            }
            sessionMap.get( hotelSessionLabel).addScan( scan);
        }
        return sessionMap.values();
    }

    public String getModalities() {
       return  _scans.stream()
               .map(HotelScan::getScanType)
               .collect(Collectors.toSet())
               .stream()
               .sorted(Comparator.naturalOrder())
               .collect(Collectors.joining(",")).toString();
    }

    public String getHotelSubjectLabel() { return _hotelSubjectLabel;}
    public String getHotelSessionLabel() { return _hotelSessionLabel;}
    public List<String> getSubjectOrder() { return _subjectOrder;}
}
