import json
import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.contrib.kubernetes import secret
from airflow.contrib.operators import kubernetes_pod_operator
from airflow.operators.python_operator import PythonOperator
from helper_dag import data_marking_done

data_marker_config = json.loads(Variable.get("data_filter_config"))
bucket_name = Variable.get("bucket")

composer_namespace = Variable.get("composer_namespace")
YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)

secret_file = secret.Secret(
    deploy_type='volume',
    deploy_target='/tmp/secrets/google',
    secret='gc-storage-rw-key',
    key='key.json')


def create_dag(data_marker_config, default_args):
    dag = DAG('data_marker_pipeline',
              schedule_interval=datetime.timedelta(days=1),
              default_args=default_args,
              start_date=YESTERDAY)

    with dag:
        after_completed = PythonOperator(
            task_id= "data_marking_done",
            python_callable=data_marking_done,
            op_kwargs={},
            )

        for source in data_marker_config.keys():
            filter_by_config = data_marker_config.get(source)
            data_marker_task = kubernetes_pod_operator.KubernetesPodOperator(
                task_id=f'data-marker-{source}',
                name='data-marker',
                cmds=["python", "invocation_script.py" ,"-a", "data_marking", "-rc", "data/audiotospeech/config/audio_processing/config.yaml",
                      "-as", source, "fb", filter_by_config],
                namespace = composer_namespace,
                startup_timeout_seconds=300,
                secrets=[secret_file],
                image='us.gcr.io/ekstepspeechrecognition/ekstep_data_pipelines:1.0.0',
                image_pull_policy='Always')

            data_marker_task >> after_completed

    return dag


dag_args = {
        'email': ['gaurav.gupta@thoughtworks.com'],
    }

create_dag(data_marker_config, dag_args)
