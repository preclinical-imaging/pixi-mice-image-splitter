package org.nrg.xnat.plugins.ccdb.rest.hotel;

import org.nrg.xdat.om.*;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.SaveItemHelper;
import org.nrg.xnat.helpers.uri.UriParserUtils;
import org.nrg.xnat.plugins.ccdb.service.XnatService;
import org.nrg.xnat.plugins.ccdb.service.XnatServiceException;
import org.nrg.xnat.services.archive.CatalogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;

import java.io.File;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Handle the loading of a collection of Hotel Sessions.
 *
 */
public class HotelSessionHandler  {

    private final SiteConfigPreferences _preferences;
    private final CatalogService _catalogService;
    private final XnatService _xnatService;
    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    public HotelSessionHandler( final SiteConfigPreferences preferences, final CatalogService catalogService) {
        _preferences = preferences;
        _catalogService = catalogService;
        // TODO: inject this
        _xnatService = new XnatService(_catalogService);
    }

    public void handleSubjects(String project, Collection<HotelSubject> subjects, UserI user) throws Exception {
        for( HotelSubject subject: subjects) {
            handleSubject( project, subject, user);
        }
    }

    public void handleSubject( String project, HotelSubject subject, UserI user) throws Exception {
        XnatProjectdata projectdata = XnatProjectdata.getProjectByIDorAlias( project, user, false);
        if( projectdata == null) {
            String msg = "Project not found: " + project;
            throw new HandlerException(msg, HttpStatus.BAD_REQUEST);
        }

        try {
            XnatSubjectdata subjectdata = _xnatService.getOrCreateSubject(projectdata, subject.getSubjectLabel(), user);

            _xnatService.insertOrUpdateField( subjectdata, "subjectorder", subject.getSubjectOrderString(), user);

            for( HotelSession session: subject.getSessions()) {

                XnatImagesessiondata imageSession = getOrCreateHotelImageSession( project, subjectdata, session.getModalities(), session.getHotelSessionLabel(), user);

                Set<String> loadedScans = new HashSet<>();
                for( HotelScan scan: session.getScans()) {
                    if( ! loadedScans.contains( scan.getScanName())) {
                    // add the first scan to the session.
                        final XnatImagescandata imageScan = _xnatService.createImageScan(imageSession.getId(), scan.getScanType(), "1", "IMAGE", user);
                        String uri = String.format("/archive/experiments/%s/scans/%s", imageSession.getId(), imageScan.getId());
                        addResources(uri, scan.getImages(), user);
                        loadedScans.add( scan.getScanName());
                    }
                    // update the session with all the scans' metadata.
                    udateScanInfo(imageSession, scan, user);
                }
            }
        } catch( XnatServiceException e) {
            throw new HandlerException( e.getMessage(), e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    protected XnatImagesessiondata getOrCreateHotelImageSession( String project, XnatSubjectdata subjectdata, String modality, String label, UserI user) throws Exception {
        XnatImagesessiondata imageSession = XnatImagesessiondata.getXnatImagesessiondatasById( label, user, false);
        if( imageSession == null) {
            imageSession = createHotelImageSession( project, subjectdata, modality, label, user);
        }
        return imageSession;
    }

    /**
     * Get an existing subject assessor (Hotel Session).
     *
     * @param subjectdata The subject
     * @param hotelScan A hotel scan that is contained by the session.
     * @param user The user.
     * @return The subject assessor (hotel session) for this scan or null if none exists.
     */
    protected XnatSubjectassessordata getAssessor(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) {
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
    /**
     * Create the particular class of subject assessor (Hotel Session) based on the type of scan.
     *
     */
    public XnatImagesessiondata createHotelImageSession( String project, XnatSubjectdata subjectdata, String modality, String label, UserI user) throws Exception {
        XnatImagesessiondata imagesessiondata = null;
        switch (modality) {
            case "CT":
                CcdbHotelct ctSession = new CcdbHotelct();
                ctSession.setId( XnatExperimentdata.CreateNewID());
                ctSession.setLabel( label);
                imagesessiondata = ctSession;
                break;
            case "PT":
            case "PET":
                CcdbHotelpet petSesion = new CcdbHotelpet();
                petSesion.setId( XnatExperimentdata.CreateNewID());
                petSesion.setLabel( label);
                imagesessiondata = petSesion;
                break;
            default:
                // unknown scan type
                imagesessiondata = null;
                break;
        }
        if( imagesessiondata != null) {
            imagesessiondata.setSubjectId(subjectdata.getId());
            imagesessiondata.setProject(project);
            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "update hotel-subject assessor with scan.");
            SaveItemHelper.authorizedSave(imagesessiondata.getItem(), user, false, false, false, false, eventMeta);
        }
        return imagesessiondata;
    }

    public XnatResourcecatalog addResources( String parentUri, List<File> files, UserI user) throws HandlerException {
        try {
            final boolean preserveDirectories = false;
            final String label = "imageData";
            final String format = "weird binary";
            final String description = "description";
            final String content = "content";

            final XnatResourcecatalog resourcecatalog = _xnatService.insertResources( parentUri, files, preserveDirectories, label, description, format, content, user);

            return  resourcecatalog;
        }
        catch( Exception e) {
            String msg = "Error attaching resources to uri: " + parentUri;
            throw new HandlerException( msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Fill in details from the scan into the assessor.
     * hotel scans referring to PET sessions add details to the subject assessor (Hotel Session).
     * @param assessor The assessor.
     * @param scan The scan.
     * @param user The user.
     * @throws HandlerException
     */
    public void udateScanInfo(XnatSubjectassessordata assessor, HotelScan scan, UserI user) throws HandlerException {
        try {
            if (assessor instanceof CcdbHotelpet) {
                CcdbHotelpet petHotel = (CcdbHotelpet) assessor;
                switch (scan.getHotelPosition()) {
                    case "1":
                        petHotel.setPos1TimePoints(scan.getTimePoints());
                        petHotel.setPos1ActivityMcl(scan.getActivity());
                        petHotel.setPos1InjectionTime(scan.getInjectionTime());
                        petHotel.setPos1ScanTimePet(scan.getScanTime());
                        petHotel.setPos1Weight(scan.getAnimalWeight());
                        break;
                    case "2":
                        petHotel.setPos2TimePoints(scan.getTimePoints());
                        petHotel.setPos2ActivityMcl(scan.getActivity());
                        petHotel.setPos2InjectionTime(scan.getInjectionTime());
                        petHotel.setPos2ScanTimePet(scan.getScanTime());
                        petHotel.setPos2Weight(scan.getAnimalWeight());
                        break;
                    case "3":
                        petHotel.setPos3TimePoints(scan.getTimePoints());
                        petHotel.setPos3ActivityMcl(scan.getActivity());
                        petHotel.setPos3InjectionTime(scan.getInjectionTime());
                        petHotel.setPos3ScanTimePet(scan.getScanTime());
                        petHotel.setPos3Weight(scan.getAnimalWeight());
                        break;
                    case "4":
                        petHotel.setPos4TimePoints(scan.getTimePoints());
                        petHotel.setPos4ActivityMcl(scan.getActivity());
                        petHotel.setPos4InjectionTime(scan.getInjectionTime());
                        petHotel.setPos4ScanTimePet(scan.getScanTime());
                        petHotel.setPos4Weight(scan.getAnimalWeight());
                        break;
                    default:
                        break;
                    // unknown hotel position.
                }
                EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "update hotel-subject assessor with scan.");
                SaveItemHelper.authorizedSave(assessor.getItem(), user, false, false, false, false, eventMeta);
            }
        }
        catch( Exception e) {
            String msg = "Error updating PT Hotel-Subject assessor.";
            throw new HandlerException( msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

}
