import yaml
import logging
import pydash as _
import os
import mimetypes
from pathlib import *
from multiprocessing.dummy import Pool as ThreadPool
import isodate
import boto3
import botocore
from braceexpand import braceexpand
from sys import exit

# Configuration

def _config_file(filename):
    try:
        with open(filename, "r") as stream:
            return yaml.load(stream)
    except yaml.YAMLError as exc:
        log.error("%s was not a valid YAML file", filename)
        exit(2)
    except:
        log.info("%s could not be opened, ignoring", filename)

    return {}



# YAML Parsers

def _parse_cache_control(directive):
    response = []

    # If the directive is a string, then return itself
    # CacheControl: max-age=3600
    if isinstance(directive, str):
        return directive

    # The following conditions assume that the directive is an object
    if "must-revalidate" in directive:
        if directive["must-revalidate"] is True:
            response.append("must-revalidate")

    if "no-cache" in directive:
        if directive["no-cache"] is True:
            response.append("no-cache")

    if "no-store" in directive:
        if directive["no-store"] is True:
            response.append("no-store")

    if "no-transform" in directive:
        if directive["no-transform"] is True:
            response.append("no-transform")

    if "public" in directive:
        if directive["public"] is True:
            response.append("public")

    if "private" in directive:
        if directive["private"] is True:
            response.append("private")

    if "proxy-revalidate" in directive:
        if directive["proxy-revalidate"] is True:
            response.append("proxy-revalidate")

    if "max-age" in directive:
        response.append('max-age="%s"' % (
            _parse_date_directive_to_seconds(directive["max-age"])
        ))

    if "s-maxage" in directive:
        response.append('s-maxage="%s"' % (
            _parse_date_directive_to_seconds(directive["s-maxage"])
        ))

    return ", ".join(response)


def _parse_date_directive_to_seconds(directive):
    # Digit directives are in seconds
    if directive.isdigit():
        return directive

    # If the directive is a string
    if isinstance(directive, str):
        try:
            date = isodate.parse_duration(directive)
            return (date.days * (60 * 60 * 24)) + date.seconds
        except Exception as e:
            log.exception(e)

    print("Could not parse directive as date: " + directive)


def _parse_mime_type_to_content_type(mime_type):
    if not isinstance(mime_type, str):
        return None
    elif mime_type.startswith("text/"):
        return "%s; charset=UTF-8" % (mime_type)
    else:
        return mime_type



# Local files

def job_files(job):
    directory_src = Path(job["src"]).resolve()
    match_globs = []
    match_files = set([])

    # Read include/exclude from the configuration
    if "match" in job:
        list(map(
            lambda x: match_globs.extend(list(braceexpand(x))),
            job["match"].splitlines()
        ))

    # If there is no inclusion, include everything
    if not match_globs:
        match_globs.append("**/*")
        match_globs.append("!**/.DS_Store")

    # Find files
    for i in match_globs:
        if i.startswith("!"):
            match_files -= set(directory_src.glob(i[1:])) # remove
        else:
            match_files |= set(directory_src.glob(i)) # append

    return match_files



# Upload

def upload_file(local_filepath, destination_key):
    # Identify MIME type and encoding
    content_mimetype, content_encoding = mimetypes.guess_type(
        str(local_filepath)
    )

    # Extra Args for S3 file
    file_settings = {}

    if content_mimetype in config["mime-types"]:
        file_settings = config["mime-types"][content_mimetype]

    # Default headers
    extra_args = { "ACL": "public-read" }

    content_type = _parse_mime_type_to_content_type(content_mimetype)
    if not content_type is None:
        extra_args["ContentType"] = content_type

    if "CacheControl" in file_settings:
        extra_args["CacheControl"] = _parse_cache_control(file_settings["CacheControl"])

    # If the item has been encoded
    if not content_encoding is None:
        extra_args["ContentEncoding"] = content_encoding

    S3Bucket.upload_file(
        str(local_filepath),
        destination_key,
        extra_args
    )



def upload_job(job):
    if "name" in job:
        log.info("Starting job: %s", job["name"])
    else:
        log.info("Starting job")

    if not "src" in job:
        job["src"] = os.environ["WERCKER_ROOT"]

    if not "dest" in job:
        job["dest"] = ""

    files = job_files(job)

    def _threadsafe_upload_file(local_filepath):
        # Only upload files
        if not local_filepath.is_file():
            return True

        local_filename = local_filepath.relative_to(Path(job["src"]).resolve())
        destination_key = os.path.join(job["dest"], str(local_filename))

        attempts = 5
        for attempt in range(1, attempts):
            try:
                upload_file(local_filepath, destination_key)
                log.debug(
                    "%s => %s (uploaded; attempts: %s)",
                    local_filename,
                    destination_key,
                    attempt
                )

                return True

            except Exception as e:
                log.debug(
                    "%s => %s (failed; attempt: %s)",
                    local_filename,
                    destination_key,
                    attempt
                )
                log.debug(e)

        log.exception(
            "%s => %s (aborted; attempts: %s)",
            local_filename,
            destination_key,
            attempt
        )
        return False

    pool = ThreadPool(10)
    results = pool.map(_threadsafe_upload_file, files)
    pool.close()
    pool.join()

    return all(results)



def upload_jobs():
    if not "jobs" in config:
        log.error("Could not find jobs in yaml configuration")
        raise

    pool = ThreadPool(1)
    results = pool.map(upload_job, config["jobs"])
    pool.close()
    pool.join()

    return all(results)



# Init

if __name__ == "__main__":

    # Setup logging
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    logging.getLogger("boto3").propagate = False
    logging.getLogger("botocore").propagate = False
    logging.getLogger("s3transfer").propagate = False
    log = logging.getLogger(os.environ["WERCKER_STEP_NAME"])

    # Establish connection to Amazon Web Services
    AWSSession = boto3.Session(
        aws_access_key_id=os.environ["WERCKER_AWS_S3_DEPLOY_AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["WERCKER_AWS_S3_DEPLOY_AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ["WERCKER_AWS_S3_DEPLOY_AWS_REGION"],
    )

    # Establish connection to S3
    S3Resource = AWSSession.resource("s3")
    S3Bucket = S3Resource.Bucket(os.environ["WERCKER_AWS_S3_DEPLOY_TARGET_BUCKET"])

    # Setup MIME types
    mimetypes.init([
        os.environ["WERCKER_STEP_ROOT"] + "/mime.types",
        os.environ["WERCKER_ROOT"] + "/mime.types"
    ])

    mimetypes.encodings_map[".gzip"] = "gzip"

    # Compile the configuration for the application
    # pydash's _defaults_deep orders from highest to lowest precedence
    config = _.defaults_deep(
        # Project configuration
        _config_file(os.environ["WERCKER_AWS_S3_DEPLOY_CONFIGURATION_FILE"]),

        # Global configuration
        _config_file(os.path.join(
            os.environ["WERCKER_STEP_ROOT"],
            "aws-s3-deploy.yml"
        )),

        # Placeholders
        { "version": "1", "mime-types": {} }
    )

    # Exit with 0 status on success
    # Exit with 1 status on failure
    exit(0 if upload_jobs() else 1)
