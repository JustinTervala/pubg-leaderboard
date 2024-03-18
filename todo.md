Script
    

Script Polish
    - add tests
    - use pydantic settings to validate config
    - split app from jobs (add[app] as optional deps)
    - add linting script (ruff?)
    - add debug level for job.py


Dockerfile polish


Infra (ADD TO INSTRUCTIONS)
    - make startup scri
    
Infra Polish
    - pod disruption budget
    - give quality of service
    - give technical labels to resources
    - deploy elasticsearch

slim vs slim buster in dockerfile
    Python buster is a big image that comes with development dependencies, and we will use it to install a virtual environment.
    Python slim-buster is a smaller image that comes with the minimal dependencies to just run Python, and we will use it to run our application.


Overall
    - Add metrics
        to instrument job with metrics use a push gateway
            https://stackoverflow.com/questions/5zz4920309/monitoring-short-lived-python-batch-job-processes-using-prometheus
    - DOCS!
    - use kustomize
    - add output pydantic models for app
    - Add documentation for setting it all up
    - add quality of service

    