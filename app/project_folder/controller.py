from viktor import ViktorController


class Controller(ViktorController):
    """
    Controller to show embankment designs
    """

    label = "Projects"
    children = ["Dyke", "CPTFolder", "BoreFolder"]
    show_children_as = "Table"  # or 'Table'
