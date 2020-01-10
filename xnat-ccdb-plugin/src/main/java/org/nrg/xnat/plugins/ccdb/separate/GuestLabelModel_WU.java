package org.nrg.xnat.plugins.ccdb.separate;

public class GuestLabelModel_WU implements GuestLabelModel {
    private String scanName;
    private String[] subjectOrderArray;

    public String getScanName() {
        return scanName;
    }

    public void setScanName(String scanName) {
        this.scanName = scanName;
    }

    public String[] getSubjectOrderArray() {
        return subjectOrderArray;
    }

    public void setSubjectOrderArray(String[] subjectOrderArray) {
        this.subjectOrderArray = subjectOrderArray;
    }

    @Override
    public String getLabel(int hotelSize, int hotelPosition) {
        return String.format("%s_%s", scanName, subjectOrderArray[hotelPosition]);
    }
}
