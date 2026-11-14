"""A small read-only FastHTML app on top of an SQLite database.

Run locally:   uv run main.py           (then open http://localhost:8000)
On Nebari:     uv run main.py {port}    (Nebari fills in the port)
"""

import random
import sqlite3
import sys
from pathlib import Path

from fasthtml.common import (
    A, Article, Button, Div, P, Small, Table, Tbody, Td, Th,
    Thead, Titled, Tr, fast_app, serve,
)

DB = Path(__file__).parent / "data.db"

SEED = [
    ("All models are wrong, but some are useful.", "George E. P. Box", "statistics"),
    ("Far better an approximate answer to the right question than an exact answer to the wrong question.", "John Tukey", "statistics"),
    ("The best thing about being a statistician is that you get to play in everyone's backyard.", "John Tukey", "statistics"),
    ("To consult the statistician after an experiment is finished is often merely to ask him to conduct a post mortem examination.", "R. A. Fisher", "statistics"),
    ("No causation without manipulation.", "Paul Holland", "causal inference"),
    ("Premature optimization is the root of all evil.", "Donald Knuth", "programming"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Abelson and Sussman", "programming"),
    ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan", "programming"),
    ("There are only two hard things in computer science: cache invalidation and naming things.", "Phil Karlton", "programming"),
    ("Simple things should be simple, complex things should be possible.", "Alan Kay", "programming"),
]

# The web app only reads. Visitors can come from the open internet, so it
# offers no route that writes. Add rows from a JupyterLab terminal instead:
#   python -c "import sqlite3; c = sqlite3.connect('data.db'); c.execute('insert into quotes (text, author, topic) values (?, ?, ?)', ('Hello', 'Me', 'demo')); c.commit()"

# Columns the user may sort by, mapped to SQL. Never put user input into SQL directly.
SORTS = {
    "author": "author, text",
    "topic": "topic, author",
    "length": "length(text)",
}


def db(readonly=True):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True) if readonly else sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup():
    with db(readonly=False) as con:
        con.execute("create table if not exists quotes (id integer primary key, text text not null, author text not null, topic text not null)")
        if con.execute("select count(*) from quotes").fetchone()[0] == 0:
            con.executemany("insert into quotes (text, author, topic) values (?, ?, ?)", SEED)


def quotes(sort="author", topic=None):
    sql = "select * from quotes"
    args = []
    if topic:
        sql += " where topic = ?"
        args.append(topic)
    rows = db().execute(f"{sql} order by {SORTS.get(sort, SORTS['author'])}", args).fetchall()
    return [dict(r) for r in rows]


def topics():
    return [r[0] for r in db().execute("select distinct topic from quotes order by topic")]


# All URLs below are relative ("table", not "/table"). Nebari serves the app
# under /user/NAME/APP/, so a leading slash would point outside the app.
def table(rows, note=""):
    header = Tr(*[Th(A(label, hx_get=f"table?sort={key}", hx_target="#quotes")) for key, label in
                  [("author", "Author ↕"), ("topic", "Topic ↕"), ("length", "Quote (sort by length) ↕")]])
    body = [Tr(Td(r["author"]), Td(r["topic"]), Td(r["text"])) for r in rows]
    return Div(Small(note) if note else "", Table(Thead(header), Tbody(*body)), id="quotes")


app, rt = fast_app()
setup()


@rt("/")
def index():
    buttons = Div(
        Button("Shuffle", hx_get="shuffle", hx_target="#quotes"),
        Button("Random topic", hx_get="random-topic", hx_target="#quotes", cls="secondary"),
        Button("Show all", hx_get="table", hx_target="#quotes", cls="outline"),
        style="display:flex; gap:0.5rem; flex-wrap:wrap",
    )
    return Titled(
        "Nebari app example",
        P("Quotes stored in SQLite. Click a column header to sort."),
        Article(Div(id="pick"), Button("Random quote", hx_get="random", hx_target="#pick")),
        buttons,
        table(quotes()),
    )


@rt("/table")
def get_table(sort: str = "author"):
    return table(quotes(sort), f"Sorted by {sort}")


@rt("/shuffle")
def shuffle():
    rows = quotes()
    random.shuffle(rows)
    return table(rows, "Shuffled")


@rt("/random-topic")
def random_topic():
    topic = random.choice(topics())
    return table(quotes(topic=topic), f"Topic: {topic}")


@rt("/random")
def random_quote():
    r = random.choice(quotes())
    return Div(P(f"“{r['text']}”"), Small(f"— {r['author']}"), id="pick")



if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    serve(host="0.0.0.0", port=port, reload=False)
