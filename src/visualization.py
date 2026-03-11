from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from .agents import Grass, Rabbit
from .model import EcosystemModel


# ------------------------------
# Visualization (SolaraViz)
# ------------------------------
def agent_portrayal(agent):
    """Define how each agent is drawn using the new Mesa style."""

    if isinstance(agent, Rabbit):
        return AgentPortrayalStyle(
            color="brown",
            marker="o",  # circle
            size=80,
        )

    if isinstance(agent, Grass):
        if agent.grown:
            return AgentPortrayalStyle(
                color="green",
                marker="s",  # square
                size=120,
            )
        else:
            return AgentPortrayalStyle(color="saddlebrown", marker="s", size=120)


def create_viz(model=None):
    if model is None:
        model = EcosystemModel()  # default instance
    components = [
        make_space_component(agent_portrayal),
        make_plot_component("Rabbit Population"),
    ]
    page = SolaraViz(
        model, components=components, name="Artificial Life Ecosystem Simulator"
    )
    return page
