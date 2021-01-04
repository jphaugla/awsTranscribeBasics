# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with the Amazon Transcribe API to
transcribe an audio file to a text file. Also shows how to define a custom vocabulary
to improve the accuracy of the transcription.

This example uses a public domain audio file downloaded from Wikipedia and converted
from .ogg to .mp3 format. The file contains a reading of the poem Jabberwocky by
Lewis Carroll. The original audio source file can be found here:
    https://en.wikisource.org/wiki/File:Jabberwocky.ogg
"""
import json
import logging
import sys
import time
import boto3
from botocore.exceptions import ClientError
import requests
import os
from pathlib import Path
sys.path.append('../..')
from demo_tools.custom_waiter import CustomWaiter, WaitState

logger = logging.getLogger(__name__)


class TranscribeCompleteWaiter(CustomWaiter):
    """
    Waits for the transcription to complete.
    """
    def __init__(self, client):
        super().__init__(
            'TranscribeComplete', 'GetTranscriptionJob',
            'TranscriptionJob.TranscriptionJobStatus',
            {'COMPLETED': WaitState.SUCCESS, 'FAILED': WaitState.FAILURE},
            client)

    def wait(self, job_name):
        self._wait(TranscriptionJobName=job_name)


class VocabularyReadyWaiter(CustomWaiter):
    """
    Waits for the custom vocabulary to be ready for use.
    """
    def __init__(self, client):
        super().__init__(
            'VocabularyReady', 'GetVocabulary', 'VocabularyState',
            {'READY': WaitState.SUCCESS}, client)

    def wait(self, vocabulary_name):
        self._wait(VocabularyName=vocabulary_name)


def start_job(
        job_name, media_uri, media_format, language_code, transcribe_client,
        vocabulary_name=None):
    """
    Starts a transcription job. This function returns as soon as the job is started.
    To get the current status of the job, call get_transcription_job. The job is
    successfully completed when the job status is 'COMPLETED'.

    :param job_name: The name of the transcription job. This must be unique for
                     your AWS account.
    :param media_uri: The URI where the audio file is stored. This is typically
                      in an Amazon S3 bucket.
    :param media_format: The format of the audio file. For example, mp3 or wav.
    :param language_code: The language code of the audio file.
                          For example, en-US or ja-JP
    :param transcribe_client: The Boto3 Transcribe client.
    :param vocabulary_name: The name of a custom vocabulary to use when transcribing
                            the audio file.
    :return: Data about the job.
    """
    try:
        job_args = {
            'TranscriptionJobName': job_name,
            'Media': {'MediaFileUri': media_uri},
            'MediaFormat': media_format,
            'Settings': {'MaxSpeakerLabels': 5, 'ShowSpeakerLabels': True},
            'LanguageCode': language_code}
        if vocabulary_name is not None:
            job_args['Settings'] = {'VocabularyName': vocabulary_name}
        response = transcribe_client.start_transcription_job(**job_args)
        job = response['TranscriptionJob']
        logger.info("Started transcription job %s.", job_name)
    except ClientError:
        logger.exception("Couldn't start transcription job %s.", job_name)
        raise
    else:
        return job


def list_jobs(job_filter, transcribe_client):
    """
    Lists summaries of the transcription jobs for the current AWS account.

    :param job_filter: The list of returned jobs must contain this string in their
                       names.
    :param transcribe_client: The Boto3 Transcribe client.
    :return: The list of retrieved transcription job summaries.
    """
    try:
        response = transcribe_client.list_transcription_jobs(
            JobNameContains=job_filter)
        jobs = response['TranscriptionJobSummaries']
        next_token = response.get('NextToken')
        while next_token is not None:
            response = transcribe_client.list_transcription_jobs(
                JobNameContains=job_filter, NextToken=next_token)
            jobs += response['TranscriptionJobSummaries']
            next_token = response.get('NextToken')
        logger.info("Got %s jobs with filter %s.", len(jobs), job_filter)
    except ClientError:
        logger.exception("Couldn't get jobs with filter %s.", job_filter)
        raise
    else:
        return jobs


def get_job(job_name, transcribe_client):
    """
    Gets details about a transcription job.

    :param job_name: The name of the job to retrieve.
    :param transcribe_client: The Boto3 Transcribe client.
    :return: The retrieved transcription job.
    """
    try:
        response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name)
        job = response['TranscriptionJob']
        logger.info("Got job %s.", job['TranscriptionJobName'])
    except ClientError:
        logger.exception("Couldn't get job %s.", job_name)
        raise
    else:
        return job


def delete_job(job_name, transcribe_client):
    """
    Deletes a transcription job. This also deletes the transcript associated with
    the job.

    :param job_name: The name of the job to delete.
    :param transcribe_client: The Boto3 Transcribe client.
    """
    try:
        transcribe_client.delete_transcription_job(
            TranscriptionJobName=job_name)
        logger.info("Deleted job %s.", job_name)
    except ClientError:
        logger.exception("Couldn't delete job %s.", job_name)
        raise


def create_vocabulary(
        vocabulary_name, language_code, transcribe_client,
        phrases=None, table_uri=None):
    """
    Creates a custom vocabulary that can be used to improve the accuracy of
    transcription jobs. This function returns as soon as the vocabulary processing
    is started. Call get_vocabulary to get the current status of the vocabulary.
    The vocabulary is ready to use when its status is 'READY'.

    :param vocabulary_name: The name of the custom vocabulary.
    :param language_code: The language code of the vocabulary.
                          For example, en-US or nl-NL.
    :param transcribe_client: The Boto3 Transcribe client.
    :param phrases: A list of comma-separated phrases to include in the vocabulary.
    :param table_uri: A table of phrases and pronunciation hints to include in the
                      vocabulary.
    :return: Information about the newly created vocabulary.
    """
    try:
        vocab_args = {'VocabularyName': vocabulary_name, 'LanguageCode': language_code}
        if phrases is not None:
            vocab_args['Phrases'] = phrases
        elif table_uri is not None:
            vocab_args['VocabularyFileUri'] = table_uri
        response = transcribe_client.create_vocabulary(**vocab_args)
        logger.info("Created custom vocabulary %s.", response['VocabularyName'])
    except ClientError:
        logger.exception("Couldn't create custom vocabulary %s.", vocabulary_name)
        raise
    else:
        return response


def list_vocabularies(vocabulary_filter, transcribe_client):
    """
    Lists the custom vocabularies created for this AWS account.

    :param vocabulary_filter: The returned vocabularies must contain this string in
                              their names.
    :param transcribe_client: The Boto3 Transcribe client.
    :return: The list of retrieved vocabularies.
    """
    try:
        response = transcribe_client.list_vocabularies(
            NameContains=vocabulary_filter)
        vocabs = response['Vocabularies']
        next_token = response.get('NextToken')
        while next_token is not None:
            response = transcribe_client.list_vocabularies(
                NameContains=vocabulary_filter, NextToken=next_token)
            vocabs += response['Vocabularies']
            next_token = response.get('NextToken')
        logger.info(
            "Got %s vocabularies with filter %s.", len(vocabs), vocabulary_filter)
    except ClientError:
        logger.exception(
            "Couldn't list vocabularies with filter %s.", vocabulary_filter)
        raise
    else:
        return vocabs


def get_vocabulary(vocabulary_name, transcribe_client):
    """
    Gets information about a customer vocabulary.

    :param vocabulary_name: The name of the vocabulary to retrieve.
    :param transcribe_client: The Boto3 Transcribe client.
    :return: Information about the vocabulary.
    """
    try:
        response = transcribe_client.get_vocabulary(VocabularyName=vocabulary_name)
        logger.info("Got vocabulary %s.", response['VocabularyName'])
    except ClientError:
        logger.exception("Couldn't get vocabulary %s.", vocabulary_name)
        raise
    else:
        return response


def update_vocabulary(
        vocabulary_name, language_code, transcribe_client, phrases=None,
        table_uri=None):
    """
    Updates an existing custom vocabulary. The entire vocabulary is replaced with
    the contents of the update.

    :param vocabulary_name: The name of the vocabulary to update.
    :param language_code: The language code of the vocabulary.
    :param transcribe_client: The Boto3 Transcribe client.
    :param phrases: A list of comma-separated phrases to include in the vocabulary.
    :param table_uri: A table of phrases and pronunciation hints to include in the
                      vocabulary.
    """
    try:
        vocab_args = {'VocabularyName': vocabulary_name, 'LanguageCode': language_code}
        if phrases is not None:
            vocab_args['Phrases'] = phrases
        elif table_uri is not None:
            vocab_args['VocabularyFileUri'] = table_uri
        response = transcribe_client.update_vocabulary(**vocab_args)
        logger.info(
            "Updated custom vocabulary %s.", response['VocabularyName'])
    except ClientError:
        logger.exception("Couldn't update custom vocabulary %s.", vocabulary_name)
        raise


def delete_vocabulary(vocabulary_name, transcribe_client):
    """
    Deletes a custom vocabulary.

    :param vocabulary_name: The name of the vocabulary to delete.
    :param transcribe_client: The Boto3 Transcribe client.
    """
    try:
        transcribe_client.delete_vocabulary(VocabularyName=vocabulary_name)
        logger.info("Deleted vocabulary %s.", vocabulary_name)
    except ClientError:
        logger.exception("Couldn't delete vocabulary %s.", vocabulary_name)
        raise


def usage_demo(number_args, all_args):
    """Shows how to use the Amazon Transcribe service."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print("number of args is:" + str(number_args))
    print("args are:" + str(all_args))
    bucket_name = all_args[1]
    print("bucket_name is: " + bucket_name)
    s3_resource = boto3.resource('s3')
    transcribe_client = boto3.client('transcribe')
    print("region name is:" + transcribe_client.meta.region_name)

    print('-'*88)
    print("Welcome to the Amazon Transcribe demo!")
    print('-'*88)
    if number_args > 2:
        filter_name = all_args[2]
        print("applying filter:" + filter_name)
        all_objects = s3_resource.Bucket(bucket_name).objects.filter(Prefix=filter_name)
    else:
        all_objects = s3_resource.Bucket(bucket_name).objects.all()
    for media_object in all_objects:
        print(f" media file {media_object}.")
        media_object_key = media_object.key
        print(f" media file {media_object_key}.")
        media_uri = f's3://{bucket_name}/{media_object_key}'
        # filename = media_object_key.name
        job_name_simple = f'FamilyThings-{bucket_name}-{time.time_ns()}'
        # job_name_simple = f"FamilyThins-1609528989041096000"
        print(f"Starting transcription job {job_name_simple}.")
        # determine file type
        lower_file_name = media_object_key.lower()
        filetype = 'mp4'
        if ".mov" in lower_file_name:
            filetype = 'mp4'
        elif ".mp4" in lower_file_name:
            filetype = 'mp4'
        elif ".m4a" in lower_file_name:
            filetype = 'mp4'
        elif ".mp3" in lower_file_name:
            filetype = 'mp3'
        elif ".flac" in lower_file_name:
            filetype = 'flac'
        elif ".wav" in lower_file_name:
            filetype = 'wav'
        start_job(
            job_name_simple, f's3://{bucket_name}/{media_object_key}', filetype, 'en-US',
            transcribe_client)
        transcribe_waiter = TranscribeCompleteWaiter(transcribe_client)
        transcribe_waiter.wait(job_name_simple)
        job_simple = get_job(job_name_simple, transcribe_client)
        transcript_simple = requests.get(
            job_simple['Transcript']['TranscriptFileUri']).json()
        print(f"Transcript for job {transcript_simple['jobName']}:")
        print(transcript_simple['results']['transcripts'][0]['transcript'])

        print('-'*88)

        basename = os.path.basename(media_object_key)
        print("basename is:" + basename)
        dir_path = os.path.dirname(media_object_key)
        print("directory path is:" + dir_path)
        p = Path(dir_path)
        p.mkdir(exist_ok=True, parents=True)
        out_file_name = media_object_key + ".json"
        with open(out_file_name, 'w') as out_file:
            json.dump(transcript_simple, out_file)

if __name__ == '__main__':
    import sys

    numargs = len(sys.argv)

    print("Number of arguments:" + str(numargs))
    print(" arguments " + str(sys.argv))
    if numargs > 1:
        usage_demo(numargs, sys.argv)
    else:
        print("must pass s3 bucket name and optionally also can pass prefix as second parameter")