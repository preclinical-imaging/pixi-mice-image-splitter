package org.nrg.xnat.plugins.ccdb.rest.guest;

import java.util.ArrayList;
import java.util.List;

public class Guest {
    private final String label;
    private List<GuestSession> sessions = new ArrayList<>();

    public Guest( String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }

    public List<GuestSession> getSessions() {
        return sessions;
    }

    public void setSessions(List<GuestSession> sessions) {
        this.sessions = sessions;
    }

    public void addSession( GuestSession session) {
        sessions.add( session);
    }
}
