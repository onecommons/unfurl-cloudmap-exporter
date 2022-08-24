import json
import os
from unfurl.init import clone
from pathlib import Path
OC_HOST = os.getenv('OC_HOST') or 'https://app.dev.unfurl.cloud'

class ResourceIconMap:
    def __init__(self, unfurl_types_dict):
        self.resource_types = unfurl_types_dict.get('ResourceType')

    @staticmethod
    def fetch_from_unfurl_types():
        if not Path("unfurl-types").is_dir():
            clone(f"{OC_HOST}/onecommons/unfurl-types", 'unfurl-types')

        with open("unfurl-types/unfurl-types.json") as f:
            return ResourceIconMap(json.load(f))

    def get(self, resource_type):
        try: return OC_HOST + self.resource_types.get(resource_type).get('icon')
        except: return None

if __name__ == "__main__":
    import unittest
    class TestResourceIconMap(unittest.TestCase):
        @staticmethod
        def sample_json():
            return json.loads("""
                {
                  "ResourceType": {
                    "MariaDBInstance": {
                      "name": "MariaDBInstance",
                      "title": "Self-hosted MariaDB",
                      "description": "https://github.com/bitnami/bitnami-docker-mariadb",
                      "badge": "Database",
                      "icon": "/onecommons/unfurl-types/-/raw/main/icons/MariaDBInstance.svg",
                      "visibility": "inherit",
                      "inputsSchema": { },
                      "computedPropertiesSchema": { },
                      "extends": [
                        "MariaDBInstance",
                        "MySQLDB",
                        "SqlDB",
                        "unfurl.nodes.SoftwareService",
                        "tosca.nodes.Root",
                        "unfurl.nodes.ContainerService",
                        "unfurl.nodes.Service",
                        "tosca.capabilities.Node",
                        "tosca.capabilities.Root"
                      ],
                      "outputsSchema": { },
                      "requirements": [ ],
                      "implementations": [ ],
                      "implementation_requirements": [ ]
                    }
                  }
                }
            """)

        def test_mariadb(self):
            icon_map = ResourceIconMap(TestResourceIconMap.sample_json())
            self.assertEqual(icon_map.get("MariaDBInstance"), OC_HOST + "/onecommons/unfurl-types/-/raw/main/icons/MariaDBInstance.svg")

        def test_fetched(self):
            icon_map = ResourceIconMap.fetch_from_unfurl_types()
            self.assertEqual(icon_map.get("MariaDBInstance"), OC_HOST + "/onecommons/unfurl-types/-/raw/main/icons/MariaDBInstance.svg")

    unittest.main()

