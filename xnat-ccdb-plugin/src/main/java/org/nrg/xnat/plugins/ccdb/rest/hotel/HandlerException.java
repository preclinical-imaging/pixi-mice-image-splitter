package org.nrg.xnat.plugins.ccdb.rest.hotel;

import org.springframework.http.HttpStatus;

/**
 * Extends Exception so handler can return Http status as part of error.
 * Particularly to distinguish between an internal error and an error from bad request info.
 *
 */
public class HandlerException extends Exception {
    final private HttpStatus _httpStatus;

    public HandlerException( String msg, Exception e, HttpStatus status) {
        super( msg, e);
        _httpStatus = status;
    }

    public HandlerException( String msg, HttpStatus status) {
        super(msg);
        _httpStatus = status;
    }

    public HandlerException( String msg, Exception e) {
        this( msg, e, HttpStatus.INTERNAL_SERVER_ERROR);
    }

    public HandlerException( String msg) {
        this(msg, HttpStatus.INTERNAL_SERVER_ERROR);
    }

    public HttpStatus getHttpStatus() {
        return _httpStatus;
    }
}
