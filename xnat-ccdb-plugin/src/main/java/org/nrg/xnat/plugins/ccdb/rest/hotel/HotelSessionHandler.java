package org.nrg.xnat.plugins.ccdb.rest.hotel;

import org.nrg.xdat.om.*;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.ResourceFile;
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
import java.util.Date;
import java.util.List;

/**
 * Handle the loading of a collection of Hotel Sessions.
 *
 */
//@Component
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

    /**
     * Ingest the collection of Hotel Sessions.
     *
     * @param project The project label of the project to receive the hotel sessions.
     * @param sessions The collection of hotel sessions to be processed.
     * @param user The user doing the processing.
     * @throws HandlerException
     */
    public void handleSessions(String project, Collection<HotelSession> sessions, UserI user) throws HandlerException {
        for( HotelSession session: sessions) {
            handleSession( project, session, user);
        }
    }

    /**
     * Ingest a single Hotel Session.
     *
     * The central method that defines the processing flow.
     * The basic flow is:
     * 1. Find or create the subject
     * 2. for each scan in the session...
     *  a. Find or create the hotel scan (subject assessor).
     *  b. Add scan data to the assessor.
     *  c. Add image data as resource on the subject assessor.
     *
     * @param project The project label of the project to receive the hotel sessions.
     * @param session The collection of hotel sessions to be processed.
     * @param user The user doing the processing.
     * @throws HandlerException
     */
    public void handleSession( String project, HotelSession session, UserI user) throws HandlerException {
        XnatProjectdata projectdata = XnatProjectdata.getProjectByIDorAlias( project, user, false);
        if( projectdata == null) {
            String msg = "Project not found: " + project;
            throw new HandlerException(msg, HttpStatus.BAD_REQUEST);
        }

        try {
            XnatSubjectdata subjectdata = _xnatService.getOrCreateSubject(projectdata, session.getSubjectLabel(), user);

            for( HotelScan scan: session.getScans()) {
                XnatSubjectassessordata assessor = getAssessor(subjectdata, scan, user);
                if( assessor == null) {
                    assessor = createAssessor(subjectdata, scan, user);
                    try {
                        subjectdata.addExperiments_experiment(assessor);
                    }
                    catch( Exception e) {
                        String msg = "Error adding assessor to hotel subject: " + subjectdata.getLabel();
                        throw new HandlerException( msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
                    }
                }
                addScan( assessor, scan, user);
                addImages( assessor, scan.getImages(), user);
            }
        } catch( XnatServiceException e) {
            throw new HandlerException( e.getMessage(), e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
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
     * Create a subject assessor (Hotel Session).
     *
     * @param subjectdata The subject
     * @param hotelScan A hotel scan that is contained by the session.
     * @param user The user.
     * @return The subject assessor (hotel session) for this scan.
     */
    protected XnatSubjectassessordata createAssessor(XnatSubjectdata subjectdata, HotelScan hotelScan, UserI user) throws HandlerException {
        XnatSubjectassessordata assessor = null;
        assessor = createHotelAssessor(hotelScan);
        assessor.setProject(subjectdata.getProject());
        assessor.setSubjectId(subjectdata.getId());
        assessor.setDate(new Date());

        try {
            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "update hotel-subject assessor.");
            SaveItemHelper.authorizedSave(assessor.getItem(), user, false, false, false, false, eventMeta);
        }
        catch( Exception e) {
            String msg = "Error saving assessor for hotel subject: " + subjectdata.getLabel();
            throw new HandlerException(msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return assessor;
    }

    /**
     * Create the particular class of subject assessor (Hotel Session) based on the type of scan.
     *
     * @param scan The hotel scan.
     * @return The appropriate subclass of assessor: CccdbHotelct or CccdbHotelpt.
     * @throws HandlerException
     */
    public XnatSubjectassessordata createHotelAssessor( HotelScan scan) throws HandlerException {
        try {
            XnatSubjectassessordata assessor = null;
            switch (scan.getScanType()) {
                case "CT":
                    CcdbHotelct ctSession = new CcdbHotelct();
                    ctSession.setId( XnatExperimentdata.CreateNewID());
                    ctSession.setLabel(scan.getScanName());
                    assessor = ctSession;
                    break;
                case "PT":
                case "PET":
                    CcdbHotelpet petSesion = new CcdbHotelpet();
                    petSesion.setId( XnatExperimentdata.CreateNewID());
                    petSesion.setLabel(scan.getScanName());
                    petSesion.setScanner(scan.getScanner());
                    assessor = petSesion;
                    break;
                default:
                    // unknown scan type
                    assessor = null;
                    break;
            }
            return assessor;
        }
        catch( Exception e) {
            String msg = "Error creating hotel subject assessor. type: " + scan.getScanType();
            throw new HandlerException(msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Add the list of files as resource on the assessor if the images are not present.
     * @param assessor The assessor
     * @param files The list of files
     * @param user The user
     * @throws HandlerException
     */
    public void addImages( XnatSubjectassessordata assessor, List<File> files, UserI user) throws HandlerException {
        if( ! assessorHasFiles( assessor, files, user)) {
            addResources( assessor, files, user);
        }
    }

    /**
     * Test if list of files are all present as resources on assessor.
     * The resource name is currently hard coded as "imageData".
     * @param assessor The assessor.
     * @param files The list of files.
     * @param user The user.
     * @return true if all are present, false otherwise.
     */
    public boolean assessorHasFiles(XnatSubjectassessordata assessor, List<File> files, UserI user) {
        List<ResourceFile> resourceFiles = assessor.getFileResources("imageData");
        for( ResourceFile resourceFile: resourceFiles) {
//            if( resourceMatches( resourceFile, files)) {
//                return true;
//            }
        }
        return false;
    }

    /**
     * Test that defines criteria for and existing resource file to match a proposed file.
     * @param rf  Existing resource file.
     * @param f Proposed file to add.
     * @return true if they are the same, false otherwise.
     */
    public boolean resourceMatches( ResourceFile rf, File f) {
        return rf.getF().getName().equals( f.getName());
    }

    /**
     * Add the list of files as resources to the assessor.
     * This currently hard codes the resource label as "imageData" and the resource format as "weird binary".
     * @param assessor The assessor.
     * @param files The list of files.
     * @param user The user.
     * @throws HandlerException
     */
    public void addResources(XnatSubjectassessordata assessor, List<File> files, UserI user) throws HandlerException {
        try {
            String parentUri = UriParserUtils.getArchiveUri(assessor);
            String label = "imageData";
            String format = "weird binary";
            final XnatResourcecatalog resourcecatalog = _catalogService.insertResources(user, parentUri, files, true, label, null, format, null);
            String createdUri = UriParserUtils.getArchiveUri(resourcecatalog);
//        _catalogService.refreshResourceCatalog( user, createdUri );
        }
        catch( Exception e) {
            String msg = "Error attaching resources to assessor: " + assessor.getId();
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
    public void addScan( XnatSubjectassessordata assessor, HotelScan scan, UserI user) throws HandlerException {
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
