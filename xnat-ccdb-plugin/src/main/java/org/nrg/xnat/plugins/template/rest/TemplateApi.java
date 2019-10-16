/*
 * xnat-template: org.nrg.xnat.plugins.template.rest.TemplateApi
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.template.rest;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import org.nrg.framework.annotations.XapiRestController;
import org.nrg.xapi.authorization.GuestUserAccessXapiAuthorization;
import org.nrg.xapi.rest.AbstractXapiRestController;
import org.nrg.xapi.rest.AuthDelegate;
import org.nrg.xapi.rest.XapiRequestMapping;
import org.nrg.xdat.security.services.RoleHolder;
import org.nrg.xdat.security.services.UserManagementServiceI;
import org.nrg.xnat.plugins.template.entities.Template;
import org.nrg.xnat.plugins.template.services.TemplateService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

import java.util.List;

import static org.nrg.xdat.security.helpers.AccessLevel.Authorizer;

@Api(description = "XNAT 1.7 Template Plugin API")
@XapiRestController
@RequestMapping(value = "/template/entities")
public class TemplateApi extends AbstractXapiRestController {
    @Autowired
    protected TemplateApi(final UserManagementServiceI userManagementService, final RoleHolder roleHolder, final TemplateService templateService) {
        super(userManagementService, roleHolder);
        _templateService = templateService;
    }

    @ApiOperation(value = "Returns a list of all templates.", response = Template.class, responseContainer = "List")
    @ApiResponses({@ApiResponse(code = 200, message = "Templates successfully retrieved."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(produces = {MediaType.APPLICATION_JSON_VALUE}, method = RequestMethod.GET, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<List<Template>> getEntities() {
        return new ResponseEntity<>(_templateService.getAll(), HttpStatus.OK);
    }

    @ApiOperation(value = "Creates a new template.", response = Template.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template successfully created."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(produces = {MediaType.APPLICATION_JSON_VALUE}, method = RequestMethod.POST, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<Template> createEntity(@RequestBody final Template entity) {
        final Template created = _templateService.create(entity);
        return new ResponseEntity<>(created, HttpStatus.OK);
    }

    @ApiOperation(value = "Retrieves the indicated template.",
                  notes = "Based on the template ID, not the primary key ID.",
                  response = Template.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template successfully retrieved."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(value = "{id}", produces = {MediaType.APPLICATION_JSON_VALUE}, method = RequestMethod.GET, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<Template> getEntity(@PathVariable final String id) {
        return new ResponseEntity<>(_templateService.findByTemplateId(id), HttpStatus.OK);
    }

    @ApiOperation(value = "Updates the indicated template.",
                  notes = "Based on primary key ID, not subject or record ID.",
                  response = Void.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template successfully updated."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(value = "{id}", produces = {MediaType.APPLICATION_JSON_VALUE}, method = RequestMethod.PUT, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<Void> updateEntity(@PathVariable final Long id, @RequestBody final Template entity) {
        final Template existing = _templateService.retrieve(id);
        existing.setTemplateId(entity.getTemplateId());
        _templateService.update(existing);
        return new ResponseEntity<>(HttpStatus.OK);
    }

    @ApiOperation(value = "Deletes the indicated template.",
                  notes = "Based on primary key ID, not subject or record ID.",
                  response = Void.class)
    @ApiResponses({@ApiResponse(code = 200, message = "Template successfully deleted."),
                   @ApiResponse(code = 401, message = "Must be authenticated to access the XNAT REST API."),
                   @ApiResponse(code = 500, message = "Unexpected error")})
    @XapiRequestMapping(value = "{id}", produces = {MediaType.APPLICATION_JSON_VALUE}, method = RequestMethod.DELETE, restrictTo = Authorizer)
    @AuthDelegate(GuestUserAccessXapiAuthorization.class)
    public ResponseEntity<Void> deleteEntity(@PathVariable final Long id) {
        final Template existing = _templateService.retrieve(id);
        _templateService.delete(existing);
        return new ResponseEntity<>(HttpStatus.OK);
    }

    private final TemplateService         _templateService;
}
