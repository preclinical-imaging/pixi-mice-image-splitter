package org.nrg.xnat.plugins.ccdb.rest.guest;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class GuestPositionLabelModel_WU implements GuestPositionLabelModel {
    private final List<String> guest1PositionLabelList = Arrays.asList("_ctr");
    private final List<String> guest2PositionLabelList = Arrays.asList("_l", "_r");
    private final List<String> guest4PositionLabelList = Arrays.asList("_lt", "_rt", "_lb", "_rb");
    private final Map<Integer, List<String>> guestPositionLabelMap = Stream.of(new Object[][] {
            { 1, guest1PositionLabelList },
            { 2, guest2PositionLabelList },
            { 4, guest4PositionLabelList }
    }).collect(Collectors.toMap(data -> (Integer) data[0], data -> (List<String>) data[1]));

    @Override
    public String getLabel( int hotelSize, int hotelPosition) {
        return guestPositionLabelMap.get( hotelSize).get( hotelPosition);
    }
}
