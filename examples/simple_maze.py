from arcengine import (
    ARCBaseGame,
    BlockingMode,
    Camera,
    GameAction,
    InteractionMode,
    Level,
    Sprite,
)

# Create sprites dictionary with all sprite definitions
sprites = {
    "player": Sprite(
        pixels=["R"],  # Red player
        name="player",
        blocking=BlockingMode.BOUNDING_BOX,
        interaction=InteractionMode.TANGIBLE,
    ),
    "exit": Sprite(
        pixels=["b"],  # Blue exit
        name="exit",
        blocking=BlockingMode.BOUNDING_BOX,
        interaction=InteractionMode.TANGIBLE,
    ),
    "maze_1": Sprite(
        pixels=[
            "BBBBBBBB",  # Row 0
            "B...B..B",  # Row 1
            "B.B.B.BB",  # Row 2
            "B.B....B",  # Row 3
            "B.BBBB.B",  # Row 4
            "B....B.B",  # Row 5
            "BBBB...B",  # Row 6
            "BBBBBBBB",  # Row 7
        ],
        name="maze_1",
        blocking=BlockingMode.PIXEL_PERFECT,
        interaction=InteractionMode.TANGIBLE,
        layer=-1,  # Render below player and exit
    ),
    "maze_2": Sprite(
        pixels=[
            "BBBBBBBBBBBB",  # Row 0
            "B...B......B",  # Row 1
            "B.B.B.BBBB.B",  # Row 2
            "B.B......B.B",  # Row 3
            "B.BBBBBB.B.B",  # Row 4
            "B......B.B.B",  # Row 5
            "BBBBBB.B.B.B",  # Row 6
            "B....B.B.B.B",  # Row 7
            "B.BB.B.B.B.B",  # Row 8
            "B.B..B...B.B",  # Row 9
            "B...BBBBBB.B",  # Row 10
            "BBBBBBBBBBBB",  # Row 11
        ],
        name="maze_2",
        blocking=BlockingMode.PIXEL_PERFECT,
        interaction=InteractionMode.TANGIBLE,
        layer=-1,  # Render below player and exit
    ),
}

# Create levels array with all level definitions
levels = [
    # Level 1
    Level(
        sprites=[
            sprites["maze_1"].clone(),
            sprites["player"].clone().set_position(1, 1),  # Start position
            sprites["exit"].clone().set_position(6, 6),  # Exit position
        ],
        grid_size=(8, 8),
    ),
    # Level 2
    Level(
        sprites=[
            sprites["maze_2"].clone(),
            sprites["player"].clone().set_position(1, 1),  # Start position
            sprites["exit"].clone().set_position(10, 10),  # Exit position
        ],
        grid_size=(12, 12),
    ),
]

BACKGROUND_COLOR = "W"

PADDING_COLOR = "G"


class SimpleMaze(ARCBaseGame):
    """A simple maze game where the player navigates to the exit."""

    def __init__(self) -> None:
        """Initialize the SimpleMaze game."""
        # Create camera with background and padding colors
        camera = Camera(background=BACKGROUND_COLOR, letter_box=PADDING_COLOR)

        # Initialize the base game
        super().__init__(game_id="simple_maze", levels=levels, camera=camera)

    def step(self) -> None:
        """Step the game forward based on the current action."""
        # Handle movement based on action ID
        dx = 0
        dy = 0
        if self.action.id == GameAction.ACTION1:  # Move Up
            dy = -1
        elif self.action.id == GameAction.ACTION2:  # Move Down
            dy = 1
        elif self.action.id == GameAction.ACTION3:  # Move Left
            dx = -1
        elif self.action.id == GameAction.ACTION4:  # Move Right
            dx = 1

        collided = self.try_move("player", dx, dy)

        # Check if player collided with exit
        if collided and any(sprite.name == "exit" for sprite in collided):
            if self.is_last_level():
                # All levels completed, set game state to WIN
                self.win()
            else:
                self.next_level()

        self.complete_action()
