package org.nrg.xnat.plugins.ccdb.rest.guest;

import org.nrg.xft.security.UserI;

import java.util.List;

public interface FrontDesk {
    List<Guest> getGuests(String hotelSessionLabel, UserI user);
}
