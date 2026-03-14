import logging

import geopandas as gpd
import mesa
import mesa_geo as mg
import numpy as np
import rasterio.features
from affine import Affine
from shapely.geometry import Point, Polygon

from .agents.foxes import Red_Fox
from .agents.rabbits import Cottontail

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class EcosystemModel(mesa.Model):
    world_boundary: Polygon
    space_crs: str
    space: mg.GeoSpace
    grassland_polygons: gpd.GeoDataFrame

    def __init__(
        self,
        shapefile_path="terrain/Riparia_HUC12_2011.shp",
        target_lat=42.2156131,
        target_lon=-79.8342163,
        initial_rabbits=50,
        initial_foxes=10,
        grass_regrowth_rate=0.1,
        grass_max_biomass=10.0,
        energy_per_grass=8,
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
        self.step_count = 0

        # Store parameters
        self.grass_regrowth_rate = grass_regrowth_rate
        self.grass_max_biomass = grass_max_biomass
        self.energy_per_grass = energy_per_grass
        self.energy_from_rabbit = energy_from_rabbit
        self.reproduction_threshold = reproduction_threshold
        self.reproduction_cost_fox = reproduction_cost_fox
        self.reproduction_cost_rabbit = reproduction_cost_rabbit
        self.min_lifespan = min_lifespan
        self.max_lifespan = max_lifespan
        self.senescence_rate = senescence_rate
        self.initial_offspring_energy = 10

        logging.info("Initializing model with seed=%s", seed)

        # ------------------- Load the shapefile -------------------
        logging.info("Loading shapefile from %s", shapefile_path)
        lc_gdf = gpd.read_file(shapefile_path)
        lc_gdf = lc_gdf.to_crs("EPSG:32617")
        self.space_crs = "EPSG:32617"

        # ------------------- Find the HUC12 polygon containing the target point -------------------
        target_point = Point(target_lon, target_lat)
        target_point_utm = (
            gpd.GeoSeries([target_point], crs="EPSG:4326")
            .to_crs(self.space_crs)
            .iloc[0]
        )
        containing = lc_gdf[lc_gdf.contains(target_point_utm)]
        if containing.empty:
            logging.warning(
                "Target point not inside any HUC12 polygon. Using first polygon."
            )
            self.world_boundary = lc_gdf.geometry.iloc[0]
        else:
            self.world_boundary = containing.geometry.iloc[0]
            logging.info(
                "Found HUC12 polygon with index %s as world boundary.",
                containing.index[0],
            )

        # ------------------- Filter grassland polygons -------------------
        possible_grass_cols = [
            "GRASSLAND",
            "PASTURE",
            "HAY",
            "NLCD71",
            "NLCD81",
            "NLCD82",
        ]
        available_cols = [col for col in possible_grass_cols if col in lc_gdf.columns]
        logging.info("Available grassland columns: %s", available_cols)

        if available_cols:
            grass_mask = False
            for col in available_cols:
                values = lc_gdf[col]
                if values.dtype == "object":
                    values = values.str.replace("%", "").astype(float)
                grass_mask = grass_mask | (values > 20)  # threshold
            self.grassland_polygons = lc_gdf[grass_mask]
        else:
            logging.warning(
                "No grassland columns found – using all polygons for grass placement"
            )
            self.grassland_polygons = lc_gdf

        logging.info(
            "Using %s polygons for grass placement.", len(self.grassland_polygons)
        )

        # ------------------- Create GeoSpace -------------------
        self.space = mg.GeoSpace(crs=self.space_crs)

        # ------------------- Create Grass Raster (as numpy array) -------------------
        self.cell_size = 10
        bounds = self.world_boundary.bounds
        self.grass_bounds = bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        cols = int(np.ceil(width / self.cell_size))
        rows = int(np.ceil(height / self.cell_size))
        self.grass_rows = rows
        self.grass_cols = cols
        logging.info(
            "Creating grass raster of size %s x %s cells (cell size %s m)",
            rows,
            cols,
            self.cell_size,
        )

        # Affine transform for world ↔ array conversion
        self.grass_transform = Affine.translation(bounds[0], bounds[3]) * Affine.scale(
            self.cell_size, -self.cell_size
        )

        # Prepare shapes: each grassland polygon contributes value 1
        shapes = [(geom, 1) for geom in self.grassland_polygons.geometry]

        # Rasterize to create a mask (1 where grassland, 0 elsewhere)
        grass_mask = rasterio.features.rasterize(
            shapes,
            out_shape=(rows, cols),
            transform=self.grass_transform,
            fill=0,
            dtype=np.uint8,
        )

        # Convert mask to biomass array
        self.grass_biomass = grass_mask.astype(float) * self.grass_max_biomass

        # Helper: random point anywhere inside world_boundary
        def random_point_in_boundary():
            minx, miny, maxx, maxy = self.world_boundary.bounds
            while True:
                p = Point(
                    self.random.uniform(minx, maxx), self.random.uniform(miny, maxy)
                )
                if self.world_boundary.contains(p):
                    return p

        # ------------------- Create rabbits and foxes -------------------
        logging.info(
            "Creating %s rabbits and %s foxes.", initial_rabbits, initial_foxes
        )
        for _ in range(initial_rabbits):
            pt = random_point_in_boundary()
            rabbit = Cottontail(model=self, geometry=pt, crs=self.space_crs)
            self.space.add_agents(rabbit)

        for _ in range(initial_foxes):
            pt = random_point_in_boundary()
            fox = Red_Fox(model=self, geometry=pt, crs=self.space_crs)
            self.space.add_agents(fox)

        # Data collector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Cottontail Population": lambda m: len(
                    [a for a in m.space.agents if isinstance(a, Cottontail)]
                ),
                "Red Fox Population": lambda m: len(
                    [a for a in m.space.agents if isinstance(a, Red_Fox)]
                ),
                "Average Grass Biomass": lambda m: m.grass_biomass.mean(),
            }
        )

        logging.info(
            "Model initialization complete. Total agents: %s", len(self.space.agents)
        )

    # ---------- Grass methods ----------
    def _point_to_raster_indices(self, point: Point):
        """Convert a Point (in CRS units) to (row, col) indices in the grass array."""
        col = int((point.x - self.grass_bounds[0]) / self.cell_size)
        row = int((self.grass_bounds[3] - point.y) / self.cell_size)
        return row, col

    def get_grass_biomass_at(self, point: Point) -> float:
        """Return grass biomass at the given point (0 if outside raster)."""
        r, c = self._point_to_raster_indices(point)
        if 0 <= r < self.grass_rows and 0 <= c < self.grass_cols:
            return self.grass_biomass[r, c]
        return 0.0

    def eat_grass_at(self, point: Point) -> float:
        """
        Eat one unit of grass from the cell containing the point.
        Returns the energy gained (energy_per_grass if biomass > 0, else 0).
        """
        r, c = self._point_to_raster_indices(point)
        if 0 <= r < self.grass_rows and 0 <= c < self.grass_cols:
            if self.grass_biomass[r, c] > 0:
                self.grass_biomass[r, c] -= 1
                return self.energy_per_grass
        return 0

    def regrow_grass(self):
        """Apply regrowth to all cells."""
        self.grass_biomass += self.grass_regrowth_rate * self.grass_max_biomass
        self.grass_biomass = np.minimum(self.grass_biomass, self.grass_max_biomass)

    # ---------- Step ----------
    def step(self):
        self.step_count += 1

        # Grass regrowth
        self.regrow_grass()

        # Animal steps
        agent_list = list(self.space.agents)
        self.random.shuffle(agent_list)
        for agent in agent_list:
            agent.step()

        self.datacollector.collect(self)

        # Log every 10 steps
        if self.step_count % 10 == 0:
            rabbits = len([a for a in self.space.agents if isinstance(a, Cottontail)])
            foxes = len([a for a in self.space.agents if isinstance(a, Red_Fox)])
            avg_grass = self.grass_biomass.mean()
            logging.info(
                "Step %s: rabbits=%s, foxes=%s, avg_grass=%.2f",
                self.step_count,
                rabbits,
                foxes,
                avg_grass,
            )
