package org.nrg.xnat.plugins.ccdb.rest.hotel;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;
import java.util.stream.Collectors;

public class HotelSubject {
    private String _subjectLabel;
    private List<String> _subjectOrder;
    private List<HotelSession> _sessions;

    public HotelSubject( String subjectLabel, List<String> subjectOrder) {
        _subjectLabel = subjectLabel;
        _subjectOrder = subjectOrder;
        _sessions = new ArrayList<>();
    }

    public static Collection<HotelSubject> getSubjectsFromFiles(List<File> files) throws FileNotFoundException {
        return getSubjects( HotelSession.getSessionsFromFiles( files));
    }

    /**
     * Create a collection of HotelSubject from the list of HotelSession.
     *
     * @param sessions
     * @return
     */
    public static Collection<HotelSubject> getSubjects( Collection<HotelSession> sessions) {
        Map<String,HotelSubject> subjectMap = new HashMap<>();

        for( HotelSession session: sessions) {
            String subjectLabel = session.getHotelSubjectLabel();
            if( ! subjectMap.containsKey( subjectLabel)) {
                subjectMap.put( subjectLabel, new HotelSubject( subjectLabel, session.getSubjectOrder()));
            }
            HotelSubject hotelSubject = subjectMap.get( subjectLabel);
            hotelSubject.addSession( session);

            // insure that subject order is set by the CT session.
            if( "CT".equals( session.getModalities())) {
                hotelSubject.setSubjectOrder( session.getSubjectOrder());
            }

        }
        return subjectMap.values();
    }

    public String getSubjectLabel() {
        return _subjectLabel;
    }

    public void setSubjectOrder( List<String> subjectOrder) {
        _subjectOrder = subjectOrder;
    }

    public List<String> getSubjectOrder() {
        return _subjectOrder;
    }

    public String getSubjectOrderString() {
        return _subjectOrder.stream()
                .collect(Collectors.joining(","));
    }

    public List<HotelSession> getSessions() {
        return _sessions;
    }

    public void addSession( HotelSession session) {
        _sessions.add( session);
    }
}
