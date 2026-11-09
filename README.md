# SoccerHub: Natural Language to SQL

A Python experiment comparing two local language models on translating English
questions into MySQL queries. It uses LangChain and Ollama to generate SQL,
executes each query against SoccerHub, and checks the numeric result against a
reference query.

Built for CS 4354 Homework 2, Part 2.

## How it works

```text
Question + database schema
          |
          v
LangChain -> Ollama -> local model
          |
          v
Generated SQL -> MySQL -> compare with reference result -> results.csv
```

The script evaluates seven questions with each model, producing 14 result rows.
The questions cover team and match counts, unattached players, player
appearances, and Real Madrid's total goals as the home or away team.

## Recorded results

| Model | Correct results | Accuracy | SQL execution errors |
|---|---:|---:|---:|
| `gpt-oss:20b` | 7/7 | 100% | 0 |
| `llama3.1:8b` | 3/7 | 42.9% | 4 |

Llama used the reserved identifier `match` without backticks in three queries.
Another query referenced `player.playerId` without including that table in its
FROM clause. The generated queries and their errors are preserved in
`results.csv`; `writeup.txt` describes the observations.

These results come from the final program's recorded run at temperature 0 on
this small dataset. A later run can produce different SQL or results depending
on the model version and local environment.

## Run locally

Prerequisites: Python 3.12, MySQL 8.0, and a running Ollama installation.
Inference is local; `gpt-oss:20b` can require substantial memory and take several
minutes on a laptop.

1. Create the sample `soccerhub` database using
   [`database/soccerhub_setup.sql`](database/soccerhub_setup.sql). The script
   creates four tables and inserts the sample data, so use an empty database.
2. Install the Python packages and download both models:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ollama pull gpt-oss:20b
   ollama pull llama3.1:8b
   ```

3. Set `DB_URI` in `nl2sql_compare.py` for your local MySQL connection. The
   supplied URI contains a placeholder password. Use the
   `mysql+mysqlconnector` driver and URL-encode special characters in the
   password when constructing a URI.
4. Run the program:

   ```powershell
   .\.venv\Scripts\python.exe nl2sql_compare.py
   ```

Each run writes `results.csv` in the repository root. The database used in the
recorded experiment was a copy of the Part 1 dataset, later checked against the
original database to confirm matching data.

## Files

| File | Purpose |
|---|---|
| `nl2sql_compare.py` | Complete question-to-SQL execution and evaluation pipeline |
| `expected.jsonl` | One canonical reference query per question |
| `results.csv` | Recorded SQL, numeric results, reference values, errors, and correctness |
| `writeup.txt` | Short observations from the recorded run |
| `database/soccerhub_setup.sql` | Table definitions and sample data |
| `requirements.txt` | Python dependencies |

The dataset contains 6 teams, 14 players, 8 matches, and 28 appearances. The
program expects each generated query to return exactly one numeric value.
Integer reference values require exact equality; other values use an absolute
tolerance of `0.000001`.
