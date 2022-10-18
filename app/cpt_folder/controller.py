from viktor import ViktorController


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "CPT folder"
    children = ["CPT"]
    show_children_as = "Table"  # or 'Table'
