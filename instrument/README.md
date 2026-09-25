# Frozen instrument documentation

The two `.txt` files are exact template literals from the historical coding
scripts. Their double JSON braces are intentional for Python `str.format`.
Fill only `venue`, `year`, `title`, and `abstract`; the historical pipeline used
the first 2,000 abstract characters. Prompts include operational and sometimes
interpretive wording present at measurement time; documenting them verbatim
does not endorse their framing as a demonstrated mechanism.

`m1_parser.py` and `penetration_parser.py` preserve the original `_extract_json`
and `_validate` functions and label vocabularies. Call them explicitly if
examining independently obtained responses. They do not send requests or read
credentials. M1 validation normalizes entity strings and may coerce values;
this is the historical behavior, not a new stricter instrument.

The two `*_output.schema.json` files document the instructed response shape;
they are not retroactively imposed on the historical, more permissive parsers.
Raw responses are not redistributed, because reasons or extracted entities can
quote licensed text. Frozen categorical labels suffice for default analyses.

`measurement_rules.json` records the keyword screens and ordered application
topic patterns extracted from the current data-export source. Reapplying these
rules requires lawfully obtained source texts/controlled terms, which are not
distributed. Frozen paper-level flags and topic buckets support the default
offline calculation.

`prompt_provenance.json` records source hashes and extraction method. The
exporter reads Python via AST; it never imports or executes the private coding
scripts. `provider_config.example.json` is a documentation schema with null
provider settings, not a working configuration or an instruction to call an API.

This archive reproduces analysis of frozen labels. It does not distribute raw
LLM responses (which may quote source texts) or promise identical predictions
from a future service call.
