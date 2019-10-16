/*
 * xnat-template: org.nrg.xnat.plugins.template.rest.TemplatePrefsApi
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.template.rest;

import io.swagger.annotations.*;
import org.nrg.framework.annotations.XapiRestController;
import org.nrg.prefs.exceptions.InvalidPreferenceName;
import org.nrg.xapi.rest.AbstractXapiRestController;
import org.nrg.xapi.rest.XapiRequestMapping;
import org.nrg.xdat.security.services.RoleHolder;
import org.nrg.xdat.security.services.UserManagementServiceI;
import org.nrg.xnat.plugins.template.preferences.TemplatePreferencesBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

import java.util.Map;

import static org.nrg.xdat.security.helpers.AccessLevel.Admin;

@Api(description = "XNAT 1.7 Template Plugin API")
@XapiRestController
@RequestMapping(value = "/template/prefs")
public class TemplatePrefsApi extends AbstractXapiRestController {
    @Autowired
    public TemplatePrefsApi(final UserManagementServiceI userManagementService, final RoleHolder roleHolder, final TemplatePreferencesBean templatePrefs) {
        super(userManagementService, roleHolder);
        _templatePrefs = templatePrefs;
    }

    @ApiOperation(value = "Returns the full map of template preferences.", response = String.class, responseContainer = "Map")
    @ApiResponses({@ApiResponse(code = 200, message = "Site configuration properties successfully retrieved."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 403, message = "Not authorized to set site configuration properties."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(produces = MediaType.APPLICATION_JSON_VALUE, method = RequestMethod.GET, restrictTo = Admin)
    public ResponseEntity<Map<String, Object>> getTemplatePreferences() {
        return new ResponseEntity<>((Map<String, Object>)_templatePrefs, HttpStatus.OK);
    }

    @ApiOperation(value = "Returns the value of the specified template preference.", response = String.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template preference value successfully retrieved."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 403, message = "Not authorized to access template preferences."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(value = "{preference}", produces = MediaType.APPLICATION_JSON_VALUE, method = RequestMethod.GET, restrictTo = Admin)
    public ResponseEntity<String> getPreferenceValue(@ApiParam(value = "The template preference to retrieve.", required = true) @PathVariable final String preference) {
        if (!_templatePrefs.keySet().contains(preference)) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
        return new ResponseEntity<>(_templatePrefs.getValue(preference), HttpStatus.OK);
    }

    @ApiOperation(value = "Updates the value of the specified template preference.", response = Void.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template preference value successfully retrieved."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 403, message = "Not authorized to access template preferences."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(value = "{preference}", consumes = MediaType.APPLICATION_JSON_VALUE, method = RequestMethod.PUT, restrictTo = Admin)
    public ResponseEntity<Void> setPreferenceValue(@ApiParam(value = "The template preference to set.", required = true) @PathVariable final String preference,
                                                   @ApiParam(value = "The template preference to set.", required = true) @RequestBody final String value) {
        if (!_templatePrefs.keySet().contains(preference)) {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
        try {
            _templatePrefs.set(value, preference);
        } catch (InvalidPreferenceName invalidPreferenceName) {
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return new ResponseEntity<>(HttpStatus.OK);
    }

    private final TemplatePreferencesBean _templatePrefs;
}
