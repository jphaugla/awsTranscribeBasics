# AWS Transcribe Basics

## Purpose

Create text transcriptions of movie and audio files.  Put the files on an S3 drive and use the AWS SDK for Python (Boto3) with Amazon Transcribe API to transcribe movie/audio files to a text format.

&nbsp;

## Outline

- [Overview](#overview)
- [Technical Overview](#technical-overview)
- [Instructions](#instructions)
  - [Getting started](#getting-started)
  - [Initial Steps](#initial-steps)
- [Create Transcripts](#create-transcripts)
- [Convert to Readable Transcript](#convert-to-readable-transcript)
- [Cleaning up](#cleaning-up)
  

&nbsp;

## Overview

Use the AWS SDK for Python (Boto3) with Amazon Transcribe API to transcribe movie/audio files to a text format.

Code can be used two ways:

* Look for movie/audio files across entire s3 bucket
* Start from a filter prefix of the s3 bucket

## Technical Overview
**AWS Transcribe**

* For an overview description of Amazon Transcribe, read [AWS Transcribe](https://aws.amazon.com/transcribe/)

**AWS Transcribe Python Code Sample**

* Code is lifted from [aws transcribe documentation](https://docs.aws.amazon.com/code-samples/latest/catalog/python-transcribe-transcribe_basics.py.html)


**Changes from sample Python Code**

* Removed use of vocabulary feature
* Added loop to find files within S3 bucket 
* Increased the timeout for transcribe process
* Save the json output of the files locally
* Use additional github to transform the json files to usable form

&nbsp;

---

&nbsp;

## Instructions

***IMPORTANT NOTE**: Creating this demo application in your AWS account will create and consume AWS resources, which **will cost money**.  Costing information is available at [AWS Transcribe Pricing](https://aws.amazon.com/transcribe/pricing/?nc=sn&loc=3)

&nbsp;

### Getting started

To transcribe move/audio files in your own AWS account, follow these steps (if you do not have an AWS account, please see [How do I create and activate a new Amazon Web Services account?](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)):
This app is not completely automated.  Several scripts are needed.  The scripts share a common set of environment variables and run with cloudformation.

###  Initial Steps
* Log into the [AWS console](https://console.aws.amazon.com/) if you are not already
* Setup python/aws environment - [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation)
* Get this github repository 
```bash
git clone https://github.com/jphaugla/awsTranscribeBasics.git
cd awsTranscribeBasics
```

### Create Transcripts
* Run transcribe_basics.py passing the bucket name as first parameter and optional a prefix for second parameter.  If no filter is provided, the full bucket will be processes
* This will create a directory with the same structure as the s3 bucket in the github home containing json output from AWS Transript
  
### Convert to Readable Transcript

* Multiple options can be found searching for githubs converting AWS transcribe json output files to readable format
* This works well [https://github.com/kibaffo33/aws_transcribe_to_docx](https://github.com/kibaffo33/aws_transcribe_to_docx)
* Starting from a new directory, these steps work:
```bash
git clone git@github.com:kibaffo33/aws_transcribe_to_docx.git
cd aws_transcribe_to_docsx.git
pip install tscribe
cp ../awsTranscribeBasics/make_readable.py .
python3 make_readable.py pathToJson
```
### Cleaning up

Remove all files from S3 to avoid accruing unnecessary charges

&nbsp;

---

&nbsp;