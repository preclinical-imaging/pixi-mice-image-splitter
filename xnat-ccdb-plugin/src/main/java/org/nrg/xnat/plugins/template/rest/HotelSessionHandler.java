package org.nrg.xnat.plugins.template.rest;

import org.nrg.xdat.om.*;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.XFTItem;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.ResourceFile;
import org.nrg.xft.utils.SaveItemHelper;
import org.nrg.xnat.helpers.uri.UriParserUtils;
import org.nrg.xnat.services.archive.CatalogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.List;

//@Component
public class HotelSessionHandler  {

    private final SiteConfigPreferences _preferences;
    private final CatalogService _catalogService;
    private static final Logger _log = LoggerFactory.getLogger( HotelSessionHandler.class);

    public HotelSessionHandler( final SiteConfigPreferences preferences, final CatalogService catalogService) {
        _preferences = preferences;
        _catalogService = catalogService;
    }

    public void handleSessions(String project, Collection<HotelSession> sessions, UserI user) throws Exception {
        for( HotelSession session: sessions) {
            handleSession( project, session, user);
        }
    }

    public void handleSession( String project, HotelSession session, UserI user) throws Exception {
        XnatProjectdata projectdata = XnatProjectdata.getProjectByIDorAlias( project, user, false);
        if( projectdata == null) {
            // bad request.  no such project.
        }

        XnatSubjectdata subjectdata = getOrCreateSubject( projectdata, session.getSubjectLabel(), user);

        for( HotelScan scan: session.getScans()) {
            XnatSubjectassessordata assessor = getAssessor(subjectdata, scan, user);
            if( assessor == null) {
                assessor = createAssessor(subjectdata, scan, user);
                subjectdata.addExperiments_experiment(assessor);
            }
            addScan( assessor, scan, user);
            addImages( assessor, scan.getImages(), user);
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
                EventMetaI eventMeta = EventUtils.DEFAULT_EVENT( user, "create subject");
                subjectdata.save( user, false, false, eventMeta);

            } catch (Exception e) {
                // throw internal server error
            }
        }
        return subjectdata;
    }

    protected XnatSubjectassessordata getAssessor(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) throws Exception {
        XnatSubjectassessordata assessor = null;

        List<? extends XnatExperimentdata> expts = subjectdata.getExperiments_experiment();
        for( XnatExperimentdata expt: expts) {
            if( expt.getLabel().matches( hotelScan.getScanName())) {
                assessor = (XnatSubjectassessordata) expt;
                break;
            }
        }
        return assessor;
    }

    protected XnatSubjectassessordata createAssessor(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) throws Exception {
        XnatSubjectassessordata assessor = null;
        assessor = createHotelAssessor( hotelScan);
        assessor.setProject( subjectdata.getProject());
        assessor.setSubjectId( subjectdata.getId());
        assessor.setDate( new Date());

        EventMetaI eventMeta = EventUtils.DEFAULT_EVENT( user, "update hotel-subject assessor.");
        SaveItemHelper.authorizedSave( assessor.getItem(), user,false, false, false, false, eventMeta);

        return assessor;
    }

    public XnatSubjectassessordata createHotelAssessor( HotelScan scan) throws Exception {
        XnatSubjectassessordata assessor = null;
        switch (scan.getScanType()) {
            case "CT":
                CcdbHotelct ctSession = new CcdbHotelct();
                ctSession.setId( XnatExperimentdata.CreateNewID());
                ctSession.setLabel( scan.getScanName());
                assessor = ctSession;
                break;
            case "PT":
            case "PET":
                CcdbHotelpet petSesion = new CcdbHotelpet();
                petSesion.setId( XnatExperimentdata.CreateNewID());
                petSesion.setLabel( scan.getScanName());
                petSesion.setScanner( scan.getScanner());
                assessor = petSesion;
                break;
            default:
                // unknown scan type
                assessor = null;
                break;
        }
        return assessor;
    }

    public void addImages( XnatSubjectassessordata assessor, List<File> files, UserI user) throws Exception {
        if( ! assessorHasFiles( assessor, files, user)) {
            addResources( assessor, files, user);
        }
    }

    public boolean assessorHasFiles(XnatSubjectassessordata assessor, List<File> files, UserI user) {
        List<ResourceFile> resourceFiles = assessor.getFileResources("imageData");
        for( ResourceFile resourceFile: resourceFiles) {
//            if( resourceMatches( resourceFile, files)) {
//                return true;
//            }
        }
        return false;
    }

    public boolean resourceMatches( ResourceFile rf, File f) {
        return rf.getF().getName().equals( f.getName());
    }

    public void addResources(XnatSubjectassessordata assessor, List<File> files, UserI user) throws Exception {
        String parentUri = UriParserUtils.getArchiveUri(assessor);
        String label = "imageData";
        String format = "weird binary";
        final XnatResourcecatalog resourcecatalog = _catalogService.insertResources(user, parentUri, files, true, label, null, format, null);
        String createdUri = UriParserUtils.getArchiveUri(resourcecatalog);
//        _catalogService.refreshResourceCatalog( user, createdUri );
    }

    public void addScan( XnatSubjectassessordata assessor, HotelScan scan, UserI user) throws Exception {
        if( assessor instanceof CcdbHotelpet) {
            CcdbHotelpet petHotel = (CcdbHotelpet) assessor;
            switch( scan.getHotelPosition()) {
                case "1":
                    petHotel.setPos1TimePoints(    scan.getTimePoints());
                    petHotel.setPos1ActivityMcl(   scan.getActivity());
                    petHotel.setPos1InjectionTime( scan.getInjectionTime());
                    petHotel.setPos1ScanTimePet(   scan.getScanTime());
                    petHotel.setPos1Weight(        scan.getAnimalWeight());
                    break;
                case "2":
                    petHotel.setPos2TimePoints(    scan.getTimePoints());
                    petHotel.setPos2ActivityMcl(   scan.getActivity());
                    petHotel.setPos2InjectionTime( scan.getInjectionTime());
                    petHotel.setPos2ScanTimePet(   scan.getScanTime());
                    petHotel.setPos2Weight(        scan.getAnimalWeight());
                    break;
                case "3":
                    petHotel.setPos3TimePoints(    scan.getTimePoints());
                    petHotel.setPos3ActivityMcl(   scan.getActivity());
                    petHotel.setPos3InjectionTime( scan.getInjectionTime());
                    petHotel.setPos3ScanTimePet(   scan.getScanTime());
                    petHotel.setPos3Weight(        scan.getAnimalWeight());
                    break;
                case "4":
                    petHotel.setPos4TimePoints(    scan.getTimePoints());
                    petHotel.setPos4ActivityMcl(   scan.getActivity());
                    petHotel.setPos4InjectionTime( scan.getInjectionTime());
                    petHotel.setPos4ScanTimePet(   scan.getScanTime());
                    petHotel.setPos4Weight(        scan.getAnimalWeight());
                    break;
                default:
                    break;
                // unknown hotel position.
            }
            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT( user, "update hotel-subject assessor with scan.");
            SaveItemHelper.authorizedSave( assessor.getItem(), user,false, false, false, false, eventMeta);
        }
    }

}
