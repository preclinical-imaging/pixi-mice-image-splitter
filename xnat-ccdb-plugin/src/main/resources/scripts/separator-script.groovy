import org.nrg.xdat.om.XnatExperimentdata
import org.nrg.xdat.om.XnatSubjectassessordata
import org.nrg.xdat.om.XnatSubjectdata
import org.nrg.xft.utils.ResourceFile
import org.nrg.xnat.turbine.utils.ArcSpecManager
import org.nrg.xnat.plugins.ccdb.separate.Separator


XnatExperimentdata exptData = XnatExperimentdata.getXnatExperimentdatasById( externalId, userI, false);
List<ResourceFile> fileResources = exptData.getFileResources("microPET");
// don't know why the above returns all file resources

for( ResourceFile f: fileResources) {
    out.println "${f.absolutePath}"
}
if( exptData instanceof XnatSubjectassessordata ) {
    XnatSubjectassessordata subjectassessordata = (XnatSubjectassessordata) exptData
    XnatSubjectdata subjectdata = subjectassessordata.getSubjectData()
//    List fields = subjectdata.getFields_field()
//    for( Object f: fields) {
//        out.println "$f"
//    }
    String subjectOrder = (String) subjectdata.getFieldByName("subjectOrder")
    out.println "subjectOrder: $subjectOrder"
}

def archiveResources = ArcSpecManager.GetInstance().getArchivePathForProject(externalId) + 'resources' + File.separator + 'groovy_proj_folder'

out.println "Writing a test file to ${archiveResources}"


new File(archiveResources, 'testFile.txt').withWriter('utf-8') { writer ->
    writer.writeLine 'Here goes nothing...'
    writer.writeLine "User: $user.login"
    writer.writeLine "srcWorkflowId: $srcWorkflowId"
    writer.writeLine "scriptWorkflowId: $scriptWorkflowId"
    writer.writeLine "dataId: $dataId"
    writer.writeLine "externalId: $externalId"
    writer.writeLine "dataType: $dataType"
    writer.writeLine "workflow: $workflow.wrkWorkflowdataId"
}
