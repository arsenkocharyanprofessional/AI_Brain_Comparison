# Vault Wars build steps

Rule: do one step, check its "Done when", tick it, then move on. A gate must pass before the next stage starts.

DEMO MINIMUM: Stages 1 to 6, plus Stage 8, plus the Replay viewer (Stage 4 and 5.7) and the Results dashboard (9.2). Everything else is extra and follows the cut list in CLAUDE.md.

## Stage 0: Setup
* [x] 0.1 Repo with folders: `engine/`, `brains/`, `experiments/`, `app/`, `data/`, `docs/`, `tests/`. Python venv outside OneDrive and listed in .gitignore, requirements.txt. Done when: `pip install -r requirements.txt` works on a fresh clone.
* [x] 0.2 Put the project description PDF and the Deliverable 2 docx in `docs/`. Done when: CLAUDE.md links resolve.

## Stage 1: Map and layout
* [x] 1.1 Download and cache the Yerevan drive network at 2, 2.5, 3 km. Done when: 3 cached graph files are committed, load offline, and node and edge counts are printed.
* [x] 1.2 Clean the graph: keep the largest strongly connected part, edge lengths in meters. Done when: every node can reach every other node.
* [x] 1.3 Place 5 vaults on a ring (at least 800 m apart, well connected nodes). Done when: a plot shows 5 vaults and the distance check passes.
* [x] 1.4 Place 40 ATMs and 2 shops. Done when: plot shows them mixed across the map.
* [x] 1.5 Generate and save 30 seeded layouts (10 per map size). No balance check; fairness comes from seat rotation. Done when: same seed gives the same layout; 30 layouts saved and load back.

## Stage 2: Engine core (no combat yet)
* [x] 2.1 Game state classes: Bank, Vault, ATM, Ultima, Shop. Done when: a state can be created from a layout file.
* [x] 2.2 Tick loop: day and week clock, simultaneous resolution order, ATM filling with one shared rate set per layout, day end teleport and reset. Done when: a 5 day run with idle Ultimas finishes and ATM cash looks right.
* [ ] 2.3 Movement along edges with speed and cargo slowdown. Done when: an Ultima driven along a fixed path arrives at the expected tick.
* [ ] 2.4 Collect and deliver cash. Done when: a scripted Ultima empties an ATM and the vault grows by that amount.
* [ ] 2.5 Fog: known map per bank, vision circle, shared bank knowledge, ATM discovery. Done when: a bank's known map grows as its Ultimas drive.
* [ ] 2.6 Event log and replay file writer. Done when: one game produces a replay file we can read back.

## Stage 3: Shared base and first brains
* [ ] 3.1 Brain interface: brain gets its bank's view only, returns one action per Ultima per tick. Done when: a do nothing brain runs a full game.
* [ ] 3.2 A* on the known map with a node counter. Done when: routes match NetworkX shortest paths on the full map.
* [ ] 3.3 Frontier exploration split among teammates. Done when: most of the map is known by day 3 (measure it).
* [ ] 3.4 ATM assignment as CSP (MRV, forward checking). Done when: every known ATM is assigned and loads are balanced.
* [ ] 3.5 Visit order: Nearest Neighbor plus 2 opt. Done when: 2 opt never makes a tour longer.
* [ ] 3.6 Fill rate learning. Done when: estimates approach true rates over the week (logged).
* [ ] 3.7 Planner and Greedy brains. Done when: 5 Planners play a full week.
* [ ] GATE A: full game runs, runtime per game measured, exploration by day 3 checked, Planner beats Greedy.

## Stage 4: First viewer
* [ ] 4.1 Small Python backend that serves replay files. Done when: browser fetches a replay as JSON.
* [ ] 4.2 Leaflet map with roads, vaults, ATMs, shops. Done when: layout shows on the real map.
* [ ] 4.3 Animated Ultimas with play, pause, speed, scrub. Done when: a full replay plays smoothly.
* [ ] 4.4 Live cash chart and event list. Done when: chart matches final scores.

## Stage 5: Combat, repair, shops
* [ ] 5.1 Line of fire along streets (road path at most 50 m, straightness ratio at least 0.95, any number of edges), safe zones. Done when: unit tests cover same edge, straight crossing, curved edge and corner cases.
* [ ] 5.2 Shooting, linear hit chance by distance, damage = firepower minus armor (minimum 5), ammo, reload, one action per tick. Done when: a scripted duel ends as expected on average.
* [ ] 5.3 Death, looting, respawn. Done when: loot and respawn numbers match the rules in tests.
* [ ] 5.4 Repair and ammo refill at the vault. Done when: parked Ultima gains 4 HP per tick and pays for ammo.
* [ ] 5.5 Default fight rule in the shared base (shoot back, flee at low HP). Done when: Planners survive attacks more often than standing still.
* [ ] 5.6 Shops: upgrades, buy rule, reserve. Done when: brains buy early and stop near Friday.
* [ ] 5.7 Viewer: HP, ammo, cargo bars, shots and deaths shown. Done when: a fight is clearly visible in the replay.
* [ ] GATE B: fights happen often enough to matter (count them per game).

## Stage 6: Smart brains (one at a time, each ends with a test game vs 4 Planners)
* [ ] 6.1 Hunter: target prediction, interception with A*, expected value attack check.
* [ ] 6.2 Tactician: Expectimax with chance nodes, 2 vs 2 help, node limit.
* [ ] 6.3 Strategist: Bayesian strength per bank, A* cost penalty, payoff tables, Friday boldness.
* [ ] 6.4 Convoy: courier transfers, meeting points, escorts, cash rescue.
* [ ] 6.5 Decision log with reasons for every brain. Done when: the viewer shows why an Ultima did what it did.

## Stage 7: Balancing
* [ ] 7.1 Self play: Planner in all 5 seats; seat results should be close.
* [ ] 7.2 Tune the open numbers (fight frequency, shop prices, thinking limit).
* [ ] GATE C: rules frozen. No rule changes after this.

## Stage 8: Experiments
* [ ] 8.1 Batch runner: 30 layouts x 5 rotations = 150 games, parallel, seeded. Each layout gets a seeded random base order of brains, then its 5 cyclic rotations.
* [ ] 8.2 Metrics from event logs into one table.
* [ ] 8.3 Statistics: summary stats, confidence intervals, Friedman, Wilcoxon, who robs whom.
* [ ] 8.4 Charts for the report and dashboard.

## Stage 9: App polish
* [ ] 9.1 Setup screen (pick layout, size, seed, seats, number of Ultimas per bank, vision range).
* [ ] 9.2 Results dashboard.
* [ ] 9.3 Fog view per bank.
* [ ] 9.4 Brain guide.
* [ ] 9.5 Heatmaps, follow an Ultima (only if time allows).
* [ ] 9.6 Batches from the app, minimal: pick layouts and number of games, run the batch runner, show progress.

## Stage 10: Demo and report
* [ ] 10.1 Split presenting parts among the 4 members.
* [ ] 10.2 Demo script: one replay, one fight explained, the dashboard, the key finding.
* [ ] 10.3 Report (3 to 5 pages) and run instructions in README.
* [ ] 10.4 Full rehearsal on a clean clone.
