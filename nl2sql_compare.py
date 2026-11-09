"""CS 4354 Homework 2 Part 2.

Install: pip install langchain langchain-ollama sqlalchemy mysql-connector-python
Set DB_URI below for your soccerhub database, start Ollama, then run this file.
"""
import csv
import json
import re
from decimal import Decimal
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from sqlalchemy import create_engine, text

# Configuration
DB_URI = "mysql+mysqlconnector://root:YOUR_PASSWORD@127.0.0.1:3306/soccerhub"
MODELS = ["gpt-oss:20b", "llama3.1:8b"]
TEMPERATURE = 0
BASE = Path(__file__).resolve().parent
EXPECTED_FILE = BASE / "expected.jsonl"
RESULTS_FILE = BASE / "results.csv"
EPSILON = Decimal("0.000001")

QUESTIONS = [
    "How many teams are in the database?",
    "How many players are currently unattached (teamId is NULL)?",
    "How many matches have been scheduled in total?",
    "How many matches have not yet been played (both scores not recorded)?",
    "How many distinct players have at least one appearance?",
    "How many players have participated in two or more appearances?",
    "What is the total number of goals scored by Real Madrid across all matches (home plus away)?",
]

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Translate the question into MySQL SQL using this schema:\n{schema}\n"
     "Output one top-level SELECT statement returning one number. "
     "Output SQL only, without explanations or Markdown."),
    ("human", "{question}"),
])


def clean_sql(output):
    output = re.sub(r"```(?:mysql|sql)?\s*", "", output, flags=re.IGNORECASE)
    output = output.replace("```", "").strip()
    return output.split(";", 1)[0].strip()


def get_number(engine, sql):
    with engine.connect() as connection:
        row = connection.execute(text(sql)).one()
    if len(row) != 1 or not isinstance(row[0], (int, float, Decimal)):
        raise ValueError("The query must return exactly one numeric value.")
    return row[0]


def is_correct(actual, expected):
    actual, expected = Decimal(str(actual)), Decimal(str(expected))
    if expected == expected.to_integral_value():
        return actual == expected
    return abs(actual - expected) <= EPSILON


def main():
    engine = create_engine(DB_URI)
    try:
        expected = {}
        with EXPECTED_FILE.open(encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    entry = json.loads(line)
                    expected[entry["qid"]] = entry["sql"]

        with engine.connect() as connection:
            schema = "\n".join(
                connection.execute(text(f"SHOW CREATE TABLE `{table}`")).one()[1]
                for table in ["Team", "Player", "Match", "Appearance"]
            )

        columns = ["qid", "prompt", "model", "generated_sql", "generated_value",
                   "gold_value", "error", "is_correct"]
        with RESULTS_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for model in MODELS:
                llm = ChatOllama(model=model, temperature=TEMPERATURE)
                for qid, question in enumerate(QUESTIONS, start=1):
                    row = dict.fromkeys(columns, "")
                    row.update(qid=qid, prompt=question, model=model, is_correct=False)
                    try:
                        row["gold_value"] = get_number(engine, expected[qid])
                        response = llm.invoke(PROMPT.format_messages(
                            schema=schema, question=question))
                        row["generated_sql"] = clean_sql(response.content)
                        row["generated_value"] = get_number(engine, row["generated_sql"])
                        row["is_correct"] = is_correct(
                            row["generated_value"], row["gold_value"])
                    except Exception as error:
                        row["error"] = str(error)
                    writer.writerow(row)
                    file.flush()
                    print(f"{model}, question {qid}: correct={row['is_correct']}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
