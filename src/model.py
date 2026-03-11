import mesa
from .agents import Grass, Rabbit

# ------------------------------
# Ecosystem Model
# ------------------------------
class EcosystemModel(mesa.Model):
    """Main model: contains grid, agents, and step logic."""

    def __init__(
        self,
        width=20,
        height=20,
        initial_rabbits=2,
        grass_regrowth_time=5,
        energy_from_grass=5,
        reproduction_threshold=20,
        seed=None,
    ):
        super().__init__(seed=seed)  # mandatory!
        self.width = width
        self.height = height
        self.grass_regrowth_time = grass_regrowth_time
        self.energy_from_grass = energy_from_grass
        self.reproduction_threshold = reproduction_threshold

        # Set up grid (toroidal world)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)

        # Create grass on every cell
        for x in range(width):
            for y in range(height):
                grass = Grass(self)
                self.grid.place_agent(grass, (x, y))

        # Create initial rabbits
        for _ in range(initial_rabbits):
            rabbit = Rabbit(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(rabbit, (x, y))

        # Data collector – track rabbit population
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Rabbit Population": lambda m: m.agents_by_type[Rabbit].__len__()
            }
        )

    def step(self):
        """Advance the model by one step."""
        # Collect data
        self.datacollector.collect(self)

        # First, let grass regrow (all grass agents do their step)
        self.agents_by_type[Grass].do("step")

        # Then rabbits act in random order
        self.agents_by_type[Rabbit].shuffle_do("step")
