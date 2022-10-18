from viktor import ViktorController


class Controller(ViktorController):
    """
    Controller to show boreholes folder
    """

    label = "Boreholes folder"
    children = ["Bore"]
    show_children_as = "Table"  # or 'Table'
