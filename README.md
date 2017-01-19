# AWS S3 Deploy

Wercker step to deploy the contents of a directory to an S3 Bucket.
Automatically attaches the appropriate headers for Content Type and Content
Encoding, and makes the file publicly readable.

## Notes

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119.

## Sample Usage

    deploy:
      box: python:latest
      steps:
        - bashaus/aws-s3-deploy:
          target-bucket: $DEPLOY_TARGET_BUCKET
          configuration-file: $WERCKER_ROOT/aws-s3-deploy.yml

Along with the available properties, ensure that you configure the
`aws-s3-deploy.yml` file.

&nbsp;

## Step Properties

### target-bucket (required)

Name of the bucket where files will be received.

* Since: `0.0.1`
* Property is `Required`
* Recommended location: `Pipeline`
* `Validation` rules:
  * Must only be the bucket name

&nbsp;

### configuration-file

The location of the configuration file which contains information about jobs
and mime type configuration.

* Since: `0.0.1`
* Property is `Optional`
* Default value is: `$WERCKER_ROOT/aws-s3-deploy.yml`
* Recommended location: `Inline`
* `Validation` rules:
  * Must be a valid YAML file

&nbsp;

### aws-access-key-id

The `AWS_ACCESS_KEY_ID` to use in this deployment.

* Since: `0.0.1`
* Property is `Required`, but is `Optional` if `AWS_ACCESS_KEY_ID` is set
* Default value is: `AWS_ACCESS_KEY_ID`
* Recommended location: `Application`

&nbsp;

### aws-secret-access-key

The `AWS_SECRET_ACCESS_KEY` to use in this deployment.

* Since: `0.0.1`
* Property is `Required`, but is `Optional` if `AWS_SECRET_ACCESS_KEY` is set
* Default value is: `AWS_SECRET_ACCESS_KEY`
* Recommended location: `Application`
* `Validation` rules:
  * Must be stored as a protected environment variable

&nbsp;

## Managing MIME types

In the root directory of this step is a `mime.types` file which contains
additional MIME type directives for file extensions. This makes it easier
to manage MIME types across multiple projects which are not included in the
system default.

If you have your own mime types you want to add on a per-project basis, you can
create a `mime.types` file in the root of your repository
(`$WERCKER_ROOT/mime.types`) using the standard `mime.types` format.

A complete list of MIME types and file extensions can be found in the
[Apache `mime.types` file](https://svn.apache.org/repos/asf/httpd/httpd/trunk/docs/conf/mime.types)

&nbsp;

## Step configuration

You can configure this step to deploy assets to different folders and assign
specific metadata for different MIME types.

By default, the configuration file is located at
`$WERCKER_ROOT/aws-s3-deploy.yml`, but you can change this by
assigning the `configuration-file` property in the YAML step.

This configuration would be included in the step, but Wercker does not allow
objects or arrays.

&nbsp;

### version

Reserved for future use. This should be `version: "1"`, as there is only one
current version of the manifest file. The version number must be a string.

&nbsp;

### jobs

An array of jobs to be uploaded. This allows you to upload multiple files to
the server without having to run the step multiple times. Below is an example
of a job:

```yaml
version: "1"
jobs:
  - name: "upload files"
    src: ./source/directory/
    dest: ./bucket/key/prefix/
    match: |
      **/*
      !**/.DS_Store
```

#### name

Each job should have a unique name. If the name is defined, it is displayed
before the job is run.

* Since: `0.0.1`
* Property is `Optional`

#### src

The source folder (`src`) to copy the files from - used as a base directory for
all files in the job.

* Since: `0.0.1`
* Property is `Optional`
* Default value is: `$WERCKER_ROOT`
* Validation rules:
 * Must be a valid local folder

#### dest

The destination folder to copy the files to. All keys will be prefixed with
this path.

* Since: `0.0.1`
* Property is `Optional`
* Default value is: `/`
* Validation rules:
 * Must be a valid path for S3

#### match

The `match` directives allow you to list glob patterns which will be matched to
find files. This also includes brace expansion in searching, so you can look
for CSS files and their GZIP counters by searching for: `**/*.css{,.gzip}`.

Patterns are matched in the order in which they are specified in the list.

The value of `match` is a string and should be represented in block scalar
style. This is because values like `*` and `/` are not interpreted well as
literal strings by YAML parsers.

**N.B. Python does not follow symlinks** when using the `**` operator as this
is considered a performance hit. If you're using symlinks like this, you will
need to know where the symlinks are and use `*` instead.

* Since: `0.0.1`
* Property is `Optional`
* Default value is: `**/*` and `!**/.DS_Store`
* Validation rules:
 * Must be valid glob patterns
 * May contain brace expansion
 * Must reference symlinks explicitly without using the `**` operator
 * Must be a string
 * May be a multiline string

&nbsp;

### mime-types

Currently, you can only define the `CacheControl` property on files which match
a particular mime type.

#### CacheControl

The `CacheControl` property can be either be a `string` or an `object`. This is
to make it easier to manage the values which are configured in the file.

When using the property as a string, simply set the value directly as you would
expect it to be returned by S3.

```yaml
version: "1"
mime-types:
  text/css:
    CacheControl: max-age="3600"
```

When using the property as an object, there are pre-defined keys that you can
use to make it easier to manage. Below is an example of how you can make a CSS
file expire after 15 minutes:

```yaml
version: "1"
mime-types:
  text/css:
    CacheControl:
      max-age: PT15M
```

As you can see, time values can be represented as an ISO 8601 duration. This
will automatically be resolved to the appropriate format in seconds.

This subset is a full list of available properties which you can use in
combination:

```yaml
CacheControl:
  must-revalidate: true
  no-cache: true
  no-store: true
  no-transform: true
  public: true
  private: true
  proxy-revalidate: true

  # Only use one of the following
  max-age: PT15M
  max-age: 900

  # Only use one of the following
  s-maxage: PT15M
  s-maxage: 900
```

You can use any of the properties in combination:

```yaml
# Yields:
# CacheControl: public, no-cache
CacheControl:
  public: true
  no-cache: true
```

Also see:

* [Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
  from MDN web docs
* [ISO 8601 - Durations](https://en.wikipedia.org/wiki/ISO_8601#Durations)
  from Wikipedia

&nbsp;
