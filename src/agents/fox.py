import mesa
from rabbit import Rabbit

# ------------------------------
# Fox Agent (Carnivore)
# ------------------------------
class Fox(mesa.Agent):
    """A fox that hunts rabbits, ages, and reproduces."""

    MAX_ENERGY = 150  # Can be adjusted

    def __init__(
        self,
        model,
        energy=None,
        gene_speed=None,
        gene_metabolism=None,
        gene_lifespan=None,
    ):
        super().__init__(model)
        self.age = 0

        # Genetic traits with mutation if not inherited
        self.gene_speed = (
            gene_speed if gene_speed else self.model.random.uniform(0.5, 2.0)
        )
        self.gene_metabolism = (
            gene_metabolism if gene_metabolism else self.model.random.uniform(0.5, 1.5)
        )
        self.gene_lifespan = (
            gene_lifespan
            if gene_lifespan
            else self.model.random.uniform(
                self.model.min_lifespan, self.model.max_lifespan
            )
        )

        # Energy at birth (or given)
        self.energy = energy if energy else self.model.random.uniform(15, 25)

    def step(self):
        """Move, hunt, age, metabolise, reproduce, possibly die."""
        # 1. Move to a random neighboring cell
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.model.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # 2. Hunt rabbits at the new position
        if self.pos is None:
            return
        # Get all agents at this cell
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        # Find rabbits (excluding itself)
        rabbits_here = [a for a in cell_agents if isinstance(a, Rabbit)]
        if rabbits_here:
            # Eat one rabbit (choose randomly)
            prey = self.model.random.choice(rabbits_here)
            self.model.grid.remove_agent(prey)   # Remove from grid
            prey.remove()                         # Remove from scheduler
            self.energy += self.model.energy_from_rabbit

        # 3. Metabolism with aging effect (senescence)
        age_ratio = self.age / self.gene_lifespan
        metabolism_multiplier = 1 + age_ratio * self.model.senescence_rate
        self.energy -= self.gene_metabolism * metabolism_multiplier

        # 4. Aging
        self.age += 1

        # 5. Reproduction
        if self.energy >= self.model.reproduction_threshold:
            self.energy /= 2   # Parent gives half its energy
            # Offspring genes mutate slightly
            new_speed = self.gene_speed * self.model.random.uniform(0.9, 1.1)
            new_metabolism = self.gene_metabolism * self.model.random.uniform(0.9, 1.1)
            new_lifespan = self.gene_lifespan * self.model.random.uniform(0.9, 1.1)
            offspring = Fox(
                self.model,
                energy=self.energy,
                gene_speed=new_speed,
                gene_metabolism=new_metabolism,
                gene_lifespan=new_lifespan,
            )
            # Place offspring in a neighboring cell
            neighbors = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False
            )
            if neighbors:
                new_pos = self.model.random.choice(neighbors)
            else:
                new_pos = self.pos
            self.model.grid.place_agent(offspring, new_pos)

        # 6. Death checks
        if self.energy <= 0 or self.age >= self.gene_lifespan:
            self.remove()
        elif self.energy > self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY