/*
 * xnat-template: org.nrg.xnat.plugins.template.plugin.XnatTemplatePlugin
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.ccdb;

import org.nrg.framework.annotations.XnatDataModel;
import org.nrg.framework.annotations.XnatPlugin;
import org.nrg.xdat.om.CcdbHotelct;
import org.nrg.xdat.om.CcdbHotelpet;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk_WU;
import org.nrg.xnat.plugins.ccdb.service.XnatService;
import org.nrg.xnat.services.archive.CatalogService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

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
@ComponentScan({ "org.nrg.xnat.plugins.ccdb.rest", "org.nrg.xnat.plugins.ccdb.service"})
@Import({org.nrg.xnat.configuration.ApplicationConfig.class, org.nrg.containers.config.ContainersConfig.class})
public class XnatCCDBPlugin {

    @Bean
    public XnatService xnatService(CatalogService catalogService) { return new XnatService( catalogService); }

    @Bean
    public FrontDesk frontDesk( XnatService xnatService) { return new FrontDesk_WU( xnatService); }

}
