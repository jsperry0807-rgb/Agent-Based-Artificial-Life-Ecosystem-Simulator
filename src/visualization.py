from mesa.visualization import SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_leaflet

from .agents.foxes import Red_Fox
from .agents.rabbits import Cottontail
from .model import EcosystemModel


def agent_portrayal(agent):
    if isinstance(agent, Cottontail):
        return {"color": "brown", "marker": "circle", "size": 8}
    if isinstance(agent, Red_Fox):
        return {"color": "orange", "marker": "triangle", "size": 10}
    return {}


def create_viz(model=None):
    if model is None:
        model = EcosystemModel()
    components = [
        make_geospace_leaflet(agent_portrayal, zoom=13),
        make_plot_component("Cottontail Population", page=1),
        make_plot_component("Red Fox Population", page=1),
        make_plot_component("Average Grass Biomass", page=2),
    ]
    page = SolaraViz(model, components=components, name="EcoSim Geo")
    return page
