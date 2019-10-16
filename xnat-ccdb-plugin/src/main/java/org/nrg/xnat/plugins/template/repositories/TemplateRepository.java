/*
 * xnat-template: org.nrg.xnat.plugins.template.repositories.TemplateRepository
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.plugins.template.repositories;

import org.nrg.framework.orm.hibernate.AbstractHibernateDAO;
import org.nrg.xnat.plugins.template.entities.Template;
import org.springframework.stereotype.Repository;

@Repository
public class TemplateRepository extends AbstractHibernateDAO<Template> {
}
