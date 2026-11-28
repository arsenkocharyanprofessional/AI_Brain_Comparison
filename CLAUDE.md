# Vault Wars: project guide for Claude

CS246/346 Artificial Intelligence group project at AUA.
Team: Arsen Kocharyan, Vahan Tonoyan, Mery Harutyunyan, Ani Sahakyan.

## Source of truth
1. This file (latest decisions). If anything here disagrees with another document, this file wins.
2. `docs/deliverable2.docx` (what we promised the professor)
3. `docs/project_description.pdf` (assignment rules and rubrics)
4. `STEPS.md` (build steps and progress; tick items off as they are done)

When a rule or number changes during the build, update this file in the same step.

## How to work with us
* Work in small steps. Finish one step from STEPS.md, show it working, then stop and wait.
* Explain reasoning slowly and simply. One decision at a time, never bundle several.
* Never change a locked rule or a brain's personality without asking first.
* Code: clarity and readability are a must. Small functions, clear names, short comments where the logic is not obvious.
* Writing: never use dashes of any kind (em dashes or hyphens used as pauses). Plain, human tone.
* Ignore calendar dates. Track progress by steps only.
* Git: one pull request per stage into main, but still stop after every step. No AI attribution anywhere: no co-author lines, no tool names or session links in commits, branches, pull requests or comments. Commits are authored by Arsen.

## Assignment rules (do not break)
One problem, at least 2 course approaches, interactive app that visualizes them, experimental comparison with at least 3 metrics on at least 30 instances. No ML, neural nets or RL.

## The game (all numbers are defaults to tune)
* 5 banks, one per brain, on the real central Yerevan road network (OSMnx drive network, cached offline; traffic rules ignored: every street is two way, so the distance from A to B always equals B to A). Map sizes: squares around Republic Square with half side 2, 2.5 and 3 km (so the 2 km map is 4 x 4 km; corners reach about 2.8 km from the center). Vault ring and fairness checks work inside that square. Credit "Map data from OpenStreetMap contributors".
* Each bank: 1 vault, 8 ATMs, 4 armored robots called Ultimas. Ultimas collect cash from own ATMs and deliver it to own vault. ATMs and vaults cannot be attacked; only cash on the road is at risk. Winner: most vault cash after Friday.
* Layout generator: vaults on a ring around the center (ring radius = half the map's half side: 1000, 1250, 1500 m), 5 evenly spaced ideal spots turned by a seeded random angle, each vault snapped to an intersection with 3 or more neighboring intersections within 250 m of its ideal spot, at least 800 m apart, 100 m safe zone. ATMs spread across the whole map, mixed with rivals: 40 random spots spread evenly over the area, each snapped to an intersection within 150 m, outside safe zones, at least 200 m apart, owners shuffled. 2 shops on opposite sides of the center on an inner ring (half the vault ring radius), well connected, safe zones not overlapping vault safe zones. No per layout balance check: fairness comes from seat rotation (every brain plays every seat on every layout, and all results are averages over the rotations).
* ATMs: hidden fill rate per ATM, cap 300, pauses when full. Per layout, draw one set of 8 rates, uniform 0.4 to 1.2 (mean 0.8 per tick), and give every bank that same set, shuffled across its own ATMs, so all banks have identical income potential. Rates stay fixed all week. Mean may be tuned at Gate A. No filling at night, cash kept overnight. Monday starts at 0.
* Time: Monday to Friday, 600 ticks per day. Day end at tick 600: every Ultima is teleported home, fully repaired and reloaded, and any cash it still carries is lost. Brains must plan to be home before the day ends. Starting vault cash 1000. Memory kept across days.
* Fog: map unknown at start (roads, own ATMs, shops must be explored; brains plan only on roads their bank has seen) plus a 150 m vision circle. An intersection is known once seen; a street is known once both its ends are known. Vision is checked at the end of every tick (and at game start, from the vault). Instant sharing inside a bank. Enemy sightings kept as fading beliefs.
* Information: own and rival vault locations known. Bank knows it owns 8 ATMs, not where. Seeing an ATM reveals its owner. Own ATM balance known only when at the ATM. Rival ATM balance never visible. Enemies in vision show position, bank, HP, rough cargo (empty at 0, light below 300, heavy from 300; counted in cash, so it still works after cargo upgrades).
* Ultima: speed about 25 m per tick, falling linearly with cargo to 70 percent at full cargo, never block each other. Unused distance at an intersection carries on to the next street in the same tick. Any Ultima can turn around anywhere, mid street included. HP 100, armor 5, firepower 25. Damage per hit = attacker firepower minus target armor, minimum 5 (defaults give 20). Ammo 12, reload 2 ticks, range 50 m. Hit chance falls linearly from 90 percent at 0 m to 40 percent at 50 m. Cargo 600. Vision 150 m.
* One action per tick per Ultima: move, shoot, collect at an own ATM, or hand over cash. Never two. Collecting takes as much cash as fits in free cargo space, only at own ATMs. Vault drop off is automatic when an Ultima ends a tick standing at its own vault, and costs no action. A handover costs only the giver's action; the receiver can still act that tick.
* Ticks are simultaneous: every Ultima decides from the same snapshot. Each tick starts with ATM filling. Resolution order inside a tick: shots, then handovers, then movement, then collection, then automatic vault drop off. The 30 m handover check uses positions at the start of the tick. If two Ultimas kill each other in the same tick, nobody loots and both cargos are lost. If several Ultimas hit one target in the same tick, the one with most total damage loots.
* Shooting only along a street: a shot is allowed when the road path between shooter and target is at most 50 m and the straight line distance is at least 0.95 of that path, across any number of edges. Corners and curves block naturally. No shooting in safe zones.
* Vault: drop off cash, ammo refill at 1 cash per shot, repair 4 HP per tick while parked (can leave anytime).
* Death: killer gets 60 percent of victim's cargo (capped by free space), rest lost; with several shooters the top damage dealer loots. Respawn at vault after 40 ticks, full HP and ammo, empty cargo.
* Cash transfer: two Ultimas of the same bank within about 30 m hand over cash in one tick, limited by receiver capacity. Only Convoy uses it.
* Shops: 6 upgrades (armor, firepower, ammo capacity, speed, cargo, vision) x 3 tiers, about 150 to 600. Bought per Ultima from vault cash, applied when that Ultima visits a shop, lasts all week. Vault reserve 300. Buy rule for all brains: buy only if expected gain before Friday beats price plus detour time.
* Removed: explosives, roadworks, road blocks, D* Lite, Minimax.

## Brains: shared base, different personality
Every brain = Planner (shared base) + one course method. They differ only in how they deal with rivals and what they buy.

* Shared base: frontier exploration split among teammates; ATM to Ultima assignment as CSP with MRV and forward checking (Auction as fallback); Nearest Neighbor plus 2 opt for visit order; A* on the known map with straight line heuristic; default fight rule (shoot back, flee home at low HP); ATM fill rate learning.
* Planner (control): shared base only, never attacks, buys cargo and speed.
* Convoy (multi robot coordination): a courier collects cash from teammates via transfers and shuttles it home, escorts through dangerous streets, searches the known map for meeting points. Cash rescue: when a Convoy Ultima is attacked it drives toward the nearest teammate, that teammate drives toward it, and the cash is handed over. Buys armor and speed (plus cargo for the courier). Key stat: cash saved by emergency handovers.
* Hunter (informed search, expected value): one dedicated hunter predicts loaded rivals' way home and intercepts with A*, attacks when expected gain beats cost; the other 3 collect but may take very good chances. Judges targets in the moment, no memory of banks. Buys firepower and ammo for the hunter.
* Tactician (Expectimax): never seeks fights; when in one, Expectimax depth about 3 to 4 with chance nodes for hits; nearest teammate joins for 2 vs 2. Buys armor and firepower. Rivals are modeled as a probability distribution over actions based on the default fight rule (mostly shoot back if in line of fire, flee at low HP, small chance of other moves). No min nodes. State this opponent model as an assumption in the report.
* Strategist (game theory, the calculating opportunist): estimates each bank's fight strength with Bayesian updating from every fight it sees (starts at 50/50); raises A* street costs where strong banks roam; attacks loaded Ultimas of weak banks it happens to meet when expected value is positive, using small attack or avoid payoff tables; never chases; bolder on Friday (backward induction); reactive buying. Differs from D2 on purpose; explain in report (see Report notes).
* Greedy: only used in the Gate A sanity check showing the Planner beats it (games with 5 Planners and games with 5 Greedys on the same layouts, no combat yet, paired comparison of cash). No module ablation of the Planner. Goes to the nearest known own ATM, collects, goes home when cargo is full or the day is ending; explores the nearest unknown area when no own ATM is known. Uses the default fight rule, never buys.
* Brain interface: each tick a brain gets only its bank's view (engine/view.py: clock, own vault and Ultimas, known map, ATMs and shops seen, all vault spots, own ATM cash while standing at it, enemies in vision) and returns one action per Ultima (move, collect, or wait). All 5 views are built from the same moment before any brain decides. An order that breaks the rules (another bank's Ultima, unseen intersections, collecting away from an own ATM) stops the game with an error, because it is always a bug. One brain object plays one bank all week, so its memory lasts across days.
* Code layout: each brain lives in its own file, and every brain writes a readable decision log, so each team member can present a part.

## Experiments
* 30 layouts: 10 each at 2, 2.5, 3 km. Each played 5 times: for each layout pick a random (seeded) base order of the 5 brains, then play its 5 cyclic rotations. Every brain sits in every seat on every layout, and neighbors vary across layouts. 150 games. Same seeds across rotations, separate random streams.
* Thinking limit, counted in search nodes: each brain's own method (Hunter interception search, Tactician Expectimax, Strategist expected value and route penalty calculations, Convoy meeting point search) gets the same per decision budget. The shared base gets its own fixed cap, identical for all brains. All nodes are recorded either way, and time too, so the thinking cost metric shows both parts. For A*, one node is one intersection taken from the open list and expanded.
* Experiments always use the default number of Ultimas (4) and vision (150 m).
* Self play check: Planner in all 5 seats, for balance.
* Fight definition: a fight is per pair of Ultimas from different banks. It starts at the first shot between them and ends at a death or after 20 ticks with no shots between them. Death: the killer wins. Otherwise whoever left line of fire first loses; if neither did, it is a draw. Fights are also counted per bank pair for the who robs whom matrix.
* Metrics: final vault cash and rank; cash flow (collected, stolen, lost); fight record; thinking cost; cash by day. Plus logged extras: exploration progress, ATM time full, cash on the road, personality stats, fill rate estimate accuracy, shop spend vs gain, fight heatmaps, who robs whom.
* Statistics: mean, min, max, confidence intervals, Friedman then Wilcoxon signed rank on 30 paired layout averages.
* Key question: do aggressive brains thrive on crowded (small) maps and peaceful ones on quiet (large) maps?

## App
Replay based: simulate in the background, then watch. Python backend, browser frontend with Leaflet map and charts.
Screens by priority: Replay viewer (map, Ultimas with HP, cargo, ammo bars, events, live cash chart, decision log with reasons, playback controls), Results dashboard, then Fog view per bank, heatmaps, Brain guide, Follow an Ultima, then batches from the app.
Setup screen options: layout, map size, seed, seats, number of Ultimas per bank, vision range (promised in D2; they are config values anyway).
Batches from the app, minimal version: pick layouts and number of games, run the existing batch runner, show progress.

## Tech
Python engine: OSMnx, NetworkX, deterministic, headless, parallel batches, writes replay and event log files. Small Python backend serves the web app.
Python 3.12. Code lives only in the GitHub repo (cloned locally to C:\dev\vault-wars); the old OneDrive folder is no longer maintained. The venv lives outside OneDrive and is in .gitignore. Cached map files are committed so every teammate uses the exact same graph.

## Open items (decide during the build, one at a time)
CSP vs Auction for assignment, exploration speed by day 3, fight frequency (revisit vault ring size at Gate B: Arsen worried vaults are too far apart; option is one fixed 1000 m ring for all map sizes), shop prices, exact thinking limit, real map speed.

## Cut order if the work runs long
Heatmaps and follow mode, then Convoy escorts (keep courier), then simplify Strategist memory, then batches from the app (minimal version). The demo minimum in STEPS.md is never cut.

## Deliverables still ahead
* Deliverable 3, live demo (50 percent): working app, all brains on the same instances, at least 3 metrics, usable interface, every member explains a part. Rubric: correctness 30, comparison 25, visualization 20, understanding 15, interface 10.
* Deliverable 4, report (15 percent): 3 to 5 pages plus code and run instructions. At least 30 instances of varying difficulty, tables, graphs, summary statistics, fair setup, strengths, weaknesses, trends, limitations. Rubric: design 25, results 30, analysis 35, quality 10.

## Report notes (collect here during the build)
* Strategist: we first designed tit for tat with forgiveness (Axelrod and Hamilton, 1981). In that version only the Hunter ever started fights, so the punishment logic would almost never trigger and could not be tested. We changed it to the opportunist so there is a second fight initiator. Keep Axelrod only as the "considered" reference.
* New references for the Strategist: Bayesian estimation and backward induction (Russell and Norvig, AIMA, probabilistic reasoning and game theory chapters; Osborne, An Introduction to Game Theory). Verify exact editions before citing.
* Tactician opponent model is an assumption (see Brains).
* Limitations: mention any remaining seat effects after the rotation fix.
* Change from D2: D2 promised a layout balance check (workload and shop distance within about 10 percent). We dropped it because it is redundant: full seat rotation already gives every brain identical conditions on every layout, and every reported result is an average over the rotations. (Random owners alone gave 1.2 to 2.3 times workload differences between seats; rotation cancels this.) State this in the report.
