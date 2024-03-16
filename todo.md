Script
    

Script Polish
    - use pydantic for response models
    - add tests
    - use pydantic settings to validate config
    - setup mypy
    - setup black


Dockerfile polish


Infra (ADD TO INSTRUCTIONS)
    - connect IRSA
    - deploy nginx ingress controller
    - deploy cronjob
    - configure redis
    - Use TLS, username password with redis

Infra Polish
    - pod disruption budget
    - give quality of service
    - give technical labels to resources
    - deploy elasticsearch

slim vs slim buster in dockerfile
    Python busteris a big image that comes with development dependencies, and we will use it to install a virtual environment.
    Python slim-busteris a smaller image that comes with the minimal dependencies to just run Python, and we will use it to run our application.

