package org.nrg.xnat.plugins.ccdb.rest.converter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;

import java.util.List;

@EnableWebMvc
@Configuration
@ComponentScan({ "org.nrg.xnat.plugins.ccdb.rest.converter" })
public class CCDBWebConfig extends WebMvcConfigurerAdapter {
    private static final Logger _log = LoggerFactory.getLogger( "ccdbLogger");

    @Override
    public void configureMessageConverters( List<HttpMessageConverter<?>> converters) {

        HttpMessageConverter converter = zipFileHttpMessageConverter();
        converters.add( converter);
        _log.debug( "Adding httpMessageConverter: {}", converter);
    }

    public HttpMessageConverter<?> zipFileHttpMessageConverter() {
        return new CcdbZipFileHttpMessageConverter();
    }
}