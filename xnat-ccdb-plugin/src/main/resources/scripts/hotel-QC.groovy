package scripts

import org.nrg.xdat.om.XnatImagesessiondata
import org.nrg.xft.utils.ResourceFile

int exec(cmd) {
    println cmd
    def process = new ProcessBuilder([ "sh", "-c", cmd])
//            .directory(new File("/tmp"))
//            .redirectErrorStream(true)
            .start()
//    process.outputStream.close()
    process.inputStream.eachLine {println it}
    process.waitFor();
    return process.exitValue()
}

String getJSession( String cred, String xnatHost) {
    String cmd = "curl -s -k -u ${cred} ${xnatHost}/REST/JSESSION"

    Process p = new ProcessBuilder(["sh", "-c", cmd])
            .redirectErrorStream(true)
            .start()
//    p.outputStream.close()
    String sessionID = p.inputStream.text
    p.waitFor();
    //return p.exitValue()
    return sessionID
}

int createSnapshotResource( String xnatHost, String sessionID, String scanID, String httpSessionID) {
    String cmd = "curl -s -k -b JSESSIONID=${httpSessionID} -X PUT \
       ${xnatHost}/data/experiments/${sessionID}/scans/${scanID}/resources/SNAPSHOTS?format=PNG"
    out.println "${cmd}"
    Process p = new ProcessBuilder(["sh", "-c", cmd])
            .redirectErrorStream(true)
            .start()
//    p.outputStream.close()
    String responce = p.inputStream.text
    p.waitFor();
    return p.exitValue()
}

int putThumbnail( String xnatHost, String sessionID, String scanID, File file, String httpSessionID) {
    String cmd = "curl -s -k -b JSESSIONID=${httpSessionID} -X PUT\
    --upload-file ${file.absolutePath} \
    \"${xnatHost}/data/experiments/${sessionID}/scans/${scanID}/resources/SNAPSHOTS/files/thumb.png?format=PNG&content=THUMBNAIL&inbody=true\""
    out.println "${cmd}"

    Process p = new ProcessBuilder(["sh", "-c", cmd])
            .redirectErrorStream(true)
            .start()
//    p.outputStream.close()
    String responce = p.inputStream.text
    p.waitFor();
    return p.exitValue()
}

int putOriginal( String xnatHost, String sessionID, String scanID, File file, String httpSessionID) {
    String cmd = "curl -s -k -b JSESSIONID=${httpSessionID} -X PUT\
    --upload-file ${file.absolutePath} \
    \"${xnatHost}/data/experiments/${sessionID}/scans/${scanID}/resources/SNAPSHOTS/files/orig.png?format=PNG&content=ORIGINAL&inbody=true\""
    out.println "${cmd}"

    Process p = new ProcessBuilder(["sh", "-c", cmd])
            .redirectErrorStream(true)
            .start()
//    p.outputStream.close()
    String responce = p.inputStream.text
    p.waitFor();
    return p.exitValue()
}


String projectID = externalId
String sessionID = dataId
String xnatHost = "https://ccdb-dev-maffitt1.nrg.wustl.edu"
String scanID = "1"

String httpSessionID = getJSession( "ccdb-svc:u123gbJx1@9O", xnatHost)
out.println "projectID: ${projectID}"
out.println "sessionID: ${sessionID}"
out.println "httpSessionID: ${httpSessionID}"

XnatImagesessiondata imagesessiondata = XnatImagesessiondata.getXnatExperimentdatasById( sessionID, user, false)
// Why does this return all the resource files?
List<ResourceFile> resourceFiles = imagesessiondata.getFileResources("SNAPSHOTS")

//Optional<File> resource = resourceFiles.stream().filter( f -> f.getF().getName().endsWith("png")).findAny()
ResourceFile resource = resourceFiles.find{it.getF().getName().endsWith("png")}
File pngFile = resource.getF()

out.println "pngFile: ${pngFile}"

int exitCode = createSnapshotResource( xnatHost, sessionID, scanID, httpSessionID)
if( exitCode != 0)
    out.println "Error: exit code = ${exitCode}"

exitCode = putThumbnail( xnatHost, sessionID, scanID, pngFile, httpSessionID)
if( exitCode != 0)
    out.println "Error: exit code = ${exitCode}"

exitCode = putOriginal( xnatHost, sessionID, scanID, pngFile, httpSessionID)
if( exitCode != 0)
    out.println "Error: exit code = ${exitCode}"

//closeJSession()