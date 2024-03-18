# Job/App ToDo
- Support using a locally-ruuning Redis server outside of the cluster (barring fixing the ingress, instead of just failing)
- Use version of package in user-agent header (use importlib)
- Add tests
- Check with mypy
- Add ruf for linting
- Support using a debug environment variable or CLI option to enable debugging logging
- Split app dependencies from the rest so it can be installed with `.[app]`
- Bump Python to 3.12
- Add metrics to app
- Add metrics to job using Prometheus push gateway
- Add docstrings
- Polish the generated Swagger docs

# Dockerfile ToDo
- Better cleanup for apt lists, etc
- If there's testing, add a dev image layer
- Add labels

# Infrastructure Polish
- Biggest issue is fixing the ingresses
- Use Kustomize to template the manifests in `infra/`
- Enable TLS
- Actually connect the Service Accounts to AWS IAM roles
    - Maybe I could make a local version following something like [this blog post](https://medium.com/@danielepolencic/binding-aws-iam-roles-to-kubernetes-service-account-for-on-prem-clusters-b8bac41f269d)
- Add a Pod Disruption budget, node affinity, quality of service to pods
- Add EFK stack for logs (maybe Loki?)
- Configure RBAC
- Better security context

    