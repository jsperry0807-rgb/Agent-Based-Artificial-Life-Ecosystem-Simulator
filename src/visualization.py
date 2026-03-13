from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from mesa.visualization.components import AgentPortrayalStyle
from .agents.grass import Grass
from .agents.rabbits import Cottontail
from .agents.foxes import Red_Fox
from .model import EcosystemModel


# ------------------------------
# Visualization (SolaraViz)
# ------------------------------
def agent_portrayal(agent):
    """Define how each agent is drawn using the new Mesa style."""
    with agent.model.lock:  # Ensure thread safety when accessing agent properties
        if isinstance(agent, Cottontail):
            return AgentPortrayalStyle(
                color="white",
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

        if isinstance(agent, Red_Fox):
            return AgentPortrayalStyle(
                color="orange",
                marker="^",  # triangle
                size=100,
            )
        return AgentPortrayalStyle(color="gray", marker="x", size=50)


def create_viz(model=None):
    if model is None:
        model = EcosystemModel()  # default instance

    components = [
        make_space_component(agent_portrayal),
        make_plot_component("Cottontail Population", page=1),
        make_plot_component("Red Fox Population", page=1),
        make_plot_component("Cottontail Avg Speed", page=2),
        make_plot_component("Red Fox Avg Speed", page=2),
        make_plot_component("Cottontail Avg Metabolism", page=3),
        make_plot_component("Red Fox Avg Metabolism", page=3),
        make_plot_component("Cottontail Avg Lifespan Gene", page=4),
        make_plot_component("Red Fox Avg Lifespan Gene", page=4),
        make_plot_component("Cottontail Avg Energy", page=5),
        make_plot_component("Red Fox Avg Energy", page=5),
        make_plot_component("Cottontail Avg Age", page=6),
        make_plot_component("Red Fox Avg Age", page=6),
    ]

    page = SolaraViz(
        model, components=components, name="Artificial Life Ecosystem Simulator", use_threads=True, play_interval=500
    )
    return page
