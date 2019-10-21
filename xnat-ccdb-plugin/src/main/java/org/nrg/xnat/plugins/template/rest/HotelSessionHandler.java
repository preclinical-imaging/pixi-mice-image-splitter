package org.nrg.xnat.plugins.template.rest;

import org.nrg.xdat.om.XnatExperimentdata;
import org.nrg.xdat.om.XnatProjectdata;
import org.nrg.xdat.om.XnatSubjectdata;
import org.nrg.xdat.om.base.BaseXnatSubjectdata;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.XFTItem;
import org.nrg.xft.event.EventDetails;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.exception.ElementNotFoundException;
import org.nrg.xft.exception.XFTInitException;
import org.nrg.xft.security.UserI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.List;

@Component
public class HotelSessionHandler  {

    private final SiteConfigPreferences _preferences;
    private static final Logger _log = LoggerFactory.getLogger( HotelSessionHandler.class);

    public HotelSessionHandler( final SiteConfigPreferences preferences) {
        _preferences = preferences;
    }

    public void handleSessions(String project, Collection<HotelSession> sessions, UserI user) {
        for( HotelSession session: sessions) {
            handleSession( project, session, user);
        }
    }

    public void handleSession( String project, HotelSession session, UserI user) {
        XnatProjectdata projectdata = XnatProjectdata.getProjectByIDorAlias( project, user, false);
        if( projectdata == null) {
            // bad request.  no such project.
        }

        XnatSubjectdata subjectdata = getOrCreateSubject( projectdata, session.getSubjectLabel(), user);

        for( HotelScan scan: session.getScans()) {
            switch (scan.getScanType()) {
                case "CT":
                    break;
                case "PT":
                case "PET":
                    break;
                default:
                    // unknown scan type
                    break;
            }
        }

    }

    protected XnatSubjectdata getOrCreateSubject( XnatProjectdata projectdata, String subjectLabel, UserI user) {
        XnatSubjectdata subjectdata = XnatSubjectdata.GetSubjectByProjectIdentifier( projectdata.getProject(), subjectLabel, user, false);
        if( subjectdata == null) {
            try {
                XFTItem item = XFTItem.NewItem("xnat:subjectData", user);
                subjectdata = new XnatSubjectdata( item);
                String id = XnatSubjectdata.CreateNewID();
                subjectdata.setProject( projectdata.getId());
                subjectdata.setId( id);
                subjectdata.setLabel( subjectLabel);
//                EventDetails eventDetails = EventUtils.newEventInstance(EventUtils.CATEGORY.DATA, EventUtils.TYPE.WEB_SERVICE, "action");
                EventMetaI eventMeta = EventUtils.DEFAULT_EVENT( user, "create subject");
                subjectdata.save( user, false, false, eventMeta);

            } catch (Exception e) {
                // throw internal server error
            }

        }
        return subjectdata;
    }

//    protected XnatExperimentdata getOrCreateSession(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) {
//        List<XnatExperimentdata> experiments = subjectdata.getExperiments_experiment( XnatExperimentdata.)
//        XnatExperimentdata experimentdata = XnatExperimentdata.G( projectdata.getProject(), subjectLabel, user, false);
//        return experimentdata;
//    }

}
