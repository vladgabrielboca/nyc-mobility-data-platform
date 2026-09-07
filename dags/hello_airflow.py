from datetime import datetime
from airflow.sdk import dag, task

@dag(
    dag_id="hello_dag",
    schedule="@monthly",
    start_date=datetime(2023, 1, 1),
    catchup=False
)
def pipeline_test():

    # {{ ds }} usage example
    @task
    def hello_world(ds=None):
        print(f"Hello World! Today is {ds}")

    hello_world()

pipeline_test()
