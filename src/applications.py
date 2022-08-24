import os
import json
import gitlab
import IPython

OC_HOST = os.getenv('OC_HOST') or 'https://app.dev.unfurl.cloud'

class Blueprint:
    def __init__(self, deployment_ensemble):
        self.deployment_ensemble = deployment_ensemble

    @property
    def icon(self) -> str:
        try:
            return list(self.deployment_ensemble["ApplicationBlueprint"].values())[0]["projectIcon"]
        except:
            return None
    
    @property
    def url(self) -> str:
        try:
            return OC_HOST + '/' + list(self.deployment_ensemble["DeploymentTemplate"].values())[0]["projectPath"]
        except:
            return None

if __name__ == "__main__":
    import unittest
    class TestBlueprint(unittest.TestCase):
        @staticmethod
        def sample_json():
            return json.loads("""
              {
                "DeploymentTemplate": {
                  "cy-only-mail-l6tix0vq": {
                    "name": "cy-only-mail-l6tix0vq",
                    "title": "Cy only-mail l6tix0vq",
                    "cloud": "unfurl.relationships.ConnectsTo.DigitalOcean",
                    "description": "Deploy using Digital Ocean Droplets",
                    "__typename": "DeploymentTemplate",
                    "slug": "cy-only-mail-l6tix0vq",
                    "blueprint": "nextcloud",
                    "primary": "the_app",
                    "resourceTemplates": [ ],
                    "projectPath": "blueprints-andrew-aug12/nextcloud"
                  }
                },
                "ApplicationBlueprint": {
                  "nextcloud": {
                    "name": "nextcloud",
                    "__typename": "ApplicationBlueprint",
                    "title": "Nextcloud",
                    "primary": "Nextcloud",
                    "deploymentTemplates": [ ],
                    "description": "A safe home for all your data. Access & share your files, calendars, contacts, mail & more from any device, on your terms.",
                    "livePreview": null,
                    "sourceCodeUrl": null,
                    "image": null,
                    "projectIcon": "https://app.dev.unfurl.cloud/assets/uf-avatar-placeholder-1-1cc5be16f82fbd1cc136bbd8cc9c2a4e948f00e30cbb8c79cc3e4755b2120aba.svg",
                    "primaryDeploymentBlueprint": "gcp"
                  }
                }
              }
            """)

        def test_lookup_ghost(self):
            ghost = Blueprint(TestBlueprint.sample_json())
            self.assertEqual(ghost.icon, 'https://app.dev.unfurl.cloud/assets/uf-avatar-placeholder-1-1cc5be16f82fbd1cc136bbd8cc9c2a4e948f00e30cbb8c79cc3e4755b2120aba.svg')
            self.assertEqual(ghost.url, 'https://app.dev.unfurl.cloud/blueprints-andrew-aug12/nextcloud')

    unittest.main()
