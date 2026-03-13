import mesa
from .rabbits import Cottontail

class Red_Fox(mesa.Agent):
    """A red fox that hunts cottontails, ages, and reproduces with polygynous mating."""

    MAX_ENERGY = 150

    def __init__(
        self,
        model,
        energy=None,
        gene_speed=None,
        gene_metabolism=None,
        gene_lifespan=None,
        sex=None,
    ):
        super().__init__(model)
        self.age = 0
        self.sex = sex if sex else self.model.random.choice(["M", "F"])

        # Genetic traits
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

        self.energy = energy if energy else self.model.random.uniform(15, 25)

        # Flag to prevent females from mating more than once per step
        self._female_mated_this_step = False   # Only used for females; males ignore

    def step(self):
        """Move, hunt, age, metabolise, reproduce (polygynous), possibly die."""
        # Reset female flag at start of step (only relevant if female)
        if self.sex == "F":
            self._female_mated_this_step = False

        # 1. Move to a random neighboring cell
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.model.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # 2. Hunt rabbits at the new position
        if self.pos is None:
            return
        cell_agents = self.model.grid.get_cell_list_contents([self.pos])
        cottontails_here = [a for a in cell_agents if isinstance(a, Cottontail)]
        if cottontails_here:
            prey = self.model.random.choice(cottontails_here)
            self.model.grid.remove_agent(prey)
            prey.remove()
            self.energy += self.model.energy_from_rabbit

        # 3. Metabolism with aging effect
        age_ratio = self.age / self.gene_lifespan
        metabolism_multiplier = 1 + age_ratio * self.model.senescence_rate
        self.energy -= self.gene_metabolism * metabolism_multiplier

        # 4. Aging
        self.age += 1

        # 5. Reproduction (polygynous)
        cost = self.model.reproduction_cost_fox

        if self.sex == "M":
            # Male: can mate with multiple females in the same cell
            # Gather all eligible females (not mated this step, opposite sex, above threshold)
            cell_contents = self.model.grid.get_cell_list_contents([self.pos])
            eligible_females = [
                a for a in cell_contents
                if isinstance(a, Red_Fox) and a.sex == "F"
                and not a._female_mated_this_step
                and a.energy >= self.model.reproduction_threshold
            ]
            # Shuffle to avoid order bias
            self.model.random.shuffle(eligible_females)
            for female in eligible_females:
                if self.energy >= self.model.reproduction_cost_fox:
                    # Deduct energy from both
                    self.energy -= cost
                    female.energy -= cost
                    # Mark female as mated
                    female._female_mated_this_step = True
                    # Produce offspring
                    self._produce_offspring_with(female)
                else:
                    break  # Male no longer has enough energy

        else:  # Female
            # Female: mate at most once per step
            if not self._female_mated_this_step and self.energy >= self.model.reproduction_cost_fox:
                cell_contents = self.model.grid.get_cell_list_contents([self.pos])
                eligible_males = [
                    a for a in cell_contents
                    if isinstance(a, Red_Fox) and a.sex == "M"
                    and a.energy >= self.model.reproduction_cost_fox
                ]
                if eligible_males:
                    # Pick a random male
                    male = self.model.random.choice(eligible_males)
                    # Deduct energy from both
                    self.energy -= cost
                    male.energy -= cost
                    # Mark female as mated
                    self._female_mated_this_step = True
                    # Produce offspring
                    self._produce_offspring_with(male)

        # 6. Death checks
        if self.energy <= 0 or self.age >= self.gene_lifespan:
            self.remove()
        elif self.energy > self.MAX_ENERGY:
            self.energy = self.MAX_ENERGY

    def _produce_offspring_with(self, mate):
        """Create offspring combining genes from self and mate, place in a neighbor cell."""
        def combine(gene1, gene2):
            base = gene1 if self.model.random.random() < 0.5 else gene2
            return base * self.model.random.uniform(0.9, 1.1)

        new_speed = combine(self.gene_speed, mate.gene_speed)
        new_metabolism = combine(self.gene_metabolism, mate.gene_metabolism)
        new_lifespan = combine(self.gene_lifespan, mate.gene_lifespan)
        offspring_sex = self.model.random.choice(["M", "F"])

        offspring = Red_Fox(
            self.model,
            energy=30,  # Starting energy for a pup
            gene_speed=new_speed,
            gene_metabolism=new_metabolism,
            gene_lifespan=new_lifespan,
            sex=offspring_sex,
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