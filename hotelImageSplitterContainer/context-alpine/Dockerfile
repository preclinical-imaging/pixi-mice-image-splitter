FROM alpine:3.10

RUN apk --no-cache add wget

RUN apk --no-cache add gcc g++ gfortran musl-dev lapack lapack-dev
RUN apk --no-cache add python3 python3-dev

# RUN apk --no-cache --update-cache add gcc gfortran py2-pip build-base wget freetype-dev libpng-dev openblas-dev
# RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip3 install --upgrade pip
RUN pip3 install nibabel 
RUN pip3 install numpy 
RUN pip3 install scipy

# scikit-image builds Pillow. add Pillow dependencies.
RUN apk --no-cache add \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev
RUN pip3 install scikit-image

CMD ["python3 --version"]

