package org.nrg.xnat.plugins.ccdb.rest.guest;

public class GuestSessionLabelModel_WU implements GuestSessionLabelModel{
    private String modality;
    private String hotelSubjectName;
    private String[] subjectOrderArray;

    public String getLabel(int hotelSize, int hotelPosition) {
        String format = "%s_%s_%s";
        String label;
        switch (modality) {
            case "PT":
            case "PET":
                label = String.format( format, hotelSubjectName, subjectOrderArray[hotelPosition], "em");
                break;
            case "CT":
                label = String.format( format, hotelSubjectName, subjectOrderArray[hotelPosition], "ct");
                break;
            default:
                label = "unknown";
        }
        return label;
    }

    public String getModality() {
        return modality;
    }

    public void setModality(String modality) {
        this.modality = modality;
    }

    public void setHotelSubjectName(String hotelSubjectName) {
        this.hotelSubjectName = hotelSubjectName;
    }

    public void setSubjectOrderArray(String[] subjectOrderArray) {
        this.subjectOrderArray = subjectOrderArray;
    }
}
