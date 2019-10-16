/*
 * xnat-template: org.nrg.xnat.plugins.template.plugin.XnatTemplatePlugin
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.ccdb.plugin;

import org.nrg.framework.annotations.XnatDataModel;
import org.nrg.framework.annotations.XnatPlugin;
import org.nrg.xdat.om.CcdbHotelct;
import org.nrg.xdat.om.CcdbHotelpet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@XnatPlugin(value = "ccdbPlugin", name = "XNAT 1.7 CCDB Plugin", entityPackages = "org.nrg.xnat.plugins.ccdb.entities",
        dataModels = {
                @XnatDataModel(value = CcdbHotelpet.SCHEMA_ELEMENT_NAME,
                        singular = "PET Hotel Session",
                        plural = "PET Hotel Sessions",
                        code = "PET_HTL"),
                @XnatDataModel(value = CcdbHotelct.SCHEMA_ELEMENT_NAME,
                        singular = "CT Hotel Session",
                        plural = "CT Hotel Sessions",
                        code = "CT_HTL")})
@ComponentScan({"org.nrg.xnat.plugins.template.preferences",
        "org.nrg.xnat.plugins.template.repositories",
        "org.nrg.xnat.plugins.template.rest",
        "org.nrg.xnat.plugins.template.services.impl"})
public class XnatCCDBPlugin {
    public XnatCCDBPlugin() {
        _log.info("Creating the XnatCCDBPlugin configuration class");
    }



    @Bean
    public String templatePluginMessage() {
        return "This comes from deep within the template plugin.";
    }

    private static final Logger _log = LoggerFactory.getLogger(XnatCCDBPlugin.class);
}
