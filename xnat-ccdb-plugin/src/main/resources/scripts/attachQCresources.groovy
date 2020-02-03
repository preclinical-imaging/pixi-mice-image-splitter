package scripts

import org.nrg.xdat.XDAT
import org.nrg.xdat.om.XnatImagescandata
import org.nrg.xdat.om.XnatImagesessiondata
import org.nrg.xdat.om.XnatPetscandata
import org.nrg.xdat.om.XnatResourcecatalog
import org.nrg.xft.security.UserI
import org.nrg.xft.utils.ResourceFile
import org.nrg.xnat.plugins.ccdb.service.XnatService

String projectID = externalId
String sessionID = dataId

out.println "${projectID}"
out.println "${sessionID}"
out.println "${user}"

XnatService xnatService = (XnatService) XDAT.getContextService().getBean( XnatService.class)

XnatImagesessiondata imagesessiondata = XnatImagesessiondata.getXnatExperimentdatasById( sessionID, user, false)
// Why does this return all the resource files?
List<ResourceFile> resourceFiles = imagesessiondata.getFileResources("SNAPSHOTS")

//Optional<File> resource = resourceFiles.stream().filter( f -> f.getF().getName().endsWith("png")).findAny()
    ResourceFile resource = resourceFiles.find{it.getF().getName().endsWith("png")}


String scanID = "1";
XnatImagescandata scandata = XnatImagescandata.getScansByIdORType( scanID, imagesessiondata, user, false)
out.println "${scandata}"
XnatPetscandata petscandata
if( resource != null) {
    File file = resource.getF()
    String catalogName = "SNAPSHOTS"
    String catalogFormat = "PNG"
    String catalogContent = "PNG"
    XnatResourcecatalog resourcecatalog = xnatService.createScanResource(scandata, catalogName, catalogFormat, catalogContent, user)

    String rootPath = catalogName
    boolean preserveDirectories = false
    String format = "PNG"
    String content = "THUMBNAIL"
    try {
        xnatService.insertResource(resourcecatalog, rootPath, file, preserveDirectories, format, content, user)
    } catch( Exception e) {
        e.printStackTrace( out)
    }
}
else {
    out.print "No png in qc resource."
}

