# Django Shutter

A Cloud Photo Toolkit for Django.

### install 

```
pip install django-shutter
```

### configure

Export the following environment variable to tag images with Google Cloud Vision:

```
GOOGLE_CLOUD_KEY=
```


### requirements

A working django-allauth installation with the flickr provider configured.

### Usage

There are four management commands.

**import_user_photos**

Import user photos from flickr.

**import_user_exif**

Import exif tags from flickr.

**import_user_gpx**

Import user gpx file and write save calculated location data.

**sync_tags**

Write tags obtained from Google Cloud Vision back to flickr.

Images can be tagged with Google Cloud Vision by selecting the photos in
the admin and performing the bulk action "Tag Photos".
