package org.nrg.xnat.plugins.template.rest;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import org.nrg.framework.annotations.XapiRestController;
import org.nrg.framework.exceptions.NrgServiceException;
import org.nrg.xapi.authorization.GuestUserAccessXapiAuthorization;
import org.nrg.xapi.rest.AbstractXapiRestController;
import org.nrg.xapi.rest.AuthDelegate;
import org.nrg.xapi.rest.XapiRequestMapping;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xdat.security.services.RoleHolder;
import org.nrg.xdat.security.services.UserManagementServiceI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.util.List;

import static org.nrg.xdat.security.helpers.AccessLevel.Authorizer;

@Api("CCDB REST Api")
@XapiRestController
@RequestMapping(value = "/ccdb")
public class CCDBApi extends AbstractXapiRestController {

    private final SiteConfigPreferences _preferences;
    private static final Logger _log = LoggerFactory.getLogger( CCDBApi.class);
    private final Zipper _zipper;

    @Autowired
    public CCDBApi(final UserManagementServiceI userManagementServiceI, final RoleHolder roleHolder, final SiteConfigPreferences preferences) {
        super( userManagementServiceI, roleHolder);
        _preferences = preferences;
        _zipper = new MyZipper();
    }

    @ApiOperation(value = "Upload CCDB Hotel data.", response = String.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Successfully uploaded CCDB Hotel data.")})
    @XapiRequestMapping(consumes = {MediaType.MULTIPART_FORM_DATA_VALUE}, method = RequestMethod.POST, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<List<String>> doUploadHotelData(@RequestParam("file") final MultipartFile file) throws NrgServiceException {
        try {
            List<File> files = _zipper.unzip(file.getInputStream());
            if( ! files.isEmpty()) {
                HotelCSVFile hotelCSVFile = new HotelCSVFile( files);
                return new ResponseEntity<List<String>>(HttpStatus.OK);
            }
            else {
                return new ResponseEntity<List<String>>(HttpStatus.NO_CONTENT);
            }
        }
        catch( Exception e) {
            _log.error("An error occured when user " + getSessionUser().getUsername() + " tried to upload CCDB Hotel data zip file " + file.getOriginalFilename(), e);
            return new ResponseEntity<List<String>> (HttpStatus.INTERNAL_SERVER_ERROR);
        }
        finally {
            try { _zipper.close();} catch (IOException e) { /* ignore */}
        }
    }
}