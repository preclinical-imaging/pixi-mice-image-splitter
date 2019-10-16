/*
 * xnat-template: org.nrg.xnat.plugins.template.services.TemplateService
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.template.services;

import org.nrg.framework.orm.hibernate.BaseHibernateService;
import org.nrg.xnat.plugins.template.entities.Template;

public interface TemplateService extends BaseHibernateService<Template> {
    /**
     * Finds the template with the indicated {@link Template#getTemplateId() template ID}.
     *
     * @param templateId The template ID.
     *
     * @return The template with the indicated ID, null if not found.
     */
    Template findByTemplateId(final String templateId);
}
