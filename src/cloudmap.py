import json
import os
import shutil
import IPython
from urllib.parse import unquote

from dotenv import load_dotenv
import gitlab

from applications import Blueprint
from resources import ResourceIconMap

load_dotenv()

from typing import Dict

OC_TOKEN = os.getenv('OC_TOKEN')
OC_HOST = os.getenv('OC_HOST')
OC_USER = os.getenv('OC_USER') or OC_TOKEN
gitlab_instance = gitlab.Gitlab(OC_HOST, private_token=OC_TOKEN)


class Root:
    name: str
    #  {provider: Cloud}
    clouds: Dict[str, "Cloud"]
    environment_providers: Dict[str, str] = {}

    def __init__(self):
        self.name = ""
        self.clouds = {}

    def add_cloud(self, cloud: str, environment: str) -> bool:
        self.environment_providers[environment] = cloud.cloud_provider
        if cloud.cloud_provider in self.clouds:
            return False
        else:
            self.clouds[cloud.cloud_provider] = cloud
            return True

    def get_provider_for_environment(self, environment: str) -> str:
        return self.environment_providers.get(environment)

    def get_cloud_region_variable_key(self, cloud_provider: str) -> str:
        return {
            "GoogleCloudProject": "CLOUDSDK_COMPUTE_ZONE",
            "AWSAccount": "AWS_DEFAULT_REGION",
            # Not sure where the default region is for DigitalOcean
            # "DigitalOcean": "CLOUDSDK_COMPUTE_ZONE",
        }[cloud_provider]

    def get_cloud_region(self, project_id: int, environment: str, cloud_provider: str) -> str:
        if cloud_provider == "DigitalOcean":
            return "nyc1"
        elif cloud_provider == "K8sCluster":
            return ""
        key = self.get_cloud_region_variable_key(cloud_provider)
        try:
            region = gitlab_instance.projects.get(project_id).variables.get(
                key, **{
                    'filter[environment_scope]': environment
                }).value
            return region
        except gitlab.exceptions.GitlabGetError as e:
            # Variable doesn't exist
            # raise e
            
            # let's just return n/a for now
            # happens for environments that weren't successfully instantiated

            return "n/a"

    def to_json(self) -> str:
        return {
            "name": self.name,
            "children": list(self.clouds.values()),
        }


class Cloud:
    cloud_provider: str
    cloud: str
    cloud_icon: str
    type: str = "cloudProvider"
    regions: Dict[str, "Region"]

    def __init__(self, cloud_provider: str) -> None:
        self.regions = {}
        self.cloud_provider = cloud_provider
        self.cloud = self.get_cloud_name(cloud_provider)
        self.cloud_icon = self.get_cloud_icon(cloud_provider)

    def add_region(self, region: "Region") -> bool:
        if region.name in self.regions:
            return False
        else:
            self.regions[region.name] = region
            return True

    def get_cloud_name(self, cloud_provider: str) -> str:
        return {
            "DigitalOcean": "digitalocean",
            "GoogleCloudProject": "googlecloud",
            "AWSAccount": "aws",
            "K8sCluster": "k8s"
        }[cloud_provider]

    def get_cloud_icon(self, cloud_provider: str) -> str:
        return {
            "DigitalOcean": "data:image/svg,",
            "GoogleCloudProject": "data:image/svg,",
            "AWSAccount": "data:image/svg,",
            "K8sCluster": "data:image/svg,"
        }[cloud_provider]

    def to_json(self):
        return {
            "cloud": self.cloud,
            "icon": self.cloud_icon,
            "type": self.type,
            "children": list(self.regions.values()),
        }


class Region:
    name: str
    type: str = "region"
    cloud: str
    accounts: Dict[str, "Account"]

    def __init__(self, name: str, cloud: str) -> None:
        self.accounts = {}
        self.name = name
        self.cloud = cloud

    def add_account(self, account: "Account") -> None:
        if account.name in self.accounts:
            return False
        else:
            self.accounts[account.name] = account
            return True

    def to_json(self):
        return {
            "name": self.name,
            "type": self.type,
            "cloud": self.cloud,
            "children": list(self.accounts.values()),
        }


class Account:
    name: str
    type: str = "Account"
    cloud: str
    avatarUrl: str
    deployments: Dict[str, "Deployment"]

    # Initialize from project id
    def __init__(self, cloud: str, project_id: int) -> None:
        self.deployments = {}
        self.cloud = cloud
        self.create_user_from_project_id(project_id)

    def create_user_from_project_id(self, project_id: int) -> bool:
        project = gitlab_instance.projects.get(project_id).asdict()

        owner = project.get('owner')
        if owner is not None:
          self.name = owner['username']
        else:
          self.name = project['name']

        # If the avatar is not set, use the default avatar
        self.avatarUrl = project['avatar_url'] or "https://app.dev.unfurl.cloud/assets/uf-avatar-placeholder-2-0483fbc376bd429dfd21d89a6b14e7fff0895fff8249d940d4434abb2bd9d163.svg"

        return True

    def add_deployment(self, deployment: "Deployment") -> None:
        if deployment.name in self.deployments:
            return False
        else:
            self.deployments[deployment.name] = deployment
            return True

    def to_json(self):
        return {
            "name": self.name,
            "type": self.type,
            "cloud": self.cloud,
            "icon": self.avatarUrl,
            "children": list(self.deployments.values()),
        }


class Deployment:
    name: str
    deploy_path: str
    dashboard_url: str
    app_icon: str
    type: str = "app"
    cloud: str
    resources: Dict[str, "Resource"]

    def __init__(self, name: str, dashboard_url: str, deploy_path: str, template_name: str, cloud: "Cloud", deployment_ensemble) -> None:
        self.resources = {}
        self.name = name
        self.dashboard_url = dashboard_url
        self.deploy_path = deploy_path
        self.deployment_ensemble = deployment_ensemble
        self.app_icon = self.get_app_icon()
        self.cloud = cloud

    def add_resource(self, resource: "Resource") -> None:
        if resource.name in self.resources:
            return False
        else:
            self.resources[resource.name] = resource
            return True

    def get_app_icon(self):
        blueprint = Blueprint(self.deployment_ensemble)
        return blueprint.icon or ""

    def to_json(self):
        return {
            "name": self.name,
            "deploy_path": self.deploy_path,
            "dashboard_url": self.dashboard_url,
            "icon": self.app_icon,
            "type": self.type,
            "cloud": self.cloud,
            "children": list(self.resources.values()),
        }


class Resource:
    name: str
    resourceType: str
    connection: int
    cloud: str
    icon: str
    value: int = 2

    def __init__(self, name: str, resourceType: str, cloud: str) -> None:
        self.name = name
        self.resourceType = resourceType
        self.icon = self.get_icon()
        self.connection = None
        self.cloud = cloud
    
    def get_icon(self):
        resource_map = ResourceIconMap.fetch_from_unfurl_types()
        return resource_map.get(self.resourceType) or ""

    def to_json(self):
        return {
            "name": self.name,
            "resourceType": self.resourceType,
            "connection": self.connection,
            "cloud": self.cloud,
            "icon": self.icon,
            "value": self.value,
        }


def handle(dashboard_url, root=None):
    from unfurl.init import clone
    clone_location = "dashboard"

    try:
        shutil.rmtree(clone_location)
    except FileNotFoundError:
        pass
    
    src_url = f"https://{OC_USER}:{OC_TOKEN}@{dashboard_url.lstrip('https://')}"
    clone(src_url, clone_location)

    with open(f'{clone_location}/environments.json', 'r') as f:
        environments = json.load(f)

    if root is None:
        root = Root()

    for name, environment in environments['DeploymentEnvironment'].items():
        if 'primary_provider' not in environment['connections']:
            # TODO: handle k8s
            print(f"Skipping environment {name}, it doesn't have a primary provider")
            continue
        provider = environment['connections']['primary_provider']['type'].split('.')[-1]
        cloud = Cloud(provider)
        root.add_cloud(cloud, name)
    
    if 'DeploymentPath' not in environments:
        print(f"Finishing {dashboard_url}, no deployments found")
        return root

    for path, deployment in environments['DeploymentPath'].items():
        # deployment_name = deployment['name']
        deployment_environment = deployment['environment']
        deployment_provider = root.get_provider_for_environment(deployment_environment)

        # Different ensembles have different keys for project id
        if 'project_id' in deployment:
            project_id = deployment['project_id']
        elif 'projectId' in deployment:
            project_id = deployment['projectId']
        else:
            # No project id found, skip this deployment
            print(f'Skipping deployment {path}, no project id found')
            continue
        region_name = root.get_cloud_region(project_id, deployment_environment, deployment_provider)
        cloud_provider = root.get_provider_for_environment(deployment_environment)
        region = Region(region_name, cloud_provider)
        root.clouds[cloud_provider].add_region(region)

        try:
          with open(f'{clone_location}/{path}/ensemble.json', 'r') as f:
              deployment_ensemble = json.load(f)

          with open(f'{clone_location}/{path}/deployment.json', 'r') as f:
              deployment_ensemble.update(json.load(f))
        except Exception as e:
            print("Exception while loading deployment info")
            print(e)
            continue

        account = Account(cloud_provider, project_id)

        root.clouds[cloud_provider].regions[region_name].add_account(account)

        deployment = deployment_ensemble.get('Deployment')
        if deployment is None: continue

        deployment_name = list(deployment)[0]
        deployment_definition = deployment_ensemble['Deployment'][deployment_name]
        deployent_name = deployment_definition['title']
        app = Deployment(deployment_name, dashboard_url, path, deployment_name, cloud_provider, deployment_ensemble)

        (root
            .clouds[cloud_provider]
            .regions[region.name]
            .add_account(account))
        (root
            .clouds[cloud_provider]
            .regions[region.name]
            .accounts[account.name]
            .add_deployment(app))

        resources = deployment_definition['resources']
        for resource_name in resources:
            # Where is the definition of the resource?
            if resource_name in deployment_ensemble['Resource']:
                resource_definition = (deployment_ensemble
                                       ['Resource']
                                       [resource_name])

            # Haven't found have a definition
            else:
                print(f"Skipping resource {resource_name}, no definition found")
                continue

            if resource_definition.get('visibility') == 'hidden':
                continue

            resource_template = resource_definition["template"]
            resource_template = deployment_ensemble["ResourceTemplate"][resource_template]

            resource_type = resource_template['type']

            resource = Resource(resource_name, resource_type, cloud_provider)
            (root
                .clouds[cloud_provider]
                .regions[region.name]
                .accounts[account.name]
                .deployments[deployment_name]
                .add_resource(resource))

    return root

def handle_group(group_name):
    root = Root()
    for project in gitlab_instance.groups.list(search=group_name)[0].projects.list():
        root = handle(project.http_url_to_repo, root=root)
    return root

###############################################################################################
def main():
    # JSON encoding for custom objects
    def default(o):
        if hasattr(o, 'to_json'):
            return o.to_json()
        raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')
    root = handle('https://app.dev.unfurl.cloud/a10/dashboard')
    with open('result-a10.json', 'w') as f:
        json.dump(root.to_json(), f, default=default, indent=2)

if __name__ == "__main__":
    main()
    # handle_group("Testbed")
