def create_embeddings(local_audio_download_path, dir_pattern, embed_file_path, fs_interface, npz_bucket_destination_path)
    is_uploaded = fs_interface.upload_to_location(embed_file_path, npz_bucket_destination_path)
    if is_uploaded:
        Logger.info('npz file uploaded to :' + npz_bucket_destination_path)
    else:
        Logger.info('npz file could not be uploaded to :' + npz_bucket_destination_path)
    file_map_dict, noise_file_map_dict = create_speaker_clusters(embed_file_path, source, min_cluster_size, partial_set_size, min_samples, fit_noise_on_similarity)
    speaker_to_file_name = speaker_to_file_name_map(file_map_dict)
    Logger.info('total speakers:' + str(len(speaker_to_file_name)))