package org.nrg.xapi.rest.ccdb;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import org.nrg.framework.annotations.XapiRestController;
import org.nrg.framework.exceptions.NrgServiceException;
import org.nrg.xapi.rest.AbstractXapiProjectRestController;
import org.nrg.xdat.preferences.SiteConfigPreferences;
import org.nrg.xdat.security.services.RoleHolder;
import org.nrg.xdat.security.services.UserManagementServiceI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;
import java.util.Map;

@Api("CCDB REST Api")
@XapiRestController
@RequestMapping(value = "/ccdb")
public class CCDBRestApi extends AbstractXapiProjectRestController {

    private final SiteConfigPreferences _preferences;
    private static final Logger _log = LoggerFactory.getLogger( CCDBRestApi.class);

    @Autowired
    public CCDBRestApi(final UserManagementServiceI userManagementServiceI, final RoleHolder roleHolder, final SiteConfigPreferences preferences) {
        super( userManagementServiceI, roleHolder);
        _preferences = preferences;
    }

    @ApiOperation(value = "Upload CCDB Hotel data.", response = String.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Successfully uploaded CCDB Hotel data.")})
    @ResponseBody
    public ResponseEntity<List<String>> doUploadHotelData(@RequestParam final Map<String,String> allRequestParams) throws NrgServiceException {
        try {

            return new ResponseEntity<List<String>>(HttpStatus.NO_CONTENT);
        }
        catch( Exception e) {
            _log.error("An error occured when user " + getSessionUser().getUsername() + " tried to upload CCDB Hotel data with params " + allRequestParams, e);
            return new ResponseEntity<List<String>> (HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
