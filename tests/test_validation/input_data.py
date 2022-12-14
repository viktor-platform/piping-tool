from app.ditch.model import Ditch

uplift_parameters_exit_point_28_first_aquifer = {
    "river_level": 5.5,
    "polder_level": -0.2,
    "damping_factor": 0.8,
    "dike_width": 25,
    "geohydrologic_model": "1",
    "distance_from_ref_line": 15.549989163594741,
    "distance_from_entry_line": 57.671996701324574,
    "ditch": None,
    "aquifer_hydraulic_head_hinterland": 0.8,
    "user_phi_avg_hinterland": None,
    "user_phi_avg_river": None,
    "soil_layout": [
        {
            "soil": {"name": "cover_layer", "color": (192, 192, 192), "properties": {"ui_name": "Deklaag"}},
            "top_of_layer": 3.439,
            "bottom_of_layer": -8.875,
            "properties": {
                "gamma_dry": 14.98984895241189,
                "gamma_wet": 15.030453142764333,
                "vertical_permeability": 0.15049537112229983,
                "horizontal_permeability": 0.21281793081045963,
                "aquifer": False,
            },
        },
        {
            "soil": {"name": "first_aquifer", "color": (202, 188, 145), "properties": {"ui_name": "Eerste aquifer"}},
            "top_of_layer": -8.875,
            "bottom_of_layer": -30.875,
            "properties": {
                "vertical_permeability": 10,
                "horizontal_permeability": 10,
                "gamma_dry": 17.0,
                "gamma_wet": 19.0,
                "grain_size_d70": 0.25,
                "aquifer": True,
            },
        },
    ],
    "leakage_length_hinterland": None,
    "leakage_length_foreland": None,
}

uplift_parameters_exit_point_28_second_aquifer = {
    "river_level": 5.5,
    "polder_level": -0.2,
    "damping_factor": 0.8,
    "dike_width": 25,
    "geohydrologic_model": "1",
    "distance_from_ref_line": 15.549989163594741,
    "distance_from_entry_line": 57.671996701324574,
    "ditch": None,
    "aquifer_hydraulic_head_hinterland": 0.8,
    "user_phi_avg_hinterland": None,
    "user_phi_avg_river": None,
    "soil_layout": [
        {
            "soil": {"name": "cover_layer", "color": (192, 192, 192), "properties": {"ui_name": "Deklaag"}},
            "top_of_layer": 3.439,
            "bottom_of_layer": -8.875,
            "properties": {
                "gamma_dry": 14.98984895241189,
                "gamma_wet": 15.030453142764333,
                "vertical_permeability": 0.15049537112229983,
                "horizontal_permeability": 0.21281793081045963,
                "aquifer": False,
            },
        },
        {
            "soil": {"name": "first_aquifer", "color": (202, 188, 145), "properties": {"ui_name": "Eerste aquifer"}},
            "top_of_layer": -8.875,
            "bottom_of_layer": -30.875,
            "properties": {
                "vertical_permeability": 10,
                "horizontal_permeability": 10,
                "gamma_dry": 17.0,
                "gamma_wet": 19.0,
                "grain_size_d70": 0.25,
                "aquifer": False,
            },
        },
        {
            "soil": {
                "name": "intermediate_aquitard",
                "color": (154, 205, 50),
                "properties": {"ui_name": "Tussenligende aquitard"},
            },
            "top_of_layer": -30.875,
            "bottom_of_layer": -33.875,
            "properties": {
                "vertical_permeability": 0.05,
                "horizontal_permeability": 0.01,
                "gamma_dry": 17.0,
                "gamma_wet": 17.0,
                "grain_size_d70": None,
                "aquifer": False,
            },
        },
        {
            "soil": {"name": "second_aquifer", "color": (219, 209, 180), "properties": {"ui_name": "Tweede aquifer"}},
            "top_of_layer": -33.875,
            "bottom_of_layer": -40.875,
            "properties": {
                "vertical_permeability": 10,
                "horizontal_permeability": 10,
                "gamma_dry": 19.0,
                "gamma_wet": 21.0,
                "grain_size_d70": 0.33,
                "aquifer": True,
            },
        },
    ],
    "leakage_length_hinterland": None,
    "leakage_length_foreland": None,
}


ditch_param_1 = {
    "ditch_points": [
        {"x": 0.0, "z": 1.556},
        {"x": 0.8999999999999999, "z": 1.0000000000000002},
        {"x": 2.3690741072458734, "z": 1.0000000000000002},
        {"x": 3.2690741072458733, "z": 1.437},
    ],
    "talu_slope": 1.5,
    "is_wet": False,
}
ditch_1 = Ditch(
    *ditch_param_1.get("ditch_points"),
    is_wet=ditch_param_1.get("is_wet"),
    talu_slope=ditch_param_1.get("talu_slope"),
)
piping_parameters_ditch_1 = {
    "river_level": 5.5,
    "polder_level": 1.8,
    "damping_factor": 1,
    "dike_width": None,
    "geohydrologic_model": "0",
    "distance_from_ref_line": 53.31466062176781,
    "distance_from_entry_line": 113.9813181624865,
    "ditch": ditch_1,
    "aquifer_hydraulic_head_hinterland": 5.5,
    "user_phi_avg_hinterland": None,
    "user_phi_avg_river": None,
    "soil_layout": [
        {
            "soil": {"name": "cover_layer", "color": (192, 192, 192), "properties": {"ui_name": "Deklaag"}},
            "top_of_layer": 1.437000036239624,
            "bottom_of_layer": 0.125,
            "properties": {
                "gamma_dry": 16.905487752245307,
                "gamma_wet": 16.905487752245307,
                "vertical_permeability": 0.049999999999999996,
                "horizontal_permeability": 0.01,
                "aquifer": False,
            },
        },
        {
            "soil": {"name": "first_aquifer", "color": (202, 188, 145), "properties": {"ui_name": "Eerste aquifer"}},
            "top_of_layer": 0.125,
            "bottom_of_layer": -3.875,
            "properties": {
                "vertical_permeability": 10,
                "horizontal_permeability": 10,
                "gamma_dry": 17.0,
                "gamma_wet": 19.0,
                "grain_size_d70": 0.25,
                "aquifer": True,
            },
        },
        {
            "soil": {
                "name": "intermediate_aquitard",
                "color": (154, 205, 50),
                "properties": {"ui_name": "Tussenligende aquitard"},
            },
            "top_of_layer": -3.875,
            "bottom_of_layer": -10.125,
            "properties": {
                "vertical_permeability": 9.40625,
                "horizontal_permeability": 3.7562499999999996,
                "gamma_dry": 17.25,
                "gamma_wet": 18.0,
                "grain_size_d70": None,
                "aquifer": False,
            },
        },
    ],
    "leakage_length_hinterland": None,
    "leakage_length_foreland": None,
}
