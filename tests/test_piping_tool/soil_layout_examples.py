# from viktor import Color
# from viktor.geo import Soil
# from viktor.geo import SoilLayer
#
#
# def example_1() -> SoilLayout:
#     """"Function returns an example SoilLayout and is used for unit testing. The SoilLayout contains one cover layer"""
#
#     color = Color(0, 0, 0)  # default color, needed to create a Soil object
#     clay = Soil("Clay", color)
#     sand = Soil("Sand", color)
#
#     soil_layout = SoilLayout(
#         [
#             SoilLayer(clay, 2, 0, properties={"gamma_dry": 17, "gamma_wet": 17, "aquifer": False}),
#             SoilLayer(sand, 0, -10, properties={"aquifer": True, "k_hor": 10, "d70": 2.00e-4}),
#         ]
#     )
#
#     return soil_layout
#
#
# def example_2() -> SoilLayout:
#     """"Function returns an example SoilLayout and is used for unit testing"""
#
#     color = Color(0, 0, 0)  # default color, needed to create a Soil object
#
#     clay = Soil("Clay", color)
#     peat = Soil("Peat", color)
#     sand = Soil("Sand", color)
#
#     soil_layout = SoilLayout(
#         [
#             SoilLayer(clay, 2, 1, properties={"gamma_dry": 17, "gamma_wet": 17, "aquifer": False}),
#             SoilLayer(peat, 1, 0, properties={"gamma_dry": 11, "gamma_wet": 11, "aquifer": False}),
#             SoilLayer(
#                 sand,
#                 0,
#                 -10,
#                 properties={"gamma_dry": 17, "gamma_wet": 19, "aquifer": True, "k_hor": 10, "d70": 2.00e-4},
#             ),
#         ]
#     )
#
#     return soil_layout
