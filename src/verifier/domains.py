"""Domaines fermés du harness ; aucune expression n'est fournie par le modèle."""

from hypothesis import strategies as st
from kernel.contracts import Domain


JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=40),
    lambda children: st.lists(children, max_size=8) | st.dictionaries(st.text(max_size=20), children, max_size=8),
    max_leaves=20,
)
DOMAINS = {
    Domain.small_ints: st.integers(min_value=-1000, max_value=1000),
    Domain.floats_finite: st.floats(allow_nan=False, allow_infinity=False),
    Domain.text_unicode: st.text(max_size=100),
    Domain.json_values: JSON_VALUES,
    Domain.paths: st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=12),
        min_size=1,
        max_size=4,
    ).map("/".join),
}

# expressions fixes équivalentes, embarquées dans le script autonome et testées par domaine
DOMAIN_CODE = {
    Domain.small_ints: "st.integers(min_value=-1000, max_value=1000)",
    Domain.floats_finite: "st.floats(allow_nan=False, allow_infinity=False)",
    Domain.text_unicode: "st.text(max_size=100)",
    Domain.json_values: (
        "st.recursive(st.none() | st.booleans() | st.integers() | "
        "st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=40), "
        "lambda children: st.lists(children, max_size=8) | "
        "st.dictionaries(st.text(max_size=20), children, max_size=8), max_leaves=20)"
    ),
    Domain.paths: (
        "st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', "
        "min_size=1, max_size=12), min_size=1, max_size=4).map('/'.join)"
    ),
}
