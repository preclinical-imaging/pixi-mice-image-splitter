package org.nrg.xnat.plugins.template.rest;

import org.nrg.xdat.om.*;
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
            CcdbHotelct ct;
        }
        return subjectdata;
    }

    protected XnatExperimentdata getOrCreateSession(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) {
        XnatExperimentdata experiment = null;

        List<? extends XnatExperimentdata> expts = subjectdata.getExperiments_experiment();
        for( XnatExperimentdata expt: expts) {
            if( expt.getLabel().matches( hotelScan.getScanName())) {
                experiment = expt;
                break;
            }
        }

        if( experiment == null) {
        }
        return experiment;
    }

    public XnatExperimentdata createSession( HotelScan scan) throws Exception {
        XnatExperimentdata expt = null;
        switch (scan.getScanType()) {
            case "CT":
                CcdbHotelct ctSession = new CcdbHotelct();
                ctSession.setId( XnatExperimentdata.CreateNewID());
                ctSession.setLabel( scan.getScanName());
                break;
            case "PT":
            case "PET":
                CcdbHotelpet petSesion = new CcdbHotelpet();
                petSesion.setId( XnatExperimentdata.CreateNewID());
                petSesion.setLabel( scan.getScanName());
                petSesion.setScanner( scan.getScanner());
                switch( scan.getHotelPosition()) {
                    case "1":
                        petSesion.setPos1TimePoints(    scan.getTimePoints());
                        petSesion.setPos1ActivityMcl(   scan.getActivity());
                        petSesion.setPos1InjectionTime( scan.getInjectionTime());
                        petSesion.setPos1ScanTimePet(   scan.getScanTime());
                        petSesion.setPos1Weight(        scan.getAnimalWeight());
                        break;
                    case "2":
                        petSesion.setPos2TimePoints(    scan.getTimePoints());
                        petSesion.setPos2ActivityMcl(   scan.getActivity());
                        petSesion.setPos2InjectionTime( scan.getInjectionTime());
                        petSesion.setPos2ScanTimePet(   scan.getScanTime());
                        petSesion.setPos2Weight(        scan.getAnimalWeight());
                        break;
                    case "3":
                        petSesion.setPos3TimePoints(    scan.getTimePoints());
                        petSesion.setPos3ActivityMcl(   scan.getActivity());
                        petSesion.setPos3InjectionTime( scan.getInjectionTime());
                        petSesion.setPos3ScanTimePet(   scan.getScanTime());
                        petSesion.setPos3Weight(        scan.getAnimalWeight());
                        break;
                    case "4":
                        petSesion.setPos4TimePoints(    scan.getTimePoints());
                        petSesion.setPos4ActivityMcl(   scan.getActivity());
                        petSesion.setPos4InjectionTime( scan.getInjectionTime());
                        petSesion.setPos4ScanTimePet(   scan.getScanTime());
                        petSesion.setPos4Weight(        scan.getAnimalWeight());
                        break;
                    default:
                        break;
                        // unknown hotel position.
                }
                break;
            default:
                // unknown scan type
                break;
        }
        return expt;
    }

}
