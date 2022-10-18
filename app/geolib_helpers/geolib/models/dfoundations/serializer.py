from datetime import datetime

from geolib import __version__ as glversion
from geolib.models.serializers import BaseSerializer
from jinja2 import Environment
from jinja2 import PackageLoader

ENV = Environment(loader=PackageLoader("geolib.models.dfoundations"), trim_blocks=True)


class DFoundationsInputSerializer(BaseSerializer):
    def render(self) -> str:
        self.ds["input_data"].update(dict(timestamp=datetime.now()))
        self.ds["input_data"].update(dict(glversion=glversion))
        template = ENV.get_template("input.foi.j2")

        return template.render(self.ds["input_data"])
