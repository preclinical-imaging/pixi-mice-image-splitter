/*
 * xnat-template: org.nrg.xnat.plugins.template.services.impl.HibernateTemplateService
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.template.services.impl;

import org.nrg.framework.orm.hibernate.AbstractHibernateEntityService;
import org.nrg.xnat.plugins.template.entities.Template;
import org.nrg.xnat.plugins.template.repositories.TemplateRepository;
import org.nrg.xnat.plugins.template.services.TemplateService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Manages {@link Template} data objects in Hibernate.
 */
@Service
public class HibernateTemplateService extends AbstractHibernateEntityService<Template, TemplateRepository> implements TemplateService {
    /**
     * {@inheritDoc}
     */
    @Transactional
    @Override
    public Template findByTemplateId(final String templateId) {
        return getDao().findByUniqueProperty("templateId", templateId);
    }
}
