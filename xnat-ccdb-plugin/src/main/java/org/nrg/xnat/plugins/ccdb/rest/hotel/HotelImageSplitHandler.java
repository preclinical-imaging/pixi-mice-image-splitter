package org.nrg.xnat.plugins.ccdb.rest.hotel;

import org.nrg.containers.exceptions.*;
import org.nrg.containers.model.command.auto.Command;
import org.nrg.containers.model.command.auto.CommandSummaryForContext;
import org.nrg.containers.model.container.auto.Container;
import org.nrg.containers.services.CommandService;
import org.nrg.containers.services.ContainerService;
import org.nrg.framework.exceptions.NotFoundException;
import org.nrg.xdat.om.*;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.exception.ElementNotFoundException;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.SaveItemHelper;
import org.nrg.xnat.plugins.ccdb.service.XnatService;
import org.nrg.xnat.plugins.ccdb.service.XnatServiceException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;

import java.io.File;
import java.util.*;

/**
 * Handle splitting hotel images into individual images.
 *
 * This version delegates to a container.
 *
 */
public class HotelImageSplitHandler {

    private final SiteConfigPreferences _preferences;
    private final XnatService _xnatService;
    private final CommandService _commandService;
    private final ContainerService _containerService;

    private String _commandName;

    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    public HotelImageSplitHandler(final SiteConfigPreferences preferences,
                                  final XnatService xnatService,
                                  final CommandService commandService,
                                  final ContainerService containerService) {
        _preferences = preferences;
        _xnatService = xnatService;
        _commandService = commandService;
        _containerService = containerService;
    }

    public void handleHotelSession(String project, String sessionID, UserI user) throws HandlerException {
//        try {
        XnatImagesessiondata session = _xnatService.getImageSession( sessionID, user);
            if( session instanceof CcdbHotelct || session instanceof CcdbHotelpet) {
                final List<CommandSummaryForContext> available;
                try {
                    available = _commandService.available(project, session.getXSIType(), user);
                } catch (ElementNotFoundException e) {
                    throw new HandlerException( String.format("Command not found for %s in project %s", session.getXSIType(), project), HttpStatus.BAD_REQUEST);
                }
                _commandName = "hotel-image-splitter-qc";
                Optional<CommandSummaryForContext> cs = available.stream().filter( c -> c.commandName().equals( _commandName)).findAny();
                long commandID;
                long wrapperID;
                if( cs.isPresent()) {
                    commandID = cs.get().commandId();
                    wrapperID = cs.get().wrapperId();
                }
                else {
                    throw new HandlerException( String.format("Command '%s' not found for %s in project %s", _commandName, session.getXSIType(), project), HttpStatus.BAD_REQUEST);
                }

                try {
                    Command command = _commandService.get(commandID);

                    Map<String, String> inputValues = new HashMap<>();
                    inputValues.put("xsiType", session.getXSIType());
                    inputValues.put("session-label", session.getId());
                    inputValues.put("session", session.getId());
                    inputValues.put("session-label-di", session.getId());
                    inputValues.put("scan", "1");

                    Container container = _containerService.resolveCommandAndLaunchContainer( wrapperID, inputValues, user);
                    _log.debug(container.toString());
                }
                catch ( NotFoundException e) {
                    throw new HandlerException( String.format("Command name '%s', id '%d' not found.", _commandName, commandID), HttpStatus.INTERNAL_SERVER_ERROR);
                } catch (ContainerException | CommandResolutionException | DockerServerException | NoDockerServerException e) {
                    throw new HandlerException( String.format("Error running '%s' on session %s.", _commandName, sessionID), e, HttpStatus.INTERNAL_SERVER_ERROR);
                } catch (UnauthorizedException e) {
                    throw new HandlerException( String.format("Unauthorized %s running '%s' on session %s.", user.getLogin(), _commandName, sessionID), e, HttpStatus.UNAUTHORIZED);
                }

            }
            else {
                throw new HandlerException( String.format("Cannot split non-hotel session: %s", session.getLabel()), HttpStatus.BAD_REQUEST);
            }
//        }
//        catch( XnatServiceException e) {
//            throw new HandlerException( e.getMessage(), e, HttpStatus.INTERNAL_SERVER_ERROR);
//        }
    }

    public String get_commandName() {
        return _commandName;
    }

    public void set_commandName(String commandName) {
        _commandName = commandName;
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