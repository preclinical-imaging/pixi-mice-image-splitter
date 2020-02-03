import org.nrg.xnat.turbine.utils.ArcSpecManager

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
