package org.nrg.xnat.plugins.ccdb.rest.guest;

import org.nrg.xdat.XDAT;
import org.nrg.xdat.om.XnatExperimentdata;
import org.nrg.xdat.om.XnatImagescandata;
import org.nrg.xdat.om.XnatImagesessiondata;
import org.nrg.xdat.om.XnatProjectdata;
import org.nrg.xft.security.UserI;

public class Separator {

    protected XnatProjectdata proj;
    protected XnatImagesessiondata session = null;
    protected XnatImagescandata scan = null;
    protected String scanID = null;

    public void foo( String pID, String experimentID, String scanID) {
        final UserI user = XDAT.getUserDetails();

        if (pID != null) {
            proj = XnatProjectdata.getProjectByIDorAlias(pID, user, false);
        }

        if (experimentID != null) {
            session = (XnatImagesessiondata) XnatExperimentdata.getXnatExperimentdatasById(experimentID, user, false);
            if (session != null && (proj != null && !session.hasProject(proj.getId()))) {
                session = null;
            }

            if (session == null && proj != null) {
                session = (XnatImagesessiondata) XnatExperimentdata.GetExptByProjectIdentifier(proj.getId(), experimentID, user, false);
            }
            final XnatImagescandata scanData = session.getScanById(scanID);


        }
    }

}
