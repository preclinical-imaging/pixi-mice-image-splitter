package scripts

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

public String getJSession( String cred) {
    String cmd = "curl -s -k -u ${cred} https://ccdb-dev-maffitt1.nrg.wustl.edu/REST/JSESSION"
    Process p = new ProcessBuilder(["sh", "-c", cmd])
            .redirectErrorStream(true)
            .start()
//    p.outputStream.close()
    String sessionID = p.inputStream.text
    p.waitFor();
    //return p.exitValue()
    return sessionID
}

public int requestCheckin( String projectID, String sessionID, String httpSessionID) {
    String cmd = "curl -s -k -b JSESSIONID=${httpSessionID} https://ccdb-dev-maffitt1.nrg.wustl.edu/xapi/ccdb/projects/${projectID}/experiments/${sessionID}/checkin"
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

String httpSessionID = getJSession( "dmaffitt:vor.viss")
out.println "projectID: ${projectID}"
out.println "sessionID: ${sessionID}"
out.println "httpSessionID: ${httpSessionID}"

int exitCode = requestCheckin( projectID, sessionID, httpSessionID)
if( exitCode != 0)
    out.println "Error: exit code = ${exitCode}"

//closeJSession()