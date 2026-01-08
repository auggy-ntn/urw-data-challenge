"""Project wide constants file."""

# CSV parameters
CSV_SEPARATOR = ","
CSV_ENCODING = "latin-1"
MISSING_VALUES = ["", "NA", "NaN", None]

CSV_PARAMS = {
    "sep": CSV_SEPARATOR,
    "encoding": CSV_ENCODING,
    "na_values": MISSING_VALUES,
}

# Date format
DATE_FORMAT = "%d/%m/%Y"
