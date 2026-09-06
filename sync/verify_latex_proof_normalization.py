#!/usr/bin/env python3
"""Regression: catalogue proof normalization must preserve reference keys."""
from generate_latex_catalog import normalize_proof_latex


def main() -> None:
    protected = [
        r'\ref{val:minimum_teaching_set_size_singleton_cosingleton}',
        r'\eqref{eq:some_long_label}',
        r'\cref{prop:first_label,prop:second_label}',
        r'\Cref{prop:first_label}',
        r'\autoref{sec:a_b}',
        r'\cite[Theorem 2]{author_long_key}',
        r'\citep[see][p. 2]{author_long_key}',
        r'\citet{author_long_key}',
        r'\ref*{val:some_long_label}',
        r'$x_i=2^n$', r'\(x_i=2^n\)', r'\[x_i=2^n\]',
    ]
    for text in protected:
        assert normalize_proof_latex(text) == text
    for text in protected[:9]:
        assert normalize_proof_latex('Use ' + text + ' and 2^n.') == 'Use ' + text + ' and $2^n$.'
    assert normalize_proof_latex('See sync/verify_example.py.') == r'See sync/verify\_example.py.'
    print('Proof normalization: 12 protected forms, 9 mixed-prose cases and path control passed.')


if __name__ == '__main__':
    main()
