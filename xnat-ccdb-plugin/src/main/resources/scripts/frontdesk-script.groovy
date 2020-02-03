package scripts

import org.nrg.xft.security.UserI

try {

    String projectID = externalId
    String hotelSessionID = dataId

    def connection = new URL( "https://localhost/" +
            URLEncoder.encode(
                    "/data/xapi/ccdb/projects/${projectID}/checkin/${hotelSessionID}",
                    'UTF-8' ) )
            .openConnection() as HttpURLConnection

    // set some headers
    connection.setRequestProperty( 'User-Agent', 'XNAT' )
    connection.setRequestProperty( 'Accept', 'text/plain' )

    // get the response code - automatically sends the request
    int responseCode = connection.getResponseCode()
    println connection.responseCode + ": " + connection.inputStream.text

} catch( Exception e) {
    out.println "Exception: ${e}"
    out.println "Exception message: ${e.message}"
    e.printStackTrace(out)
}
