import mesa
from .agents import Grass, Rabbit, Fox

class EcosystemModel(mesa.Model):
    """Main model: contains grid, agents, and step logic with aging."""

    def __init__(
        self,
        width=20,
        height=20,
        initial_rabbits=2,
        initial_foxes=2,
        grass_regrowth_time=5,
        energy_from_grass=5,
        energy_from_rabbit=20,
        reproduction_threshold=20,
        min_lifespan=30,
        max_lifespan=60,
        senescence_rate=0.5,
        seed=None,
    ):
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.grass_regrowth_time = grass_regrowth_time
        self.energy_from_grass = energy_from_grass
        self.energy_from_rabbit = energy_from_rabbit
        self.reproduction_threshold = reproduction_threshold
        self.min_lifespan = min_lifespan
        self.max_lifespan = max_lifespan
        self.senescence_rate = senescence_rate

        # Set up grid (toroidal world)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)
        self.grass_grid: list[list[Grass | None]] = [
            [None for _ in range(height)] for _ in range(width)
        ]

        # Create grass on every cell
        for x in range(width):
            for y in range(height):
                grass = Grass(self)
                self.grid.place_agent(grass, (x, y))
                self.grass_grid[x][y] = grass

        # Create initial rabbits
        for _ in range(initial_rabbits):
            rabbit = Rabbit(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(rabbit, (x, y))

        for _ in range(initial_foxes):
            fox = Fox(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(fox, (x, y))

        # Data collector – track rabbit population and genetic traits
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Rabbit Population": lambda m: len(m.agents_by_type[Rabbit]),
                "Fox Population": lambda m: len(m.agents_by_type[Fox]),
                "Avg Speed": lambda m: (
                    sum(r.gene_speed for r in m.agents_by_type[Rabbit])
                    / len(m.agents_by_type[Rabbit])
                    if m.agents_by_type[Rabbit]
                    else 0
                ),
                "Avg Metabolism": lambda m: (
                    sum(r.gene_metabolism for r in m.agents_by_type[Rabbit])
                    / len(m.agents_by_type[Rabbit])
                    if m.agents_by_type[Rabbit]
                    else 0
                ),
                "Avg Lifespan Gene": lambda m: (
                    sum(r.gene_lifespan for r in m.agents_by_type[Rabbit])
                    / len(m.agents_by_type[Rabbit])
                    if m.agents_by_type[Rabbit]
                    else 0
                ),
                "Avg Energy": lambda m: (
                    sum(r.energy for r in m.agents_by_type[Rabbit])
                    / len(m.agents_by_type[Rabbit])
                    if m.agents_by_type[Rabbit]
                    else 0
                ),
                "Avg Age": lambda m: (
                    sum(r.age for r in m.agents_by_type[Rabbit])
                    / len(m.agents_by_type[Rabbit])
                    if m.agents_by_type[Rabbit]
                    else 0
                ),
            }
        )

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")