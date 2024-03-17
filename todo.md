Script
    

Script Polish
    - add tests
    - use pydantic settings to validate config
    - split app from jobs (add[app] as optional deps)
    - add linting script (ruff?)
    - add debug level for job.py


Dockerfile polish


Infra (ADD TO INSTRUCTIONS)
    - connect IRSA
    
Infra Polish
    - pod disruption budget
    - give quality of service
    - give technical labels to resources
    - deploy elasticsearch

slim vs slim buster in dockerfile
    Python buster is a big image that comes with development dependencies, and we will use it to install a virtual environment.
    Python slim-buster is a smaller image that comes with the minimal dependencies to just run Python, and we will use it to run our application.


Overall
    - IRSA
    - Deploy prometheus, grapfana
    - Add metrics
    - Add documentation for setting it all up
    - Add pod disruption for app
    