# Combinatorial Parameters Database

This repository contains a structured database of combinatorial parameters, classes, relationships, and values, organized for mathematical research and reference.

Browse the database [here](https://obousquet.github.io/Combinatorial-Parameters).

## Structure
- `data/classes/` — Set families (possibly parameterized)
- `data/parameters/` — Parameters measuring the size of set families
- `data/relationships/` — Relationships between parameters
- `data/values/` — Values assigned to parameters for specific classes

Each subdirectory contains:
- A `schema.json` file describing the structure and fields for entries
- Generated JSON files for each entry

## Editing and Contributing

### Step-by-step Contribution Guide

1. **Clone the repositories**
	- First, clone the main database editor repository:
	  ```bash
	  git clone https://github.com/obousquet/math_database
	  ```
	- Then, clone this data repository:
	  ```bash
	  git clone https://github.com/obousquet/Combinatorial-Parameters
	  ```

2. **Install requirements**
	- In the `math_database` repository, install the required Python packages:
	  ```bash
	  cd math_database
	  pip install -r requirements.txt
	  ```

3. **Run the local editing server**
	- Start the server, pointing it to the data directory of this repository:
	  ```bash
	  python3 server.py --data-dir=<path to Combinatorial-Parameters/data>
	  ```

4. **Edit the database locally**
	- Open your browser and go to [http://localhost:8080](http://localhost:8080)
	- You can now edit, add, or update entries in the database. All changes will be saved in the `data` directory of the `Combinatorial-Parameters` repository.

5. **Contribute your changes**
	- When you are ready, commit your changes in the `Combinatorial-Parameters` repository and make a pull request to share your updates.

For more details, scripts, and best practices, see the documentation in [math_database](https://github.com/obousquet/math_database).

## License
See the repository for licensing information.
