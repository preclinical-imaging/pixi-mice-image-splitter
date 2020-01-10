import org.nrg.xnat.plugins.ccdb.separate.FrontDesk
import org.nrg.xnat.plugins.ccdb.separate.FrontDesk_WU
import org.nrg.xnat.plugins.ccdb.separate.Guest
import org.nrg.xnat.plugins.ccdb.service.XnatService

try {
    out.println "${externalId}"
    out.println "${dataId}"

//    String hotelSessionID = dataId
    FrontDesk frontDesk = new FrontDesk_WU()
    out.println "xnatService: ${frontDesk.xnatService}"
//    List<Guest> guestList = frontDesk.getGuests(hotelSessionID, user)

//    for (Guest g : guestList) {
//        out.println "${g.label}"
//        g.sessions.each{ sess ->
//            println "${sess}"
//            println "label: ${sess.label}"
//            println "resource files:"
//            sess.resourceFiles.each { rf ->
//                println "${rf.absolutePath}"
//            }
//        }
//    }

//    XnatService service = frontDesk.xnatService
//    XnatResourcecatalog catalog = service.createScanResource( user)
//    out.println "catalog: ${catalog}"

} catch( Exception e) {
    out.println "Exception: ${e}"
    out.println "Exception message: ${e.message}"
    e.printStackTrace(out)
}
