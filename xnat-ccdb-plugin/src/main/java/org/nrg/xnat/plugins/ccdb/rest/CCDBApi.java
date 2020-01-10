package org.nrg.xnat.plugins.ccdb.rest;

import io.swagger.annotations.*;
import org.nrg.framework.annotations.XapiRestController;
import org.nrg.framework.exceptions.NrgServiceException;
import org.nrg.xapi.authorization.GuestUserAccessXapiAuthorization;
import org.nrg.xapi.rest.AbstractXapiRestController;
import org.nrg.xapi.rest.AuthDelegate;
import org.nrg.xapi.rest.XapiRequestMapping;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xdat.security.services.RoleHolder;
import org.nrg.xdat.security.services.UserManagementServiceI;
import org.nrg.xft.security.UserI;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk_WU;
import org.nrg.xnat.plugins.ccdb.rest.guest.Guest;
import org.nrg.xnat.plugins.ccdb.rest.hotel.HandlerException;
import org.nrg.xnat.plugins.ccdb.rest.hotel.HotelSession;
import org.nrg.xnat.plugins.ccdb.rest.hotel.HotelSessionHandler;
import org.nrg.xnat.services.archive.CatalogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static org.nrg.xdat.security.helpers.AccessLevel.Authorizer;

@Api("CCDB REST Api")
@XapiRestController
@RequestMapping(value = "/ccdb")
public class CCDBApi extends AbstractXapiRestController {

    private final CatalogService _catalogService;
    private final SiteConfigPreferences _preferences;
    private final FrontDesk _frontDesk;
    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    @Autowired
    public CCDBApi(final UserManagementServiceI userManagementServiceI,
                   final RoleHolder roleHolder,
                   final SiteConfigPreferences preferences,
                   final CatalogService catalogService,
                   final FrontDesk frontDesk) {
        super( userManagementServiceI, roleHolder);
        _preferences = preferences;
        _catalogService = catalogService;
        _frontDesk = frontDesk;
    }

    @ApiOperation(value = "Upload CCDB Hotel data.", response = String.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Successfully uploaded CCDB Hotel session(s)."),
            @ApiResponse(code = 500, message = "An unexpected or unknown error occurred")})
    @XapiRequestMapping(value = "projects/{projectID}/hotelSessions",
            consumes = {"application/zip"},
            method = RequestMethod.POST,
            restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<String> doUploadHotelDataCustom(
            @ApiParam("The project label or ID") @PathVariable final String  projectID,
            @ApiParam("Zip file with hotel-session csv and image data") @RequestBody final Map<String, File> files) throws NrgServiceException {
        try {
            if( ! files.isEmpty()) {

                Collection<HotelSession> hotelSessions = HotelSession.getSessionsFromFiles( files.values().stream().collect(Collectors.toList()));
                if( hotelSessions.isEmpty()) {
                    return new ResponseEntity<>("Failed to find hotel-scan csv.", HttpStatus.BAD_REQUEST);
                }
                UserI user = getSessionUser();

                HotelSessionHandler sessionHandler = new HotelSessionHandler( _preferences, _catalogService);

                sessionHandler.handleSessions( projectID, hotelSessions, user);

                return new ResponseEntity<>(HttpStatus.OK);
            }
            else {
                return new ResponseEntity<>("Zip file is invalid or empty.", HttpStatus.BAD_REQUEST);
            }
        }
        catch( Exception e) {
            HttpStatus status = (e instanceof HandlerException)? ((HandlerException) e).getHttpStatus(): HttpStatus.INTERNAL_SERVER_ERROR;
            String msg = "An error occurred when user '" + getSessionUser().getUsername() + "' tried to upload CCDB hotel-data zip file.";
            msg += "\n" + e.getMessage();
            _log.error( msg, e);
            ResponseEntity<String> response = new ResponseEntity<> (msg, status);
            return response;
        }
    }

//    @ApiOperation(value = "Upload CCDB Hotel data.", response = String.class)
//    @ApiResponses({@ApiResponse(code = 200, message = "Successfully uploaded CCDB Hotel session(s)."),
//            @ApiResponse(code = 500, message = "An unexpected or unknown error occurred")})
//    @XapiRequestMapping(value = "projects/{projectID}/hotelSessions",
//            consumes = {MediaType.MULTIPART_FORM_DATA_VALUE},
//            method = RequestMethod.POST,
//            restrictTo = Authorizer)
//    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
//    public ResponseEntity<String> doUploadHotelDataMultipart(
//            @ApiParam("The project label or ID") @PathVariable final String  projectID,
//            @ApiParam("Zip file with hotel-session csv and image data") @RequestParam("file") final MultipartFile file) throws NrgServiceException {
//        try {
//            List<File> files = _zipper.unzip(file.getInputStream());
//            if( ! files.isEmpty()) {
//
//                Collection<HotelSession> hotelSessions = HotelSession.getSessionsFromFiles( files);
//                if( hotelSessions.isEmpty()) {
//                    return new ResponseEntity<>("Failed to find hotel-scan csv.", HttpStatus.BAD_REQUEST);
//                }
//                UserI user = getSessionUser();
//
//                HotelSessionHandler sessionHandler = new HotelSessionHandler( _preferences, _catalogService);
//
//                sessionHandler.handleSessions( projectID, hotelSessions, user);
//
//                return new ResponseEntity<>(HttpStatus.OK);
//            }
//            else {
//                return new ResponseEntity<>("Zip file is invalid or empty.", HttpStatus.BAD_REQUEST);
//            }
//        }
//        catch( Exception e) {
//            HttpStatus status = (e instanceof HandlerException)? ((HandlerException) e).getHttpStatus(): HttpStatus.INTERNAL_SERVER_ERROR;
//            String msg = "An error occurred when user '" + getSessionUser().getUsername() + "' tried to upload CCDB hotel-data zip file: " + file.getOriginalFilename();
//            msg += "\n" + e.getMessage();
//            _log.error( msg, e);
//            ResponseEntity<String> response = new ResponseEntity<> (msg, status);
//            return response;
//        }
//        finally {
//            try { _zipper.close();} catch (IOException e) { /* ignore */}
//        }
//    }

    @ApiOperation(value = "Split hotel session into multiple guest sessions.", response = String.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Successfully created guest session(s)."),
            @ApiResponse(code = 500, message = "An unexpected or unknown error occurred")})
    @XapiRequestMapping(value = "projects/{projectID}/experiments/{hotelSessionID}/checkin",
            method = RequestMethod.PUT,
            restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<String> doCheckinHotelSession(
            @ApiParam("The project label or ID") @PathVariable final String  projectID,
            @ApiParam("The hotel session ID") @PathVariable final String  hotelSessionID) throws NrgServiceException {
        try {
            UserI user = getSessionUser();
            FrontDesk_WU frontDesk = (FrontDesk_WU) _frontDesk;

            List<Guest> guestList = frontDesk.getGuests(hotelSessionID, user);

//            for (Guest g : guestList) {
//                out.println "${g.label}"
//                g.sessions.each{ sess ->
//                    println "${sess}"
//                    println "label: ${sess.label}"
//                    println "resource files:"
//                    sess.resourceFiles.each { rf ->
//                        println "${rf.absolutePath}"
//                    }
//                }
//            }
//
//            XnatService service = frontDesk.xnatService
//            XnatResourcecatalog catalog = service.createScanResource( user)
//            out.println "catalog: ${catalog}"

            return new ResponseEntity<>(HttpStatus.OK);
        }
        catch( Exception e) {
            HttpStatus status = (e instanceof HandlerException)? ((HandlerException) e).getHttpStatus(): HttpStatus.INTERNAL_SERVER_ERROR;
            String msg = "An error occurred when user '" + getSessionUser().getUsername() + "' tried to checkin hotel session '" + hotelSessionID + "'.";
            msg += "\n" + e.getMessage();
            _log.error( msg, e);
            ResponseEntity<String> response = new ResponseEntity<> (msg, status);
            return response;
        }
    }

}
