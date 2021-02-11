# CCDB XNAT-plugin #

This is the CCDB XNAT-plugin source code repository.

# Description #

This code contains or generates multiple components that work together to implement the CCDB workflow of uploading 
"hotel imaging sessions" and breaking them into individual subjects and session data. 

## Data Types ##

This plugin adds the following data types:
1. hotelPET
1. hotelCT

## Code ##

The following image summarizes the workflow as of 2020-02-03. Items on left depict steps in the workflow while the right side illustrates each step's impact on the XNAT data model.

![Overview](overview.jpg)

1. Upload zip to REST endpoint. Content is a single file in the body, content type is custom MIME type "application/zip".
This was done to get around XNAT's inability to modify Spring parameters to set a larger max file upload size. This is preventing the normal upload of large files through multi-part file upload.
1. Run hotel-splitter container on session. This can be done manually through the interface or via a REST endpoint.
1. Run hotel-QC script on hotel session. This can be done in the UI via an automation script, or via a REST call. 
Ideally, this would
be done as part of the hotel-splitter container command. However, Container Service currently has several limitations that
made it necessary to break this out separately. The resource catalog entries for the snaphot images must have content = 'THUMBNAIL' and 'ORIGINAL'. Container Service does not support setting attributes on resource files. This is currently implemented as an automation script that uses the XNAT REST Api to create the SNAPSHOT resources. Ideally, this script, with it's native access to XNAT code would not use REST.
1. Run the FrontDesk container on hotel sessions. This can be done in the UI or by calling the REST endpoint directly.

# To Do #

There currently is not a mechanism to run the entire workflow from a single interaction. XNAT currently lacks workflow management that could allow the coordination of multiple steps like those above.  Code needs to be written to do this.

# Build #

```
./gradlew clean fatJar
```

# Dependencies #

1. Container Service plugin.
1. Hotel-Splitter container.

# Installation #

1. This is a standard XNAT plugin installed by copying the jar file to the XNAT user's plugins directory.
   Installing the plugin will cause the REST endpoints to automatically be created.  See the Swagger page: ccdb-api for details about these endpoints.
1. Container Service plugin
1. Hotel-Splitter Container
    1. The code to build and configure this container is in hotelImageSplitterContainer folder of this repo. Follow the instruction there.
1. Hotel-QC Automation Script
    1. This script is at scripts/attachQCresources.groovy.
    1. Administer -> Automation -> Scripts
    1. Select a language = groovy, then click "Add Script".
    1. Script Editor content:
    scriptID = frontDesk
    scriptLabel = frontDesk
    text box = content of frontdesk_curl.groovy.
    1. edit script context to have credentials of user with read/write permission in the project.
    1. Browse to a project.
    1. Manage -> "Event Handlers"
    1. Click "Add Event Handlers"
    1. Pop-up content:
    Event type = ScriptLaunchEventRequest
    Event ID = Custom Value, split_qc
    Script = hotel_split_qc
    1. Click Save
    1. Click "configure uploader"
    1. Pop-up content:
    Usage = "Do not use uploader"
    Output type = Text
    Upload window options = "Show close window on submit option"
    Unselect "applicable across all contexts"
    Remove all entries except "xnat:imageSessionData"
    1. Click "Save Configuration"
    1. Browse to session in project
    1. Click "Run automation script"
    1. You should be able to select "split_qq" under "Script to Run".
    
1. FrontDesk Automation Script
    1. FrontDesk functionality is provided at a REST endpoint that can be launched directly from the Swagger page.
    1. The FrontDesk can also be launched from an automation script on a session by following the script-installation instruction above.
