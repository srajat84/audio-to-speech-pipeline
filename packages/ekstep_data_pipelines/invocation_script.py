import json
import os
import uuid
import argparse
from google.cloud import storage
from urllib.parse import urlparse
from data_marker.data_marker import DataMarker
from audio_processing.audio_processer import AudioProcessor
from audio_transcription.audio_transcription import AudioTranscription
from common.utils import get_logger
from common import get_periperhals

STT_CLIENT = ['google','azure']


class ACTIONS:
    DATA_MARKING = 'data_marking'
    AUDIO_PROCESSING = 'audio_processing'
    AUDIO_TRANSCRIPTION = 'audio_transcription'


LOGGER = get_logger('EKSTEP_PROCESSOR')
ACTIONS_LIST = [ACTIONS.DATA_MARKING, ACTIONS.AUDIO_PROCESSING,ACTIONS.AUDIO_TRANSCRIPTION]
CONFIG_BUCKET = 'ekstepspeechrecognition-dev'

parser = argparse.ArgumentParser(
    description='Util for data processing for EkStep')


parser.add_argument('-a', '--action', dest='action', default=None, choices=ACTIONS_LIST, required=True,
                    help='Action for the processor to perform')

parser.add_argument('-c', '--config-path', dest='local_config', default=None,
                    help='path to local config, use this when running on local')

parser.add_argument('-rc', '--remote-config-path', dest='remote_config', default=None,
                    help='path to remote gcs config file. Use this when running on cluster mode')

parser.add_argument('-ai', '--audio-ids', dest='audio_ids', default=[],
                    help='list of all the audio ids that need to processed, this needs to a comma seperated list eg. audio_id1,audio_id2 . Only works with the audio processor')

parser.add_argument('-as', '--audio-source', dest='audio_source', default=None,
                   help='The name of the source of the audio which is being processed. Only works with audio processor')

parser.add_argument('-af', '--audio-format', dest='audio_format', default=None,
                   help='The format of the audio which is being processed eg mp4,mp3 . Only works with audio processor')

parser.add_argument('-stt', '--speech-to-text',dest='speech_to_text_client',default=None,
                    help='The client name which we want to call for stt')

parser.add_argument('-fb', '--filter_by', dest='filter_by', default=None,
                    help='The filter that needs to be applied for data marking')

processor_args = parser.parse_args()


def download_config_file(config_file_path):
    LOGGER.info(f'Downloading config file from Google Cloud Storage')

    download_file_path = f'/tmp/{str(uuid.uuid4())}'
    gcs_storage_client = storage.Client()
    bucket = gcs_storage_client.bucket(CONFIG_BUCKET)

    LOGGER.info(f'Getting config file from config bucket {CONFIG_BUCKET}')

    src_blob = bucket.blob(config_file_path)
    src_blob.download_to_filename(download_file_path)

    LOGGER.info(f'Config file downloaded to {download_file_path}')

    return download_file_path


def process_config_input(arguments):
    LOGGER.info('validating config file path')

    LOGGER.info('Checking configeration file path')
    config_file_path = None

    if arguments.local_config == None and arguments.remote_config == None:
        raise argparse.ArgumentTypeError(f'No config specified')

    if arguments.local_config != None and arguments.remote_config != None:
        raise argparse.ArgumentTypeError(
            f'mulitple configs specified, specify only local_config or remote_config but not both')

    if arguments.local_config:
        LOGGER.info('Checking the file path on local machine')
        config_file_path = arguments.local_config
        exists = os.path.exists(config_file_path)

        if not exists:
            raise argparse.ArgumentTypeError(
                f'Cannot find config file on path {config_file_path}')

    if arguments.remote_config:
        LOGGER.info(
            f'http/https file path f{arguments.remote_config} found for config file. Downloading config file')
        config_file_path = download_config_file(arguments.remote_config)

    return config_file_path

def validate_data_filter_config(arguments):
    LOGGER.info('validating input for audio processing')

    if arguments.audio_source is None:
        raise argparse.ArgumentTypeError(
            f'Source is missing'
        )

    if arguments.filter_by is None:
        raise argparse.ArgumentTypeError(
            f'Filter config is missing'
        )

    return {'filter': json.loads(arguments.filter_by), 'source': arguments.audio_source}


def validate_audio_processing_input(arguments):
    LOGGER.info('validating input for audio processing')

    if arguments.audio_ids == []:
        raise argparse.ArgumentTypeError(
            f'Audio Id list missing. Please specify comma seperated audio IDs for processing'
        )

    audio_ids = [i.strip() for i in list(filter(None, arguments.audio_ids.split(',')))]

    if audio_ids == []:
        raise argparse.ArgumentTypeError(
            f'Audio Id list missing. Please specify comma seperated audio IDs for processing'
        )

    if arguments.audio_source is None:
        raise argparse.ArgumentTypeError(
            f'Audio Source missing. Please specify source for the source for the audio'
        )

    audio_source = arguments.audio_source

    if arguments.audio_format is None:
        raise argparse.ArgumentTypeError(
            f'Audio format missing. Please specify formar for the audio'
        )

    audio_format = arguments.audio_format

    return {'audio_id_list': audio_ids, 'source': audio_source, 'extension': audio_format}

def validate_audio_transcription_input(arguments):

    if arguments.audio_ids == []:
        raise argparse.ArgumentTypeError(
            f'Audio Id list missing. Please audio ID for processing'
        )

    audio_ids = [i.strip() for i in list(filter(None, arguments.audio_ids.split(',')))]

    if arguments.speech_to_text_client not in STT_CLIENT:
        raise argparse.ArgumentTypeError(
            f'Stt client must be google or azure'
        )

    speech_to_text_client = arguments.speech_to_text_client

    if arguments.audio_source is None:
        raise argparse.ArgumentTypeError(
            f'Audio Source missing. Please specify source for the source for the audio'
        )

    audio_source = arguments.audio_source

    return {'audio_ids': audio_ids,"speech_to_text_client":speech_to_text_client,"audio_source":audio_source}


def perform_action(arguments, **kwargs):
    current_action = arguments.action

    curr_processor = None


    if current_action == ACTIONS.DATA_MARKING:
        kwargs.update(validate_data_filter_config(arguments))
        LOGGER.info('Intializing data marker with given config')

        config_params = {'config_file_path': kwargs.get('config_file_path')}

        object_dict = get_periperhals(config_params)

        data_processor = object_dict.get('data_processor')
        gcs_instance = object_dict.get('gsc_instance')

        curr_processor = DataMarker.get_instance(data_processor, gcs_instance)

    elif current_action == ACTIONS.AUDIO_PROCESSING:
        kwargs.update(validate_audio_processing_input(arguments))
        LOGGER.info('Intializing audio processor marker with given config')
        config_params = {'config_file_path': kwargs.get('config_file_path')}

        object_dict = get_periperhals(config_params)

        data_processor = object_dict.get('data_processor')
        gcs_instance = object_dict.get('gsc_instance')
        audio_commons = object_dict.get('audio_commons')

        curr_processor = AudioProcessor.get_instance(data_processor, gcs_instance, audio_commons)

    elif current_action == ACTIONS.AUDIO_TRANSCRIPTION:
        kwargs.update(validate_audio_transcription_input(arguments))
        LOGGER.info('Intializing audio processor marker with given config')
        config_params = {'config_file_path': kwargs.get('config_file_path')}

        object_dict = get_periperhals(config_params)

        data_processor = object_dict.get('data_processor')
        gcs_instance = object_dict.get('gsc_instance')
        audio_commons = object_dict.get('audio_commons')
        catalogue_dao = object_dict.get('catalogue_dao')

        curr_processor = AudioTranscription.get_instance(data_processor, gcs_instance, audio_commons, catalogue_dao)

    LOGGER.info(f'Starting processing for {current_action}')
    curr_processor.process(**kwargs)
    LOGGER.info(f'Ending processing for {current_action}')


if __name__ == "__main__":
    config_file_path = process_config_input(processor_args)
    LOGGER.info('Loaded configeration file path, performing action')
    action_kwargs = {'config_file_path': config_file_path}
    perform_action(processor_args, **action_kwargs)
