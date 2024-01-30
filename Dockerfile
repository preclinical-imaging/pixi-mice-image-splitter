FROM python:3.11-slim

# Create a non-root user and group
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set the working directory and copy requirements
WORKDIR /usr/src/app
COPY requirements.txt ./

# Install the requirements and set the permissions
RUN pip install --no-cache-dir -r requirements.txt && \
    chown -R appuser:appgroup /usr/src/app && \
    rm requirements.txt

# Copy the source code
COPY splitter_of_mice ./

# Update the PYTHONPATH with the source code
ENV PYTHONPATH=${PYTHONPATH}:/usr/src/app:/usr/src/app/splitter_of_mice
ENV PYTHONUNBUFFERED=1

# Switch to the non-root user
USER appuser

# Set the entrypoint and command
ENTRYPOINT [ "python", "splitter_of_mice/main.py" ]
CMD ["--help"]

# Label is a JSON string for XNAT's container service to parse
LABEL org.nrg.commands="[{\"name\": \"scan-record-splitter-auto\", \"label\": \"scan-record-splitter-auto\", \"description\": \"Split hotel image sessions into single subject image sessions based on a scan record form\", \"version\": \"0.1.0\", \"schema-version\": \"1.0\", \"info-url\": \"\", \"container-name\": \"\", \"type\": \"docker\", \"index\": \"\", \"working-directory\": \"/usr/src/app\", \"command-line\": \"python run.py /input/SCANS /output --log-level DEBUG -u \$XNAT_USER -p \$XNAT_PASS -s \$XNAT_HOST #PROJECT_ID# #SESSION_LABEL#\", \"override-entrypoint\": true, \"mounts\": [{\"name\": \"input-mount\", \"writable\": false, \"path\": \"/input\"}, {\"name\": \"output-mount\", \"writable\": true, \"path\": \"/output\"}], \"environment-variables\": {}, \"ports\": {}, \"inputs\": [{\"name\": \"project_id\", \"label\": null, \"description\": \"XNAT id of the project\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": \"#PROJECT_ID#\", \"sensitive\": null, \"command-line-flag\": \"-r\", \"command-line-separator\": null, \"true-value\": null, \"false-value\": null, \"select-values\": [], \"multiple-delimiter\": null}, {\"name\": \"hotel_session_label\", \"label\": null, \"description\": \"XNAT label of the hotel session\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": \"#SESSION_LABEL#\", \"sensitive\": null, \"command-line-flag\": \"-e\", \"command-line-separator\": null, \"true-value\": null, \"false-value\": null, \"select-values\": [], \"multiple-delimiter\": null}], \"outputs\": [], \"xnat\": [{\"name\": \"scan-record-splitter\", \"label\": \"Scan Record Splitter\", \"description\": \"Split hotel image sessions into single subject image sessions based on scan record inputs\", \"contexts\": [\"pixi:hotelScanRecord\"], \"external-inputs\": [{\"name\": \"scan-record\", \"label\": null, \"description\": \"Hotel scan record input\", \"type\": \"ProjectAsset\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": null, \"provides-files-for-command-mount\": null, \"via-setup-command\": null, \"user-settable\": null, \"load-children\": true}], \"derived-inputs\": [{\"name\": \"hotel-session-label\", \"label\": null, \"description\": \"The hotel session's label\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": \"#SESSION_LABEL#\", \"sensitive\": null, \"provides-value-for-command-input\": \"hotel_session_label\", \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"scan-record\", \"derived-from-xnat-object-property\": \"datatype-string\", \"via-setup-command\": null, \"multiple\": false, \"parser\": \"/XFTItem/session_label[1]\"}, {\"name\": \"project\", \"label\": null, \"description\": \"Input project\", \"type\": \"Project\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": null, \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"scan-record\", \"derived-from-xnat-object-property\": null, \"via-setup-command\": null, \"multiple\": false, \"parser\": null}, {\"name\": \"project-id\", \"label\": null, \"description\": \"XNAT Project ID\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": \"project_id\", \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"project\", \"derived-from-xnat-object-property\": \"id\", \"via-setup-command\": null, \"multiple\": false, \"parser\": null}, {\"name\": \"subject\", \"label\": null, \"description\": \"Subject\", \"type\": \"Subject\", \"matcher\": \"'#SESSION_LABEL#' in @.sessions[*].label\", \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": null, \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"project\", \"derived-from-xnat-object-property\": null, \"via-setup-command\": null, \"multiple\": false, \"parser\": null}, {\"name\": \"session\", \"label\": null, \"description\": \"Session\", \"type\": \"Session\", \"matcher\": \"@.label == '#SESSION_LABEL#'\", \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": null, \"provides-files-for-command-mount\": \"input-mount\", \"user-settable\": null, \"load-children\": false, \"derived-from-wrapper-input\": \"subject\", \"derived-from-xnat-object-property\": null, \"via-setup-command\": null, \"multiple\": false, \"parser\": null}], \"output-handlers\": []}], \"runtime\": \"\", \"ipc-mode\": \"\", \"network\": \"\", \"container-labels\": {}, \"generic-resources\": {}, \"ulimits\": {}}, \
	{\"name\": \"hotel-splitter-auto\", \"label\": \"hotel-splitter-auto\", \"description\": \"Split hotel image sessions into single subject image sessions\", \"version\": \"0.1.0\", \"schema-version\": \"1.0\", \"info-url\": \"\", \"container-name\": \"\", \"type\": \"docker\", \"index\": \"\", \"working-directory\": \"/usr/src/app\", \"command-line\": \"python run.py /input/SCANS /output --log-level DEBUG -u \$XNAT_USER -p \$XNAT_PASS -s \$XNAT_HOST #PROJECT_ID# #SESSION_LABEL#\", \"override-entrypoint\": true, \"mounts\": [{\"name\": \"input-mount\", \"writable\": false, \"path\": \"/input\"}, {\"name\": \"output-mount\", \"writable\": true, \"path\": \"/output\"}], \"environment-variables\": {}, \"ports\": {}, \"inputs\": [{\"name\": \"project_id\", \"label\": null, \"description\": \"XNAT id of the project\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": \"#PROJECT_ID#\", \"sensitive\": null, \"command-line-flag\": \"-r\", \"command-line-separator\": null, \"true-value\": null, \"false-value\": null, \"select-values\": [], \"multiple-delimiter\": null}, {\"name\": \"hotel_session_label\", \"label\": null, \"description\": \"XNAT label of the hotel session\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": \"#SESSION_LABEL#\", \"sensitive\": null, \"command-line-flag\": \"-e\", \"command-line-separator\": null, \"true-value\": null, \"false-value\": null, \"select-values\": [], \"multiple-delimiter\": null}], \"outputs\": [], \"xnat\": [{\"name\": \"hotel-session-splitter\", \"label\": \"Hotel Session Splitter\", \"description\": \"Split hotel image sessions into single subject image sessions\", \"contexts\": [\"xnat:imageSessionData\"], \"external-inputs\": [{\"name\": \"session\", \"label\": null, \"description\": \"Hotel session input\", \"type\": \"Session\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": null, \"provides-files-for-command-mount\": \"input-mount\", \"via-setup-command\": null, \"user-settable\": null, \"load-children\": true}], \"derived-inputs\": [{\"name\": \"project-id\", \"label\": null, \"description\": \"XNAT Project ID\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": \"project_id\", \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"session\", \"derived-from-xnat-object-property\": \"project-id\", \"via-setup-command\": null, \"multiple\": false, \"parser\": null}, {\"name\": \"hotel-session-label\", \"label\": null, \"description\": \"The hotel session's label\", \"type\": \"string\", \"matcher\": null, \"default-value\": null, \"required\": true, \"replacement-key\": null, \"sensitive\": null, \"provides-value-for-command-input\": \"hotel_session_label\", \"provides-files-for-command-mount\": null, \"user-settable\": null, \"load-children\": true, \"derived-from-wrapper-input\": \"session\", \"derived-from-xnat-object-property\": \"label\", \"via-setup-command\": null, \"multiple\": false, \"parser\": null}], \"output-handlers\": []}], \"runtime\": \"\", \"ipc-mode\": \"\", \"network\": \"\", \"container-labels\": {}, \"generic-resources\": {}, \"ulimits\": {}}]"

