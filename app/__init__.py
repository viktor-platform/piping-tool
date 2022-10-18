from viktor import InitialEntity

from .bore.controller import Controller as Bore
from .bore_folder.controller import Controller as BoreFolder
from .cpt.controller import Controller as CPT
from .cpt_folder.controller import Controller as CPTFolder
from .dyke.controller import Controller as Dyke
from .exit_point.controller import Controller as ExitPoint
from .ground_model.controller import Controller as GroundModel
from .models.controller import Controller as Models
from .project_folder.controller import Controller as ProjectFolder
from .segment.controller import Controller as Segment

initial_entities = [
    InitialEntity(
        "ProjectFolder",
        name="Projects",
        children=[
            InitialEntity(
                "Dyke",
                name="dijk.zip",
                params="../manifest/dyke.json",
                children=[InitialEntity("Segment", name="Segment1", params="../manifest/segment.json")],
            )
        ],
    ),
    InitialEntity("Models", name="Models folder"),
]
