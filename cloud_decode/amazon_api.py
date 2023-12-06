# coding=utf-8
# To use amazon transcribe, you should set amazon-cli first.
import glob
import os.path
import boto3
import click
from botocore.exceptions import ClientError

from utils import *

STORE_BUCKET = "lusanwavbucket"
JSON_BUCKET = "lusanjsonbucket"
MEDIA_JOB_URL = "https://s3.ap-northeast-1.amazonaws.com/"


def amazon_decode_multi(audio_files: List[str], store_bucket: str = STORE_BUCKET, json_bucket: str = JSON_BUCKET, media_job_uri: str = MEDIA_JOB_URL, save_result: bool = True, output_format: str = "transaction", max_workers: int = None, language="en-US") -> List[str]:
    with futures.ProcessPoolExecutor(max_workers=max_workers) as _executor_:
        jobs = []
        for audio_file in audio_files:
            jobs.append(
                _executor_.submit(
                    amazon_decode, audio_file, store_bucket, json_bucket, media_job_uri, save_result, output_format, language=language
                )
            )
        results = wait_for_jobs(jobs, _executor_, "[Amazon] Decode Sample Progress: ")
    return results


def amazon_find(json_file: str, expected_string: str, delete_stop_words: bool = False) -> Tuple[bool, Union[str, None], Union[float, None]]:
    with open(json_file, 'r') as _file_:
        decode_result = json.load(_file_)

    did_find, decode_string, find_confidence = False, None, 1.0
    if decode_result['success'] is True:
        result = decode_result['result']
        segments = result['segments']
        for segment in segments:
            alternatives = segment['alternatives']
            for alternative in alternatives:
                transcript = check_transaction(alternative['transcript'], delete_stop_words)
                split_transcript = transcript.split()
                if all([expected_word in split_transcript for expected_word in expected_string.split()]):
                    did_find = True
                    decode_string = transcript
                    break
    return did_find, decode_string, find_confidence


@exception_printer
def amazon_decode(wav_file: str, store_bucket: str = STORE_BUCKET, json_bucket: str = JSON_BUCKET, media_job_uri: str = MEDIA_JOB_URL, save_result: bool = True, output_format: str = "transaction", language: str = 'en-US'):
    # calculate wav hash
    wav_folder = os.path.dirname(wav_file)
    wav_hash = get_wav_hash(wav_file)
    wav_type = os.path.basename(wav_file).split(".")[-1]
    assert wav_type == "wav"
    store_wav_name = wav_hash + "." + wav_type

    # check the wav file existing and upload the wav file
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=store_bucket, Key=store_wav_name)
    except ClientError:
        # wav file not found in s3 bucket
        s3.upload_file(wav_file, store_bucket, store_wav_name)

    # transcribe audio file
    transcribe = boto3.client("transcribe")
    transcription_job_name = wav_hash + "_" + language
    job_uri = media_job_uri + store_bucket + "/" + store_wav_name
    try:
        status = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
    except ClientError:
        transcribe.start_transcription_job(
            TranscriptionJobName=transcription_job_name,
            Media={"MediaFileUri": job_uri},
            MediaFormat=wav_type,
            LanguageCode=language,
            OutputBucketName=json_bucket,
            Settings={
                "ShowAlternatives": True,
                "MaxAlternatives": 5
            }
        )
        status = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
    while True:
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)
        status = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)

    # download transaction result
    if status['TranscriptionJob']['TranscriptionJobStatus'] == "COMPLETED":
        json_file_name = transcription_job_name + ".json"
        tmp_result_file = os.path.join(wav_folder, wav_hash + ".json")
        s3.download_file(json_bucket, json_file_name, tmp_result_file)
        with open(tmp_result_file, 'r', encoding='utf-8') as _file_:
            decode_result = json.load(_file_)
        wav_result = {
            "success": True,
            "result": decode_result['results']
        }
        os.remove(tmp_result_file)
    else:
        wav_result = {
            "success": False
        }

    if save_result:
        decode_result_file = wav_file.replace('.wav', AMAZON_JSON_SUFFIX)
        with open(decode_result_file, 'w') as _file_:
            json.dump(wav_result, _file_, ensure_ascii=False)

    if output_format == "transaction":
        if not wav_result['success']:
            transaction = ""
        else:
            # only return the best result
            transcripts = wav_result['result'].get('transcripts')
            if transcripts:
                transaction = ""
            else:
                transaction = transcripts[0].get("transcript") or ""
        return transaction
    if output_format == "json":
        return wav_result


@click.command("API Recognize Script for Amazon Transcribe.")
@click.argument("wav_folder", type=click.Path(exists=True))
@click.option("--re_decode_all", expose_value=True, is_flag=True, default=False, help="Whether re-decode all the wav files. Default is False.")
@click.option("--re_decode_failed", expose_value=True, is_flag=True, default=False, help="Whether re-decode all the wav files. Default is False.")
@click.option("--max_workers", default=4, type=int, help="The number of the multi-process. Default is 4.")
@click.option("--language", '-l', default="en-US", type=click.Choice(['en-US', 'zh-CN']), help="Language Code in ['en-US', 'zh-CN']")
def api_recognize(wav_folder: str, re_decode_all: bool = False, re_decode_failed: bool = False, max_workers: int = 4, language='en-US'):
    logger.info("Start decode folder '{}' using Amazon Transcribe.".format(wav_folder))

    with futures.ProcessPoolExecutor(max_workers=max_workers) as _executor_:
        jobs = []

        wav_files = glob.glob(os.path.join(wav_folder, "**", "*.wav"), recursive=True)
        wav_files = filter_irrelevant_wav(wav_files)
        for wav_file in wav_files:
            wav_decode_file = wav_file.replace(".wav", AMAZON_JSON_SUFFIX)

            if os.path.exists(wav_decode_file):
                try:
                    with open(wav_decode_file, 'r') as _file_:
                        wav_result = json.load(_file_)

                        if wav_result['success'] and not re_decode_all:  # 成功不重新解码
                            continue
                        elif not wav_result['success'] and not re_decode_failed:  # 失败但不重新解码
                            continue
                except json.decoder.JSONDecodeError:
                    logger.warning("Load wav_decode_file '{}' Error. Re-decode the wav file using Amazon.".format(wav_decode_file))

            jobs.append(
                _executor_.submit(amazon_decode, wav_file, language=language)
            )

        wait_for_jobs(jobs, _executor_)

    logger.info("Decoding folder '{}' Done!".format(wav_folder))


if __name__ == '__main__':
    api_recognize()
