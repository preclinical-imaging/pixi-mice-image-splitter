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
import org.nrg.xnat.plugins.ccdb.rest.converter.CcdbZipFileHttpMessageConverter;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk;
import org.nrg.xnat.plugins.ccdb.rest.guest.FrontDesk_WU;
import org.nrg.xnat.plugins.ccdb.service.XnatService;
import org.nrg.xnat.services.archive.CatalogService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.http.converter.HttpMessageConverter;

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
                        code = "CT_HTL")},
        log4jPropertiesFile = "ccdb-log4j.properties")
@ComponentScan({ "org.nrg.xnat.plugins.ccdb.rest", "org.nrg.xnat.plugins.ccdb.service"})
@Import({org.nrg.xnat.configuration.ApplicationConfig.class})
public class XnatCCDBPlugin {
    public XnatCCDBPlugin() {
        _log.info("Creating the XnatCCDBPlugin configuration class");
    }

    @Bean
    public String templatePluginMessage() {
        return "This comes from deep within the template plugin.";
    }

    @Bean
    public XnatService xnatService(CatalogService catalogService) { return new XnatService( catalogService); }

    @Bean
    public FrontDesk frontDesk( XnatService xnatService) { return new FrontDesk_WU( xnatService); }

    private static final Logger _log = LoggerFactory.getLogger("ccdbLogger");
}
