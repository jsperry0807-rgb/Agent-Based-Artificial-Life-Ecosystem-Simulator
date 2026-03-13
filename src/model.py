import mesa
import threading
from .agents.grass import Grass
from .agents.rabbits import Cottontail
from .agents.foxes import Red_Fox


class EcosystemModel(mesa.Model):
    """Main model: contains grid, agents, and step logic with aging."""

    def __init__(
        self,
        width=50,
        height=50,
        initial_rabbits=200,
        initial_foxes=20,
        grass_regrowth_time=10,
        energy_from_grass=8,
        energy_from_rabbit=40,
        reproduction_threshold=30,
        reproduction_cost_fox=15,
        reproduction_cost_rabbit=5,
        min_lifespan=300,
        max_lifespan=800,
        senescence_rate=0.1,
        seed=None,
    ):
        super().__init__(seed=seed)
        self.lock = threading.RLock()  # For thread safety
        self.width = width
        self.height = height
        self.grass_regrowth_time = grass_regrowth_time
        self.energy_from_grass = energy_from_grass
        self.energy_from_rabbit = energy_from_rabbit
        self.reproduction_threshold = reproduction_threshold
        self.reproduction_cost_fox = reproduction_cost_fox
        self.reproduction_cost_rabbit = reproduction_cost_rabbit
        self.initial_offspring_energy = 10  # Energy given to newborns
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

        # Create initial cottontails
        for _ in range(initial_rabbits):
            cottontail = Cottontail(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(cottontail, (x, y))

        for _ in range(initial_foxes):
            fox = Red_Fox(self)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(fox, (x, y))

        # Data collector – track cottontail population and genetic traits
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Cottontail Population": lambda m: m.get_rabbit_population(),
                "Red Fox Population": lambda m: m.get_fox_population(),
                "Cottontail Avg Speed": lambda m: m.get_rabbit_avg_speed(),
                "Red Fox Avg Speed": lambda m: m.get_fox_avg_speed(),
                "Cottontail Avg Metabolism": lambda m: m.get_rabbit_avg_metabolism(),
                "Red Fox Avg Metabolism": lambda m: m.get_fox_avg_metabolism(),
                "Cottontail Avg Lifespan Gene": lambda m: m.get_rabbit_avg_lifespan(),
                "Red Fox Avg Lifespan Gene": lambda m: m.get_fox_avg_lifespan(),
                "Cottontail Avg Energy": lambda m: m.get_rabbit_avg_energy(),
                "Red Fox Avg Energy": lambda m: m.get_fox_avg_energy(),
                "Cottontail Avg Age": lambda m: m.get_rabbit_avg_age(),
                "Red Fox Avg Age": lambda m: m.get_fox_avg_age(),
                "Cottontail Sex Ratio (M/F)": lambda m: m.get_rabbit_sex_ratio(),
            }
        )

    # Add getter methods for all data collector metrics
    def get_rabbit_population(self):
        with self.lock:
            return len(self.agents_by_type[Cottontail])

    def get_fox_population(self):
        with self.lock:
            return len(self.agents_by_type[Red_Fox])

    def get_rabbit_avg_speed(self):
        with self.lock:
            rabbits = self.agents_by_type[Cottontail]
            return sum(r.gene_speed for r in rabbits) / len(rabbits) if rabbits else 0

    def get_fox_avg_speed(self):
        with self.lock:
            foxes = self.agents_by_type[Red_Fox]
            return sum(r.gene_speed for r in foxes) / len(foxes) if foxes else 0

    def get_rabbit_avg_metabolism(self):
        with self.lock:
            rabbits = self.agents_by_type[Cottontail]
            return (
                sum(r.gene_metabolism for r in rabbits) / len(rabbits) if rabbits else 0
            )

    def get_fox_avg_metabolism(self):
        with self.lock:
            foxes = self.agents_by_type[Red_Fox]
            return sum(r.gene_metabolism for r in foxes) / len(foxes) if foxes else 0

    def get_rabbit_avg_lifespan(self):
        with self.lock:
            rabbits = self.agents_by_type[Cottontail]
            return (
                sum(r.gene_lifespan for r in rabbits) / len(rabbits) if rabbits else 0
            )

    def get_fox_avg_lifespan(self):
        with self.lock:
            foxes = self.agents_by_type[Red_Fox]
            return sum(r.gene_lifespan for r in foxes) / len(foxes) if foxes else 0

    def get_rabbit_avg_energy(self):
        with self.lock:
            rabbits = self.agents_by_type[Cottontail]
            return sum(r.energy for r in rabbits) / len(rabbits) if rabbits else 0

    def get_fox_avg_energy(self):
        with self.lock:
            foxes = self.agents_by_type[Red_Fox]
            return sum(r.energy for r in foxes) / len(foxes) if foxes else 0

    def get_rabbit_avg_age(self):
        with self.lock:
            rabbits = self.agents_by_type[Cottontail]
            return sum(r.age for r in rabbits) / len(rabbits) if rabbits else 0

    def get_fox_avg_age(self):
        with self.lock:
            foxes = self.agents_by_type[Red_Fox]
            return sum(r.age for r in foxes) / len(foxes) if foxes else 0

    def get_rabbit_sex_ratio(self):
        with self.lock:
            rabbits = list(self.agents_by_type[Cottontail])
            males = sum(1 for r in rabbits if r.sex == "M")
            females = sum(1 for r in rabbits if r.sex == "F")
            return males / females if females else 0

    def step(self):
        """Advance the model by one step."""
        with self.lock:  # <-- lock the entire step
            self.datacollector.collect(self)

            # Remove zombies before step
            for agent in list(self.agents):
                if agent.pos is None:
                    print(
                        f"Zombie agent before step: {agent} of type {type(agent).__name__}"
                    )
                    agent.remove()

            self.agents.shuffle_do("step")

            # Remove zombies after step
            for agent in list(self.agents):
                if agent.pos is None:
                    print(
                        f"Zombie agent after step: {agent} of type {type(agent).__name__}"
                    )
                    agent.remove()
