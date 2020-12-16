
from ekstep_data_pipelines.common.utils import get_logger

from ekstep_data_pipelines.audio_analysis.speaker_analysis.create_embeddings import encoder
from ekstep_data_pipelines.audio_analysis.speaker_analysis.file_cluster_mapping import speaker_to_file_name_map
from ekstep_data_pipelines.audio_analysis.speaker_analysis.speaker_clustering import create_speaker_clusters


Logger = get_logger("analyse_speakers")


def analyse_gender(embed_file_path, dir_pattern, local_audio_download_path, source, catalogue_dao,fs_interface, npz_bucket_destination_path):
    pass