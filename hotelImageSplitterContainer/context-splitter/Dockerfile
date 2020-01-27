FROM python-base:v1

ARG inFile=/inFile
ARG outDir=/outDir
ARG script=splitter_of_mice.py

RUN mkdir -p $outDir

COPY splitter_of_mice.py $homedir

CMD [ "python", "splitter_of_mice.py", "/inFile", "/outDir" ]
