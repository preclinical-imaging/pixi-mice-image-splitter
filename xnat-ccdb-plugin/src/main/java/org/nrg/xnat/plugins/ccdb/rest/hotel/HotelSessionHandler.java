package org.nrg.xnat.plugins.ccdb.rest.hotel;

import org.nrg.xdat.om.*;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.SaveItemHelper;
import org.nrg.xnat.plugins.ccdb.service.XnatService;
import org.nrg.xnat.plugins.ccdb.service.XnatServiceException;
import org.nrg.xnat.services.archive.CatalogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;

import java.io.File;
import java.util.*;

/**
 * Handle the loading of a collection of Hotel Sessions.
 *
 */
public class HotelSessionHandler  {

    private final SiteConfigPreferences _preferences;
    private final CatalogService _catalogService;
    private final XnatService _xnatService;
    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    public HotelSessionHandler( final SiteConfigPreferences preferences, final CatalogService catalogService, final XnatService xnatService) {
        _preferences = preferences;
        _catalogService = catalogService;
        _xnatService = xnatService;
    }

    public void handleSubjects(String project, Collection<HotelSubject> subjects, Map<String, File> files, UserI user) throws Exception {
        for( HotelSubject subject: subjects) {
            handleSubject( project, subject, files, user);
        }
    }

    public void handleSubject(String project, HotelSubject subject, Map<String, File> files, UserI user) throws Exception {
        XnatProjectdata projectdata = XnatProjectdata.getProjectByIDorAlias( project, user, false);
        if( projectdata == null) {
            String msg = "Project not found: " + project;
            throw new HandlerException(msg, HttpStatus.BAD_REQUEST);
        }

        try {
            XnatSubjectdata subjectdata = _xnatService.getOrCreateSubject(projectdata, subject.getSubjectLabel(), user);
            subjectdata.setGroup("hotel");

            Optional<File> csvFile = getCSVFile( files);
            if( csvFile.isPresent()) {
                _xnatService.addResources(subjectdata, Arrays.asList(csvFile.get()), false, "metaData", "", "csv", "metadata", user);
                _xnatService.insertResources(subjectdata, Arrays.asList(csvFile.get()), false, "metaData", "", "csv", "metadata", user);
            }
            else {
                _log.warn("Missing CSV file for subject {}.", subject.getSubjectLabel());
            }

            Optional<File> xlsFile = getXLSXFile( files, subject.getSubjectLabel());
            if( xlsFile.isPresent()) {
                _xnatService.addResources(subjectdata, Arrays.asList(csvFile.get()), false, "metaData", "", "csv", "metadata", user);
                _xnatService.insertResources( subjectdata, Arrays.asList(xlsFile.get()), false, "metaData", "", "xlsx", "metadata", user);
            }
            else {
                _log.warn("Missing XLS file for subject {}.", subject.getSubjectLabel());
            }

            // don't do this per CCDB-16
            // _xnatService.insertOrUpdateField( subjectdata, "subjectorder", subject.getSubjectOrderString(), user);

            for( HotelSession session: subject.getSessions()) {

                XnatImagesessiondata imageSession = getOrCreateHotelImageSession( project, subjectdata, session.getModalities(), session.getHotelSessionLabel(), user);
                imageSession.setDate( session.getStudyDate());
                imageSession.setTime( session.getScanTime());
                if( imageSession instanceof CcdbHotelct) {
                    CcdbHotelct hotelct = (CcdbHotelct) imageSession;
                    hotelct.setOrganOfInterest( session.getOrganOfInterest());
                }
                else if( imageSession instanceof CcdbHotelpet) {
                    CcdbHotelpet hotelpet = (CcdbHotelpet) imageSession;
                    hotelpet.setOrganOfInterest( session.getOrganOfInterest());
                }

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
                    updateScanInfo(imageSession, scan, user);
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
            final String format = "IMG";
            final String description = "description";
            final String content = "RAW";

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
    public void updateScanInfo(XnatSubjectassessordata assessor, HotelScan scan, UserI user) throws HandlerException {
        if (assessor instanceof CcdbHotelpet) {
            updatePTScanInfo( (CcdbHotelpet) assessor, scan, user);
        }
        else if (assessor instanceof CcdbHotelct) {
            updateCTScanInfo( (CcdbHotelct) assessor, scan, user);
        }
    }

    public void updatePTScanInfo(CcdbHotelpet hotelpet, HotelScan scan, UserI user) throws HandlerException {
        try {
            String hotelPositionLabel = scan.getHotelPosition().get(0);
            switch (hotelPositionLabel) {
                case "1":
                case "ctr":
                case "l":
                case "tl":
                case "lt":
                    hotelpet.setPos1TimePoints( scan.getTimePoints());
                    hotelpet.setPos1ActivityMcl( scan.getActivity());
                    hotelpet.setPos1InjectionTime( scan.getInjectionTime());
                    hotelpet.setPos1ScanTimePet( scan.getScanTime());
                    hotelpet.setPos1Weight( scan.getAnimalWeight());
                    hotelpet.setPos1AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                    hotelpet.setPos1HotelPosition( hotelPositionLabel);
                    hotelpet.setPos1Tracer( scan.getTracer());
                    hotelpet.setPos1Notes( scan.getNotes());
                    hotelpet.setPos1SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                    hotelpet.setPos1SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                    break;
                case "2":
                case "r":
                case "tr":
                case "rt":
                    hotelpet.setPos2TimePoints( scan.getTimePoints());
                    hotelpet.setPos2ActivityMcl( scan.getActivity());
                    hotelpet.setPos2InjectionTime( scan.getInjectionTime());
                    hotelpet.setPos2ScanTimePet( scan.getScanTime());
                    hotelpet.setPos2Weight( scan.getAnimalWeight());
                    hotelpet.setPos2AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                    hotelpet.setPos2HotelPosition( hotelPositionLabel);
                    hotelpet.setPos2Tracer( scan.getTracer());
                    hotelpet.setPos2Notes( scan.getNotes());
                    hotelpet.setPos2SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                    hotelpet.setPos2SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                    break;
                case "3":
                case "rb":
                case "br":
                    hotelpet.setPos3TimePoints( scan.getTimePoints());
                    hotelpet.setPos3ActivityMcl( scan.getActivity());
                    hotelpet.setPos3InjectionTime( scan.getInjectionTime());
                    hotelpet.setPos3ScanTimePet( scan.getScanTime());
                    hotelpet.setPos3Weight( scan.getAnimalWeight());
                    hotelpet.setPos3AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                    hotelpet.setPos3HotelPosition( hotelPositionLabel);
                    hotelpet.setPos3Tracer( scan.getTracer());
                    hotelpet.setPos3Notes( scan.getNotes());
                    hotelpet.setPos3SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                    hotelpet.setPos3SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                    break;
                case "4":
                case "lb":
                case "bl":
                    hotelpet.setPos4TimePoints( scan.getTimePoints());
                    hotelpet.setPos4ActivityMcl( scan.getActivity());
                    hotelpet.setPos4InjectionTime( scan.getInjectionTime());
                    hotelpet.setPos4ScanTimePet( scan.getScanTime());
                    hotelpet.setPos4Weight( scan.getAnimalWeight());
                    hotelpet.setPos4AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                    hotelpet.setPos4HotelPosition( hotelPositionLabel);
                    hotelpet.setPos4Tracer( scan.getTracer());
                    hotelpet.setPos4Notes( scan.getNotes());
                    hotelpet.setPos4SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                    hotelpet.setPos4SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                    break;
                default:
                    break;
                // unknown hotel position.
            }
            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "update hotel-subject assessor with scan info.");
            SaveItemHelper.authorizedSave(hotelpet.getItem(), user, false, false, false, false, eventMeta);
        } catch (Exception e) {
            String msg = "Error updating PT Hotel-Subject assessor.";
            throw new HandlerException(msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    public void updateCTScanInfo( CcdbHotelct hotelct, HotelScan scan, UserI user) throws HandlerException {
        for( String hotelPositionLabel: scan.getHotelPosition()) {
            try {
                switch (hotelPositionLabel) {
                    case "1":
                    case "ctr":
                    case "l":
                    case "tl":
                    case "lt":
                        hotelct.setPos1AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                        hotelct.setPos1HotelPosition( hotelPositionLabel);
                        hotelct.setPos1Notes( scan.getNotes());
                        hotelct.setPos1SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                        hotelct.setPos1SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                        break;
                    case "2":
                    case "r":
                    case "tr":
                    case "rt":
                        hotelct.setPos2AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                        hotelct.setPos2HotelPosition( hotelPositionLabel);
                        hotelct.setPos2Notes( scan.getNotes());
                        hotelct.setPos2SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                        hotelct.setPos2SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                        break;
                    case "3":
                    case "rb":
                    case "br":
                        hotelct.setPos3AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                        hotelct.setPos3HotelPosition( hotelPositionLabel);
                        hotelct.setPos3Notes( scan.getNotes());
                        hotelct.setPos3SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                        hotelct.setPos3SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                        break;
                    case "4":
                    case "lb":
                    case "bl":
                        hotelct.setPos4AnimalNum( scan.getAnimalNumber( hotelPositionLabel));
                        hotelct.setPos4HotelPosition( hotelPositionLabel);
                        hotelct.setPos4Notes( scan.getNotes());
                        hotelct.setPos4SubjectLabel( scan.getSubjectLabel( hotelPositionLabel));
                        hotelct.setPos4SessionLabel( scan.getSessionLabel( hotelPositionLabel));
                        break;
                    default:
                        break;
                    // unknown hotel position.
                }
                EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "update hotel-subject assessor with scan info.");
                SaveItemHelper.authorizedSave(hotelct.getItem(), user, false, false, false, false, eventMeta);
            } catch (Exception e) {
                String msg = "Error updating CT Hotel-Subject assessor.";
                throw new HandlerException(msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
            }
        }
    }

    private Optional<File> getCSVFile( Map<String, File> files) {
        return files.values().stream().filter(f -> f.getName().endsWith(".csv")).findAny();
    }

    private Optional<File> getXLSXFile( Map<String, File> files, String subjectLabel) {
        String matchString = subjectLabel.substring(0,8);
        return files.values().stream()
                .filter(f -> f.getName().endsWith(".xlsx"))
                .filter(f -> f.getName().startsWith( matchString))
                .findAny();
    }
}