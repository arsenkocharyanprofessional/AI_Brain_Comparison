"""Game numbers in one place. Every value comes from CLAUDE.md.

All numbers are defaults that we may tune later; change them only here.
"""

# Banks and robots
NUM_BANKS = 5
ULTIMAS_PER_BANK = 4          # setup option; experiments always use 4
STARTING_VAULT_CASH = 1000

# Time
TICKS_PER_DAY = 600
DAYS_PER_WEEK = 5             # Monday to Friday

# ATMs
ATM_CAP = 300
FILL_RATE_MIN = 0.4           # cash per tick
FILL_RATE_MAX = 1.2

# Ultima
SPEED_M_PER_TICK = 25
FULL_CARGO_SPEED_SHARE = 0.7  # speed at full cargo
MAX_HP = 100
ARMOR = 5
FIREPOWER = 25
MIN_DAMAGE = 5
MAX_AMMO = 12
RELOAD_TICKS = 2
SHOT_RANGE_M = 50
CARGO_CAPACITY = 600
VISION_M = 150                # setup option; experiments always use 150
