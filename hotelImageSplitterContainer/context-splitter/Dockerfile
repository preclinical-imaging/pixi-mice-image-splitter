FROM python-base:v1

ARG homedir=/home/splitter
ARG inFile=$homedir/inFile
ARG outDir=$homedir/outDir
ARG script=splitter_of_mice.py

RUN mkdir -p $outDir

COPY splitter_of_mice.py $homedir

CMD [ "python", "/home/splitter/splitter_of_mice.py", "/home/splitter/inFile", "/home/splitter/outDir" ]
