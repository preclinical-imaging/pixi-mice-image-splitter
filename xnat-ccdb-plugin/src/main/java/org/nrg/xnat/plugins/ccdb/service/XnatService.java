package org.nrg.xnat.plugins.ccdb.service;

import org.nrg.xdat.om.*;
import org.nrg.xft.XFTItem;
import org.nrg.xft.event.EventMetaI;
import org.nrg.xft.event.EventUtils;
import org.nrg.xft.security.UserI;
import org.nrg.xft.utils.SaveItemHelper;
import org.nrg.xnat.helpers.uri.UriParserUtils;
import org.nrg.xnat.plugins.ccdb.rest.hotel.HandlerException;
import org.nrg.xnat.services.archive.CatalogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.File;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Common things done in xnat.
 */
@Service
public class XnatService {
    private final CatalogService _catalogService;

    @Autowired
    public XnatService(CatalogService catalogService) {
        _catalogService = catalogService;
    }

    /**
     * Get existing subject or create a new one.
     *
     * @param projectdata The project data for the subject
     * @param subjectLabel The subject's label.
     * @param user The user performing this action.
     * @return The subject data for the specified subject.
     * @throws HandlerException
     */
    public XnatSubjectdata getOrCreateSubject(XnatProjectdata projectdata, String subjectLabel, UserI user) throws XnatServiceException {
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
                String msg = "Error creating hotel subject: " + subjectLabel;
                throw new XnatServiceException( msg, e);
            }
        }
        return subjectdata;
    }

    public XnatImagesessiondata getOrCreateImageSession(XnatSubjectdata subjectdata,
                                                        String modality, String sessionLabel,
                                                        UserI user) throws XnatServiceException {
        XnatImagesessiondata imagesessiondata = null;

        List<XnatSubjectassessordata> subjectassessordataList = subjectdata.getExperiments_experiment("");

        List<XnatImagesessiondata> imagesessiondataList = subjectassessordataList.stream()
                .filter( sad -> sad.getLabel().matches( sessionLabel))
                .filter( sad -> sad instanceof XnatImagesessiondata)
                .map( sad -> {return (XnatImagesessiondata) sad;})
                .collect(Collectors.toList());

        if( imagesessiondataList.isEmpty()) {
            imagesessiondata = createImageSession( modality, sessionLabel, subjectdata, user);
        }
        else {
            imagesessiondata = imagesessiondataList.get(0);
        }
        return imagesessiondata;
    }

    public XnatImagesessiondata createImageSession( String modality, String sessionLabel, XnatSubjectdata subjectdata, UserI user) throws XnatServiceException {
        try {
            XnatImagesessiondata imagesessiondata;
            switch( modality) {
                case "PET":
                    imagesessiondata = new XnatPetsessiondata();
                    break;
                case "CT":
                    imagesessiondata = new XnatCtsessiondata();
                    break;
                default:
                    imagesessiondata = new XnatImagesessiondata();
            }
            imagesessiondata.setId( XnatExperimentdata.CreateNewID());
            imagesessiondata.setLabel( sessionLabel);
            imagesessiondata.setModality( modality);

            imagesessiondata.setProject( subjectdata.getProject());
            imagesessiondata.setSubjectId( subjectdata.getId());
            imagesessiondata.setDate( new Date());

            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "create image session.");
            SaveItemHelper.authorizedSave(imagesessiondata.getItem(), user, false, false, false, false, eventMeta);

            return imagesessiondata;
        }
        catch( Exception e) {
            String msg = "Error creating imagesessiondata for subject: " + subjectdata.getLabel();
            throw new XnatServiceException(msg, e);
        }
    }

    public XnatImagescandata createImageScan( String imageSessionID, String modality, String id, String type, UserI user) throws XnatServiceException {
        try {
            XnatImagescandata scandata;
            switch (modality) {
                case "PET":
                    scandata = new XnatPetscandata(user);
                    break;
                case "CT":
                    scandata = new XnatCtscandata( user);
                    break;
                default:
                    scandata = new XnatImagescandata( user);
            }
            scandata.setId( id);
            scandata.setType( type);
            scandata.setImageSessionId( imageSessionID);

            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "create image scan.");
            SaveItemHelper.authorizedSave( scandata.getItem(), user, false, false, false, false, eventMeta);
            return scandata;
        }
        catch( Exception e) {
            String msg = "Error creating image scan data for session: " + imageSessionID;
            throw new XnatServiceException(msg, e);
        }
    }

    public XnatResourcecatalog createScanResource(XnatImagesessiondata imagesessiondata, UserI user) throws XnatServiceException {
        try {
            final XnatResourcecatalog catalog;
            String parentURI = UriParserUtils.getArchiveUri( imagesessiondata);
            String resourceName = "microPET";
            String format = "microPET";
            String content = "microPET";
            catalog = _catalogService.createAndInsertResourceCatalog(user, parentURI, resourceName, "Creating resource catalog \"" + resourceName + "\" for microPET \"", format, content);

            return catalog;
        }
        catch( Exception e) {
            String msg = "Error creating scan resource. ";
            throw new XnatServiceException(msg, e);
        }
    }

    public XnatResourcecatalog insertResources(String parentUri, Collection<File> resources, final boolean preserveDirectories, final String label, final String description, final String format, final String content, UserI user) throws Exception {
        return _catalogService.insertResources( user, parentUri, resources, preserveDirectories, label, description, format, content);
    }

//    public XnatImagescandata createImageScan(String scanLabel, List<ResourceFile> files) throws XnatServiceException {
//        try {
//            XnatImagescandata imagescandata = new XnatImagescandata();
//            XnatCtscandata ctscandata = new XnatCtscandata();
//            imagescandata.setId( "1");
//            imagescandata.addFile( files.get(0));
//            ctscandata.addFile( files.get(0));
//
//
//            EventMetaI eventMeta = EventUtils.DEFAULT_EVENT(user, "create image session.");
//            SaveItemHelper.authorizedSave(imagesessiondata.getItem(), user, false, false, false, false, eventMeta);
//
//            return imagescandata;
//        }
//        catch( Exception e) {
//            String msg = "Error creating imagesessiondata for subject: " + scanLabel;
//            throw new XnatServiceException(msg, e);
//        }
//    }
}
